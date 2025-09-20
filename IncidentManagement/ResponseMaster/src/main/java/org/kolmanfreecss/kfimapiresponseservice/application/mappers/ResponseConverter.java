package org.kolmanfreecss.kfimapiresponseservice.application.mappers;
 

import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;
import org.springframework.stereotype.Component;

@Component
public class ResponseConverter {

    public ResponseTeamDto toDto(final ResponseTeam responseTeam) {
        return   ResponseTeamDto.builder()
        .id(responseTeam.getId())
        .teamName(responseTeam.getTeamname())
        .members(responseTeam.getMembers())
        .incidents(responseTeam.getIncidents())
        .build();
    }

    public ResponseTeam toEntity(final ResponseTeamDto responseTeamDto) {
        System.out.println("Converting ResponseTeamDto to ResponseTeam: " + responseTeamDto.getIncidents());
        return ResponseTeam.builder()
                .id(responseTeamDto.getId())
                .teamname(responseTeamDto.getTeamName())
                .members(responseTeamDto.getMembers())
                .incidents(responseTeamDto.getIncidents())
                .build();
    }
        

}
