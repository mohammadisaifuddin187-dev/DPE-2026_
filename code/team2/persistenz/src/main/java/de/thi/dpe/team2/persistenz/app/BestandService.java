// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.app;

import de.thi.dpe.team2.persistenz.daten.Bestand;
import de.thi.dpe.team2.persistenz.daten.BestandRepository;
import de.thi.dpe.team2.persistenz.daten.Versorgungsprofil;
import de.thi.dpe.team2.persistenz.daten.VersorgungsprofilRepository;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.BadRequestException;
import jakarta.ws.rs.NotFoundException;
import java.time.LocalDateTime;
import java.util.Optional;

/** Fachlogik rund um den Bestand (T2-03, T2-04). Team 2 ist führendes System für den Ist-Bestand. */
@ApplicationScoped
public class BestandService {

    @Inject
    BestandRepository bestaende;

    @Inject
    VersorgungsprofilRepository profile;

    /** Ergebnis einer gespeicherten Meldung; der Mindestbestand wird für den Prozessstart gebraucht. */
    public record Gespeichert(Long bestandId, int menge, int mindestbestand) {
    }

    /**
     * Speichert eine Bestandsmeldung aus der Pflege-App als neuen Eintrag.
     * Die Transaktion endet mit dieser Methode, damit die Worker den neuen Bestand sofort lesen können.
     */
    @Transactional
    public Gespeichert meldungSpeichern(String pflegehaushaltId, String produktId, int menge) {
        if (menge < 0) {
            throw new BadRequestException("Die Menge darf nicht negativ sein.");
        }
        Versorgungsprofil profil = profile.profil(pflegehaushaltId, produktId)
                .orElseThrow(() -> new NotFoundException(
                        "Kein Versorgungsprofil für Haushalt " + pflegehaushaltId + " und Produkt " + produktId));

        Bestand b = new Bestand();
        b.pflegehaushaltId = pflegehaushaltId;
        b.produktId = produktId;
        b.menge = menge;
        b.zeitpunkt = LocalDateTime.now();
        b.herkunft = Bestand.HERKUNFT_APP;
        bestaende.persist(b);

        return new Gespeichert(b.id, menge, profil.mindestbestand);
    }

    public Optional<Bestand> aktuell(String pflegehaushaltId, String produktId) {
        return bestaende.aktuell(pflegehaushaltId, produktId);
    }
}

// KI-Anteil Ende
