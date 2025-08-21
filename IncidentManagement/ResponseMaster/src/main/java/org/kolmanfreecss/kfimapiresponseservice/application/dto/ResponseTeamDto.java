package org.kolmanfreecss.kfimapiresponseservice.application.dto;
/*
import com.fasterxml.jackson.annotation.JsonIgnore;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;
import java.util.Optional;

 
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;






public record ResponseTeamDto(@Schema(hidden = true)    Long id,
                          @Schema(requiredMode = Schema.RequiredMode.REQUIRED, description = "Name of the team")  String teamName,
                          @Schema(requiredMode = Schema.RequiredMode.REQUIRED, description = "List of team members") List<String> members,
                          @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED, description = "List of incidents")  List<IncidentSummaryDto> incidents){

                                    @JsonIgnore
                                    public Optional<String> getMembersasString() {
                                    return Optional.ofNullable(members.toString());
                                    }
                                    @JsonIgnore
                                    public Optional<String> getIncidentsasString() {
                                    return Optional.ofNullable(incidents.toString());
                                    }
                            }



 */
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;
import java.util.List;

import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;

@Builder
@Data
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