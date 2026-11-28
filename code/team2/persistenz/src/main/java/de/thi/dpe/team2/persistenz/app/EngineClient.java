// Verantwortlich: Erion Kelmendi
// KI-Anteil Beginn (Claude, Anthropic) - von Erion geprüft
package de.thi.dpe.team2.persistenz.app;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Schickt Nachrichten an die REST-API von CIB seven (POST /message).
 * Die Engine sucht selbst den passenden Nachrichtenstart bzw. die wartende Empfangsaufgabe.
 */
@ApplicationScoped
public class EngineClient {

    @ConfigProperty(name = "team2.engine.rest-url")
    String restUrl;

    @Inject
    ObjectMapper json;

    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

    /**
     * Korreliert eine Nachricht mit der Engine.
     *
     * @return ID der gestarteten bzw. getroffenen Prozessinstanz (oder null, wenn die Engine keine liefert)
     */
    public String nachrichtSenden(String nachrichtenName, String businessKey, Map<String, Object> variablen) {
        ObjectNode body = json.createObjectNode();
        body.put("messageName", nachrichtenName);
        body.put("businessKey", businessKey);
        body.put("resultEnabled", true);
        ObjectNode vars = body.putObject("processVariables");
        variablen.forEach((name, wert) -> {
            ObjectNode v = vars.putObject(name);
            v.putPOJO("value", wert);
            v.put("type", typ(wert));
        });

        try {
            HttpRequest anfrage = HttpRequest.newBuilder(URI.create(restUrl + "/message"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(json.writeValueAsString(body)))
                    .build();
            HttpResponse<String> antwort = http.send(anfrage, HttpResponse.BodyHandlers.ofString());
            if (antwort.statusCode() != 200) {
                throw new IllegalStateException("Engine antwortet mit " + antwort.statusCode() + ": " + antwort.body());
            }
            JsonNode ergebnis = json.readTree(antwort.body());
            JsonNode erstes = ergebnis.isArray() && ergebnis.size() > 0 ? ergebnis.get(0) : ergebnis;
            String id = erstes.path("processInstance").path("id").asText(null);
            return id != null ? id : erstes.path("execution").path("processInstanceId").asText(null);
        } catch (IOException e) {
            throw new IllegalStateException("Engine nicht erreichbar: " + e.getMessage(), e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Nachricht unterbrochen", e);
        }
    }

    /** Variablentyp für die REST-API von Camunda 7 / CIB seven. */
    private static String typ(Object wert) {
        if (wert instanceof Integer) {
            return "Integer";
        }
        if (wert instanceof Long) {
            return "Long";
        }
        if (wert instanceof Boolean) {
            return "Boolean";
        }
        if (wert instanceof Number) {
            return "Double";
        }
        return "String";
    }
}

// KI-Anteil Ende
