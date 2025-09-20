package org.kolmanfreecss.kfimapiresponseservice.infrastructure.adapters.in;

 
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.Arrays;
import java.util.Collection;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.kolmanfreecss.kfimapiresponseservice.application.ResponseEventHandlerPort;
import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;
import org.kolmanfreecss.kfimapiresponseservice.application.services.ResponseService;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.kafka.support.TopicPartitionOffset;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class KafkaConsumer implements ResponseEventHandlerPort {

        
    @Autowired
    @Lazy
    private ResponseService responseService_KC;

     
    private final ObjectMapper objectMapper;
    private final ResponseRepository responseRepository;
    private final ResponseConverter  responseConverter;
    
    @Value("${responseteam_defaultteam:Level1Support}")  // Add back the @Value annotation with default
    private String DefaultTeam;

    public KafkaConsumer(ObjectMapper objectMapper, ResponseRepository responseRepository, ResponseConverter responseConverter) {
        this.objectMapper = objectMapper;
        this.responseRepository = responseRepository;
        this.responseConverter = responseConverter;
    }
    
    @Lazy
    @KafkaListener(
        topics = "${kafka_topic_incident_channel:kf_imapi_incident_channel}", 
        groupId = "${kafka_consumer_groupid:CG2}"
        //containerFactory = "kafkaListenerContainerFactory"
    )
    public void rcvIncident(

        ConsumerRecord<String, String> record,
        @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
        @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
        @Header(KafkaHeaders.OFFSET) long offset
    ) {
        try {
            log.info("Received message from topic: {}, partition: {}, offset: {}", topic, partition, offset);
            
            switch (partition) {
                case 0 -> {
                    
                    log.info("Incident Created: {}", record.value());
                    // Process incident creation
                    IncidentSummaryDto incident = objectMapper.readValue(record.value(), IncidentSummaryDto.class);
                    ResponseTeamDto New_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(DefaultTeam).get());
                    incident.setEventtype("OPEN");
                    New_ResponseTeamDto.setIncidents(Arrays.asList(incident));
                    responseService_KC.handleIncident(New_ResponseTeamDto);  
                    // Handle incident...
                }
                case 1 -> {
                    log.info("Incident Updated: {}", record.value());
                    // Process incident update
                    IncidentSummaryDto incident = objectMapper.readValue(record.value(), IncidentSummaryDto.class);
                    // Handle incident...
                }
                default -> log.warn("Unknown partition: {}", partition);
            }
            
        } catch (JsonProcessingException e) {
              log.error("Error processing message: {}", record.value(), e);
        } catch (Exception e) {
            log.error("Error while consuming message", e);
        }
    }
    
    // Keep this method if required by your interface, but it won't be used
    @Override
    public void rcvIncident(Collection<TopicPartitionOffset> response_ConsumerDetails) {
        log.warn("Manual polling method called - consider using @KafkaListener instead");
    }
}

