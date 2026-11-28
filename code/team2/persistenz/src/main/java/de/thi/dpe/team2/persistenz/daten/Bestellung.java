// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/** Eine (simulierte) Bestellung beim Lieferanten, angelegt in der Bestellabwicklung. */
@Entity
@Table(name = "t2_bestellung")
public class Bestellung {

    /** Erlaubte Werte für {@link #status}. */
    public static final String STATUS_UEBERMITTELT = "UEBERMITTELT";
    public static final String STATUS_BESTAETIGT = "BESTAETIGT";
    public static final String STATUS_NICHT_VERFUEGBAR = "NICHT_VERFUEGBAR";
    public static final String STATUS_GELIEFERT = "GELIEFERT";

    /** Kennung der Bestellung, dient zur Korrelation der Bestellantwort. */
    @Id
    @Column(length = 40)
    public String id;

    @Column(name = "vorgang_id", nullable = false, length = 40)
    public String vorgangId;

    @Column(name = "pflegehaushalt_id", nullable = false, length = 20)
    public String pflegehaushaltId;

    @Column(name = "produkt_id", nullable = false, length = 20)
    public String produktId;

    @Column(name = "lieferant_id", nullable = false, length = 20)
    public String lieferantId;

    @Column(nullable = false)
    public int packungen;

    /** Bestellte Menge in Stück. */
    @Column(nullable = false)
    public int stueck;

    @Column(name = "preis_gesamt", nullable = false, precision = 8, scale = 2)
    public BigDecimal preisGesamt;

    @Column(nullable = false, length = 20)
    public String status;

    @Column(name = "angelegt_am", nullable = false)
    public LocalDateTime angelegtAm;
}

// KI-Anteil Ende
