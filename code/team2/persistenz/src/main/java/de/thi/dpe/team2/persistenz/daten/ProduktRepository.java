// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class ProduktRepository implements PanacheRepositoryBase<Produkt, String> {
}

// KI-Anteil Ende
