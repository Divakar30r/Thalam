package org.kolmanfreecss.kfimapiresponseservice.application.mappers;
import lombok.NoArgsConstructor;

import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;
import org.springframework.stereotype.Component;

@Component
public class ResponseConverter {

    public ResponseTeamDto toDto(final ResponseTeam responseTeam) {
        return   ResponseTeamDto.builder()
        .teamName(responseTeam.getTeamname())
        .members(responseTeam.getMembers())
        .incidents(responseTeam.getIncidents())
        .build();
    }

    public ResponseTeam toEntity(final ResponseTeamDto responseTeamDto) {
        System.out.println("Converting ResponseTeamDto to ResponseTeam: " + responseTeamDto.getIncidents());
        return ResponseTeam.builder()
                .teamname(responseTeamDto.getTeamName())
                .members(responseTeamDto.getMembers())
                .incidents(responseTeamDto.getIncidents())
                .build();
    }
        

}
