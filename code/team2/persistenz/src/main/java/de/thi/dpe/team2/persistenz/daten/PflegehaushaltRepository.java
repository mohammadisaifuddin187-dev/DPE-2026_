// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;

/** Panache im Repository-Stil: die Entity erbt nicht von PanacheEntity, der Zugriff liegt hier. */
@ApplicationScoped
public class PflegehaushaltRepository implements PanacheRepositoryBase<Pflegehaushalt, String> {
}

// KI-Anteil Ende
