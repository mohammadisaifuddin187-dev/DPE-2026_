// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import io.quarkus.hibernate.orm.panache.PanacheRepository;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.List;
import java.util.Optional;

@ApplicationScoped
public class BestandRepository implements PanacheRepository<Bestand> {

    /** Der aktuelle Ist-Bestand = jüngster Eintrag je Haushalt und Produkt. */
    public Optional<Bestand> aktuell(String pflegehaushaltId, String produktId) {
        return find("pflegehaushaltId = ?1 and produktId = ?2 order by zeitpunkt desc, id desc", pflegehaushaltId, produktId)
                .firstResultOptional();
    }

    /** Die letzten Einträge, neuester zuerst (für den beobachteten Verbrauch). */
    public List<Bestand> letzte(String pflegehaushaltId, String produktId, int anzahl) {
        return find("pflegehaushaltId = ?1 and produktId = ?2 order by zeitpunkt desc, id desc", pflegehaushaltId, produktId)
                .page(0, anzahl).list();
    }
}

// KI-Anteil Ende
