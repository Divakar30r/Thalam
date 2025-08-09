package com.blazenn.realtime_document_editing.controller.rest;

import com.blazenn.realtime_document_editing.dto.DocumentDTO;
import com.blazenn.realtime_document_editing.service.DocumentService;
import org.apache.coyote.BadRequestException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;

@RestController
@RequestMapping("/api/document")
public class DocumentController {
    Logger log = LoggerFactory.getLogger(DocumentController.class);
    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @PostMapping("")
    public ResponseEntity<DocumentDTO> save(@RequestBody DocumentDTO documentDTO) throws URISyntaxException, BadRequestException {
        if (documentDTO.getId() != null) throw new BadRequestException("A new document cannot have an Id");
        log.info("POST request to save document: {}", documentDTO);
        DocumentDTO result = documentService.save(documentDTO);
        return ResponseEntity.created(new URI("/api/document/" + result.getId())).body(result);
    }

    @GetMapping("")
    public ResponseEntity<List<DocumentDTO>> findAll(Pageable page) {
        log.info("GET request to get all documents");
        List<DocumentDTO> result = documentService.findAll(page);
        return ResponseEntity.ok().body(result);
    }

    @GetMapping("/{id}")
    public ResponseEntity<DocumentDTO> findById(@PathVariable Long id) {
        log.info("GET request to get Document by id: {}", id);
        DocumentDTO documentDTO = documentService.findOneById(id);
        return ResponseEntity.ok().body(documentDTO);
    }

    @PutMapping("/{id}")
    public ResponseEntity<DocumentDTO> update(@PathVariable Long id, @RequestBody DocumentDTO documentDTO) throws URISyntaxException, BadRequestException {
        log.info("PUT request to update document: {}", documentDTO);
        documentService.validateDocumentForUpdate(id, documentDTO);
        DocumentDTO result = documentService.save(documentDTO);
        return ResponseEntity.created(new URI("/api/document/" + result.getId())).body(result);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<DocumentDTO> delete(@PathVariable Long id) {
        log.info("DELETE request to delete document: {}", id);
        documentService.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    @PatchMapping("/{id}")
    public ResponseEntity<DocumentDTO> patch(@PathVariable Long id, @RequestBody DocumentDTO documentDTO) throws BadRequestException, URISyntaxException {
        log.info("PATCH request to update document: {}", documentDTO);
        documentService.validateDocumentForUpdate(id, documentDTO);
        DocumentDTO result = documentService.partialUpdate(documentDTO);
        return ResponseEntity.created(new URI("/api/document/" + result.getId())).body(result);
    }
}
