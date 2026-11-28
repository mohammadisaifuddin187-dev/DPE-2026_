# Team 2 – Persistenz und App-Simulation (Stories T2-03, T2-04)

> Verantwortlich: Erion Kelmendi
> KI-Kennzeichnung: mit KI-Unterstützung erstellt (Claude, Anthropic), von Erion geprüft und lokal getestet.

## Inhalt

| Story | Was | Wo |
|---|---|---|
| T2-03 | Datenmodell: `Pflegehaushalt`, `Lieferant`, `Produkt`, `Versorgungsprofil`, `Bestand`, `Bestellung`, `Lieferung`, je mit Repository (Panache **Repository-Stil**, kein `extends PanacheEntity`) | `daten/` |
| T2-04 | App-Simulation `POST /bestand`: speichert den gemeldeten Ist-Bestand und startet den Hauptprozess über die Nachricht `PflegeApp_Bestandsmeldung_Team2` | `app/BestandResource.java` |

Tabellen wie in `testdaten/team2/T2_Testdaten.sql` (`t2_…`). Neu: `t2_bestellung`, `t2_lieferung` (legt Hibernate an).

**Begriffe:** Ist-Bestand = jüngster Eintrag in `t2_bestand` · Mindestbestand = Auslöser für den bedingten Start · Zielbestand = Menge nach einer Lieferung.

## Starten (lokal, macOS/Linux)

Voraussetzungen: Docker mit MySQL (`team2-mysql`, Port 3306) und CIB seven (`cibseven`, Port 8080), Java 21, Maven.

```bash
# 1. Testdaten laden (legt die Tabellen an, falls noch nicht da)
docker exec -i team2-mysql mysql -u team2 -p<passwort> team2 < testdaten/team2/T2_Testdaten.sql

# 2. Modelle deployen (Camunda Modeler: Deploy-Button, Endpoint http://localhost:8080/engine-rest)

# 3. Modul starten
export DB_PASSWORD=<passwort>
cd code/team2 && mvn -pl persistenz quarkus:dev
```

## Testen

```bash
# Bestand melden -> Prozess startet
curl -i -X POST http://localhost:8093/bestand \
  -H "Content-Type: application/json" \
  -d '{"pflegehaushaltId":"PH-0001","produktId":"TP-M","menge":25}'

# Aktuellen Ist-Bestand ansehen
curl http://localhost:8093/bestand/PH-0001/TP-M
```

Antworten:
- `201` – Bestand gespeichert, Prozess gestartet (`prozessInstanzId` → im Cockpit unter http://localhost:8080/webapp/ sichtbar)
- `400` – Pflichtangabe fehlt oder Menge negativ
- `404` – kein Versorgungsprofil für Haushalt/Produkt
- `502` – Bestand gespeichert, aber die Engine hat den Prozess nicht gestartet (meist: Modell nicht deployt)

An die Engine gehen: Business Key `PH-0001:TP-M` sowie `pflegehaushaltId`, `produktId`, `bestandMenge`, `mindestbestand`.

## Offen (Sprint 2)
- T2-05: nach jeder Bestandsänderung `POST /condition` (bedingter Start)
- T2-12: App-Simulation für Kundenentscheidung und Lieferbestätigung
- Abstimmung mit Saifudin: Die vorläufigen Entities im Modul `prozesslogik` durch dieses Modul ersetzen.
