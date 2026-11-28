// Verantwortlich: Amar
package de.thi.dpe.team2.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Nachricht für die Queue mit dem Bestellvorschlag aus den Testdaten (TF01 und Ersatz TF11). */
class BestellnachrichtTest {

    private static final String VORSCHLAG = "{\"pflegehaushaltId\":\"PH-0001\",\"produktId\":\"TP-M\","
            + "\"produktName\":\"Testprodukt M\",\"lieferantId\":\"LF-0001\",\"packungen\":3,\"stueck\":90,\"preisGesamt\":74.70}";

    @Test
    void tf01BusinessKeyUndVersuchStehenVorne() {
        assertEquals("{\"businessKey\":\"PH-0001:TP-M\",\"bestellversuch\":1,\"pflegehaushaltId\":\"PH-0001\","
                + "\"produktId\":\"TP-M\",\"produktName\":\"Testprodukt M\",\"lieferantId\":\"LF-0001\","
                + "\"packungen\":3,\"stueck\":90,\"preisGesamt\":74.7}",
                Bestellnachricht.bauen(VORSCHLAG, "PH-0001:TP-M", 1));
    }

    @Test
    void tf11ErsatzMitZweitemVersuch() {
        String n = Bestellnachricht.bauen(VORSCHLAG.replace("\"TP-M\"", "\"TP-M-PLUS\""), "PH-0001:TP-M", 2);
        assertTrue(n.contains("\"bestellversuch\":2") && n.contains("\"produktId\":\"TP-M-PLUS\""));
    }

    @Test
    void ohneVorschlagOderBusinessKeyWirdNichtBestellt() {
        assertThrows(IllegalArgumentException.class, () -> Bestellnachricht.bauen("{}", "PH-0001:TP-M", 1));
        assertThrows(IllegalArgumentException.class, () -> Bestellnachricht.bauen(VORSCHLAG, null, 1));
        assertThrows(IllegalArgumentException.class, () -> Bestellnachricht.bauen("kein json", "PH-0001:TP-M", 1));
    }
}
