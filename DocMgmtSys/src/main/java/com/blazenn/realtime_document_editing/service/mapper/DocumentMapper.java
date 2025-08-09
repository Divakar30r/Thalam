package com.blazenn.realtime_document_editing.service.mapper;

import com.blazenn.realtime_document_editing.dto.DocumentDTO;
import com.blazenn.realtime_document_editing.model.Document;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel = "spring")
public interface DocumentMapper {
    DocumentMapper INSTANCE = Mappers.getMapper(DocumentMapper.class);

    Document documentDTOToDocument(DocumentDTO documentDTO);

    DocumentDTO documentToDocumentDTO(Document document);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    Document updateDocumentFromDTO(DocumentDTO documentDTO, @MappingTarget Document document);
}
