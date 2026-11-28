// Verantwortlich: Amar
package de.thi.dpe.team2.integration;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;
import com.fasterxml.jackson.dataformat.xml.ser.ToXmlGenerator;
import java.util.Map;

/**
 * XML <-> JSON für die Camel-Route (T2-15).
 * Ersetzt XmlJsonDataFormat aus Deck 09, Folie 45 (camel-xmljson gibt es ab Camel 3 nicht mehr).
 * Wie in der Folie (setRootName("order")) bekommt das XML ein festes Wurzelelement.
 */
public final class XmlJson {

    private static final ObjectMapper JSON = new ObjectMapper();
    private static final XmlMapper XML = XmlMapper.builder().enable(ToXmlGenerator.Feature.WRITE_XML_DECLARATION).build();

    private XmlJson() {
    }

    public static String jsonZuXml(String json, String wurzel) {
        try {
            return XML.writer().withRootName(wurzel).withDefaultPrettyPrinter()
                    .writeValueAsString(JSON.readValue(json, Map.class));
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("kein gültiges JSON: " + json, e);
        }
    }

    /** XML kennt keine Datentypen: Zahlen kommen als Text zurück ("3" statt 3). */
    public static String xmlZuJson(String xml) {
        try {
            return JSON.writerWithDefaultPrettyPrinter().writeValueAsString(XML.readValue(xml, Map.class));
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("kein gültiges XML: " + xml, e);
        }
    }
}
