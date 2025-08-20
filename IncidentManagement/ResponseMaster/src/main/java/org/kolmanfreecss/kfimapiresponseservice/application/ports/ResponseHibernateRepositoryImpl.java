package org.kolmanfreecss.kfimapiresponseservice.application.ports;


import lombok.AllArgsConstructor;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.configurationprocessor.json.JSONObject;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Repository;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.jayway.jsonpath.internal.filter.ValueNodes.JsonNode;

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
    
    @Override
    public ResponseTeam create(final ResponseTeam responseTeam) {
        // can you verify whether responseTeam.incidents is a JSONB field
  final ObjectMapper objectMapper1 = new ObjectMapper();
  try{
     
        System.out.println("Printed out:" + responseTeam.getIncidents().toString() + " Processed " +
        objectMapper1.writeValueAsString((responseTeam.getIncidents())));
    }catch (Exception e){
         System.out.println("ExceptionIssue:" + responseTeam.getIncidents().toString());
    e.printStackTrace();
    }
    


        return responseHibernateRepository.save(responseTeam);
    }

    @Override
    public List<ResponseTeam> getAll() {
        System.out.println("Fetching all ResponseTeams"+ responseHibernateRepository.findAll().toArray().toString());
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
 

}
