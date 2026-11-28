// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;

/**
 * Versorgungsprofil eines Haushalts für ein Produkt (Teamauftrag 2, Abschnitt 6).
 * Zielbestand = Menge nach einer Lieferung, Mindestbestand = Auslöser für den bedingten Start.
 */
@Entity
@Table(name = "t2_versorgungsprofil")
public class Versorgungsprofil {
    @Id
    @Column(length = 20)
    public String id;

    @Column(name = "pflegehaushalt_id", nullable = false, length = 20)
    public String pflegehaushaltId;

    /** Bevorzugtes Produkt. */
    @Column(name = "produkt_id", nullable = false, length = 20)
    public String produktId;

    /** Hinterlegte Ersatzoption (kein medizinischer Ersatz), darf fehlen. */
    @Column(name = "ersatz_produkt_id", length = 20)
    public String ersatzProduktId;

    /** Stück nach einer Lieferung. */
    @Column(nullable = false)
    public int zielbestand;

    /** Stück; wird er unterschritten, startet ein Vorgang (bedingter Start, T2-05). */
    @Column(nullable = false)
    public int mindestbestand;

    /** Verbrauchsannahme in Stück pro Tag. */
    @Column(name = "verbrauch_pro_tag", nullable = false, precision = 6, scale = 2)
    public BigDecimal verbrauchProTag;

    /** Woher die Verbrauchsannahme stammt, z. B. 'konfiguriert'. */
    @Column(name = "verbrauch_herkunft", nullable = false, length = 40)
    public String verbrauchHerkunft;

    /** Gesamtpreis je Bestellung; darüber ist eine Kundenfreigabe nötig (DMN Berechtigungsregel). */
    @Column(nullable = false, precision = 8, scale = 2)
    public BigDecimal preisgrenze;

    @Column(name = "pruefintervall_tage", nullable = false)
    public int pruefintervallTage;
}

// KI-Anteil Ende
