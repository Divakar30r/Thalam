package org.kolmanfreecss.kfimapiincidentservice.application.services;

import io.micrometer.observation.annotation.Observed;

import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentCreateRequestDto;
import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentDto;
import org.kolmanfreecss.kfimapiincidentservice.application.entity.Incident;
import org.kolmanfreecss.kfimapiincidentservice.application.mappers.IncidentConverter;
import org.kolmanfreecss.kfimapiincidentservice.application.ports.IncidentEventHandlerPort;
import org.kolmanfreecss.kfimapiincidentservice.application.ports.IncidentRepositoryPort;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.Timestamp;
import java.util.List;
import java.util.Optional;
import java.util.Objects;

/**
 * IncidentService
 * Used to define the methods that the IncidentService must implement.
 * 
 * @author Kolman-Freecss
 * @version 1.0
 */
@Service
public class IncidentService {
    
    Logger log = LoggerFactory.getLogger(IncidentService.class);
    private final IncidentRepositoryPort incidentRepositoryPort;
    
    private final IncidentEventHandlerPort incidentEventHandlerPort;
    
    private final IncidentConverter incidentConverter;
    
    public IncidentService(@Qualifier("incidentHibernateRepositoryPortImpl") final IncidentRepositoryPort incidentRepositoryPort,
                           final IncidentEventHandlerPort incidentEventHandlerPort,
                           final IncidentConverter incidentConverter) {
        this.incidentRepositoryPort = incidentRepositoryPort;
        this.incidentEventHandlerPort = incidentEventHandlerPort;
        this.incidentConverter = incidentConverter;
    }
    
    private String IncString;
   // (Long id, String incidentId, String title, String description, Status status, Priority priority, Date reportDate, Date resolutionDate)
    
   @Transactional
    public Mono<IncidentDto> create(final IncidentCreateRequestDto Ip_incidentDto) {

        System.out.println("Create from Service");
        IncString   = "INC"+ new java.text.SimpleDateFormat("yyyyMMdd").format(new java.util.Date())+"000";
        IncidentDto incidentDto = new IncidentDto(
            null,
             IncString
            ,Ip_incidentDto.title()
            ,Ip_incidentDto.description()
            ,Ip_incidentDto.keydata()
            ,Ip_incidentDto.complexitylevel()
            ,Incident.Status.OPEN
            ,Ip_incidentDto.priority()
            ,new java.sql.Timestamp(System.currentTimeMillis())
            ,(java.util.Date) null
        );
        System.out.println("Incident ID "+ IncString);
        return this.incidentRepositoryPort.create(this.incidentConverter.toEntity(incidentDto))
                .flatMap(entity -> {
                    
                    IncString = "INC" +  new java.text.SimpleDateFormat("yyyyMMdd").format(new java.util.Date())  +  String.format("%03d", entity.getId());
                    System.out.println("Incident flatamp "+ IncString);
                    entity.setIncidentId(IncString);
                    entity.setDescription(entity.getDescription().trim() + " " + IncString);
                    entity.setTitle(entity.getTitle().trim()+ " "+ IncString);
                    return this.incidentRepositoryPort.update(entity).then(Mono.just(this.incidentConverter.toDto(entity)));
                })
                
                //.doOnNext(dto -> Schedulers.parallel().schedule(() -> this.incidentEventHandlerPort.sendIncident(dto).subscribe()));
                .doOnNext(dto -> Schedulers.parallel().schedule(() -> this.incidentEventHandlerPort.sendIncidentToPartition(dto, "CRT", 0).subscribe()));
    }
    
    @Cacheable(value = "incidents", key = "#root.methodName")
    @Observed(name = "getAllIncidents",
            contextualName = "IncidentService",
            lowCardinalityKeyValues = {"getAllIncidents", "IncidentService"})
    public Mono<List<IncidentDto>> getAll() {
        log.info("Fetching from database for getAll()");
        return this.incidentRepositoryPort.getAll()
                .flatMap(incidents -> Mono.just(incidents.stream().map(incidentConverter::toDto).toList()));
    }
    
    public Mono<IncidentDto> getById(final Long id) {
        return this.incidentRepositoryPort.getById(id)
                .flatMap(incident -> Mono.just(Objects.requireNonNull(incident.map(incidentConverter::toDto).orElse(null))));
    }
    
    public Mono<IncidentDto> update(final IncidentDto incidentDto) {
        return this.incidentRepositoryPort.update(this.incidentConverter.toEntity(incidentDto))
                .flatMap(entity -> Mono.just(this.incidentConverter.toDto(entity)));
    }
    
    public Mono<Void> delete(final Long id) {
         Mono<Optional<Incident>> incidentRecord =  this.incidentRepositoryPort.getById(id);
         // set the incident.setStatus  as "closed" in incidentRecord and invoked update service
            incidentRecord.subscribe(incident -> {
                if(incident.isPresent()){
                    Incident inc = incident.get();
                    inc.setStatus(Incident.Status.CLOSED);
                    inc.setResolutionDate(new Timestamp(System.currentTimeMillis()));
                    this.incidentRepositoryPort.update(inc).subscribe();
                    //this.incidentEventHandlerPort.sendIncidentToPartition(this.incidentConverter.toDto(inc), "DEL", 0).subscribe();
                }
            });

            // return Mono<void> after updating the record
            return Mono.fromRunnable(() -> {
            }).then();
    }
         
    
}
