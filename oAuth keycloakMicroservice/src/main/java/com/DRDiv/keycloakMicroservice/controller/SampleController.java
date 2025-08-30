package com.DRDiv.keycloakMicroservice.controller;

import com.DRDiv.keycloakMicroservice.service.OtherServiceCall;
import com.DRDiv.keycloakMicroservice.service.RtvAccessToken;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/Forward")
public class SampleController {

    @Autowired
    RtvAccessToken rtvAccessToken;

    @Autowired
            OtherServiceCall otherServiceCall;
    Logger log = LoggerFactory.getLogger(SampleController.class);
    @GetMapping("/GetDatafromOther")
    public ResponseEntity GetDatafromOther(){
         return otherServiceCall.invokeServerService(rtvAccessToken.retreiver());

    }
}

