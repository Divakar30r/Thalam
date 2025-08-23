package org.kolmanfreecss.kfimapiresponseservice.shared.dto;

 

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Builder
@Data
@AllArgsConstructor
@NoArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonPropertyOrder({"incidentId", "eveenttype", "status", "assignee", "activitytimestamp"})
public class IncidentSummaryDto  {
      
 
    @JsonProperty
    @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED, description = "Unique ID of the incident")
    private Long incidentId;

    @JsonProperty
    @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED, description = "event of the activity")
    private String eventtype;    
 
    @JsonProperty
    @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED, description = "Current status of the incident")
    String status;

    @JsonProperty
    @Schema(requiredMode = Schema.RequiredMode.NOT_REQUIRED, description = "Current status of the incident")
    private String assignee;

    @JsonProperty
    @Schema(requiredMode = Schema.RequiredMode.REQUIRED, description = "Timestamp of the recent activity on the incident")
    private String activitytimestampinUTCString;

}
