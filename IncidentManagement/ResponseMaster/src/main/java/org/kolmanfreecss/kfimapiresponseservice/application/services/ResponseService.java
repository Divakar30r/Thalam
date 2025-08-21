package org.kolmanfreecss.kfimapiresponseservice.application.services;

 
import org.kolmanfreecss.kfimapiresponseservice.application.ResponseRepository;
import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;
import org.kolmanfreecss.kfimapiresponseservice.application.*;

import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import io.micrometer.observation.annotation.Observed;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.Callable;
 
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

 
    public ResponseTeamDto attachMembers(final ResponseTeamDto responseTeamDto) {
        ResponseTeamDto Ref_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(responseTeamDto.getTeamName()).get());
        List<String> w_members = Ref_ResponseTeamDto.getMembers();
        responseTeamDto.getMembers().forEach(member_itr-> {
             if (this.responseRepository.findByMember(member_itr).isEmpty()) {
                w_members.add(member_itr);
             }
        });
        Ref_ResponseTeamDto.setMembers(w_members);
        return this.responseConverter.toDto(this.responseRepository.update(this.responseConverter.toEntity(Ref_ResponseTeamDto)));
    }

    public ResponseTeamDto detachMembers(final ResponseTeamDto responseTeamDto) {
        /*
        if (this.responseRepository.findByTeamName(responseTeamDto.getTeamName()).isEmpty()) throw new TeamNotFoundException("Team not found: " + responseTeamDto.getTeamName());
        */

        ResponseTeamDto Ref_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(responseTeamDto.getTeamName()).get());
        List<String> w_members = Ref_ResponseTeamDto.getMembers();
        responseTeamDto.getMembers().forEach(member_itr-> {
             if ((this.responseRepository.findByMember(member_itr).isPresent())
                    && (    this.responseRepository.findByMember(member_itr).get().getTeamname().equals(responseTeamDto.getTeamName()))) {
                w_members.remove(member_itr);
             }
        });
        Ref_ResponseTeamDto.setMembers(w_members);
        // TODO: reassigning logic
        return this.responseConverter.toDto(this.responseRepository.update(this.responseConverter.toEntity(Ref_ResponseTeamDto)));
    }

    public void removeMembers(List<String> members) {
        members.forEach(member_itr -> {
            ResponseTeamDto Ref_ResponseTeamDto = this.responseConverter.toDto(this.responseRepository.findByTeamName(this.responseRepository.findByMember(member_itr).get().getTeamname()).get()) ;
            // TODO: reassigning logic
            List<String> w_members = Ref_ResponseTeamDto.getMembers();
            w_members.remove(member_itr);
            Ref_ResponseTeamDto.setMembers(w_members);
        });
    }

    @Transactional(propagation = Propagation.SUPPORTS)
    // This method is used to run transactional code receiving Runnable object and just execute it  accept any type out of output as return
    public <T> T RunTransactional(java.util.function.Function<String, T> runnable) throws Exception {
        return runnable.apply("RunTransactional");
    }

    @Transactional
    public <T> T RunTransactional(Callable<T> task) throws Exception {
        return task.call();
    }
/*
    public <T> RunTransactional(Runnable runnable) throws Exception {
        runnable.run();
    }

    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void RunNonTransactional(Runnable runnable) throws Exception {
        runnable.run();
    }
         



     
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

    
    public Mono<Void> delete(final Long id) {
        return this.ResponseRepository.delete(id);
    }
*/    
}
