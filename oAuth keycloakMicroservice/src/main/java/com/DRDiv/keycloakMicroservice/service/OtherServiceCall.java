package com.DRDiv.keycloakMicroservice.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class OtherServiceCall {

    RestTemplate rest;
    @Value("${service2.url}")
    private String otherService;

    public ResponseEntity invokeServerService(String token){
        RestTemplate restTemplate = new RestTemplate();
        System.out.println("Token rcv on fwd "+ token + " ste "+  otherService);
        // Prepare headers
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        headers.setBearerAuth(token);
        HttpEntity<Void> entity = new HttpEntity<>(headers);

        return      (restTemplate.exchange(
                otherService + "/Sample/Data",
                HttpMethod.GET,
                entity,
                String.class
        ));



    }
}

