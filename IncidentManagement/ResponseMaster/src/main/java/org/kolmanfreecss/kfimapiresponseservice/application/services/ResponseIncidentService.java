package org.kolmanfreecss.kfimapiresponseservice.application.services;

import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;

import java.sql.SQLOutput;
import java.time.Instant;
import java.util.List;

import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

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
    
    private final ResponseService responseServiceTransactional;
    private final ResponseRepository responseRepository;
    private final ResponseConverter responseConverter;
    List<RuleStructure> rules;
    // constructor loading the above three values
    public ResponseIncidentService(ResponseService responseServiceTransactional,
                                ResponseRepository responseRepository,
                                ResponseConverter responseConverter) {
        this.responseServiceTransactional = responseServiceTransactional;
        this.responseRepository = responseRepository;
        this.responseConverter = responseConverter;
        rules = RuleValidator.loadRules("/AssignmentRules.json");
        // Now you can use rules.stream().filter(r -> r.event().equals("ASSIGN")).findFirst()...

    }

    public String ValidateInput(ResponseTeamDto responseTeamDto) {

        ResponseTeamDto TeamRef_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(responseTeamDto.getTeamName()).get());

        String inputEvent =responseTeamDto.getIncidents().getFirst().getEventtype().toUpperCase();
        rules.stream()
            .filter(r -> r.event().equals(inputEvent))
            .findFirst()
            .ifPresent(rule -> {
                if (rule.isValidStatus(TeamRef_ResponseTeamDto.getIncidents().getFirst().getStatus())) {
                    log.info("Current status is valid for the event: " + inputEvent);
                } else {
                    log.error("Current status is not valid for the event: " + inputEvent);
                 //   throw new InvalidInputException("Current status is not valid for the event: " + inputEvent);
                }

                if (rule.isMandatory("member")  && (responseTeamDto.getMembers().size() != 1)) {
                    //throw new InvalidInputException("Either no member or multiple members - not allowed ");
                }
                if (rule.isMandatory("incidentId")&&(responseTeamDto.getIncidents().size() != 1)) {
                    //throw new InvalidInputException("Either no incident or multiple incidents - not allowed");
                }
                if (rule.isMandatory("Team") && this.responseRepository.findByMember(responseTeamDto.getMembers().getFirst()).isEmpty()) {
                    //throw new InvalidInputExcpetion("Member not found");
                }

                if ((this.responseRepository.findByMember(responseTeamDto.getMembers().getFirst()).get().getTeamname()!= TeamRef_ResponseTeamDto.getTeamName())
                         || (!responseTeamDto.getMembers().contains(responseTeamDto.getMembers().getFirst()))) {
                      //       throw new InvalidInputExcpetion("Member& Team mismatch");} 
    
                    }

            });
             
            return "Sucess";
            
    }

    public String assignIncident(ResponseTeamDto responseTeamDto) throws Exception  {

        return (String) responseServiceTransactional.RunTransactional(() -> {    
            
            if (this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).isPresent()) {  // Incident exists

                ResponseTeamDto Existing_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByINC(responseTeamDto.getIncidents().getFirst().getIncidentId()).get());
                if (Existing_ResponseTeamDto.getTeamName().equals(responseTeamDto.getTeamName())) {                         // Reassignment in the same team
                    log.info("Incident already assigned to the team: " + responseTeamDto.getTeamName());
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
                    
                    return "Incident reassigned to the same team: " + responseTeamDto.getTeamName();       
                
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
                return null;
                 
            


        });
 
    }
    
    public String updateIncident(ResponseTeamDto responseTeamDto) throws Exception {
        

       return (String) responseServiceTransactional.RunTransactional(() -> {
        
        final int SQLoutput;
            switch (responseTeamDto.getIncidents().getFirst().getEventtype().toUpperCase()) {

                case "STARTED" -> {
                    SQLoutput =  this.responseRepository.updateIncidentDetails(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "INPROGRESS", null);}
                case "HOLD" -> {
                    SQLoutput = this.responseRepository.updateIncidentDetails(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "ONHOLD", " ");}
                case "CLOSE" -> {
                    SQLoutput = this.responseRepository.updateIncidentDetails(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "CLOSED", null);}
                case "RESOLVE" -> {
                    SQLoutput = this.responseRepository.updateIncidentDetails(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "RESOLVED", null);}                    
                case "REOPEN"-> {
                    SQLoutput = this.responseRepository.updateIncidentDetails(responseTeamDto.getTeamName(), responseTeamDto.getIncidents().getFirst().getIncidentId(), "REOPENED", null);}
                default -> {}
            }
            return "";
        });

        


    }
}
