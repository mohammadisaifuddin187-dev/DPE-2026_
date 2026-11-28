// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.daten;

import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.List;

@ApplicationScoped
public class BestellungRepository implements PanacheRepositoryBase<Bestellung, String> {

    public List<Bestellung> zuVorgang(String vorgangId) {
        return list("vorgangId = ?1 order by angelegtAm", vorgangId);
    }
}

// KI-Anteil Ende
