// Verantwortlich: Amar
package de.thi.dpe.team2.integration;

import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;
import org.camunda.bpm.client.ExternalTaskClient;
import org.camunda.bpm.client.task.ExternalTask;
import org.camunda.bpm.client.task.ExternalTaskService;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

/**
 * External-Task-Worker für t2-bestellung-senden ("Bestellung übermitteln" in T2_Bestellabwicklung, T2-14).
 * Legt die Bestellung per POST an die REST-API von ActiveMQ in die Queue Team2_Bestellung_Lieferant.
 * Das ist derselbe Request nur aus einem Worker statt aus dem HTTP-Connector,
 * weil bei uns die Integration in Workern läuft und die Engine nur steuert.
 * Camel (T2-15) liest die Queue und verteilt die Bestellung an den Lieferanten.
 */
@ApplicationScoped
public class BestellungWorker {

    static final String TOPIC = "t2-bestellung-senden";
    private static final Logger LOG = Logger.getLogger(BestellungWorker.class);

    @ConfigProperty(name = "team2.engine.rest-url")
    String restUrl;
    @ConfigProperty(name = "team2.worker.id")
    String workerId;
    @ConfigProperty(name = "team2.worker.lock-dauer-ms")
    long lockDauer;
    @ConfigProperty(name = "team2.worker.wiederholungen")
    int wiederholungen;
    @ConfigProperty(name = "team2.activemq.rest-url")
    String activemqUrl;
    @ConfigProperty(name = "team2.activemq.benutzer")
    String benutzer;
    @ConfigProperty(name = "team2.activemq.passwort")
    String passwort;
    @ConfigProperty(name = "team2.activemq.queue")
    String queue;

    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    private ExternalTaskClient client;

    void starten(@Observes StartupEvent ev) {
        client = ExternalTaskClient.create().baseUrl(restUrl).workerId(workerId).asyncResponseTimeout(10_000).build();
        client.subscribe(TOPIC).lockDuration(lockDauer).handler(this::bearbeiten).open();
        LOG.infof("Integrations-Worker gestartet (%s), Topic: %s -> Queue %s", restUrl, TOPIC, queue);
    }

    void stoppen(@Observes ShutdownEvent ev) {
        if (client != null) {
            client.stop();
        }
    }

    private void bearbeiten(ExternalTask task, ExternalTaskService ts) {
        try {
            Object versuch = task.getVariable("anzahlBestellversuche");
            String nachricht = Bestellnachricht.bauen(task.getVariable("bestellvorschlag"), task.getBusinessKey(),
                    versuch instanceof Number n ? n.intValue() : 1);
            LOG.infof("[debug] %s abgeholt (Instanz %s) -> POST %s/%s?type=queue %s",
                    TOPIC, task.getProcessInstanceId(), activemqUrl, queue, nachricht);
            int status = senden(nachricht);
            LOG.infof("[debug] ✓ ActiveMQ HTTP %d - Bestellung liegt in %s", status, queue);
            ts.complete(task);
            LOG.infof("[debug] ✓ %s abgeschlossen (Instanz %s)", TOPIC, task.getProcessInstanceId());
        } catch (RuntimeException | IOException e) {
            int rest = task.getRetries() == null ? wiederholungen : task.getRetries() - 1;
            LOG.errorf(e, "[debug] ✗ %s fehlgeschlagen, verbleibende Versuche: %d", TOPIC, rest);
            ts.handleFailure(task, TOPIC + " fehlgeschlagen: " + e.getMessage(), e.toString(), Math.max(rest, 0), 10_000L);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    /** POST an ActiveMQ: JSON im Body, Basic-Auth. Wirft bei allem außer 2xx. */
    private int senden(String nachricht) throws IOException, InterruptedException {
        String auth = Base64.getEncoder().encodeToString((benutzer + ":" + passwort).getBytes(StandardCharsets.UTF_8));
        HttpRequest req = HttpRequest.newBuilder(URI.create(activemqUrl + "/" + queue + "?type=queue"))
                .timeout(Duration.ofSeconds(10))
                .header("Content-Type", "application/json")
                .header("Authorization", "Basic " + auth)
                .POST(HttpRequest.BodyPublishers.ofString(nachricht, StandardCharsets.UTF_8))
                .build();
        HttpResponse<String> r = http.send(req, HttpResponse.BodyHandlers.ofString());
        if (r.statusCode() / 100 != 2) {
            throw new IOException("ActiveMQ antwortet mit HTTP " + r.statusCode() + ": " + r.body());
        }
        return r.statusCode();
    }
}
