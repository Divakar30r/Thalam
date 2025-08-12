package com.DRDiv.DocMgmt.service.mapper;

import com.DRDiv.DocMgmt.dto.AppUserDTO;
import com.DRDiv.DocMgmt.entity.AppUser.AppUserEntity;

import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel = "spring")
public interface AppUserMapper {
    AppUserMapper INSTANCE = Mappers.getMapper(AppUserMapper.class);

    AppUserDTO appUserToAppUserDTO(AppUserEntity appUser);

    AppUserEntity appUserDTOToAppUser(AppUserDTO appUserDTO);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    AppUserEntity updateAppUserFromDTO(AppUserDTO appUserDTO, @MappingTarget AppUserEntity appUser);
}
