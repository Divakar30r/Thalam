package com.blazenn.realtime_document_editing.controller.rest;

import com.blazenn.realtime_document_editing.dto.AppUserDTO;
import com.blazenn.realtime_document_editing.service.AppUserService;
import org.apache.coyote.BadRequestException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.net.URISyntaxException;

@RestController
@RequestMapping("/api/app-user")
public class AppUserController {
    Logger log = LoggerFactory.getLogger(AppUserController.class);
    private final AppUserService appUserService;

    public AppUserController(AppUserService appUserService) {
        this.appUserService = appUserService;
    }

    @PostMapping("/register")
    ResponseEntity<AppUserDTO> registerNewAppUser(@RequestBody AppUserDTO appUserDTO) throws URISyntaxException, BadRequestException {
        if (appUserDTO.getId() != null) throw new BadRequestException("A new application user cannot have an id");
        log.info("POST request of /app-user/register with body: {}", appUserDTO);
        AppUserDTO result = appUserService.create(appUserDTO);
        return ResponseEntity.created(new URI("/api/app-user/" + result.getId())).body(result);
    }

    @PutMapping("/{id}")
    ResponseEntity<AppUserDTO> updateAppUser(@RequestBody AppUserDTO appUserDTO, @PathVariable(value = "id", required = false) final Long id) throws BadRequestException, URISyntaxException {
        appUserService.validateAppUserForUpdate(appUserDTO, id);
        log.info("PUT request of /app-user/{} with body: {}", id, appUserDTO);
        AppUserDTO result = appUserService.create(appUserDTO);
        return ResponseEntity.created(new URI("/api/app-user/" + result.getId())).body(result);
    }

    @PatchMapping("/{id}")
    ResponseEntity<AppUserDTO> partialUpdateAppUser(@RequestBody AppUserDTO appUserDTO, @PathVariable(value = "id", required = false) final Long id) throws BadRequestException, URISyntaxException {
        appUserService.validateAppUserForUpdate(appUserDTO, id);
        log.info("PATCH request of /app-user/{} with body: {}", id, appUserDTO);
        AppUserDTO result = appUserService.partialUpdate(appUserDTO);
        return ResponseEntity.created(new URI("/api/app-user/" + result.getId())).body(result);
    }
}
