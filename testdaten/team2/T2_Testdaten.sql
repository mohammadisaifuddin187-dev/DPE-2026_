-- =====================================================================
-- Team 2 Materialversorgung - Testdaten (Story T2-19)
-- Verantwortlich: Saifudin Mohammadi
--
-- Grundlage: Integrationspaket Kap. 8.1 "Künstlicher Testhaushalt"
--   (PH 0001 Haushalt Bergmann, Lieferant Versorgungsdienst Beispiel,
--    Verbrauchsprodukt Inkontinenzmaterial Testprodukt M).
-- Alle Namen, Kennungen und Werte sind frei erfunden (Integrationspaket 8.1).
-- Zahlen (Packungsgröße, Verbrauch, Preise, Grenzen, Fristen) sind
-- PROJEKTANNAHMEN, nicht von Prof. Stiehl vorgegeben.
--
-- Datenbank: MySQL 8. Tabellen- und Spaltennamen sind ein VORSCHLAG und
-- müssen mit den JPA-Entities von Erion (Story T2-03) abgeglichen werden.
-- Erzeugt Hibernate das Schema selbst, nur die INSERTs (Teil 2) ausführen.
--
-- Ausführen:  mysql -u <user> -p <datenbank> < T2_Testdaten.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- Teil 1: Tabellen (Vorschlag, nur falls noch nicht vorhanden)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t2_pflegehaushalt (
  id                 VARCHAR(20)  PRIMARY KEY,          -- z. B. PH-0001
  bezeichnung        VARCHAR(100) NOT NULL,
  pflegebeduerftige  VARCHAR(100) NOT NULL,
  pflegegrad         INT          NOT NULL,
  hauptpflegeperson  VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS t2_lieferant (
  id                 VARCHAR(20)  PRIMARY KEY,
  name               VARCHAR(100) NOT NULL,
  lieferzeit_tage    INT          NOT NULL
);

CREATE TABLE IF NOT EXISTS t2_produkt (
  id                 VARCHAR(20)  PRIMARY KEY,          -- z. B. TP-M
  name               VARCHAR(100) NOT NULL,
  kategorie          VARCHAR(100) NOT NULL,
  packungsgroesse    INT          NOT NULL,             -- Stück je Packung
  preis_packung      DECIMAL(8,2) NOT NULL,             -- aktueller Preis beim Lieferanten
  verfuegbar         BOOLEAN      NOT NULL DEFAULT TRUE,
  lieferant_id       VARCHAR(20)  NOT NULL,
  FOREIGN KEY (lieferant_id) REFERENCES t2_lieferant(id)
);

CREATE TABLE IF NOT EXISTS t2_versorgungsprofil (
  id                     VARCHAR(20)  PRIMARY KEY,
  pflegehaushalt_id      VARCHAR(20)  NOT NULL,
  produkt_id             VARCHAR(20)  NOT NULL,         -- bevorzugtes Produkt
  ersatz_produkt_id      VARCHAR(20)  NULL,             -- hinterlegte Ersatzoption (kein medizinischer Ersatz)
  zielbestand            INT          NOT NULL,         -- Stück
  mindestbestand         INT          NOT NULL,         -- Stück, Auslöser bedingter Start
  verbrauch_pro_tag      DECIMAL(6,2) NOT NULL,         -- Verbrauchsannahme (Stück/Tag)
  verbrauch_herkunft     VARCHAR(40)  NOT NULL,         -- 'konfiguriert' oder 'aus Testdaten abgeleitet'
  preisgrenze            DECIMAL(8,2) NOT NULL,         -- Gesamtpreis je Bestellung, darüber Kundenfreigabe (DMN: preisGesamt > preisgrenze)
  pruefintervall_tage    INT          NOT NULL,         -- Timer-Start R/P10D
  FOREIGN KEY (pflegehaushalt_id) REFERENCES t2_pflegehaushalt(id),
  FOREIGN KEY (produkt_id)        REFERENCES t2_produkt(id),
  FOREIGN KEY (ersatz_produkt_id) REFERENCES t2_produkt(id)
);

CREATE TABLE IF NOT EXISTS t2_bestand (
  id                 BIGINT       AUTO_INCREMENT PRIMARY KEY,
  pflegehaushalt_id  VARCHAR(20)  NOT NULL,
  produkt_id         VARCHAR(20)  NOT NULL,
  menge              INT          NOT NULL,             -- Ist-Bestand in Stück
  zeitpunkt          DATETIME     NOT NULL,
  herkunft           VARCHAR(40)  NOT NULL,             -- 'Fortschreibung', 'Meldung Pflege-App', 'Testdaten'
  FOREIGN KEY (pflegehaushalt_id) REFERENCES t2_pflegehaushalt(id),
  FOREIGN KEY (produkt_id)        REFERENCES t2_produkt(id)
);

-- Testfälle mit erwartetem Endzustand (Story T2-19: "je Fall das erwartete Ende")
CREATE TABLE IF NOT EXISTS t2_testfall (
  id                     VARCHAR(10)  PRIMARY KEY,
  beschreibung           VARCHAR(200) NOT NULL,
  ist_bestand            INT          NOT NULL,
  verbrauch_pro_tag      DECIMAL(6,2) NOT NULL,
  preis_packung          DECIMAL(8,2) NOT NULL,
  produkt_verfuegbar     BOOLEAN      NOT NULL,
  ersatz_hinterlegt      BOOLEAN      NOT NULL,
  simulation             VARCHAR(400) NOT NULL,         -- simulierte Antworten (App, Lieferant, Team 3, Prüfstelle)
  erwartetes_ende        VARCHAR(60)  NOT NULL,         -- Endereignis im Hauptprozess T2_Materialversorgung
  erwarteter_zustand     VARCHAR(40)  NOT NULL          -- gemeinsamer Vorgangszustand (Integrationspaket 6.3)
);

-- ---------------------------------------------------------------------
-- Teil 2: Stammdaten (Integrationspaket 8.1)
-- ---------------------------------------------------------------------
DELETE FROM t2_testfall;
DELETE FROM t2_bestand            WHERE pflegehaushalt_id = 'PH-0001';
DELETE FROM t2_versorgungsprofil  WHERE pflegehaushalt_id = 'PH-0001';
DELETE FROM t2_produkt            WHERE id IN ('TP-M', 'TP-M-PLUS');
DELETE FROM t2_lieferant          WHERE id = 'LF-0001';
DELETE FROM t2_pflegehaushalt     WHERE id = 'PH-0001';

INSERT INTO t2_pflegehaushalt VALUES
  ('PH-0001', 'Haushalt Bergmann', 'Erika Bergmann', 2, 'Anna Bergmann');

INSERT INTO t2_lieferant VALUES
  ('LF-0001', 'Versorgungsdienst Beispiel', 3);                       -- Annahme: 3 Tage Lieferzeit

INSERT INTO t2_produkt VALUES
  ('TP-M',      'Testprodukt M',      'Inkontinenzmaterial', 30, 24.90, TRUE, 'LF-0001'),
  ('TP-M-PLUS', 'Testprodukt M Plus', 'Inkontinenzmaterial', 30, 26.40, TRUE, 'LF-0001');  -- hinterlegte Ersatzoption

-- Annahmen: Zielbestand 120 Stück (4 Packungen), Mindestbestand 40, Verbrauch 4 Stück/Tag,
-- Preisgrenze 75,00 € je Bestellung (= 3 Packungen à 25,00 €), Prüfung alle 10 Tage (Beispiel von Stiehl).
INSERT INTO t2_versorgungsprofil VALUES
  ('VP-0001', 'PH-0001', 'TP-M', 'TP-M-PLUS', 120, 40, 4.00, 'konfiguriert', 75.00, 10);

-- Ausgangsbestand für den Happy Path (TF01): 30 Stück < Mindestbestand 40
INSERT INTO t2_bestand (pflegehaushalt_id, produkt_id, menge, zeitpunkt, herkunft) VALUES
  ('PH-0001', 'TP-M', 30, DATE_SUB(NOW(), INTERVAL 1 DAY), 'Testdaten');

-- ---------------------------------------------------------------------
-- Teil 3: Testfälle mit erwartetem Ende
-- Rechenregel Bedarf (Annahme, DMN "Nachversorgungsbedarf"):
--   Reichweite = Ist-Bestand / Verbrauch pro Tag
--   nachbestellen, wenn Reichweite < Prüfintervall (10) + Lieferzeit (3) = 13 Tage
-- Bestellmenge = Zielbestand - Ist-Bestand, aufgerundet auf volle Packung (30 Stück)
-- Freigabeweg (DMN "Berechtigungsregel", Hit Policy FIRST): Produkt nicht hinterlegt oder
--   Verbrauchssprung -> PRUEFUNG; Gesamtpreis > 75,00 €, Ersatzprodukt, anderer Lieferant oder
--   Menge > Zielbestand -> KUNDENFREIGABE; sonst AUTOMATISCH
-- Beispiel TF01: 120 - 30 = 90 Stück = 3 Packungen x 24,90 € = 74,70 € <= 75,00 € -> AUTOMATISCH
-- Business Key je Vorgang: PH-0001:TP-M
-- ---------------------------------------------------------------------
INSERT INTO t2_testfall VALUES
('TF01','Happy Path: Bestand niedrig, Preis unter Grenze, alles läuft glatt',
  30, 4.00, 24.90, TRUE, TRUE,
  'Lieferant: BESTAETIGT; Versandmeldung; Pflege-App lieferbefund=RICHTIG',
  'Nachversorgung abgeschlossen', 'Erfolgreich abgeschlossen'),
('TF02','Bestand reicht: 110 Stück = 27,5 Tage Reichweite',
  110, 4.00, 24.90, TRUE, TRUE,
  'keine',
  'Bestand ausreichend', '-'),
('TF03','Zweiter Start (manuelle Meldung) während TF01 noch läuft',
  25, 4.00, 24.90, TRUE, TRUE,
  'TF01 wartet noch auf Lieferant; dann Nachricht PflegeApp_Bestandsmeldung_Team2',
  'Vorgang bereits offen', '-'),
('TF04','Preis über Grenze (3 x 27,50 € = 82,50 € > 75,00 €), Kunde gibt frei',
  30, 4.00, 27.50, TRUE, TRUE,
  'Pflege-App entscheidung=FREIGEBEN; Lieferant BESTAETIGT; lieferbefund=RICHTIG',
  'Nachversorgung abgeschlossen', 'Erfolgreich abgeschlossen'),
('TF05','Preis über Grenze, Kunde lehnt ab',
  30, 4.00, 27.50, TRUE, TRUE,
  'Pflege-App entscheidung=ABLEHNEN',
  'Bestellung nicht freigegeben', 'Erfolglos abgeschlossen'),
('TF06','Preis über Grenze, Kunde schiebt auf',
  30, 4.00, 27.50, TRUE, TRUE,
  'Pflege-App entscheidung=AUFSCHIEBEN',
  'Bestellung aufgeschoben', 'Erfolglos abgeschlossen'),
('TF07','Preis über Grenze, keine Antwort trotz Nachfassen über Team 3',
  30, 4.00, 27.50, TRUE, TRUE,
  'keine Antwort: Timer P3D auslösen -> Nachfass-Auftrag an Team 3 -> Timer P3D erneut auslösen',
  'Bestellung nicht freigegeben', 'Erfolglos abgeschlossen'),
('TF08','Kunde wünscht 3-mal eine Änderung (keine Einigung)',
  30, 4.00, 27.50, TRUE, TRUE,
  'Pflege-App entscheidung=AENDERN, 3-mal',
  'Bestellung nicht freigegeben', 'Erfolglos abgeschlossen'),
('TF09','Grenzfall: Produkt nicht im Versorgungsprofil hinterlegt, Prüfstelle: nicht zulässig',
  30, 4.00, 24.90, TRUE, TRUE,
  'produktHinterlegt=false -> freigabeweg=PRUEFUNG; Prüfstelle pruefergebnis=NICHT_ZULAESSIG',
  'Bestellung nicht zulässig', 'Erfolglos abgeschlossen'),
('TF10','Verbrauch deutlich verändert (4 -> 12 Stück/Tag), Prüfstelle holt Kundenfreigabe ein, Kunde gibt frei',
  30, 12.00, 24.90, TRUE, TRUE,
  'verbrauchssprung=true -> freigabeweg=PRUEFUNG; Prüfstelle pruefergebnis=KUNDENFREIGABE; entscheidung=FREIGEBEN; Lieferant BESTAETIGT; lieferbefund=RICHTIG',
  'Nachversorgung abgeschlossen', 'Erfolgreich abgeschlossen'),
('TF11','Produkt nicht verfügbar, Ersatz hinterlegt -> 2. Versuch mit Testprodukt M Plus',
  30, 4.00, 24.90, FALSE, TRUE,
  'Lieferant 1. Versuch NICHT_VERFUEGBAR; Ersatzprodukt (3 x 26,40 € = 79,20 €) -> KUNDENFREIGABE; entscheidung=FREIGEBEN; Lieferant 2. Versuch BESTAETIGT; lieferbefund=RICHTIG',
  'Nachversorgung abgeschlossen', 'Erfolgreich abgeschlossen'),
('TF12','Produkt nicht verfügbar, kein Ersatz hinterlegt',
  30, 4.00, 24.90, FALSE, FALSE,
  'Lieferant NICHT_VERFUEGBAR; ersatzMoeglich=false',
  'Keine Bestellung möglich', 'Erfolglos abgeschlossen'),
('TF13','Lieferant antwortet nicht, auch nicht nach Nachfassen; kein Ersatz',
  30, 4.00, 24.90, TRUE, FALSE,
  'keine Antwort: Timer P1D -> Nachfass-Auftrag Team 3 -> Timer P1D erneut; ersatzMoeglich=false',
  'Keine Bestellung möglich', 'Erfolglos abgeschlossen'),
('TF14','Teillieferung, Nachlieferung über Team 3 bestätigt',
  30, 4.00, 24.90, TRUE, TRUE,
  'Lieferant BESTAETIGT; lieferbefund=TEILWEISE; Klärungs-Auftrag Team 3; klaerungsergebnis=NACHLIEFERUNG_BESTAETIGT',
  'Nachversorgung abgeschlossen', 'Erfolgreich abgeschlossen'),
('TF15','Falschlieferung, Klärung ohne Ergebnis',
  30, 4.00, 24.90, TRUE, TRUE,
  'Lieferant BESTAETIGT; lieferbefund=FALSCH; klaerungsergebnis=NICHT_GEKLAERT',
  'Lieferung ungeklärt', 'Übergeben'),
('TF16','Lieferung bleibt unbestätigt, Team 3 meldet sich nicht',
  30, 4.00, 24.90, TRUE, TRUE,
  'Lieferant BESTAETIGT; Versandmeldung; keine Lieferbestätigung: Timer P3D; keine Klärung: Timer P7D',
  'Lieferung ungeklärt', 'Übergeben');


