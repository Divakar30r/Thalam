package org.kolmanfreecss.kfimapiresponseservice.infrastructure.adapters.out;

import org.apache.kafka.clients.producer.ProducerRecord;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class KafkaProducer {

    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final ObjectMapper objectMapper;

    @Value("${kafka_topic_response_channel}")
    private String incidentUpdTopic;

    public KafkaProducer(KafkaTemplate<String, Object> kafkaTemplate, ObjectMapper objectMapper) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
    }

    /**
     * Send a message to a Kafka topic with control over topic, partition, offset, and key.
     *
     * @param topic     the topic to send to
     * @param partition the partition to send to (nullable)
     * @param key       the key for the message
     * @param value     the message payload
     */
    public void UpdIncidenttoMasterEvent(IncidentSummaryDto incidentSummaryDto,  Integer partition, String key) {
    try {
        String incidentSummaryDtoasString = objectMapper.writeValueAsString(incidentSummaryDto);

    Message<String> message = MessageBuilder.withPayload(incidentSummaryDtoasString)
        .setHeader(KafkaHeaders.TOPIC, incidentUpdTopic)
        .setHeader(KafkaHeaders.KEY, key)
        .setHeader(KafkaHeaders.PARTITION, partition)
        .build();
        kafkaTemplate.send(message);
    } catch (JsonProcessingException e) {
        // TODO Auto-generated catch block
        e.printStackTrace();
    }

    }     
}
