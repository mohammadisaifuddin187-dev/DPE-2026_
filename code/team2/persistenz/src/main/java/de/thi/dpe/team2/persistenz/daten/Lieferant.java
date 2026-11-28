// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Lieferant (Testdaten: LF-0001 Versorgungsdienst Beispiel). */
@Entity
@Table(name = "t2_lieferant")
public class Lieferant {
    @Id
    @Column(length = 20)
    public String id;

    @Column(nullable = false, length = 100)
    public String name;

    @Column(name = "lieferzeit_tage", nullable = false)
    public int lieferzeitTage;
}

// KI-Anteil Ende
