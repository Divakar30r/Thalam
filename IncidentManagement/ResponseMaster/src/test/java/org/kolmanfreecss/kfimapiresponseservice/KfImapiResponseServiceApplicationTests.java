package org.kolmanfreecss.kfimapiresponseservice;

import java.time.Instant;
import java.util.List;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.actuate.autoconfigure.metrics.MetricsProperties.System;
import org.springframework.boot.test.context.SpringBootTest;
import org.kolmanfreecss.kfimapiresponseservice.application.services.*;
import org.kolmanfreecss.kfimapiresponseservice.infrastructure.rest.ResponseController;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;
import org.kolmanfreecss.kfimapiresponseservice.shared.exceptions.InvalidInputException;
import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.dto.*;
import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;


@SpringBootTest
class KfImapiResponseServiceApplicationTests {

    @Autowired
    ResponseRepository  responseRepository ;
    @Autowired
    ResponseController responseControllrer ;

    @Autowired
    ResponseConverter responseConverter ;

     @Test
    void contextLoads() {
    }


    @Test
    void setUp() {
         
        
        

        List<RuleStructure> rules = RuleValidator.loadRules("/AssignmentRules.json");
        ResponseTeamDto responseTeamDto = new ResponseTeamDto();
        responseTeamDto.setTeamName("t5");
        responseTeamDto.setMembers(List.of("2sw"));
        responseTeamDto.setIncidents(List.of(new IncidentSummaryDto(116L,"REOPEN","RESOLVED","", Instant.now().toString()),
                                    new IncidentSummaryDto(116L,"REOPEN","RESOLVED","", Instant.now().toString())));
                                    try{
        responseControllrer.incidentAPI(responseTeamDto);                                    
                                    }
                                    catch(InvalidInputException e)
                                    {

                                        e.getMessage();
                                    } 
                                    catch (Exception e) {
                                  
                                 //        try (java.io.PrintWriter pw = new java.io.PrintWriter("stacktrace.txt")) {
                                            e.printStackTrace();
                                //        } catch (Exception fileEx) {
                                //                fileEx.printStackTrace();
                                //        }
                                     
                                    }
        /*
        if (responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).isPresent()){
        ResponseTeamDto DBrec = responseConverter.toDto(responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).get());
        int a = responseRepository.updateIncidentDetails(
            responseTeamDto.getTeamName(),
            responseTeamDto.getIncidents().getFirst().getIncidentId(),
            responseTeamDto.getIncidents().getFirst().getStatus(),
            responseTeamDto.getIncidents().getFirst().getAssignee(),
            Instant.now().toString()
        );
        System.out.println("Updated Incident Details: " + a);
        responseRepository.detachIncidentById("t5", 117L);
        rules.stream()
            .filter(r-> 
                r.event().equals(responseTeamDto.getIncidents().getFirst().getEventtype().toUpperCase())
                )
            .findFirst()
            .ifPresent(rule -> {
                // Process the rule
                System.out.println("Processing rule for event: " + rule.event());
                System.out.println("Current State: " + rule.CurrSts().contains(DBrec.getIncidents().getFirst().getStatus()));

            });

    }
 
    */
       }
}