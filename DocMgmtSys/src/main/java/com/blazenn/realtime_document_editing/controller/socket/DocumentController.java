package com.blazenn.realtime_document_editing.controller.socket;

import com.blazenn.realtime_document_editing.dto.DocumentDTO;
import com.blazenn.realtime_document_editing.messaging.producer.DocumentUpdateEventProducer;
import com.blazenn.realtime_document_editing.service.DocumentService;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;

import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

@Controller("DocumentSocketController")
public class DocumentController {
    Logger log = LogManager.getLogger(DocumentController.class);
    private final DocumentUpdateEventProducer documentUpdateEventProducer;

    public DocumentController(DocumentUpdateEventProducer documentUpdateEventProducer) {
        this.documentUpdateEventProducer = documentUpdateEventProducer;
    }

    @MessageMapping("/documents/{id}")
    public void getDocumentById(@DestinationVariable String id, @Payload DocumentDTO documentDTO) {
        log.info("Socket request to update document of id '{}' with this payload: {}", id, documentDTO);
        documentUpdateEventProducer.sendDocumentUpdate(documentDTO);
    }
}
