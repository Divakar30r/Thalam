package org.kolmanfreecss.kfimapiresponseservice.infrastructure.rest;
 
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import lombok.AllArgsConstructor;
 
import reactor.core.publisher.Mono;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.mappers.ResponseConverter;
import org.kolmanfreecss.kfimapiresponseservice.application.services.ResponseService;
import org.kolmanfreecss.kfimapiresponseservice.infrastructure.rest.model.ResponseWrapper;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.IncidentSummaryDto;
import org.kolmanfreecss.kfimapiresponseservice.shared.exceptions.*;
import org.springframework.web.bind.annotation.*;
//import reactor.core.publisher.Mono;

import java.util.List;
 
@AllArgsConstructor
@RestController
@RequestMapping("/api/v1/response")
public class ResponseController {

    private static final Logger log = LoggerFactory.getLogger(ResponseController.class);
    private final ResponseService responseService;

    @Operation(summary = "Create Response team", description = "Save Response team  ")
    @ApiResponse(responseCode = "201", description = "New ResponseTeam saved successfully")
    @ApiResponse(responseCode = "500", description = "Error in creating NewResponseTeam")
    @PostMapping("/")
    public ResponseWrapper<ResponseTeamDto> createTeam(final @RequestBody ResponseTeamDto responseTeamDto) {
        log.info("Creating Response Team: {}", responseTeamDto);
        return new ResponseWrapper<>(responseService.createTeam(responseTeamDto),"Successfully created");
    }


    
    @Operation(summary = "Get All Responses", description = "Get all Responses")
    @ApiResponse(responseCode = "200", description = "Responses retrieved successfully")
    @ApiResponse(responseCode = "500", description = "Error retrieving Responses")
    @GetMapping("/")
    public ResponseWrapper<List<ResponseTeamDto>> getAllResponses() {
         
        return new ResponseWrapper<>(responseService.getAllItems(),"Fetched the list ");
    }
    
    
    @Operation(summary = "Get Response by id", description = "Get Response by the given ResponseId")
    @ApiResponse(responseCode = "200", description = "Response retrieved successfully")
    @ApiResponse(responseCode = "500", description = "Error retrieving Response")
    @GetMapping("/{id}")
    public ResponseWrapper<ResponseTeamDto>  getResponseById(final @PathVariable Long id) {
        if (responseService.getItemById(id)!= null)
        return new ResponseWrapper<>(responseService.getItemById(id),"Fetch by ID");
        else return new ResponseWrapper<>((ResponseTeamDto) null, "No data found");
    }

    @Operation(summary = "Incident updates", description = "Incident updates")
    @ApiResponse(responseCode = "200", description = "Incident updated successfully")
    @ApiResponse(responseCode = "500", description = "Error handling Incident")
    @PutMapping("/")
    public ResponseWrapper<String>  incidentAPI(final @RequestBody ResponseTeamDto responseTeamDto) throws InvalidInputException, UpdFailureException, Exception {
         
        return new ResponseWrapper<String>(responseService.handleIncident(responseTeamDto));
         
    }

    /*
    @Operation(summary = "Update ResponseTeam", description = "Update ResponseTeam users")
    @ApiResponse(responseCode = "200", description = "Response updated successfully")
    @ApiResponse(responseCode = "500", description = "Error updating Response")
    @PutMapping("/")
    public ResponseWrapper<ResponseTeamDto> updateResponse(final @RequestBody ResponseTeamDto responseTeamDto) {
        return ResponseService.addmember(responseTeamDto);
                 
    }
     */
    /*
    @Operation(summary = "Delete Response", description = "Delete Response by ResponseId")
    @ApiResponse(responseCode = "200", description = "Response deleted successfully")
    @ApiResponse(responseCode = "500", description = "Error deleting Response")
    @DeleteMapping("/{id}")
    public Mono<Void> deleteResponse(final @PathVariable Long id) {
        return ResponseService.delete(id)
                .doOnSuccess(recordMetadata -> log.info("Response deleted successfully"))
                .doOnError(exception -> log.error("Error while deleting the Response", exception))
                .then();
    }
    */

}
