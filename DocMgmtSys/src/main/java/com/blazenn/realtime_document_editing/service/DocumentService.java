package com.blazenn.realtime_document_editing.service;

import com.blazenn.realtime_document_editing.dto.DocumentDTO;
import com.blazenn.realtime_document_editing.model.Document;
import com.blazenn.realtime_document_editing.repository.DocumentRepository;
import com.blazenn.realtime_document_editing.service.mapper.DocumentMapper;
import org.apache.coyote.BadRequestException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
public class DocumentService {
    Logger log = LoggerFactory.getLogger(DocumentService.class);
    private final DocumentRepository documentRepository;
    private final DocumentMapper documentMapper;

    public DocumentService(DocumentRepository documentRepository, DocumentMapper documentMapper) {
        this.documentRepository = documentRepository;
        this.documentMapper = documentMapper;
    }

    @CachePut(cacheNames = "document", key = "#documentDTO.id")
    public DocumentDTO save(DocumentDTO documentDTO) {
        log.info("Request to save document {}", documentDTO);
        Document document = documentMapper.documentDTOToDocument(documentDTO);
        document = documentRepository.save(document);
        return documentMapper.documentToDocumentDTO(document);
    }

    @Cacheable(value = "document", key = "#id")
    public DocumentDTO findOneById(Long id) {
        log.info("Request to find document by id {}", id);
        Document document = documentRepository.findById(id).orElse(null);
        return documentMapper.documentToDocumentDTO(document);
    }

    public List<DocumentDTO> findAll(Pageable pageable) {
        log.info("Request to find all documents");
        return documentRepository.findAll(pageable).stream().map(documentMapper::documentToDocumentDTO).collect(Collectors.toList());
    }

    @CachePut(cacheNames = "document", key = "#documentDTO.id")
    public DocumentDTO partialUpdate(DocumentDTO documentDTO) {
        log.info("Request to partial update document {}", documentDTO);
        return documentRepository.findById(documentDTO.getId()).map(document -> documentMapper.updateDocumentFromDTO(documentDTO, document)).map(documentMapper::documentToDocumentDTO).orElse(null);
    }

    @CacheEvict(cacheNames = "document", key = "#id", beforeInvocation = true)
    public void deleteById(Long id) {
        log.info("Request to delete document {}", id);
        documentRepository.deleteById(id);
    }

    public Boolean checkIfDocumentExists(Long id) {
        log.info("Request to find document by id to find its existence: {}", id);
        return documentRepository.findById(id).isPresent();
    }

    public void validateDocumentForUpdate(Long id, DocumentDTO documentDTO) throws BadRequestException {
        if (documentDTO.getId() == null) throw new BadRequestException("Payload doesn't contain id to update");
        if (!Objects.equals(documentDTO.getId(), id)) throw new BadRequestException("Document id mismatch");
        if (Boolean.FALSE.equals(checkIfDocumentExists(id))) throw new BadRequestException("No document was found for id " + documentDTO.getId());
    }

    @CachePut(value = "document", key = "#id")
    public DocumentDTO saveContentAndTitle(Long id, DocumentDTO documentDTO) {
        if (documentDTO.getTitle() == null || documentDTO.getContent() == null) {
            DocumentDTO documentFromRepository = this.findOneById(id);
            documentDTO.setContent(documentDTO.getContent() == null ? documentFromRepository.getContent() : documentDTO.getContent());
            documentDTO.setTitle(documentDTO.getTitle() == null ? documentFromRepository.getTitle() : documentDTO.getTitle());
        }
        return this.save(documentDTO);
    }
}
