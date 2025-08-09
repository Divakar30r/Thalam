package com.blazenn.realtime_document_editing.messaging.producer;

import com.blazenn.realtime_document_editing.constants.RabbitMQConstants;
import com.blazenn.realtime_document_editing.dto.DocumentDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

@Component
public class DocumentUpdateEventProducer {
    Logger log = LoggerFactory.getLogger(DocumentUpdateEventProducer.class);
    private final RabbitTemplate rabbitTemplate;

    public DocumentUpdateEventProducer(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void sendDocumentUpdate(DocumentDTO documentDTO) {
        log.info("Adding document to the queue[{}] with this payload: [{}]", RabbitMQConstants.UPDATE_DOC_QUEUE, documentDTO);
        rabbitTemplate.convertAndSend(RabbitMQConstants.UPDATE_DOC_EXCHANGE, RabbitMQConstants.UPDATE_DOC_ROUTING_KEY, documentDTO);
    }
}
