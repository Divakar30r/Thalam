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
}

