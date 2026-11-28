// Verantwortlich: Amar
package de.thi.dpe.team2.integration;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Baut die Nachricht für die Queue Team2_Bestellung_Lieferant.
 * Inhalt = der Bestellvorschlag (Prozessvariable bestellvorschlag) plus Business Key und Bestellversuch.
 * Der Business Key muss mit, damit die Antwort des Lieferanten (T2-16) später wieder zur Instanz findet.
 */
public final class Bestellnachricht {

    private static final ObjectMapper JSON = new ObjectMapper();

    private Bestellnachricht() {
    }

    @SuppressWarnings("unchecked")
    public static String bauen(String bestellvorschlag, String businessKey, int bestellversuch) {
        if (bestellvorschlag == null || bestellvorschlag.isBlank() || bestellvorschlag.equals("{}")) {
            throw new IllegalArgumentException("bestellvorschlag fehlt, es gibt nichts zu bestellen");
        }
        if (businessKey == null || businessKey.isBlank()) {
            throw new IllegalArgumentException("Business Key fehlt, die Lieferantenantwort könnte nicht zugeordnet werden");
        }
        try {
            Map<String, Object> n = new LinkedHashMap<>();
            n.put("businessKey", businessKey);
            n.put("bestellversuch", bestellversuch);
            n.putAll(JSON.readValue(bestellvorschlag, Map.class));
            return JSON.writeValueAsString(n);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("bestellvorschlag ist kein JSON: " + bestellvorschlag, e);
        }
    }
}
