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

/** Eine Lieferung zu einer Bestellung inklusive Befund der Pflegeperson (Lieferprüfung). */
@Entity
@Table(name = "t2_lieferung")
public class Lieferung {

    /** Erlaubte Werte für {@link #befund}, wie im Modell T2_Lieferpruefung. */
    public static final String BEFUND_RICHTIG = "RICHTIG";
    public static final String BEFUND_TEILWEISE = "TEILWEISE";
    public static final String BEFUND_FALSCH = "FALSCH";
    public static final String BEFUND_NICHT_GELIEFERT = "NICHT_GELIEFERT";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    @Column(name = "bestellung_id", nullable = false, length = 40)
    public String bestellungId;

    /** Tatsächlich gelieferte Menge in Stück. */
    @Column(name = "menge_geliefert", nullable = false)
    public int mengeGeliefert;

    /** Befund der Pflegeperson; leer, solange noch nicht bestätigt. */
    @Column(length = 20)
    public String befund;

    @Column(length = 400)
    public String bemerkung;

    @Column(nullable = false)
    public LocalDateTime zeitpunkt;
}

// KI-Anteil Ende
