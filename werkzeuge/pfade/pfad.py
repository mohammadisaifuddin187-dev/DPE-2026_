#!/usr/bin/env python3
# Pfade selbst durchgehen: spielt die Rollen, die es noch nicht gibt (Worker, Lieferant, Pflege-App, Team 3),
# damit eine Instanz von T2_Materialversorgung Schritt für Schritt durch CIB seven läuft.
# Du entscheidest an jedem Haltepunkt, welchen Weg die Instanz nimmt. Nur Python 3 nötig (keine Zusatzpakete).
# Verantwortlich: Amar
#
#   python3 pfad.py einrichten           Modelle aus dem Repo deployen + Gruppe "pruefstelle" für demo anlegen
#   python3 pfad.py start [art]          neue Instanz starten (art: manuell = Standard, bedingt, timer) und loslegen
#   python3 pfad.py weiter [instanz-id]  die zuletzt gestartete (oder eine beliebige, z. B. echt gestartete) Instanz weiterspielen
#   python3 pfad.py status               zeigen, wo die Instanz gerade steht
#   python3 pfad.py aufraeumen           alle laufenden Team-2-Instanzen löschen (fragt vorher)
#   ... --details                        alle Elemente, alle Variablen und IDs zeigen (statt der Kurzfassung)
#   ... --alles-simulieren               die Liste ECHT ignorieren und alles simulieren (echte Worker vorher beenden!)
#
# Windows: statt "python3 pfad.py" einfach "pfad" (pfad.cmd im selben Ordner). Anleitung: README.md
# Umgebung: CIB_URL (Standard http://localhost:8080/engine-rest), REPO (Standard: das Repo, in dem diese Datei liegt)
import base64, glob, json, os, sys, time, uuid, urllib.error, urllib.request, xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------------------------------------------
# ECHT: was es schon wirklich gibt. pfad.py simuliert diese Topics/Nachrichten NICHT mehr, sondern wartet auf sie.
# Regel: Wer einen Worker (Topic) oder einen echten Nachrichten-Sender fertig hat, trägt ihn hier im selben PR ein.
# Eine Zeile pro Eintrag (weniger Merge-Konflikte). Mögliche Namen: Schlüssel von TOPICS und NACHRICHTEN unten.
# ---------------------------------------------------------------------------------------------------------------
ECHT = {
    # "t2-vorgang-pruefen",                   # Beispiel: Worker Prozesslogik (Saifudin, #7)
    # "Lieferant_Bestellantwort_Team2",       # Beispiel: Camel leitet die Lieferantenantwort weiter (Amar, #15/#16)
    "t2-bestellung-senden",                   # Bestellung in die Queue (Amar, #14)
}

R = os.environ.get("CIB_URL", "http://localhost:8080/engine-rest")
REPO = os.path.abspath(os.path.expanduser(os.environ.get("REPO", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))))
MERKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".aktuelle_instanz")
AUTH = "Basic " + base64.b64encode(b"demo:demo").decode()
VORAUSWAHL = []  # nur für automatische Läufe: --wahl 1,2,1
CMD = "pfad" if os.name == "nt" else "python3 pfad.py"

sys.stdout.reconfigure(errors="replace")  # Konsole ohne UTF-8: ? statt Absturz bei ✓ ⏳
if os.name == "nt": os.system("")  # schaltet im Windows-Konsolenfenster die Farbcodes ein
FETT, GRUEN, GELB, BLAU, ROT, AUS = ("\033[1m", "\033[32m", "\033[33m", "\033[36m", "\033[31m", "\033[0m") \
    if sys.stdout.isatty() and not os.environ.get("NO_COLOR") else ("",) * 6

def call(method, path, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    req = urllib.request.Request(R + path, method=method, data=data, headers={"Content-Type": ctype, "Authorization": AUTH})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            t = r.read().decode()
            return json.loads(t) if t else None
    except urllib.error.HTTPError as e:
        sys.exit(f"{ROT}Fehler von CIB seven bei {method} {path}: {e.code} {e.read().decode()[:500]}{AUS}")
    except urllib.error.URLError:
        sys.exit(f"{ROT}CIB seven nicht erreichbar ({R}). Mac: läuft der Docker-Container 'cibseven'? "
                 f"Windows: ist das Fenster von cib_starten.cmd offen?{AUS}")

def typ(v): return "Boolean" if isinstance(v, bool) else "Integer" if isinstance(v, int) else "Double" if isinstance(v, float) else "String"
def vars_(m): return {k: {"value": v, "type": typ(v)} for k, v in m.items()}

# ---------------------------------------------------------------------------------------------------------------
# Haltepunkte: was hier in echt passiert und welche Wege du wählen kannst  (Text, Variablen, wohin es führt)
# ---------------------------------------------------------------------------------------------------------------
STANDARD_BESTAND = {"istBestand": 30, "bestandMenge": 30, "verbrauchProTag": 4.0, "tageBisPruefung": 10,
                    "lieferzeitTage": 3, "mindestbestand": 40, "zielbestand": 120, "verbrauchssprung": False}
STANDARD_VORSCHLAG = {"produktHinterlegt": True, "produktGewechselt": False, "lieferantGewechselt": False,
                      "preisGesamt": 74.70, "preisgrenze": 75.0, "bestellmenge": 90, "zielbestand": 120,
                      "bestellvorschlag": "{\"produktId\":\"TP-M\",\"produktName\":\"Testprodukt M\",\"lieferantId\":\"L-01\",\"packungen\":3,\"stueck\":90,\"preisGesamt\":74.70}",
                      "freigabeHandlung": "3 Packungen Testprodukt M", "freigabeFolgen": "Vorrat reicht ca. 7 Tage"}
def mit(basis, **neu): d = dict(basis); d.update(neu); return d
NUR_ABSCHLIESSEN = [("Erledigt melden (Worker schließt die Aufgabe ab)", {}, "weiter im Modell")]

TOPICS = {
    "t2-vorgang-pruefen": ("Worker Prozesslogik (Saifudin, #7): sucht per REST, ob für denselben Business Key schon ein Vorgang läuft.", [
        ("Kein offener Vorgang", {"vorgangOffen": False}, "weiter zu 'Verbrauch und Reichweite berechnen'"),
        ("Vorgang ist schon offen", {"vorgangOffen": True}, "ENDE 'Vorgang bereits offen' (End_Offen)")]),
    "t2-reichweite-berechnen": ("Worker Prozesslogik (Saifudin, #7): rechnet aus der DB Bestand, Verbrauch und Reichweite. Danach entscheidet die DMN 'Nachversorgungsbedarf' automatisch.", [
        ("Bestand 30 Stück (unter Mindestbestand 40)", STANDARD_BESTAND, "DMN sagt: Nachversorgung nötig -> Teilprozess Bestellfreigabe"),
        ("Bestand 110 Stück (genug Vorrat)", mit(STANDARD_BESTAND, istBestand=110, bestandMenge=110), "DMN sagt: nicht nötig -> ENDE 'Bestand ausreichend' (End_Ausreichend)"),
        ("Bestand 30 Stück + Verbrauchssprung", mit(STANDARD_BESTAND, verbrauchssprung=True), "Nachversorgung nötig, später schickt die DMN 'Berechtigungsregel' den Fall an die Prüfstelle (Tasklist!)")]),
    "t2-vorschlag-erstellen": ("Worker Prozesslogik (Saifudin, #8): erstellt Produkt + Menge. Danach entscheidet die DMN 'Berechtigungsregel' den Freigabeweg (AUTOMATISCH / KUNDENFREIGABE / PRUEFUNG).", [
        ("Normaler Vorschlag: 74,70 EUR, Preisgrenze 75 EUR", STANDARD_VORSCHLAG, "DMN: AUTOMATISCH -> Bestellung freigegeben (außer es gab einen Verbrauchssprung -> Prüfstelle)"),
        ("Zu teuer: 82,50 EUR, Preisgrenze 75 EUR", mit(STANDARD_VORSCHLAG, preisGesamt=82.5), "DMN: KUNDENFREIGABE -> Teilprozess Kundenentscheidung"),
        ("Produkt nicht im Profil hinterlegt", mit(STANDARD_VORSCHLAG, produktHinterlegt=False), "DMN: PRUEFUNG -> Benutzeraufgabe 'Grenzfall prüfen' in der Tasklist")]),
    "t2-freigabeanfrage-senden": ("Benachrichtigungs-Worker (Saifudin, #11): schreibt die Freigabeanfrage ins App-Postfach der Pflegeperson.", NUR_ABSCHLIESSEN),
    "t2-nachfassen-beauftragen": ("Kommunikationsauftrag an Team 3 (Amar, #17: Stub/Queue). Danach wartet die Instanz noch einmal auf die Antwort.", NUR_ABSCHLIESSEN),
    "t2-bestellung-senden": ("DEINE TASK #14: Worker legt die Bestellung in die ActiveMQ-Queue, Camel (#15) verteilt sie an den Lieferanten.", NUR_ABSCHLIESSEN),
    "t2-ersatzoption-pruefen": ("Worker Prozesslogik (Saifudin, #8): gibt es eine hinterlegte Ersatzoption (höchstens 2 Bestellversuche)?", [
        ("Ersatz möglich", {"ersatzMoeglich": True}, "ENDE Teilprozess 'Ersatz erforderlich' -> Hauptprozess geht zurück zur Bestellfreigabe (Schleife)"),
        ("Kein Ersatz möglich", {"ersatzMoeglich": False}, "ENDE 'Keine Bestellung möglich' (End_KeineBestellung)")]),
    "t2-lieferbestaetigung-anfordern": ("Benachrichtigungs-Worker (Saifudin, #11): bittet die Pflegeperson in der App, die Lieferung zu bestätigen.", NUR_ABSCHLIESSEN),
    "t2-klaerung-beauftragen": ("Klärungsauftrag an Team 3 (Amar, #17: Stub/Queue). Danach wartet die Instanz auf das Klärungsergebnis.", NUR_ABSCHLIESSEN),
    "t2-klaerungsfall-uebergeben": ("Fall geht ungeklärt an Team 3 / Backoffice.", NUR_ABSCHLIESSEN),
    "t2-bestand-fortschreiben": ("Worker Prozesslogik (Saifudin, #10): schreibt den neuen Bestand in die DB.", NUR_ABSCHLIESSEN),
    "t2-nachweis-uebergeben": ("Liefernachweis an Team 1 übergeben.", NUR_ABSCHLIESSEN),
    "t2-ergebnis-mitteilen": ("Benachrichtigungs-Worker (Saifudin, #11): teilt das Ergebnis in der App mit (auch bei jedem Abbruch, kein stummes Ende).", NUR_ABSCHLIESSEN),
}
FRIST = object()
NACHRICHTEN = {
    "PflegeApp_Kundenentscheidung_Team2": ("Pflege-App (Erion, #12): Die Pflegeperson antwortet auf die Freigabeanfrage. Frist 3 Tage.", [
        ("Freigeben", {"entscheidung": "FREIGEBEN"}, "Bestellung freigegeben -> Bestellabwicklung"),
        ("Ablehnen", {"entscheidung": "ABLEHNEN"}, "ENDE 'Bestellung nicht freigegeben'"),
        ("Aufschieben", {"entscheidung": "AUFSCHIEBEN"}, "ENDE 'Bestellung aufgeschoben'"),
        ("Ändern (neuer Vorschlag, höchstens 3 Vorschläge)", {"entscheidung": "AENDERN"}, "zurück zu 'Produkt und Menge vorschlagen'; beim 3. Mal ENDE 'nicht freigegeben'"),
        ("Keine Antwort: Frist (3 Tage) sofort ablaufen lassen", FRIST, "1. Mal: Nachfassen über Team 3, dann neu warten; 2. Mal: ENDE 'nicht freigegeben'")]),
    "Lieferant_Bestellantwort_Team2": ("Lieferant (simuliert, Amar #16): antwortet über JMS -> Camel -> POST /message. Frist 1 Tag.", [
        ("Bestellung bestätigt", {"bestellantwortStatus": "BESTAETIGT"}, "Teilprozess Lieferprüfung"),
        ("Nicht verfügbar", {"bestellantwortStatus": "NICHT_VERFUEGBAR"}, "'Ersatzoption prüfen'"),
        ("Keine Antwort: Frist (1 Tag) sofort ablaufen lassen", FRIST, "1. Mal: Nachfassen, dann neu warten; 2. Mal: 'Ersatzoption prüfen'")]),
    "Lieferant_Versandmeldung_Team2": ("Lieferant (simuliert, Amar #16): meldet den Versand. Frist 5 Tage.", [
        ("Versandmeldung kommt", {}, "'Lieferbestätigung anfordern'"),
        ("Keine Versandmeldung: Frist (5 Tage) sofort ablaufen lassen", FRIST, "Klärung über Team 3")]),
    "PflegeApp_Lieferbestaetigung_Team2": ("Pflege-App (Erion, #12): Pflegeperson bestätigt die Lieferung. Frist 3 Tage.", [
        ("Richtig geliefert", {"lieferbefund": "RICHTIG"}, "ENDE Teilprozess 'Lieferung abgeschlossen' -> Bestand fortschreiben"),
        ("Teilweise geliefert", {"lieferbefund": "TEILWEISE"}, "Klärung über Team 3"),
        ("Falsch geliefert", {"lieferbefund": "FALSCH"}, "Klärung über Team 3"),
        ("Keine Bestätigung: Frist (3 Tage) sofort ablaufen lassen", FRIST, "Klärung über Team 3")]),
    "Team3_Klaerungsergebnis_Team2": ("Team 3 (Stub, Amar #17): Ergebnis der Klärung. Frist 7 Tage.", [
        ("Nachlieferung bestätigt", {"klaerungsergebnis": "NACHLIEFERUNG_BESTAETIGT"}, "ENDE Teilprozess 'Lieferung abgeschlossen'"),
        ("Nicht geklärt", {"klaerungsergebnis": "NICHT_GEKLAERT"}, "'Klärungsfall übergeben' -> ENDE 'Lieferung ungeklärt'"),
        ("Keine Antwort: Frist (7 Tage) sofort ablaufen lassen", FRIST, "'Klärungsfall übergeben' -> ENDE 'Lieferung ungeklärt'")]),
}

# ---------------------------------------------------------------------------------------------------------------
def baum(pi):
    ids = [h["id"] for h in call("GET", f"/history/process-instance?rootProcessInstanceId={pi}")]
    return ids or [pi]

def prozessname(defid): return defid.split(":")[0]

def waehle(optionen):
    for i, (text, _, folge) in enumerate(optionen, 1):
        print(f"   {FETT}{i}{AUS}) {text}\n      {BLAU}-> {folge}{AUS}")
    frage = f"   Deine Wahl (1-{len(optionen)}{', Enter = 1' if len(optionen) == 1 else ''}, q = Pause): "
    while True:
        if VORAUSWAHL: e = VORAUSWAHL.pop(0); print(frage + e)
        else: e = input(frage).strip().lower()
        if e == "" and len(optionen) == 1: e = "1"
        if e == "q": print(f"Pausiert. Weiter mit:  {CMD} weiter"); sys.exit(0)
        if e.isdigit() and 1 <= int(e) <= len(optionen):
            print(f"   {GRUEN}gewählt: {optionen[int(e) - 1][0]}{AUS}")
            return optionen[int(e) - 1]

def zeit(aid):  # Activity-Instance-IDs sind zeitbasierte UUIDs -> exakte Reihenfolge, auch innerhalb derselben Millisekunde
    u = aid.split(":")[-1].split("-"); return (int(u[2], 16) & 0x0fff) << 48 | int(u[1], 16) << 32 | int(u[0], 16)

AUFGERUFEN = {"CA_Bestellfreigabe": "T2_Bestellfreigabe", "CA_Bestellabwicklung": "T2_Bestellabwicklung",
              "CA_Lieferpruefung": "T2_Lieferpruefung", "CA_KE": "T2_Kundenentscheidung"}
gesehen = set()      # bereits ausgegebene Activity-Instanzen
gesehen_var = set()  # bereits ausgewertete Variablen-Änderungen
STAND = {}           # letzter bekannter Wert je Variable (für "alt -> neu" und die Statuszeile)
DETAILS = False      # --details: alle Elemente, alle Variablen, IDs
LABEL = {"vorgangOffen": "Vorgang schon offen", "istBestand": "Bestand", "reichweiteTage": "Reichweite Tage",
         "verbrauchssprung": "Verbrauchssprung", "nachversorgungErforderlich": "nachbestellen", "bestellvorschlag": "Vorschlag",
         "freigabeweg": "Freigabeweg", "freigabeBegruendung": "weil", "ersatzMoeglich": "Ersatz möglich", "entscheidung": "Kunde",
         "pruefergebnis": "Prüfstelle", "pruefbegruendung": "Begründung", "bestellantwortStatus": "Lieferant",
         "lieferbefund": "Lieferung", "klaerungsergebnis": "Klärung", "vorgangszustand": "Vorgang"}
HINWEIS = {"t2-freigabeanfrage-senden": "Freigabeanfrage ins App-Postfach", "t2-lieferbestaetigung-anfordern": "Bitte um Bestätigung ins App-Postfach",
           "t2-ergebnis-mitteilen": "Ergebnis ins App-Postfach", "t2-bestellung-senden": "Bestellung an den Lieferanten",
           "t2-nachfassen-beauftragen": "Nachfassen bei Team 3", "t2-klaerung-beauftragen": "Klärung bei Team 3",
           "t2-klaerungsfall-uebergeben": "Fall ungeklärt übergeben", "t2-nachweis-uebergeben": "Liefernachweis an Team 1"}

def kurz(v):
    t = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    return t if len(t) <= 70 else t[:67] + "..."

def wert(n, v):
    if isinstance(v, bool): return "ja" if v else "nein"
    if n == "preisGesamt": return f"{v:.2f} €".replace(".", ",")
    if n == "bestellvorschlag":
        try: b = json.loads(v); return f"{b['produktName']}, {b['packungen']} Pck., " + f"{b['preisGesamt']:.2f} €".replace(".", ",")
        except (ValueError, KeyError, TypeError): pass
    return kurz(v)

def zahl(v):
    return f"{v:g}".replace(".", ",") if isinstance(v, float) else str(v)

def euro(v): return f"{v:.2f} €".replace(".", ",")

def warum(aid, st):
    """Eine Zeile Begründung zu Rechnungen und Regeln, aus den Variablen zum Zeitpunkt der Aufgabe."""
    g = st.get
    try:
        if aid == "T_Offen":
            return "für diesen Haushalt und dieses Produkt läuft schon eine Instanz" if g("vorgangOffen") \
                else "keine andere laufende Instanz für diesen Haushalt und dieses Produkt"
        if aid == "SB_Reichweite":
            t = f"Reichweite = Bestand {g('istBestand')} ÷ {zahl(g('verbrauchProTag'))} Stück/Tag = {g('reichweiteTage')} Tage"
            return t + ("; Sprung: zuletzt beobachteter Verbrauch ≥ 1,5 × Annahme" if g("verbrauchssprung") else "")
        if aid == "SB_Bedarf":
            tage = g("tageBisPruefung") + g("lieferzeitTage")
            rest = g("istBestand") - g("verbrauchProTag") * tage
            t = (f"nach {g('tageBisPruefung')} + {g('lieferzeitTage')} Tagen blieben {g('istBestand')} − {zahl(g('verbrauchProTag'))} × {tage} = "
                 f"{zahl(rest)} Stück, Mindestbestand {g('mindestbestand')}")
            return t + (f" → zu wenig, Bedarf {g('zielbestand')} − {g('istBestand')} = {g('nachversorgungsbedarf')}" if rest < g("mindestbestand") else " → reicht")
        if aid == "T_Vorschlag":
            b = json.loads(g("bestellvorschlag"))
            t = (f"Zielbestand {g('zielbestand')} − Bestand {g('istBestand')} = {g('zielbestand') - g('istBestand')} Stück → "
                 f"{b['packungen']} Pck. ({b['stueck']} Stück), Preis {euro(b['preisGesamt'])}")
            return t + (f"; Ersatzprodukt, weil: {g('ersatzGrund') or 'bevorzugtes Produkt nicht lieferbar'}" if g("produktGewechselt") else "")
        if aid == "T_Regel":
            p, gr, m, z = g("preisGesamt"), g("preisgrenze"), g("bestellmenge"), g("zielbestand")
            abw = [n for n, ja in (("Produkt nicht hinterlegt", not g("produktHinterlegt")), ("Verbrauchssprung", g("verbrauchssprung")),
                                   (f"Preis {euro(p)} > Grenze {euro(gr)}", p > gr), ("Ersatzprodukt", g("produktGewechselt")),
                                   ("anderer Lieferant", g("lieferantGewechselt")), (f"Menge {m} > Zielbestand {z}", m > z)) if ja]
            if not abw: return f"keine Abweichung (Preis {euro(p)} ≤ {euro(gr)}, Menge {m} ≤ {z}, Produkt hinterlegt, kein Sprung, kein Wechsel) → AUTOMATISCH"
            return "Abweichung: " + " · ".join(abw) + f" → {g('freigabeweg')}" + (" (die strengste Regel gewinnt)" if len(abw) > 1 else "")
        if aid == "T_Ersatz":
            n = g("anzahlBestellversuche")
            return f"Ersatz im Profil hinterlegt, Bestellversuch {n} von höchstens 2" if g("ersatzMoeglich") \
                else (f"schon {n} Bestellversuche (höchstens 2)" if n and n >= 2 else "keine verfügbare Ersatzoption hinterlegt")
    except (TypeError, ValueError, KeyError):
        return None  # Variablen fehlen (z. B. simulierter Schritt mit anderen Werten): dann keine Begründung
    return None

def ohne_t2(proz): return proz.replace("T2_", "")

LETZTER_STAND = None
BLOCK_OFFEN = False  # "Was passiert ist:" schon ausgegeben und seitdem keine neue Überschrift
def statuszeile():
    t = []
    if STAND.get("istBestand") is not None: t.append(f"Bestand {STAND['istBestand']}")
    if STAND.get("reichweiteTage") is not None: t.append(f"Reichweite {STAND['reichweiteTage']} Tage")
    if STAND.get("bestellvorschlag"): t.append("Vorschlag " + wert("bestellvorschlag", STAND["bestellvorschlag"]))
    if STAND.get("freigabeweg"): t.append(f"Freigabe {STAND['freigabeweg']}")
    if STAND.get("anzahlBestellversuche"): t.append(f"Bestellversuch {STAND['anzahlBestellversuche']}")
    if STAND.get("vorgangszustand"): t.append(STAND["vorgangszustand"])
    global LETZTER_STAND
    if t and t != LETZTER_STAND: print(f"   {FETT}Stand:{AUS} " + " · ".join(t))  # nur wenn sich etwas geändert hat
    LETZTER_STAND = t

def neu_gelaufen(pi, zeigen=True):
    """Zeigt, was seit der letzten Eingabe passiert ist: welche Aufgabe, wer sie erledigt hat, was dabei herauskam."""
    zeilen, aenderungen, log, alle_ai = [], [], {}, set()
    for i in baum(pi):
        for a in call("GET", f"/history/activity-instance?processInstanceId={i}&sortBy=startTime&sortOrder=asc"):
            alle_ai.add(a["id"])
            if a["id"] in gesehen or a["endTime"] is None: continue
            gesehen.add(a["id"])
            if not a["activityName"] and a["activityType"] == "exclusiveGateway": continue  # Zusammenführung ohne Namen
            if a.get("canceled") and not DETAILS: continue  # z. B. Empfang, den die abgelaufene Frist beendet hat
            zeilen.append((zeit(a["id"]), prozessname(a["processDefinitionId"]), a["activityType"], a["activityName"] or a["activityId"], a["activityId"], a["id"]))
        aenderungen += [d for d in call("GET", f"/history/detail?processInstanceId={i}&variableUpdates=true") if d["id"] not in gesehen_var]
        log.update({l["activityInstanceId"]: (l["workerId"], l["topicName"]) for l in call("GET", f"/history/external-task-log?processInstanceId={i}&successLog=true")})
    zeilen.sort()
    # Eine Call Activity ist erst fertig, wenn ihr Teilprozess fertig ist: hinter dessen letztes Element schieben
    for ca in [z for z in zeilen if z[2] == "callActivity"]:
        kind = AUFGERUFEN.get(ca[4]); zeilen.remove(ca)
        pos = max([i for i, z in enumerate(zeilen) if z[1] == kind], default=-1)
        zeilen.insert(pos + 1, ca)
    gesetzt, schnapp = {}, {}  # Activity-Instanz -> [(name, alt, neu)] bzw. Variablen nach dieser Aufgabe
    for d in sorted(aenderungen, key=lambda d: d["time"]):
        if d.get("activityInstanceId") not in gesehen and d.get("activityInstanceId") in alle_ai: continue  # Aufgabe läuft noch: später zeigen
        gesehen_var.add(d["id"])
        n, v, vorher = d["variableName"], d["value"], STAND.get(d["variableName"])
        STAND[n] = v
        schnapp[d.get("activityInstanceId")] = dict(STAND)
        if v is not None: gesetzt.setdefault(d.get("activityInstanceId"), []).append((n, vorher, v))
    if not (zeigen and zeilen): return
    ausgabe = []
    for _, proz, typ_, name, aid, ai in zeilen:
        w, topic = log.get(ai, (None, None))
        if DETAILS:
            ausgabe.append(f"{GELB}     · {proz:24} {typ_:22} {name}{AUS}  [{aid}{', ' + w if w else ''}]")
            for n, alt, v in gesetzt.get(ai, []):
                if typ_ != "callActivity": ausgabe.append(f"         {n}: {kurz(alt)} -> {kurz(v)}" if alt not in (None, v) else f"         {n} = {kurz(v)}")
            continue
        if typ_ == "startEvent" and proz != "T2_Materialversorgung":
            ausgabe.append(f"     {BLAU}» hinein in Teilprozess {ohne_t2(proz)}{AUS}")
        elif typ_ == "noneEndEvent" and proz != "T2_Materialversorgung":
            ausgabe.append(f"     {BLAU}« {ohne_t2(proz)} fertig: {name}{AUS}")
        elif "Timer" in typ_:
            ausgabe.append(f"     ⏰ Frist abgelaufen: {name}")
        elif typ_ in ("serviceTask", "sendTask", "receiveTask", "businessRuleTask", "userTask") or (typ_ == "messageEndEvent" and w):
            von = "echter Worker" if w and w != "pfad-py" else "pfad.py" if w else "DMN" if typ_ == "businessRuleTask" \
                else "Tasklist" if typ_ == "userTask" else "Nachricht" if typ_ == "receiveTask" else ""
            info = [f"{LABEL[n]}: {wert(n, v)}" + (f" (vorher {wert(n, alt)})" if alt not in (None, v) and n not in ("freigabeBegruendung", "pruefbegruendung") else "")
                    for n, alt, v in gesetzt.get(ai, []) if n in LABEL]
            if not info and topic in HINWEIS: info = [HINWEIS[topic]]
            farbe = GRUEN if von == "echter Worker" else BLAU
            ausgabe.append(f"     ✓ {name:36} {farbe}{('[' + von + ']') if von else '':16}{AUS} {', '.join(info)}")
            grund = warum(aid, schnapp.get(ai, STAND))
            if grund: ausgabe.append(f"       {' ':36} {' ':16} {GELB}↳ {grund}{AUS}")
    global BLOCK_OFFEN
    if ausgabe: print((f"{GELB}   Was passiert ist:{AUS}\n" if not BLOCK_OFFEN else "") + "\n".join(ausgabe)); BLOCK_OFFEN = True
    statuszeile()

def haltepunkt(pi):
    ids = baum(pi)
    q = ",".join(ids)
    ext = call("GET", f"/external-task?processInstanceIdIn={q}&active=true")  # auch gesperrte: die hält gerade ein echter Worker
    if ext: return "ext", ext[0]
    ut = call("GET", f"/task?processInstanceIdIn={q}&active=true")
    if ut: return "user", ut[0]
    for i in ids:
        for s in call("GET", f"/event-subscription?eventType=message&processInstanceId={i}"):
            if s.get("executionId"):
                s["processDefinitionId"] = call("GET", f"/process-instance/{i}")["definitionId"]
                return "msg", s
    return None, None

def aktivitaet_name(proc_inst, activity_id):
    h = call("GET", f"/history/activity-instance?processInstanceId={proc_inst}&activityId={activity_id}&unfinished=true")
    return h[0]["activityName"] if h else activity_id

ALLES = False  # --alles-simulieren: ECHT ignorieren
def ist_echt(name): return name in ECHT and not ALLES

def auf_echt_warten(was, offen):
    """Wartet, bis ein echter Worker/Sender den Haltepunkt erledigt hat. offen() liefert, was noch offen ist."""
    global BLOCK_OFFEN
    sek = 0
    while True:
        o = offen()
        if not o: return
        if sek == 2: print(f"\n   ⏳ {was} ... (Strg+C = Pause)"); BLOCK_OFFEN = False  # erst melden, wenn es wirklich dauert
        if o[0].get("retries") == 0:  # Worker hat handleFailure ohne Retries gemeldet -> Incident
            sys.exit(f"{ROT}Der echte Worker meldet einen Fehler (Incident): {o[0].get('errorMessage')}. Im Cockpit nachsehen.{AUS}")
        time.sleep(1); sek += 1

def kopf(nr, name, proz, wo, wer, technik):
    global BLOCK_OFFEN; BLOCK_OFFEN = False
    print(f"\n{FETT}━━ Schritt {nr}: {name} {AUS}{BLAU}({ohne_t2(proz)}{', Teilprozess' if wo != 'Hauptprozess' else ''}){AUS}"
          + (f"  [{technik}]" if DETAILS else ""))
    print(f"   In echt: {wer}")

def spielen(pi, fortsetzen=False):
    if fortsetzen: neu_gelaufen(pi, zeigen=False)  # Bisheriges nicht nochmal auflisten
    schritt = warte = 0
    while True:
        h = call("GET", f"/history/process-instance/{pi}")
        neu_gelaufen(pi)
        if h["state"] != "ACTIVE":
            ende = [a for a in call("GET", f"/history/activity-instance?processInstanceId={pi}&activityType=noneEndEvent")] + \
                   [a for a in call("GET", f"/history/activity-instance?processInstanceId={pi}&activityType=messageEndEvent")]
            name = ende[0]["activityName"] + f" ({ende[0]['activityId']})" if ende else h["state"]
            print(f"\n{GRUEN}{FETT}FERTIG: Hauptprozess endet in '{name}'.{AUS}")
            print(f"Im Cockpit: Prozesse -> T2_Materialversorgung -> Reiter 'Historie' (bzw. Filter auf beendete Instanzen), Instanz {pi}")
            if os.path.exists(MERKER): os.remove(MERKER)
            return
        art, x = haltepunkt(pi)
        if art is None and warte < 5:  # Instanz ist evtl. gerade fertig geworden oder ein Worker schließt gerade ab
            warte += 1; time.sleep(1); continue
        warte = 0
        if art is None:
            inc = [i for p in baum(pi) for i in call("GET", f"/incident?processInstanceId={p}")]
            sys.exit(f"{ROT}Die Instanz hängt (kein Haltepunkt gefunden). Incidents: {[i['incidentMessage'] for i in inc]}{AUS}")
        proz = prozessname(x["processDefinitionId"])
        wo = "Hauptprozess" if x["processInstanceId"] == pi else "Teilprozess (Call Activity)"
        if art == "ext":
            name = aktivitaet_name(x["processInstanceId"], x["activityId"])
            wer, optionen = TOPICS.get(x["topicName"], ("Unbekanntes Topic", NUR_ABSCHLIESSEN))
            fremd = x.get("lockExpirationTime") and x.get("workerId") != "pfad-py"
            if ist_echt(x["topicName"]) or fremd:
                auf_echt_warten(f"'{name}': warte auf echten Worker" + (f" {x['workerId']}" if fremd else ""),
                                lambda: call("GET", f"/external-task?externalTaskId={x['id']}"))
                continue
            schritt += 1
            kopf(schritt, name, proz, wo, wer, f"External Task {x['activityId']}, Topic {x['topicName']}")
            text, werte, _ = waehle(optionen)
            l = call("POST", "/external-task/fetchAndLock", {"workerId": "pfad-py", "maxTasks": 1,
                     "topics": [{"topicName": x["topicName"], "lockDuration": 60000, "processInstanceIdIn": [x["processInstanceId"]]}]})
            if not l:  # hat ein anderer Worker die Aufgabe geschnappt? Dann nochmal schauen
                print(f"{ROT}   Aufgabe war schon gesperrt (läuft ein echter Worker?). Ich schaue nochmal nach.{AUS}"); time.sleep(2); continue
            call("POST", f"/external-task/{l[0]['id']}/complete", {"workerId": "pfad-py", "variables": vars_(werte)})
        elif art == "user":
            schritt += 1
            kopf(schritt, x["name"], proz, wo, "Ein Mensch der Prüfstelle entscheidet in der Tasklist.", f"Benutzeraufgabe {x['taskDefinitionKey']}")
            print(f"   {FETT}Jetzt DU in der Tasklist:{AUS} http://localhost:8080/webapp/ -> Tasklist -> Filter 'My Group Tasks' (oder 'All Tasks')")
            print("   -> Aufgabe 'Grenzfall prüfen' öffnen -> 'Beanspruchen' -> Prüfergebnis wählen:")
            print(f"      {BLAU}'Kundenfreigabe einholen' -> Teilprozess Kundenentscheidung{AUS}")
            print(f"      {BLAU}'Nicht zulässig'          -> ENDE 'Bestellung nicht zulässig'{AUS}")
            print("   -> Begründung eintippen -> 'Abschließen'.")
            if VORAUSWAHL:  # automatischer Lauf: Aufgabe selbst erledigen
                e = VORAUSWAHL.pop(0)
                if e == "q": print(f"Pausiert. Weiter mit:  {CMD} weiter"); sys.exit(0)
                print("   Enter drücken, wenn du die Aufgabe abgeschlossen hast (q = Pause): ")
                print(f"   {GRUEN}in der Tasklist gewählt: Prüfergebnis = {'Kundenfreigabe einholen' if e == 'KUNDENFREIGABE' else 'Nicht zulässig'}{AUS}")
                call("POST", f"/task/{x['id']}/complete", {"variables": vars_({"pruefergebnis": e, "pruefbegruendung": "automatisch"})})
            else:
                while call("GET", f"/task?taskId={x['id']}"):
                    e = input("   Enter drücken, wenn du die Aufgabe abgeschlossen hast (q = Pause): ").strip().lower()
                    if e == "q": print(f"Pausiert. Weiter mit:  {CMD} weiter"); sys.exit(0)
        else:
            name = aktivitaet_name(x["processInstanceId"], x["activityId"])
            wer, optionen = NACHRICHTEN.get(x["eventName"], ("Unbekannte Nachricht", [("Senden", {}, "weiter")]))
            if ist_echt(x["eventName"]):
                auf_echt_warten(f"'{name}': warte auf echte Nachricht {x['eventName']}",
                                lambda: call("GET", f"/event-subscription?eventType=message&executionId={x['executionId']}&eventName={x['eventName']}"))
                continue
            schritt += 1
            kopf(schritt, name, proz, wo, wer, f"wartet auf Nachricht {x['eventName']}")
            text, werte, _ = waehle(optionen)
            if werte is FRIST:
                jobs = call("GET", f"/job?processInstanceId={x['processInstanceId']}&timers=true")
                call("POST", f"/job/{jobs[0]['id']}/execute")
                print("   Timer sofort ausgelöst (statt Tage zu warten).")
            else:
                call("POST", "/message", {"messageName": x["eventName"], "processInstanceId": x["processInstanceId"],
                                          "processVariables": vars_(werte)})
                if DETAILS: print(f"   Nachricht {x['eventName']} gesendet{' mit ' + str(werte) if werte else ''}.")
        if not VORAUSWAHL: time.sleep(0.3)

# ---------------------------------------------------------------------------------------------------------------
def einrichten():
    ordner = os.path.join(REPO, "prozesse", "team2")
    dateien = sorted(glob.glob(os.path.join(ordner, "*.bpmn")) + glob.glob(os.path.join(ordner, "*.dmn")))
    if len(dateien) < 7: sys.exit(f"{ROT}Im Ordner {ordner} fehlen Modelle (gefunden: {len(dateien)}). REPO=... setzen?{AUS}")
    grenze = uuid.uuid4().hex
    teile = []
    for k, v in (("deployment-name", "team2"), ("enable-duplicate-filtering", "true")):
        teile.append(f'--{grenze}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for d in dateien:
        n = os.path.basename(d)
        teile.append(f'--{grenze}\r\nContent-Disposition: form-data; name="{n}"; filename="{n}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
                     + open(d, "rb").read() + b"\r\n")
    teile.append(f"--{grenze}--\r\n".encode())
    r = call("POST", "/deployment/create", raw=b"".join(teile), ctype=f"multipart/form-data; boundary={grenze}")
    neu = list((r.get("deployedProcessDefinitions") or {}).values()) + list((r.get("deployedDecisionDefinitions") or {}).values())
    print(f"Deployment: {len(dateien)} Dateien aus {ordner}")
    print("  neu deployt: " + (", ".join(f"{d['key']} v{d['version']}" for d in neu) if neu else "nichts (unverändert, schon aktuell)"))
    if not any(g["id"] == "pruefstelle" for g in call("GET", "/group")):
        call("POST", "/group/create", {"id": "pruefstelle", "name": "Prüfstelle Team 2", "type": "WORKFLOW"})
        print("  Gruppe 'pruefstelle' angelegt")
    if not any(g["id"] == "pruefstelle" for g in call("GET", "/group?member=demo")):
        call("PUT", "/group/pruefstelle/members/demo")
        print("  Benutzer demo zur Gruppe 'pruefstelle' hinzugefügt (sieht 'Grenzfall prüfen' unter 'My Group Tasks')")
    print(f"{GRUEN}Fertig eingerichtet.{AUS} Weiter mit:  {CMD} start")

def starten(art):
    key = "PH-0001:TP-M"
    if art == "manuell":
        r = call("POST", "/message", {"messageName": "PflegeApp_Bestandsmeldung_Team2", "businessKey": key, "resultEnabled": True,
                 "processVariables": vars_({"pflegehaushaltId": "PH-0001", "produktId": "TP-M"})})
        pi = r[0]["processInstance"]["id"]
        print(f"Gestartet über Nachrichten-Startereignis 'Bestand manuell gemeldet' (PflegeApp_Bestandsmeldung_Team2)")
    elif art == "bedingt":
        r = call("POST", "/condition", {"businessKey": key, "variables": vars_({"bestandMenge": 30, "mindestbestand": 40,
                 "pflegehaushaltId": "PH-0001", "produktId": "TP-M"})})
        pi = [x for x in r if x["definitionId"].startswith("T2_Materialversorgung")][0]["id"]
        print("Gestartet über bedingtes Startereignis 'Bestand unterschritten' (bestandMenge 30 < mindestbestand 40)")
    elif art == "timer":
        d = call("GET", "/process-definition/key/T2_Materialversorgung")
        jobs = call("GET", f"/job?processDefinitionId={d['id']}&timers=true")
        if not jobs: sys.exit(f"Kein Timer-Start-Job gefunden. Erst '{CMD} einrichten'.")
        call("POST", f"/job/{jobs[0]['id']}/execute")
        pi = call("GET", f"/history/process-instance?processDefinitionId={d['id']}&startActivityId=Start_Timer&sortBy=startTime&sortOrder=desc&maxResults=1")[0]["id"]
        print("Gestartet über Timer-Startereignis 'Prüftermin erreicht (alle 10 Tage)', Timer sofort ausgelöst")
    else:
        sys.exit("Art muss manuell, bedingt oder timer sein.")
    open(MERKER, "w", encoding="utf-8").write(pi)
    print(f"Instanz {FETT}{pi}{AUS}, Business Key {key}")
    print("Tipp: Cockpit öffnen: http://localhost:8080/webapp/ -> Cockpit -> Prozesse -> T2_Materialversorgung -> Instanz anklicken")
    spielen(pi)

def aktuelle():
    if not os.path.exists(MERKER): sys.exit(f"Keine laufende Instanz gemerkt. Starte eine mit:  {CMD} start")
    return open(MERKER, encoding="utf-8").read().strip()

def status():
    pi = aktuelle()
    art, x = haltepunkt(pi)
    if art is None: print("Kein Haltepunkt (Instanz beendet?)"); return
    name = x.get("name") or aktivitaet_name(x["processInstanceId"], x["activityId"])
    print(f"Instanz {pi} steht in {prozessname(x['processDefinitionId'])} bei '{name}' ({art})")

def aufraeumen():
    laufend = [p for k in ("T2_Materialversorgung", "T2_Bestellfreigabe", "T2_Bestellabwicklung", "T2_Kundenentscheidung", "T2_Lieferpruefung")
               for p in call("GET", f"/process-instance?processDefinitionKey={k}")]
    haupt = [p for p in laufend if p["definitionId"].startswith("T2_Materialversorgung")]
    print(f"Laufende Team-2-Hauptinstanzen: {len(haupt)} (Teilprozesse werden mitgelöscht)")
    if haupt and input("Alle löschen? (j/n) ").strip().lower() == "j":
        for p in haupt: call("DELETE", f"/process-instance/{p['id']}?skipCustomListeners=true&skipSubprocesses=false")
        print("Gelöscht.")
    if os.path.exists(MERKER): os.remove(MERKER)

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--wahl" in a:
        i = a.index("--wahl"); VORAUSWAHL[:] = a[i + 1].split(","); del a[i:i + 2]
    if "--alles-simulieren" in a: ALLES = True; a.remove("--alles-simulieren")
    if "--details" in a: DETAILS = True; a.remove("--details")
    befehl = a[0] if a else "hilfe"
    try:
        if befehl == "einrichten": einrichten()
        elif befehl == "start": starten(a[1] if len(a) > 1 else "manuell")
        elif befehl == "weiter":
            if len(a) > 1: open(MERKER, "w", encoding="utf-8").write(a[1])  # z. B. eine echt gestartete Instanz übernehmen
            spielen(aktuelle(), fortsetzen=True)
        elif befehl == "status": status()
        elif befehl == "aufraeumen": aufraeumen()
        else: print(open(__file__, encoding="utf-8").read().split("import base64")[0])
    except KeyboardInterrupt:
        print(f"\nPausiert. Weiter mit:  {CMD} weiter")
