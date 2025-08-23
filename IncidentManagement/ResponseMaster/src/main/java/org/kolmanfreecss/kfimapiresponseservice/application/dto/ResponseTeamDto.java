package org.kolmanfreecss.kfimapiresponseservice.application.dto;
 import com.fasterxml.jackson.annotation.JsonInclude;
 import com.fasterxml.jackson.annotation.JsonPropertyOrder;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;

import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;
 
@Data
@Builder
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL) 
@JsonPropertyOrder({"teamName", "members", "incidents"})
public class ResponseTeamDto implements Serializable {

    @Serial
    private static final long serialVersionUID = 5865597278076349945L;
 

    @Schema(requiredMode = Schema.RequiredMode.REQUIRED, description = "Name of the team") 
    private String teamName;

    @Schema(requiredMode = Schema.RequiredMode.REQUIRED, description = "List of team members")
    private List<String> members;

    @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED, description = "List of incidents")
    private List<IncidentSummaryDto> incidents;

     
}                            