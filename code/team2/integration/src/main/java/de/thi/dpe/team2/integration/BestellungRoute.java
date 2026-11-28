// Verantwortlich: Amar
package de.thi.dpe.team2.integration;

import jakarta.enterprise.context.ApplicationScoped;
import org.apache.camel.builder.RouteBuilder;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Camel-Routen für T2-15, aufgebaut wie Deck 09, Folie 45.
 * 1. Bestellung aus der Queue lesen und per Content-Based Router nach lieferantId verteilen:
 *    LF-0001 spricht XML (JSON -> XML), LF-0002 bekommt JSON unverändert, alles andere wird nicht ausgeliefert.
 * 2. Gegenrichtung: XML-Datei (z. B. Antwort eines Lieferanten) lesen und als JSON ablegen. Vorbereitung für T2-16.
 * Statt Main + ActiveMQConnectionFactory (Folie 46) startet Quarkus die Routen zusammen mit dem Worker aus T2-14.
 */
@ApplicationScoped
public class BestellungRoute extends RouteBuilder {

    @ConfigProperty(name = "team2.activemq.queue")
    String queue;
    @ConfigProperty(name = "team2.camel.ordner")
    String ordner;

    @Override
    public void configure() {
        // Kaputte Nachrichten nicht verlieren, sondern ablegen
        onException(Exception.class).handled(true)
                .log("[debug] ✗ Camel: ${exception.message}")
                .to("file:" + ordner + "/fehler?fileName=${date:now:yyyyMMdd-HHmmss-SSS}.txt")
                .log("[debug] ✗ Nachricht abgelegt in ${header.CamelFileNameProduced}");

        String zeit = "${date:now:yyyyMMdd-HHmmss-SSS}";

        from("activemq:queue:" + queue).routeId("t2-bestellung-cbr")
                .log("[debug] Camel: Nachricht aus " + queue + " gelesen: ${body}")
                .choice()
                    .when().jsonpath("$[?(@.lieferantId == 'LF-0001')]")
                        .log("[debug] CBR: lieferantId LF-0001 -> Lieferant spricht XML, wandle JSON -> XML")
                        .transform().body(String.class, json -> XmlJson.jsonZuXml(json, "bestellung"))
                        .log("[debug] nach der Umwandlung:\n${body}")
                        .to("file:" + ordner + "/lieferant-LF-0001?fileName=bestellung-" + zeit + ".xml")
                        .log("[debug] ✓ Datei geschrieben: ${header.CamelFileNameProduced}")
                    .when().jsonpath("$[?(@.lieferantId == 'LF-0002')]")
                        .log("[debug] CBR: lieferantId LF-0002 -> Lieferant spricht JSON, ohne Umwandlung")
                        .to("file:" + ordner + "/lieferant-LF-0002?fileName=bestellung-" + zeit + ".json")
                        .log("[debug] ✓ Datei geschrieben: ${header.CamelFileNameProduced}")
                    .otherwise()
                        .log("[debug] CBR: unbekannter Lieferant -> nicht ausgeliefert")
                        .to("file:" + ordner + "/abgelehnt?fileName=bestellung-" + zeit + ".json")
                        .log("[debug] ✓ Datei geschrieben: ${header.CamelFileNameProduced}")
                .end();

        from("file:" + ordner + "/eingang-xml?include=.*\\.xml&move=erledigt").routeId("t2-xml-zu-json")
                .log("[debug] Camel: XML-Datei ${header.CamelFileName} gelesen, wandle XML -> JSON")
                .transform().body(String.class, XmlJson::xmlZuJson)
                .log("[debug] nach der Umwandlung:\n${body}")
                .to("file:" + ordner + "/ausgang-json?fileName=${file:onlyname.noext}.json")
                .log("[debug] ✓ Datei geschrieben: ${header.CamelFileNameProduced}");
    }
}
