package org.kolmanfreecss.kfimapiresponseservice.application.ports;


import lombok.AllArgsConstructor;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.configurationprocessor.json.JSONObject;
import org.springframework.context.annotation.Lazy;
import org.springframework.data.jpa.repository.Query;
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
        return responseHibernateRepository.findByMember(member);
    }

    public Optional<ResponseTeam> findByTeamName(final String member) {
        return responseHibernateRepository.findByTeamName(member);
    }

    public Optional<ResponseTeam> findByINC(final Long incidentId) {
        return responseHibernateRepository.findByINC(incidentId);
    }

    public int detachIncidentById(final String teamName, final Long incidentId) {
        return responseHibernateRepository.detachIncidentById(teamName, incidentId);
    }

    public int updateIncidentDetails(final String teamName, final Long incidentId, final String newStatus, final String assignee) {
        return responseHibernateRepository.updateIncidentDetails(teamName, incidentId, newStatus, assignee);
    }
}
