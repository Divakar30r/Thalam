package com.DRDiv.DocMgmt.controller.rest;

import com.DRDiv.DocMgmt.dto.LoginVM;
import com.DRDiv.DocMgmt.security.JwtSigner;
import com.DRDiv.DocMgmt.service.AppUserService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/authenticateJWT")
public class JWTAuthenticationController {
    Logger log = LoggerFactory.getLogger(AuthenticationController.class);
    
    @Autowired
    JwtSigner jwtSigner;
    
    @PostMapping("")
    public ResponseEntity<String> authenticateAdminforSignedJWT() {
        log.info("POST Request to authenticateAdminforSignedJWT");
        // to pass signedJWT to keycloak and get access token
        try{
            String accesstokenfromSignedjwt = jwtSigner.sendKeycloak(jwtSigner.generateSignedJwt());
            return ResponseEntity.ok(accesstokenfromSignedjwt);
        }
        catch(Exception e){
            e.printStackTrace();
            return ResponseEntity.ok(e.getMessage());

        }
        
    }

}
