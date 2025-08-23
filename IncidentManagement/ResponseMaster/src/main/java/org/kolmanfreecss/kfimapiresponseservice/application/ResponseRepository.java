package org.kolmanfreecss.kfimapiresponseservice.application;

import java.util.List;
import java.util.Optional;

import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;
 

public interface ResponseRepository {

    ResponseTeam create(final ResponseTeam responseTeam);
    
    List<ResponseTeam> getAll();
    
    Optional<ResponseTeam> getById(final Long id);
    
    ResponseTeam update(final ResponseTeam responseTeam);
    
    void delete(final Long id);

    Optional<ResponseTeam> findByMember(String member);

    Optional<ResponseTeam> findByTeamName(String teamName);

    Optional<ResponseTeam> findByINC(Long incidentId);

    int detachIncidentById(String teamname, Long incidentId);

    int updateIncidentDetailsEvent(String teamname, Long incidentId, String newStatus, String assignee, String activitytimestamp);
} 

