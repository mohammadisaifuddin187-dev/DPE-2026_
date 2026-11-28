// Verantwortlich: Amar
package de.thi.dpe.team2.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import org.junit.jupiter.api.Test;

class XmlJsonTest {

    private static final String BESTELLUNG = "{\"businessKey\":\"PH-0001:TP-M\",\"bestellversuch\":1,"
            + "\"produktId\":\"TP-M\",\"lieferantId\":\"LF-0001\",\"packungen\":3,\"preisGesamt\":74.7}";

    @Test
    void jsonWirdXmlMitWurzelBestellung() {
        String xml = XmlJson.jsonZuXml(BESTELLUNG, "bestellung");
        assertTrue(xml.startsWith("<?xml"), xml);
        assertTrue(xml.contains("<bestellung>"), xml);
        assertTrue(xml.contains("<businessKey>PH-0001:TP-M</businessKey>"), xml);
        assertTrue(xml.contains("<packungen>3</packungen>"), xml);
    }

    @Test
    void hinUndZurueckErgibtDieselbenWerteAlsText() throws Exception {
        Map<?, ?> zurueck = new ObjectMapper().readValue(XmlJson.xmlZuJson(XmlJson.jsonZuXml(BESTELLUNG, "bestellung")), Map.class);
        assertEquals("PH-0001:TP-M", zurueck.get("businessKey"));
        assertEquals("LF-0001", zurueck.get("lieferantId"));
        assertEquals("3", zurueck.get("packungen")); // XML kennt keine Zahlen
        assertEquals("74.7", zurueck.get("preisGesamt"));
    }

    @Test
    void kaputteEingabeWirdGemeldet() {
        assertThrows(IllegalArgumentException.class, () -> XmlJson.jsonZuXml("kein json", "bestellung"));
        assertThrows(IllegalArgumentException.class, () -> XmlJson.xmlZuJson("<offen>"));
    }
}
