// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.Optional;

@ApplicationScoped
public class VersorgungsprofilRepository implements PanacheRepositoryBase<Versorgungsprofil, String> {

    /** Profil eines Haushalts für ein Produkt; gilt auch, wenn das Produkt die hinterlegte Ersatzoption ist. */
    public Optional<Versorgungsprofil> profil(String pflegehaushaltId, String produktId) {
        return find("pflegehaushaltId = ?1 and (produktId = ?2 or ersatzProduktId = ?2)", pflegehaushaltId, produktId)
                .firstResultOptional();
    }
}

// KI-Anteil Ende
