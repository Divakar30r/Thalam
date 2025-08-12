package com.DRDiv.DocMgmt.service.mapper;

import com.DRDiv.DocMgmt.dto.DocumentDTO;
import com.DRDiv.DocMgmt.entity.document.DocumentEntity;

import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel = "spring")
public interface DocumentMapper {
    DocumentMapper INSTANCE = Mappers.getMapper(DocumentMapper.class);

    DocumentEntity documentDTOToDocument(DocumentDTO documentDTO);

    DocumentDTO documentToDocumentDTO(DocumentEntity document);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    DocumentEntity updateDocumentFromDTO(DocumentDTO documentDTO, @MappingTarget DocumentEntity document);
}
