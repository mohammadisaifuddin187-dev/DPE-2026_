# Team 2 – Integration (T2-14)

> Verantwortlich: Amar

Worker für das Topic **`t2-bestellung-senden`** („Bestellung übermitteln“ in `T2_Bestellabwicklung`).
Er legt die Bestellung in die ActiveMQ-Queue **`Team2_Bestellung_Lieferant`**. Camel (T2-15) liest die Queue und verteilt die Bestellung an den Lieferanten.

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
