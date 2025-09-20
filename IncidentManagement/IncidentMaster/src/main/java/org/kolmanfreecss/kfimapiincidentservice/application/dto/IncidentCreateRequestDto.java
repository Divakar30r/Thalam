package org.kolmanfreecss.kfimapiincidentservice.application.dto;

import org.kolmanfreecss.kfimapiincidentservice.application.entity.Incident;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;

/**
 * IncidentCreateRequestDto
 * Used as a restricted POST request body for incident creation.
 * Only allows fields that are actually considered from input.
 *
 * @author Kolman-Freecss
 */
public record IncidentCreateRequestDto(
        @Schema(requiredMode = Schema.RequiredMode.REQUIRED) 
        @NotNull(message = "Title cannot be null")
        
        String title,
        @Schema(requiredMode = Schema.RequiredMode.REQUIRED) 
        @NotNull(message = "Description cannot be null")
        String description,

        @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED) String keydata,
        @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED) String complexitylevel,
        @Schema(requiredMode = Schema.RequiredMode.REQUIRED) Incident.Priority priority
) {}
