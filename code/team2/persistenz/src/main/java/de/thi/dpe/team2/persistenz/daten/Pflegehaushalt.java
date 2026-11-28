// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Pflegehaushalt (Testdaten: PH-0001 Haushalt Bergmann). Nur Stammdaten, keine Gesundheitsdaten. */
@Entity
@Table(name = "t2_pflegehaushalt")
public class Pflegehaushalt {
    @Id
    @Column(length = 20)
    public String id;

    @Column(nullable = false, length = 100)
    public String bezeichnung;

    @Column(nullable = false, length = 100)
    public String pflegebeduerftige;

    @Column(nullable = false)
    public int pflegegrad;

    @Column(nullable = false, length = 100)
    public String hauptpflegeperson;
}

// KI-Anteil Ende
