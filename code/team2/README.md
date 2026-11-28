# Team 2 – Code (Maven-Projekt, Story T2-02)

> Verantwortlich: Saifudin Mohammadi (von Mohammed übernommen).

| Modul | Inhalt | Stories | Verantwortlich |
|---|---|---|---|
| `benachrichtigung` | Benachrichtigungs-Worker (Freigabeanfrage, Lieferbestätigung, Ergebnis) | T2-11 | Saifudin |
| `prozesslogik` | Worker für Vorgang prüfen, Reichweite, Vorschlag, Ersatzoption, Bestand fortschreiben | T2-07, T2-08, T2-10 | Saifudin (übernommen) |
| `persistenz` | Datenmodell (JPA/Panache, MySQL), App-Simulation `POST /bestand` | T2-03, T2-04 (T2-05, T2-12 folgen) | Erion |
| `integration`, `eventing` *(geplant)* | JMS, Camel, Lieferant-Simulation, Esper | T2-14 bis T2-18 | Amar |

```bash
cd code/team2
mvn package            # alle Module bauen
mvn -pl prozesslogik quarkus:dev
```

Tests der Modelle (ohne Code): `werkzeuge/dmn-test` (DMN) und `werkzeuge/endzustand-test` (alle Endzustände).
