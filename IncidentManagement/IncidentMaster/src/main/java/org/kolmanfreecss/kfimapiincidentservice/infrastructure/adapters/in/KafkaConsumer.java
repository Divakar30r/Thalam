
package org.kolmanfreecss.kfimapiincidentservice.infrastructure.adapters.in;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentDto;
import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentSummaryDto;
import org.kolmanfreecss.kfimapiincidentservice.application.entity.Incident;
import org.kolmanfreecss.kfimapiincidentservice.application.mappers.IncidentConverter;
import org.kolmanfreecss.kfimapiincidentservice.application.ports.IncidentRepositoryPort;
import org.kolmanfreecss.kfimapiincidentservice.application.services.IncidentService;
import java.util.Objects;
import reactor.core.publisher.Mono;

@Component
public class KafkaConsumer {

    private static final Logger log = LoggerFactory.getLogger(KafkaConsumer.class);
    @Autowired
    private IncidentConverter incidentConverter;

    @Autowired
    private IncidentService incidentService;

    @Autowired
    private IncidentRepositoryPort incidentRepositoryPort;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @KafkaListener(
        topicPartitions = @org.springframework.kafka.annotation.TopicPartition(
            topic = "${kafka_topic_response_channel}", partitions = {"0"}
        )
    )
    public void UpdIncident(
            ConsumerRecord<String, Object> record,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset) {
        switch (partition) {
            case 0 -> {
                try {
                    // Only process if the key is 'UPD'
                    String messageKey = record.key();
                    if (!"UPD".equals(messageKey)) return;
                    String json = Objects.toString(record.value(), null);
                    if (json == null) return;
                    log.info("Received message: " + json + " from topic: " + topic + " partition: " + partition + " offset: " + offset);
                    IncidentSummaryDto incidentSummaryDto = objectMapper.readValue(json, IncidentSummaryDto.class);
                    if (incidentSummaryDto.getIncidentId() == null) return;
                    // Check if incident exists
                    incidentRepositoryPort.getByIncidentId(incidentSummaryDto.getIncidentId())
                        .subscribe(optionalIncident -> {
                            if (optionalIncident.isPresent()) {
                                IncidentDto existingDto = incidentConverter.toDto(optionalIncident.get());
                                // Only update the status field
                                IncidentDto updatedDto = new IncidentDto(
                                    existingDto.id(),
                                    existingDto.incidentId(),
                                    existingDto.title(),
                                    existingDto.description(),
                                    existingDto.keydata(),
                                    existingDto.complexitylevel(),
                                    Incident.Status.valueOf(incidentSummaryDto.getStatus()), // update only status
                                    existingDto.priority(),
                                    existingDto.reportDate(),
                                    existingDto.resolutionDate()
                                );
                                try {
                                    log.info("Updating incident: " + objectMapper.writeValueAsString(updatedDto));
                                    incidentService.update(updatedDto).subscribe();
                                } catch (JsonProcessingException e) {
                                    log.error("Error serializing incident DTO", e);
                                }
                            }
                        });
                } catch (Exception e ) {
                    log.error("Error processing Kafka message", e);
                    e.printStackTrace();
                }
            }
            default -> {
                // Handle other partitions if needed
            }
        }
    }
 
}

