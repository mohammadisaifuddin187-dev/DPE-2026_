// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.app;

import de.thi.dpe.team2.persistenz.daten.Bestand;
import jakarta.inject.Inject;
import jakarta.ws.rs.BadRequestException;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.NotFoundException;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.Map;
import org.jboss.logging.Logger;

/**
 * Simulation der Pflege-App (klar als Simulation gekennzeichnet, keine echte App).
 * T2-04: Die Pflegeperson meldet einen abweichenden Bestand, der Prozess startet über die Nachricht
 * PflegeApp_Bestandsmeldung_Team2 (Nachrichtenstart "Bestand manuell gemeldet" in T2_Materialversorgung).
 */
@Path("/bestand")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class BestandResource {

    static final String NACHRICHT_BESTANDSMELDUNG = "PflegeApp_Bestandsmeldung_Team2";
    private static final Logger LOG = Logger.getLogger(BestandResource.class);

    @Inject
    BestandService service;

    @Inject
    EngineClient engine;

    /** Eingabe der App, z. B. {"pflegehaushaltId":"PH-0001","produktId":"TP-M","menge":25}. */
    public record Meldung(String pflegehaushaltId, String produktId, Integer menge) {
    }

    @POST
    public Response melden(Meldung m) {
        if (m == null || leer(m.pflegehaushaltId()) || leer(m.produktId()) || m.menge() == null) {
            throw new BadRequestException("pflegehaushaltId, produktId und menge sind Pflichtangaben.");
        }

        // 1. Bestand speichern (eigene Transaktion, ist danach festgeschrieben)
        BestandService.Gespeichert g = service.meldungSpeichern(m.pflegehaushaltId(), m.produktId(), m.menge());

        // 2. Prozess starten: Business Key wie im Team vereinbart (PH-0001:TP-M), damit
        //    "Laufenden Vorgang prüfen" doppelte Vorgänge erkennt.
        String businessKey = m.pflegehaushaltId() + ":" + m.produktId();
        Map<String, Object> variablen = Map.of(
                "pflegehaushaltId", m.pflegehaushaltId(),
                "produktId", m.produktId(),
                "bestandMenge", g.menge(),
                "mindestbestand", g.mindestbestand());
        try {
            String instanz = engine.nachrichtSenden(NACHRICHT_BESTANDSMELDUNG, businessKey, variablen);
            LOG.infof("Bestand %s gemeldet (%d Stück), Prozessinstanz %s", businessKey, g.menge(), instanz);
            return Response.status(Response.Status.CREATED).entity(Map.of(
                    "bestandId", g.bestandId(),
                    "businessKey", businessKey,
                    "bestandMenge", g.menge(),
                    "prozessInstanzId", instanz == null ? "" : instanz)).build();
        } catch (IllegalStateException e) {
            // Der Bestand ist gespeichert; nur der Prozessstart ist fehlgeschlagen (z. B. Modell nicht deployt).
            LOG.errorf("Bestand gespeichert, Prozessstart fehlgeschlagen: %s", e.getMessage());
            return Response.status(Response.Status.BAD_GATEWAY).entity(Map.of(
                    "bestandId", g.bestandId(),
                    "fehler", "Bestand gespeichert, aber Prozess nicht gestartet: " + e.getMessage())).build();
        }
    }

    /** Aktueller Ist-Bestand, zum Nachsehen beim Testen: GET /bestand/PH-0001/TP-M */
    @GET
    @Path("/{pflegehaushaltId}/{produktId}")
    public Bestand aktuell(@PathParam("pflegehaushaltId") String pflegehaushaltId,
                           @PathParam("produktId") String produktId) {
        return service.aktuell(pflegehaushaltId, produktId)
                .orElseThrow(() -> new NotFoundException("Noch kein Bestand für " + pflegehaushaltId + ":" + produktId));
    }

    private static boolean leer(String s) {
        return s == null || s.isBlank();
    }
}

// KI-Anteil Ende
