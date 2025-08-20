package org.kolmanfreecss.kfimapiresponseservice.application.services;

 
import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;
import org.kolmanfreecss.kfimapiresponseservice.application.*;

import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;

import io.micrometer.observation.annotation.Observed;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Objects;
 
@Service
public class ResponseService {
    
    Logger log = LoggerFactory.getLogger(ResponseService.class);
    private final ResponseRepository responseRepository;
    
    //private final ResponseEventHandlerPort ResponseEventHandlerPort;
    
    private final ResponseConverter responseConverter;
    
     
    public ResponseService(@Lazy @Qualifier("responseHibernateRepositoryImplBean") final ResponseRepository responseRepository,
                           //final ResponseEventHandlerPort ResponseEventHandlerPort,
                           final ResponseConverter responseConverter) {
        this.responseRepository = responseRepository;
        //this.ResponseEventHandlerPort = ResponseEventHandlerPort;
        this.responseConverter = responseConverter;
    }
    
    public ResponseTeamDto createTeam(final ResponseTeamDto responseTeamDto) {
       return this.responseConverter.toDto(this.responseRepository.create(this.responseConverter.toEntity(responseTeamDto)));
    }
    public List<ResponseTeamDto> getAllItems() {
       return (this.responseRepository.getAll()).stream().map(responseConverter::toDto).toList();
    }
    
    public ResponseTeamDto getItemById(final Long id) {
        if  (this.responseRepository.getById(id).isPresent())
            return this.responseConverter.toDto(this.responseRepository.getById(id).get());
        else return null;
                
    }
  /*  
    @Cacheable(value = "Responses", key = "#root.methodName")
    @Observed(name = "getAllResponses",
            contextualName = "ResponseService",
            lowCardinalityKeyValues = {"getAllResponses", "ResponseService"})

    public List<ResponseTeamDto> getAll() {
        log.info("Fetching from database for getAll()");
          return (this.responseRepository.getAll()).stream().map(responseConverter::toDto).toList();
    }
    
    public Mono<ResponseDto> getById(final Long id) {
        return this.ResponseRepository.getById(id)
                .flatMap(Response -> Mono.just(Objects.requireNonNull(Response.map(ResponseConverter::toDto).orElse(null))));
    }
    
    public Mono<ResponseDto> update(final ResponseDto ResponseDto) {
        return this.ResponseRepository.update(this.ResponseConverter.toEntity(ResponseDto))
                .flatMap(entity -> Mono.just(this.ResponseConverter.toDto(entity)));
    }
    
    public Mono<Void> delete(final Long id) {
        return this.ResponseRepository.delete(id);
    }
*/    
}
