package org.kolmanfreecss.kfimapiincidentservice.application.mappers;

import lombok.NoArgsConstructor;

import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentCreateRequestDto;
import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentDto;
import org.kolmanfreecss.kfimapiincidentservice.application.entity.Incident;
import org.springframework.stereotype.Component;

import org.modelmapper.ModelMapper;

/**
 * IncidentConverter
 * Used to convert the Incident entity to a DTO and vice versa.
 *
 * @version 1.0
 * @author Kolman-Freecss
 */
@NoArgsConstructor
@Component
public class IncidentConverter {

    private static final ModelMapper modelMapper = new ModelMapper();

    public IncidentDto toDto(final Incident incident) {
        return new IncidentDto(incident.getId(), incident.getIncidentId(), incident.getTitle(), incident.getDescription(),
                incident.getKeydata(), incident.getComplexitylevel(), incident.getStatus(), incident.getPriority(), incident.getReportDate(), incident.getResolutionDate());
    }

    public Incident toEntity(final IncidentDto incidentDto) {
        return new Incident(incidentDto.id(), 
                incidentDto.incidentId(),
                incidentDto.title(), 
                incidentDto.description(),
                incidentDto.keydata(),
                incidentDto.complexitylevel(),
                incidentDto.getStatus().orElse(null),
                incidentDto.priority(),
                incidentDto.getReportDate().orElse(null),
                incidentDto.getResolutionDate().orElse(null));
    }

    public IncidentDto fromCreateRequestDto(final IncidentCreateRequestDto req) {
        // Map only allowed fields from request DTO to IncidentDto
        return new IncidentDto(
            null, // id
            null, // incidentId (generated in service)
            req.title(),
            req.description(),
            req.keydata(),
            req.complexitylevel(),
            null, // status (set in service)
            req.priority(),
            null, // reportDate (set in service)
            null  // resolutionDate
        );
    }

}
