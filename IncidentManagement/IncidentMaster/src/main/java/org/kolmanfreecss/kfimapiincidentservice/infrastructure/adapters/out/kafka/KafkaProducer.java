package org.kolmanfreecss.kfimapiincidentservice.infrastructure.adapters.out.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.header.Headers;
import org.apache.kafka.common.header.internals.RecordHeaders;
import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentDto;
import org.kolmanfreecss.kfimapiincidentservice.application.ports.IncidentEventHandlerPort;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;
import org.apache.kafka.common.header.Headers;
import org.apache.kafka.common.header.internals.RecordHeaders;
/**
 * KafkaProducer
 * Kafka producer to send messages to the Kafka topic.
 * @version 1.0
 * @uthor Kolman-Freecss
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KafkaProducer implements IncidentEventHandlerPort {
    
    //@Value annotation to load topic from application.properties
    @Value("${kafka_topic_incident_channel}")
    private String topic;
    
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
     
    // Create headers with topic and partition info
     @Override
    //public Mono<SendResult<String, String>> sendIncidentToPartition(final IncidentDto incidentDto, final String key, final Integer partition) {
    public Mono<Void> sendIncidentToPartition(final IncidentDto incidentDto, final String key, final Integer partition) {
        try {
            Headers headers = new RecordHeaders();
            headers.add("topic", topic.getBytes());
            headers.add("partition", String.valueOf(partition).getBytes());
            headers.add("message-type", "incident-created".getBytes());
            headers.add("timestamp", String.valueOf(System.currentTimeMillis()).getBytes());

            final String jsonEvent = objectMapper.writeValueAsString(incidentDto);
            log.info("Producer produced the message to partition: {} with key: {} - {}", partition, key, jsonEvent);
            
            // Create ProducerRecord with specific partition and key
            ProducerRecord<String, String> producerRecord = new ProducerRecord<>(topic, partition, key, jsonEvent, headers);

            return Mono.fromFuture(() -> kafkaTemplate.send(producerRecord))
                    .doOnSuccess(result -> {
                        log.info("Message with key '{}' produced successfully to partition: {} with offset: {}", 
                                key, partition, result.getRecordMetadata().offset());
                    })
                    .doOnError(exception -> 
                    log.error("Error while producing the message to partition: {} with key: {}", partition, key, exception))
                    .then();
        } catch (JsonProcessingException e) {
            log.error("Error while producing the message", e);
            return Mono.error(e);
        }
    }

}