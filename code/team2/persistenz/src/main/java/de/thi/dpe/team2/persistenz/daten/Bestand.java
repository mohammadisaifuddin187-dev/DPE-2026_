// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

/**
 * Ein Bestandseintrag. Der jüngste Eintrag je Haushalt und Produkt ist der Ist-Bestand.
 * Einträge werden nie überschrieben, so bleibt der Verlauf für die Verbrauchsberechnung erhalten.
 */
@Entity
@Table(name = "t2_bestand")
public class Bestand {

    /** Erlaubte Werte für {@link #herkunft}. */
    public static final String HERKUNFT_APP = "Meldung Pflege-App";
    public static final String HERKUNFT_FORTSCHREIBUNG = "Fortschreibung";
    public static final String HERKUNFT_TESTDATEN = "Testdaten";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    @Column(name = "pflegehaushalt_id", nullable = false, length = 20)
    public String pflegehaushaltId;

    @Column(name = "produkt_id", nullable = false, length = 20)
    public String produktId;

    /** Ist-Bestand in Stück. */
    @Column(nullable = false)
    public int menge;

    @Column(nullable = false)
    public LocalDateTime zeitpunkt;

    @Column(nullable = false, length = 40)
    public String herkunft;
}

// KI-Anteil Ende
