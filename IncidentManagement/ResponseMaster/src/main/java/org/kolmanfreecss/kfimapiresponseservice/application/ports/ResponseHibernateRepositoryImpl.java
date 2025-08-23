package org.kolmanfreecss.kfimapiresponseservice.application.ports;


import lombok.AllArgsConstructor;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.configurationprocessor.json.JSONObject;
import org.springframework.context.annotation.Lazy;
import org.springframework.dao.IncorrectResultSizeDataAccessException;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.jayway.jsonpath.internal.filter.ValueNodes.JsonNode;

import jakarta.persistence.NonUniqueResultException;

import org.hibernate.type.format.jakartajson.JsonBJsonFormatMapper;
import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;

import java.util.List;
import java.util.Optional;
 
//@AllArgsConstructor
@Repository("responseHibernateRepositoryImplBean")
public class ResponseHibernateRepositoryImpl  implements ResponseRepository {
    
    @Autowired
    @Lazy
    private ResponseHibernateRepository responseHibernateRepository;
    
    private ResponseTeam responseTeam;
    private List<IncidentSummaryDto> incidentsList;


    @Override
    public ResponseTeam create(final ResponseTeam responseTeam) {
        return responseHibernateRepository.save(responseTeam);
    }

    @Override
    public List<ResponseTeam> getAll() {
       return responseHibernateRepository.findAll();
    }

    @Override
    public Optional<ResponseTeam> getById(final Long id) {
        return responseHibernateRepository.findById(id);
    }

    @Override
    public ResponseTeam update(final ResponseTeam responseTeam) {
        return responseHibernateRepository.save(responseTeam);
    }

    @Override
    public void delete(final Long id) {
          responseHibernateRepository.deleteById(id);
    }            

    public Optional<ResponseTeam> findByMember(final String member) {
         if (responseHibernateRepository.findByMember(member).isEmpty()){
            return Optional.empty();
        }
        else{
            try{
            return responseHibernateRepository.findByMember(member);
            }catch(IncorrectResultSizeDataAccessException e){
                System.out.println("Duplicate members found - Contact Admin");
                return Optional.empty();
            } 
        }  

    }

    public Optional<ResponseTeam> findByTeamName(final String member) {
        
        return responseHibernateRepository.findByTeamName(member);

    }

    public Optional<ResponseTeam> findByINC(final Long incidentId) {
        try{
            if (responseHibernateRepository.findByINC(incidentId).isEmpty()){
                return Optional.empty();
            }
            else{
                System.out.println("Incident found in team: " );
                responseTeam =  responseHibernateRepository.findByINC(incidentId).get();
                incidentsList = responseTeam.getIncidents().stream()
                .filter(incident -> incident.getIncidentId().equals(incidentId)).toList();

                responseTeam.setIncidents(incidentsList);
                return Optional.of(responseTeam);
            }
        }catch(IncorrectResultSizeDataAccessException e){
            System.out.println("Duplicate incidents found - Contact Admin");
            return Optional.empty();
        }

    }

    public int detachIncidentById(final String teamName, final Long incidentId) {
        return responseHibernateRepository.detachIncidentById(teamName, incidentId);
    }

    public int updateIncidentDetailsEvent(final String teamName, final Long incidentId, final String newStatus, final String assignee,final String activitytimestamp) {
        return responseHibernateRepository.updateIncidentDetails(teamName, incidentId, newStatus, assignee, activitytimestamp);
    }

     
}
