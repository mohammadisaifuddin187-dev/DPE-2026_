# Team 2 – Code (Maven-Projekt, Story T2-02)

> Verantwortlich: Saifudin Mohammadi (von Mohammed übernommen).

| Modul | Inhalt | Stories | Verantwortlich |
|---|---|---|---|
| `benachrichtigung` | Benachrichtigungs-Worker (Freigabeanfrage, Lieferbestätigung, Ergebnis) | T2-11 | Saifudin |
| `prozesslogik` | Worker für Vorgang prüfen, Reichweite, Vorschlag, Ersatzoption, Bestand fortschreiben | T2-07, T2-08, T2-10 | Saifudin (übernommen) |
| `persistenz` *(geplant)* | Datenmodell, REST der App-Simulation, bedingter Start | T2-03 bis T2-05, T2-12 | Erion |
| `integration` | Worker `t2-bestellung-senden`: Bestellung in die ActiveMQ-Queue `Team2_Bestellung_Lieferant`; Camel liest die Queue, verteilt per CBR, wandelt XML ↔ JSON (später Lieferant-Simulation) | T2-14, T2-15 (T2-16, T2-17 geplant) | Amar |
| `eventing` *(geplant)* | Esper | T2-18 | Amar |

```bash
cd code/team2
mvn package            # alle Module bauen
mvn -pl prozesslogik quarkus:dev
```

Tests der Modelle (ohne Code): `werkzeuge/dmn-test` (DMN) und `werkzeuge/endzustand-test` (alle Endzustände).
