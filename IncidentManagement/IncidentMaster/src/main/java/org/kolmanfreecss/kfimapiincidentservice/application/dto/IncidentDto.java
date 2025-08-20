package org.kolmanfreecss.kfimapiincidentservice.application.dto;

import com.fasterxml.jackson.annotation.JsonIgnore;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.Date;
import java.util.Optional;

import org.kolmanfreecss.kfimapiincidentservice.application.entity.Incident;

/**
 * IncidentDto
 * Used to define the IncidentDto object.
 * 
 * @version 1.0
 * @author Kolman-Freecss
 */
public record IncidentDto(@Schema(hidden = true) Long id,
                          @Schema(requiredMode = Schema.RequiredMode.REQUIRED) String title,
                          @Schema(requiredMode = Schema.RequiredMode.REQUIRED) String description,
                          @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED) Incident.Status status,
                          @Schema(requiredMode = Schema.RequiredMode.REQUIRED) Incident.Priority priority,
                          @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED) Date reportDate,
                          @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED) Date resolutionDate) {
    
    @JsonIgnore
    public Optional<Incident.Status> getStatus() {
        return Optional.ofNullable(status);
    }
    
    @JsonIgnore
    public Optional<Date> getReportDate() {
        return Optional.ofNullable(reportDate);
    }
    
    @JsonIgnore
    public Optional<Date> getResolutionDate() {
        return Optional.ofNullable(resolutionDate);
    }
}
