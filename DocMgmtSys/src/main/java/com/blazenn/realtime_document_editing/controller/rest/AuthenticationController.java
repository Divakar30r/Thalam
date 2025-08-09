package com.blazenn.realtime_document_editing.controller.rest;

import com.blazenn.realtime_document_editing.dto.LoginVM;
import com.blazenn.realtime_document_editing.service.AppUserService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/authenticate")
public class AuthenticationController {
    Logger log = LoggerFactory.getLogger(AuthenticationController.class);
    private final AppUserService appUserService;

    public AuthenticationController(AppUserService appUserService) {
        this.appUserService = appUserService;
    }

    @PostMapping("")
    public ResponseEntity<String> authenticateUser(@Valid @RequestBody LoginVM loginVM) {
        log.info("POST Request to authenticateUser");
        String jwt = appUserService.authenticateAppUser(loginVM);
        return ResponseEntity.ok(jwt);
    }
}
