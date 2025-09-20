package org.kolmanfreecss.kfimapiincidentservice.application.ports;

import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentDto;

import reactor.core.publisher.Mono;

/**
 * IncidentEventHandler
 * Used to define the methods that the IncidentEventHandler must implement.
 * 
 * @version 1.0
 * @uthor Kolman-Freecss
 */
public interface IncidentEventHandlerPort {
    
    //Mono<Void> sendIncident(final IncidentDto incidentDto);

    Mono<Void> sendIncidentToPartition(final IncidentDto incidentDto, final String key, final Integer partition);
    
}
