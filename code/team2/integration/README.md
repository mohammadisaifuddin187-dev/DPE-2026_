# Team 2 – Integration (T2-14, T2-15)

> Verantwortlich: Amar

Worker für das Topic **`t2-bestellung-senden`** („Bestellung übermitteln“ in `T2_Bestellabwicklung`).
Er legt die Bestellung in die ActiveMQ-Queue **`Team2_Bestellung_Lieferant`**. Camel (T2-15) liest die Queue und verteilt die Bestellung an den Lieferanten (Abschnitt [Camel (T2-15)](#camel-t2-15)).

## Wie die Nachricht in die Queue kommt

Per `POST` an die REST-API von ActiveMQ Classic, genau wie in Deck 09, Folie 19–21:

```
POST http://localhost:8161/api/message/Team2_Bestellung_Lieferant?type=queue
Content-Type: application/json
Authorization: Basic …   (admin/admin lokal)
```

Unterschied zur Folie: Den Request schickt ein External-Task-Worker, nicht der HTTP-Connector in der Sendeaufgabe. In unserem Modell steuert die Engine nur, die Integration läuft in Workern (wie bei `prozesslogik` und `benachrichtigung`).

Queue-Name nach dem Schema `Sender_Nachricht_Empfänger` (Deck 07, Folie 40–42).

## Nachrichtenformat

Der Bestellvorschlag (Prozessvariable `bestellvorschlag`, setzt `t2-vorschlag-erstellen`) plus Business Key und Bestellversuch:

```json
{"businessKey":"PH-0001:TP-M","bestellversuch":1,"pflegehaushaltId":"PH-0001","produktId":"TP-M",
 "produktName":"Testprodukt M","lieferantId":"LF-0001","packungen":3,"stueck":90,"preisGesamt":74.7}
```

- **`businessKey`** muss mit: Die Antwort des Lieferanten (T2-16) wird darüber wieder der Instanz zugeordnet.
- **`bestellversuch`** = `anzahlBestellversuche`. Beim Ersatz-Pfad kommt eine zweite Nachricht mit `bestellversuch` 2 und dem Ersatzprodukt (`TP-M-PLUS`, 79,20 €).

Fehlen Vorschlag oder Business Key, wird nichts gesendet. Der Worker meldet dann `handleFailure` mit 3 Wiederholungen, danach entsteht ein Incident im Cockpit.

## Testen: Schritt für Schritt (für alle im Team)

Ziel: Du siehst, dass „Bestellung übermitteln“ von diesem Worker erledigt wird und die Bestellung in ActiveMQ landet.
Dauer beim ersten Mal ca. 15 Minuten, danach 5 Minuten.

Du brauchst 3 Fenster: **A** = CIB seven, **B** = dieser Worker (Log), **C** = `pfad.py`. Dazu den Browser für die ActiveMQ-Konsole.

### Schritt 1: CIB seven und Modelle

Wie in [`werkzeuge/pfade/README.md`](../../../werkzeuge/pfade/README.md), Abschnitt 1:
- **Mac:** `docker start cibseven`
- **Windows:** `werkzeuge\start\cib_starten.cmd` doppelklicken, Fenster offen lassen (= Fenster A)

Dann einmal im Ordner `werkzeuge/pfade`: `python3 pfad.py einrichten` (Windows: `pfad einrichten`).

### Schritt 2: ActiveMQ starten (einmalig anlegen, danach nur starten)

Mit Docker (Mac und Windows mit Docker Desktop):
```
docker run -d --name activemq -p 127.0.0.1:61616:61616 -p 127.0.0.1:8161:8161 apache/activemq-classic:5.18.7
```
Beim nächsten Mal reicht `docker start activemq`.

Ohne Docker (Windows): [ActiveMQ Classic 5.18.7](https://activemq.apache.org/components/classic/download/) als ZIP laden, entpacken, im Ordner `bin` eine Konsole öffnen: `activemq start`. Das Fenster offen lassen.

**Prüfen:** <http://localhost:8161/admin/queues.jsp> öffnet sich, Login **admin / admin**.

### Schritt 3: Worker bauen und starten (Fenster B)

**Mac** (JDK 17 oder neuer, Maven):
```bash
cd code/team2
mvn -pl integration package
export ENGINE_REST_URL=http://localhost:8080/engine-rest ACTIVEMQ_PASSWORD=admin
java -jar integration/target/quarkus-app/quarkus-run.jar
```

**Windows** (cmd im Ordner `code\team2`; Java 21 und Maven liegen schon in `Dokumente\DPE-Werkzeuge`, sobald du einmal `werkzeuge\start\tests_starten.cmd` laufen lassen hast (das lädt beides)):
```
set W=%USERPROFILE%\Documents\DPE-Werkzeuge
for /d %d in ("%W%\jdk-21*") do set JAVA_HOME=%d
set PATH=%JAVA_HOME%\bin;%W%\apache-maven-3.9.11\bin;%PATH%
mvn -pl integration package
set ACTIVEMQ_PASSWORD=admin
java -jar integration\target\quarkus-app\quarkus-run.jar
```

**Prüfen:** Im Log steht
`Integrations-Worker gestartet (http://localhost:8080/engine-rest), Topic: t2-bestellung-senden -> Queue Team2_Bestellung_Lieferant`.
Fenster B offen lassen, dort erscheinen gleich die `[debug]`-Zeilen.

### Schritt 4: Einen Pfad spielen (Fenster C)

Im Ordner `werkzeuge/pfade`:
```
python3 pfad.py start          (Windows: pfad start)
```
`t2-bestellung-senden` steht in `ECHT`, also simuliert `pfad.py` diesen Schritt nicht, sondern wartet auf den Worker.
Alles andere (auch Saifudins Topics, solange sie nicht in `ECHT` stehen) simuliert `pfad.py` wie gewohnt.

| Pfad | Eingaben | Erwartet in ActiveMQ |
|---|---|---|
| Happy Path | überall **1** bzw. Enter | **+1** Nachricht, `bestellversuch` 1 |
| Ersatz | bei „Bestellantwort“ **2**, danach überall **1** | **+2** Nachrichten, die zweite mit `bestellversuch` 2 |
| Kein Bedarf | bei „Verbrauch und Reichweite“ **2** (Bestand 110) | **keine** neue Nachricht |

Mit echten Prozesslogik-Workern entscheidet die Datenbank statt deiner Eingabe, siehe `werkzeuge/pfade/README.md`, Abschnitt „Einen bestimmten Pfad erzwingen“.

**Prüfen:**
1. In `pfad.py` steht `✓ Bestellung übermitteln  [echter Worker]`.
2. In Fenster B stehen drei Zeilen (siehe unten „Was das Log zeigt“).
3. In der ActiveMQ-Konsole: Zeile `Team2_Bestellung_Lieferant`, Spalte **Number Of Pending Messages** ist gestiegen (Seite neu laden).
   Auf den Queue-Namen klicken, dann auf eine Nachricht: Dort steht das JSON.

### Wenn etwas nicht klappt

| Was du siehst | Ursache | Lösung |
|---|---|---|
| `pfad.py` wartet ewig bei „Bestellung übermitteln“ | Worker läuft nicht | Schritt 3. Oder ohne Worker testen: `pfad start --alles-simulieren` |
| Im Log `✗ … fehlgeschlagen … Connection refused` | ActiveMQ läuft nicht | Schritt 2 |
| Im Log `ActiveMQ antwortet mit HTTP 401` | Passwort fehlt | `ACTIVEMQ_PASSWORD=admin` setzen (Schritt 3) |
| Incident im Cockpit bei „Bestellung übermitteln“ | 3 Fehlversuche | Fehlermeldung im Cockpit lesen, Ursache beheben, im Cockpit „Retry“ |
| Worker startet nicht, `JAXBException` | alter Build | `mvn -pl integration clean package` |

### Umgebungsvariablen

| Variable | Standard |
|---|---|
| `ENGINE_REST_URL` | `http://localhost:8080/engine-rest` |
| `ACTIVEMQ_REST_URL` | `http://localhost:8161/api/message` |
| `ACTIVEMQ_USER` / `ACTIVEMQ_PASSWORD` | `admin` / leer (nie ins Repo) |

## Was das Log zeigt

```
[debug] t2-bestellung-senden abgeholt (Instanz …) -> POST …/Team2_Bestellung_Lieferant?type=queue {…}
[debug] ✓ ActiveMQ HTTP 200 - Bestellung liegt in Team2_Bestellung_Lieferant
[debug] ✓ t2-bestellung-senden abgeschlossen (Instanz …)
```

## Getestet

- `BestellnachrichtTest`: Nachricht für TF01 und den Ersatz (TF11), kein Senden ohne Vorschlag oder Business Key.
- Mit der Engine (Mac, CIB seven 2.2.0, ActiveMQ Classic 5.18.7, dieser Worker zusammen mit Saifudins Workern): Happy Path → 1 Nachricht. Ersatz → 2 Nachrichten (Versuch 1 `TP-M`, Versuch 2 `TP-M-PLUS`). Kein Ersatz mehr → 2 Nachrichten, Ende „Keine Bestellung möglich“.
- Unter Windows noch nicht getestet (die Befehle in Schritt 3 sind ungeprüft).

---

## Camel (T2-15)

Läuft im selben Programm wie der Worker: Wer `quarkus-run.jar` startet, startet beide. Aufbau wie Deck 09, Folie 44–46, Code in `BestellungRoute.java`.

### Was die Routen machen

**Route `t2-bestellung-cbr`:** liest `Team2_Bestellung_Lieferant` per JMS (`tcp://localhost:61616`) und verteilt per Content-Based Router nach `lieferantId`:

| `lieferantId` | Ziel (Ordner unter `camel-daten/`) | Format |
|---|---|---|
| `LF-0001` (Versorgungsdienst Beispiel, unser Testlieferant) | `lieferant-LF-0001/bestellung-<zeit>.xml` | **JSON → XML**, Wurzel `<bestellung>` |
| `LF-0002` (zweiter Lieferant, nur simuliert) | `lieferant-LF-0002/bestellung-<zeit>.json` | JSON unverändert |
| alles andere | `abgelehnt/bestellung-<zeit>.json` | wird **nicht ausgeliefert** (Filter nach Inhalt, Pflichtpunkt 3 der Projektvorgaben) |
| kein gültiges JSON | `fehler/<zeit>.txt` | Nachricht bleibt erhalten, im Log steht der Grund |

**Route `t2-xml-zu-json`:** Gegenrichtung. Jede `.xml`-Datei in `camel-daten/eingang-xml/` wird als JSON nach `camel-daten/ausgang-json/<name>.json` geschrieben, das Original wandert nach `eingang-xml/erledigt/`. Vorbereitung für T2-16 (Antwort des Lieferanten).

### Abweichungen von der Folie (und warum)

| Folie | Hier | Grund |
|---|---|---|
| `camel-xmljson` (`XmlJsonDataFormat`, Folie 44/45) | Jackson (`jackson-dataformat-xml`), Klasse `XmlJson` | `camel-xmljson` gibt es ab Camel 3 nicht mehr |
| `Main` + `ActiveMQConnectionFactory` (Folie 46) | Camel Quarkus startet die Routen | ein Programm für Worker und Routen, Konfiguration in `application.properties` |
| `jms:queue:…` | `activemq:queue:…` | Camel-Komponente für ActiveMQ Classic, intern dasselbe JMS |
| JSONPath `$.item[0][?(@.product == 'Car')]` | `$[?(@.lieferantId == 'LF-0001')]` | an unser Nachrichtenformat angepasst (die Bestellung ist ein einzelnes Objekt, kein Array) |

XML kennt keine Datentypen: Bei XML → JSON kommen Zahlen als Text zurück (`"packungen" : "3"`).

### Testen: Schritt für Schritt

Voraussetzung: Schritt 1–3 von oben (CIB seven, ActiveMQ, `quarkus-run.jar` läuft). Dauer ca. 10 Minuten.

**Prüfen, dass Camel läuft:**
- Im Log steht `Routes startup (total:2)`, darunter `Started t2-bestellung-cbr (activemq://queue:Team2_Bestellung_Lieferant)` und `Started t2-xml-zu-json (file://…/camel-daten/eingang-xml)`.
- In der ActiveMQ-Konsole (<http://localhost:8161/admin/queues.jsp>) steht bei `Team2_Bestellung_Lieferant`: **Number Of Consumers = 1**, **Pending Messages = 0**. Lagen vorher Nachrichten in der Queue, sind sie jetzt abgeholt.
- Der Ordner `camel-daten` liegt dort, wo du `java -jar` gestartet hast (ändern mit `CAMEL_ORDNER`).

| # | Was du tust | Was du erwartest |
|---|---|---|
| 1 | Happy Path mit `pfad.py start` (wie Schritt 4 oben) | Neue Datei `lieferant-LF-0001/bestellung-….xml` mit `<produktId>TP-M</produktId>`, `<bestellversuch>1</bestellversuch>` |
| 2 | Ersatz-Pfad (bei „Bestellantwort“ **2**) | **2** neue XML-Dateien in `lieferant-LF-0001`, die zweite mit `TP-M-PLUS` und Versuch 2 |
| 3 | In der ActiveMQ-Konsole: Queues → `Team2_Bestellung_Lieferant` → **Send To**, Body `{"businessKey":"TEST:1","lieferantId":"LF-0002","packungen":1}` → Send | Neue Datei in `lieferant-LF-0002`, Inhalt unverändert JSON |
| 4 | Wie 3, aber `"lieferantId":"LF-9999"` | Neue Datei in `abgelehnt`, nicht beim Lieferanten |
| 5 | Wie 3, Body `das ist kein json` | Neue Datei in `fehler`, im Log `✗ Camel: …InvalidJsonException…` |
| 6 | Datei `antwort.xml` mit `<bestellantwort><status>BESTAETIGT</status><packungen>3</packungen></bestellantwort>` nach `camel-daten/eingang-xml/` legen | Nach ca. 1 s: `ausgang-json/antwort.json` = `{"status" : "BESTAETIGT", "packungen" : "3"}`, das Original liegt in `eingang-xml/erledigt/` |

Bei jedem Schritt erscheint die Pending-Zahl in der Konsole kurz und geht sofort wieder auf 0, weil Camel abholt.

### Was das Log zeigt

```
[debug] Camel: Nachricht aus Team2_Bestellung_Lieferant gelesen: {"businessKey":"PH-0001:TP-M",…,"lieferantId":"LF-0001",…}
[debug] CBR: lieferantId LF-0001 -> Lieferant spricht XML, wandle JSON -> XML
[debug] nach der Umwandlung:
<?xml version='1.0' encoding='UTF-8'?>
<bestellung> … </bestellung>
[debug] ✓ Datei geschrieben: …/camel-daten/lieferant-LF-0001/bestellung-20261128-181600-377.xml
```

Die Zeilen bedeuten der Reihe nach: Camel hat die Nachricht aus der Queue geholt (JMS funktioniert) → der CBR hat den Zweig gewählt → die Umwandlung hat geklappt → die Datei ist geschrieben.

### Wenn etwas nicht klappt

| Was du siehst | Ursache | Lösung |
|---|---|---|
| Programm startet nicht, `JmsPoolConnectionFactory` | Pool-Einstellung fehlt | `camel.component.activemq.use-pooled-connection=false` muss in `application.properties` stehen |
| Programm startet nicht, `Connection refused … 61616` | ActiveMQ läuft nicht oder Port 61616 nicht freigegeben | Schritt 2 (beim `docker run` beide Ports angeben) |
| Pending Messages steigt, Consumers = 0 | Camel hört nicht zu | Programm läuft nicht, Log ansehen |
| Leere Datei in `fehler`, Log `json string can not be null or empty` | Nachricht hatte keinen Body (z. B. curl ohne `Content-Type: application/json`) | mit Header senden |

| Variable | Standard |
|---|---|
| `ACTIVEMQ_JMS_URL` | `tcp://localhost:61616` |
| `CAMEL_ORDNER` | `camel-daten` (relativ zum Startordner) |

### Getestet (T2-15)

- `XmlJsonTest`: JSON → XML mit Wurzel `<bestellung>`, Hin- und Rückweg ergibt dieselben Werte, kaputte Eingaben werden gemeldet.
- Mit der Engine (Mac, CIB seven 2.2.0, ActiveMQ Classic 5.18.7, mit Saifudins Workern): Happy Path → XML-Datei bei `LF-0001`. Die 5 Bestellungen aus dem T2-14-Test (Versuch 1 und 2) hat Camel beim Start abgeholt. Zweige `LF-0002`, abgelehnt, fehler und XML → JSON per Testnachricht geprüft.
- Später: ein Ziel auf eine MySQL-Tabelle umstellen (sobald T2-03 fertig ist), Windows-Test.
