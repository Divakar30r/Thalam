package org.kolmanfreecss.kfimapiresponseservice.application.entity;
import jakarta.persistence.*;
import lombok.*;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.Type;
//import org.hibernate.annotations.TypeDef;
import org.hibernate.type.SqlTypes;

//import com.vladmihalcea.hibernate.type.json.JsonBinaryType;
import org.kolmanfreecss.kfimapiresponseservice.shared.dto.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
 
 
@Data
@Builder
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "Responseteam")
 
 
 
public class ResponseTeam{
     
    
    @Id
    @SequenceGenerator(name = "responseteam_id_seq", sequenceName = "responseteam_id_seq", allocationSize = 1)
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "responseteam_id_seq")
    @Column(name = "id", updatable = false)
    private Long id;

    @Column(nullable = false)
    private String teamname;
    
    
    @Column(columnDefinition = "text[]", nullable = false)
    private List<String> members;

    @JdbcTypeCode(SqlTypes.JSON)
    //@Type(type = "jsonb")
    @Column(name = "incidents", nullable = true,columnDefinition = "jsonb")
    private List<IncidentSummaryDto> incidents;

    @Override
    public int hashCode() {
        return Objects.hash(id, teamname, members, incidents);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ResponseTeam IpObj = (ResponseTeam) o;
        return Objects.equals(id, IpObj.id) && Objects.equals(teamname, IpObj.teamname) && Objects.equals(members, IpObj.members) && Objects.equals(incidents, IpObj.incidents);
    }

// getters and setters for ID and teamname
/*
    public Long getId() {
        return id;
    }

    public String getTeamname() {
        return teamname;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public void setTeamname(String teamname) {
        this.teamname = teamname;
    }

    public void setMembers(List<String> members) {

        this.members = members;
    }

    public void setIncidents(List<IncidentSummaryDto> incidentsArr) {
         
        this.incidents.clear();
        incidentsArr.forEach(itr->{this.incidents.add(itr);});
         
    }

    public List<String> getMembers() {
        return members;
    }

    public List<IncidentSummaryDto> getIncidents() {
        return incidents;
    }

    public ResponseTeam(String teamName2, List<String> members2, List<IncidentSummaryDto> incidents2) {
         
        this.teamname = teamName2;
        this.members = members2 != null ? members2 : new ArrayList<>();
        this.incidents = incidents2 != null ? incidents2 : new ArrayList<>();
    }
*/
}