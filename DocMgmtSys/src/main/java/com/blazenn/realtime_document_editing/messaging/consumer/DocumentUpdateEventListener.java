package com.blazenn.realtime_document_editing.messaging.consumer;

import com.blazenn.realtime_document_editing.constants.RabbitMQConstants;
import com.blazenn.realtime_document_editing.dto.DocumentDTO;
import com.blazenn.realtime_document_editing.messaging.producer.DocumentUpdateEventProducer;
import com.blazenn.realtime_document_editing.service.DocumentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

@Component
public class DocumentUpdateEventListener {
    Logger log = LoggerFactory.getLogger(DocumentUpdateEventListener.class);
    private final DocumentService documentService;
    private final SimpMessagingTemplate messagingTemplate;

    public DocumentUpdateEventListener(DocumentService documentService, SimpMessagingTemplate messagingTemplate) {
        this.documentService = documentService;
        this.messagingTemplate = messagingTemplate;
    }

    @RabbitListener(queues = RabbitMQConstants.UPDATE_DOC_QUEUE)
    public void receiveUpdateDocument(DocumentDTO documentDTO) {
        log.info("Event for update document received on queue[{}]: {}",RabbitMQConstants.UPDATE_DOC_QUEUE, documentDTO);
        DocumentDTO updatedDocumentDTO = documentService.saveContentAndTitle(documentDTO.getId(), documentDTO);
        messagingTemplate.convertAndSend("/topic/documents/" + documentDTO.getId(), updatedDocumentDTO);
    }
}
