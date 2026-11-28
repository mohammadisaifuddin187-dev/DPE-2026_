// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import io.quarkus.hibernate.orm.panache.PanacheRepository;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.List;

@ApplicationScoped
public class LieferungRepository implements PanacheRepository<Lieferung> {

    public List<Lieferung> zuBestellung(String bestellungId) {
        return list("bestellungId = ?1 order by zeitpunkt", bestellungId);
    }
}

// KI-Anteil Ende
