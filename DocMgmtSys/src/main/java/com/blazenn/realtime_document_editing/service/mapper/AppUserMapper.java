package com.blazenn.realtime_document_editing.service.mapper;

import com.blazenn.realtime_document_editing.dto.AppUserDTO;
import com.blazenn.realtime_document_editing.model.AppUser;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel = "spring")
public interface AppUserMapper {
    AppUserMapper INSTANCE = Mappers.getMapper(AppUserMapper.class);

    AppUserDTO appUserToAppUserDTO(AppUser appUser);

    AppUser appUserDTOToAppUser(AppUserDTO appUserDTO);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    AppUser updateAppUserFromDTO(AppUserDTO appUserDTO, @MappingTarget AppUser appUser);
}
