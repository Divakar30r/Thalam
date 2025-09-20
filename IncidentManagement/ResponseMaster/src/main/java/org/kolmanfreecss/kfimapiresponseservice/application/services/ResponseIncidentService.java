package org.kolmanfreecss.kfimapiresponseservice.application.services;

import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;

import java.sql.SQLException;
import java.sql.SQLOutput;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;
import org.kolmanfreecss.kfimapiresponseservice.infrastructure.adapters.out.KafkaProducer;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;
import org.kolmanfreecss.kfimapiresponseservice.shared.exceptions.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import jakarta.persistence.EntityManager;
import jakarta.ws.rs.client.Entity;

 

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
    private  ResponseTransactionService responseTransactionService;

    @Autowired
    private EntityManager entityManager;

    @Autowired
    private KafkaProducer kafkaProducer; 

    private final ResponseRepository responseRepository;
    private final ResponseConverter responseConverter;

    private ResponseTeamDto ref_INC_TeamDto;
    private ResponseTeam TeamRef_ResponseTeam;

    List<RuleStructure> rules;
    // constructor loading the above three values
    public ResponseIncidentService(ResponseRepository responseRepository,
                                ResponseConverter responseConverter) {
        //this.responseServiceTransactional = responseServiceTransactional;
        this.responseRepository = responseRepository;
        this.responseConverter = responseConverter;
        rules = RuleValidator.loadRules("/AssignmentRules.json");
   }
 
   public void ValidateInput(ResponseTeamDto responseTeamDto) throws InvalidInputException {
    
          
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
                
                
                ResponseTeam ref_INC_Team = this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId())
                .orElseThrow(() -> new InvalidInputException("Incident not found", responseTeamDto));
                entityManager.detach(ref_INC_Team);
                ref_INC_TeamDto = this.responseConverter.toDto(ref_INC_Team);

                TeamRef_ResponseTeam = this.responseRepository.findByTeamName(responseTeamDto.getTeamName())
                .orElseThrow(() -> new InvalidInputException("Team not found", responseTeamDto));
                ResponseTeamDto TeamRef_ResponseTeamDto = this.responseConverter.toDto(TeamRef_ResponseTeam);
                entityManager.detach(TeamRef_ResponseTeam);
                TeamRef_ResponseTeamDto.setIncidents(null);
                
                
                if (ruleOpt.get().isValidStatus(ref_INC_TeamDto.getIncidents().getFirst().getStatus())) {
                    log.info("Current status is valid for the event: " + inputEvent + " Current status: " + ref_INC_TeamDto.getIncidents().getFirst().getStatus() + " Incident#: " + ref_INC_TeamDto.getIncidents().getFirst().getIncidentId()  );
                } else {
                    log.error("Current status is not valid for the event: " + inputEvent+ " Current status: " + ref_INC_TeamDto.getIncidents().getFirst().getStatus()+ " Incident#: " + ref_INC_TeamDto.getIncidents().getFirst().getIncidentId()  );
                    throw new InvalidInputException("Current status is not valid for the event: " + inputEvent, responseTeamDto);
                }

                 // member check
                if (ruleOpt.get().isMandatory("Team") && this.responseRepository.findByMember(responseTeamDto.getMembers().getFirst()).isEmpty()) {
                    throw new InvalidInputException("Member not found", responseTeamDto);
                }
                if (!TeamRef_ResponseTeamDto.getMembers().contains(responseTeamDto.getMembers().getFirst())) {
                    throw new InvalidInputException("Member & Team mismatch", responseTeamDto);
                } 
            }
            else{
                throw new InvalidInputException("Event type not recognized", responseTeamDto);
            }

    }

    public String assignIncident(ResponseTeamDto responseTeamDto) throws InvalidInputException, UpdFailureException,Exception  {

        // as Runnable
        return (String) responseTransactionService.RunTransactional(() -> {
            try{    


            ValidateInput(responseTeamDto);
            System.out.println("Validated Input from assignIncident");

            if (ref_INC_TeamDto.getId() != null) {  // Incident exists

                ResponseTeamDto Existing_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).get());
                if (Existing_ResponseTeamDto.getTeamName().equals(responseTeamDto.getTeamName())) {                         // Reassignment in the same team
                    log.info("Incident already assigned to the team: " + responseTeamDto.getTeamName());
                     responseTeamDto.getIncidents().getFirst().setEventtype("TRANSFER");
                     updateIncident(responseTeamDto);
                     
                     return "Incident reassigned to the same team: " + responseTeamDto.getTeamName();       
                
                }
                else{
                       log.info("Detaching incident from team: " + Existing_ResponseTeamDto.getTeamName() + " for Incident "+ responseTeamDto.getIncidents().getFirst().getIncidentId());
                    entityManager.clear();
                    System.out.println("Count before detach " + this.responseRepository.getById(6L).get().getIncidents().size());
                    this.responseRepository.detachIncident(Existing_ResponseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId());
                    System.out.println("Count after detach " + this.responseRepository.getById(6L).get().getIncidents().size());
                 }
            }

            // Now assign the incident to the new team
                ResponseTeamDto New_ResponseTeamDto = this.responseConverter.toDto(TeamRef_ResponseTeam);
                System.out.println("Assigning incident to new team: " + New_ResponseTeamDto.getTeamName());
                //+ New_ResponseTeamDto.getIncidents().size());
                responseTeamDto.getIncidents().getFirst().setStatus("ASSIGNED");
                responseTeamDto.getIncidents().getFirst().setActivitytimestampinUTCString(Instant.now().toString());
                if (responseTeamDto.getMembers().getFirst()!=null)  
                    responseTeamDto.getIncidents().getFirst().setAssignee(responseTeamDto.getMembers().getFirst());

                New_ResponseTeamDto.getIncidents().add(responseTeamDto.getIncidents().getFirst());
                this.responseRepository.update(this.responseConverter.toEntity(New_ResponseTeamDto));
                
                // Also send the original incident from responseTeamDto
                kafkaProducer.UpdIncidenttoMasterEvent(responseTeamDto.getIncidents().getFirst(), 0, "UPD");
                return "new Incident assigned to the team: " + responseTeamDto.getTeamName();
                 
        }   catch (UpdFailureException ue) {             throw ue;          }
            catch (InvalidInputException e) {            throw e;           }
             
            catch (Exception e) {
                log.error("General Exception: " + e.getMessage());
                throw new Exception("General Exception: " + e.getMessage());
            }


        });
       
    }
    
    public String addIncident(ResponseTeamDto responseTeamDto) throws InvalidInputException, UpdFailureException,Exception {

        // as Runnable
        return (String) responseTransactionService.RunTransactional(() -> {
            try{    

                // Now assign the incident to the new team
                ResponseTeamDto New_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(responseTeamDto.getTeamName()).get());
                responseTeamDto.getIncidents().getFirst().setStatus("OPEN");
                responseTeamDto.getIncidents().getFirst().setEventtype("Creation");
                responseTeamDto.getIncidents().getFirst().setActivitytimestampinUTCString(Instant.now().toString());
                if (New_ResponseTeamDto.getIncidents()==null)
                    {  
                         New_ResponseTeamDto.setIncidents(new java.util.ArrayList<>());
                        New_ResponseTeamDto.setIncidents(responseTeamDto.getIncidents());
                }
                else
                    {New_ResponseTeamDto.getIncidents().add(responseTeamDto.getIncidents().getFirst());}
                // update the repository
                
                this.responseRepository.update(this.responseConverter.toEntity(New_ResponseTeamDto));
                return "new Incident added to the team: " + responseTeamDto.getTeamName();
            }catch(Exception e) {throw e;}
        });      
    }
    
    public String updateIncident(ResponseTeamDto responseTeamDto) throws Exception {
       System.out.println("Reached UpdateIncident"); 
       ValidateInput(responseTeamDto);
       System.out.println("Validated Input");
       System.out.println("Event type: " + responseTeamDto.getIncidents().getFirst().getEventtype());
        // Obtain EntityManager instance
       entityManager.clear();
        
       // Check if we're already in a transaction
       if (TransactionSynchronizationManager.isActualTransactionActive()) {
           System.out.println("Already in transaction, executing directly");
           return executeUpdateIncidentLogic(responseTeamDto);
       } else {
           System.out.println("No active transaction, wrapping in transaction");
           return (String) responseTransactionService.RunTransactional(() -> {
               return executeUpdateIncidentLogic(responseTeamDto);
           });
       }
   }

   private String executeUpdateIncidentLogic(ResponseTeamDto responseTeamDto) throws Exception {
       try {

           int SQLoutput = 0;
           switch (responseTeamDto.getIncidents().getFirst().getEventtype().toUpperCase()) {
               case "TRANSFER" -> {
                   SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "ASSIGNED", responseTeamDto.getMembers().getFirst(), Instant.now().toString());
               }
               case "STARTED" -> {
                   SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "INPROGRESS", null, Instant.now().toString());
               }
               case "HOLD" -> {
                   SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "ONHOLD", " ", Instant.now().toString());
               }
               case "CLOSE" -> {
                   SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "CLOSED", null, Instant.now().toString());
               }
               case "RESOLVE" -> {
                   SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "RESOLVED", null, Instant.now().toString());
               }
               case "REOPEN" -> {
                   SQLoutput = this.responseRepository.updateIncidentDetailsEvent(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "REOPENED", null, Instant.now().toString());
               }
               default -> {
                   log.error("Event type not recognized: " + responseTeamDto.getIncidents().getFirst().getEventtype());
               } 
           }

           if (SQLoutput < 0) {
               log.error("Failed to update incident in team: " + responseTeamDto.getTeamName());
               throw new UpdFailureException("Failed to update incident ", responseTeamDto);
           } else {
               // After successful update, fetch the latest incident from repository and send only the first incident to Kafka
               ResponseTeam updatedTeam = this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId())
                   .orElseThrow(() -> new UpdFailureException("Incident not found after update", responseTeamDto));
               entityManager.detach(updatedTeam);
               ResponseTeamDto updatedTeamDto = this.responseConverter.toDto(updatedTeam);
                   if (updatedTeamDto.getIncidents() != null && !updatedTeamDto.getIncidents().isEmpty()) {
                       kafkaProducer.UpdIncidenttoMasterEvent(updatedTeamDto.getIncidents().getFirst(), 0, "UPD");
                       log.info("Successfully updated incident in team: " + updatedTeamDto.getTeamName());
                   } else {
                       log.error("No incidents found in updated team DTO after update for incident: " + responseTeamDto.getIncidents().getFirst().getIncidentId());
                   }
           
           }
           
           return "SQL Output" + String.valueOf(SQLoutput);
       } catch (UpdFailureException ue) {
           throw ue;
       }
   }
}
