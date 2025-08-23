package org.kolmanfreecss.kfimapiresponseservice.application.services;

import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;

import java.sql.SQLException;
import java.sql.SQLOutput;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;
import org.kolmanfreecss.kfimapiresponseservice.shared.exceptions.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;

@Service
public class ResponseIncidentService {
//Design
/*
                    switch responseTeamDto.getIncidents().getFirst().getEventtype().toUpperCase() {
                    case 'ASSIGN' -> {//Inputs -  Team & member check, 1 incident,  1 member - ACT: admin/member/creator}
                          check incident by incident# 
                            Transactional: remove incident from other team if any, insert incident to new team. Update the incident with member as assignee
                    case 'INPROGRESS'   -> {//Inputs -  Team & member check, 1 incident,  1 member - ACT: member}
                    case 'REASSIGN' -> {//Inputs -  Team & member check, 1 incident,  1 member - ACT: admin/member/creator}
                            Transactional: remove incident from other team if any, insert incident to new team. Update the incident with member as assignee
                    case 'ONHOLD' -> {//Inputs -  1 incident ,1 member - ACT: member}
                        Transactional: update status of incident to ONHOLD(if OPEN/ASSIGNED)
                    case 'CLOSE' -> {//Inputs -  1 incident,1 member - ACT: member/creator}
                        Transactional: update status of incident to CLOSED (if OPEN/ASSIGNED
                    case 'RESOLVE' -> {//Inputs -  1 incident,1 member - ACT: member}
                        Transactional: update status of incident to RESOLVED (if ASSIGNED)
                    case 'REOPEN' -> {//Inputs -  1 incident,1 member - ACT: creator}
                        Transactional: update status of incident to REOPENED (if CLOSED)
                    default -> {}
*/  
 
    Logger log = LoggerFactory.getLogger(ResponseIncidentService.class);
    
    @Autowired
    @Lazy
    private  ResponseService responseServiceTransactional;

    private final ResponseRepository responseRepository;
    private final ResponseConverter responseConverter;
    List<RuleStructure> rules;
    // constructor loading the above three values
    public ResponseIncidentService(ResponseRepository responseRepository,
                                ResponseConverter responseConverter) {
        //this.responseServiceTransactional = responseServiceTransactional;
        this.responseRepository = responseRepository;
        this.responseConverter = responseConverter;
        rules = RuleValidator.loadRules("/AssignmentRules.json");
   }
/*
   @PostConstruct
   public void setResponseServiceObj(ResponseService responseServiceTransactional) {
       this.responseServiceTransactional = responseServiceTransactional;
    }
*/
    public void ValidateInput(ResponseTeamDto responseTeamDto) throws InvalidInputException {
        System.out.println("Reached validateInput");
        
          
        String inputEvent =responseTeamDto.getIncidents().getFirst().getEventtype().toUpperCase();
        Optional<RuleStructure> ruleOpt  =      rules.stream()
            .filter(r -> r.event().equals(inputEvent))
            .findFirst();
        if (ruleOpt.isPresent())
        
            {
                if (ruleOpt.get().isMandatory("member")  && (responseTeamDto.getMembers().size() != 1)) {
                   throw new InvalidInputException("Either no member or multiple members - not allowed ", responseTeamDto);
                }
                if (ruleOpt.get().isMandatory("incidentId")&&(responseTeamDto.getIncidents().size() != 1)) {
                   throw new InvalidInputException("Either no incident or multiple incidents - not allowed", responseTeamDto);
                }

                ResponseTeamDto TeamRef_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(responseTeamDto.getTeamName()).get());
                TeamRef_ResponseTeamDto.setIncidents(null);
                ResponseTeamDto ref_INC_TeamDto = this.responseConverter.toDto(this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).get());

                if (ruleOpt.get().isValidStatus(ref_INC_TeamDto.getIncidents().getFirst().getStatus())) {
                    log.info("Current status is valid for the event: " + inputEvent + " Current status: " + ref_INC_TeamDto.getIncidents().getFirst().getStatus() + " Incident#: " + ref_INC_TeamDto.getIncidents().getFirst().getIncidentId()  );
                } else {
                    log.error("Current status is not valid for the event: " + inputEvent+ " Current status: " + ref_INC_TeamDto.getIncidents().getFirst().getStatus()+ " Incident#: " + ref_INC_TeamDto.getIncidents().getFirst().getIncidentId()  );
                    throw new InvalidInputException("Current status is not valid for the event: " + inputEvent, responseTeamDto);
                }


                if (ruleOpt.get().isMandatory("Team") && this.responseRepository.findByMember(responseTeamDto.getMembers().getFirst()).isEmpty()) {
                    throw new InvalidInputException("Member not found", responseTeamDto);
                }
                if ((this.responseRepository.findByMember(responseTeamDto.getMembers().getFirst()).get().getTeamname()!= TeamRef_ResponseTeamDto.getTeamName())
                         || (!responseTeamDto.getMembers().contains(responseTeamDto.getMembers().getFirst()))) {
                    throw new InvalidInputException("Member & Team mismatch", responseTeamDto);
                } 
            }
            else{
                throw new InvalidInputException("Event type not recognized", responseTeamDto);
            }


             
    }

    public String assignIncident(ResponseTeamDto responseTeamDto) throws InvalidInputException, UpdFailureException,Exception  {
        System.out.println("Reached assignIncident");
        return (String) responseServiceTransactional.RunTransactional(() -> {    

            ValidateInput(responseTeamDto);
            System.out.println("Validated Input from assignIncident");
            
            if (this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).isPresent()) {  // Incident exists

                ResponseTeamDto Existing_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).get());
                if (Existing_ResponseTeamDto.getTeamName().equals(responseTeamDto.getTeamName())) {                         // Reassignment in the same team
                    log.info("Incident already assigned to the team: " + responseTeamDto.getTeamName());
                     responseTeamDto.getIncidents().getFirst().setEventtype("TRANSFER");
                     updateIncident(responseTeamDto);
                     
                     return "Incident reassigned to the same team: " + responseTeamDto.getTeamName();       

                /* 
                    //search for the incident in the list
                    Existing_ResponseTeamDto.getIncidents().stream()
                           .filter(incident -> incident.getIncidentId().equals(responseTeamDto.getIncidents().getFirst().getIncidentId()))
                           .findFirst()
                           .ifPresent(incident -> {
                                incident.setEventtype(responseTeamDto.getIncidents().getFirst().getEventtype());
                                incident.setStatus("ASSIGNED");
                                incident.setAssignee(responseTeamDto.getMembers().getFirst());
                                incident.settimet....
                                });
                    
                    this.responseRepository.update(this.responseConverter.toEntity(Existing_ResponseTeamDto));
                    */
                    
                
                }
                else{
                    this.responseRepository.detachIncidentById(Existing_ResponseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId());
                    log.info("Incident detached from the team: " + Existing_ResponseTeamDto.getTeamName());
                }
            }

            // Now assign the incident to the new team
                ResponseTeamDto New_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(responseTeamDto.getTeamName()).get());
                responseTeamDto.getIncidents().getFirst().setStatus("ASSIGNED");
                responseTeamDto.getIncidents().getFirst().setActivitytimestampinUTCString(Instant.now().toString());
                  
                New_ResponseTeamDto.getIncidents().add(responseTeamDto.getIncidents().getFirst());
                this.responseRepository.update(this.responseConverter.toEntity(New_ResponseTeamDto));
                return "new Incident assigned to the team: " + responseTeamDto.getTeamName();
                 
            


        });
 
    }
    
    public String updateIncident(ResponseTeamDto responseTeamDto) throws Exception {
       System.out.println("Reached UpdateIncident"); 
       ValidateInput(responseTeamDto); //TODO: need to do this if invoked directly from ResponseService 
       System.out.println("Validated Input");
       // print the responseTeamDto eventtype
         System.out.println("Event type: " + responseTeamDto.getIncidents().getFirst().getEventtype());
       return (String) responseServiceTransactional.RunTransactional(() -> {
        
         int SQLoutput=0;
            switch (responseTeamDto.getIncidents().getFirst().getEventtype().toUpperCase()) {

                case "TRANSFER" -> {
                    SQLoutput =  this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "ASSIGNED", responseTeamDto.getIncidents().getFirst().getAssignee(), Instant.now().toString());}
                case "STARTED" -> {
                    SQLoutput =  this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "INPROGRESS", null, Instant.now().toString());}
                case "HOLD" -> {
                    SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "ONHOLD", " ", Instant.now().toString());}
                case "CLOSE" -> {
                    SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "CLOSED", null, Instant.now().toString());}
                case "RESOLVE" -> {
                    SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "RESOLVED", null, Instant.now().toString());}                    
                case "REOPEN"-> {
                    SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "REOPENED", null, Instant.now().toString());}
                default -> {
                    log.error("Event type not recognized: " + responseTeamDto.getIncidents().getFirst().getEventtype());

                }
            }

            if (SQLoutput < 0) 
            {

                log.error("Failed to update incident in team: " + responseTeamDto.getTeamName());
                throw new UpdFailureException("Failed to update incident ", responseTeamDto);
            
            }
            
            return "SQL Output" + String.valueOf(SQLoutput);
        });

        


    }
}
