package org.kolmanfreecss.kfimapiresponseservice.application.ports;

import java.util.List;
import java.util.Optional;

import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.rest.core.annotation.RepositoryRestResource;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

 
@RepositoryRestResource(exported = false) // This annotation is used to disable the automatic prototype generation of the repository.
@Repository
public interface ResponseHibernateRepository extends JpaRepository<ResponseTeam, Long> {
    
    @Transactional(readOnly = true)
    @Query(value = "SELECT * FROM responseteam WHERE ?1 = ANY(members)",  nativeQuery = true)
    public Optional<ResponseTeam> findByMember(String member);

    @Transactional(readOnly = true)
    @Query(value = "SELECT * FROM responseteam WHERE ?1 = id",  nativeQuery = true)
    public Optional<ResponseTeam> findById(long id);

    @Transactional(readOnly = true)
    @Query(value = "SELECT * FROM responseteam WHERE ?1 = teamname",  nativeQuery = true)
    public Optional<ResponseTeam> findByTeamName(String teamName);

    @Transactional(readOnly = true)
    @Query(value = "SELECT * FROM responseteam WHERE incidents @> jsonb_build_array(jsonb_build_object('incidentId', ?1))",
               nativeQuery = true)
    public Optional<ResponseTeam> findByINC(String incidentId);

     
    @Modifying
    @Transactional
        @Query(value = """
            UPDATE responseteam 
            SET incidents = COALESCE((
            SELECT jsonb_agg(incident) 
            FROM jsonb_array_elements(incidents) AS incident 
            WHERE incident->>'incidentId' != ?2
), '[]'::jsonb
        )
        WHERE teamname = ?1
        """, nativeQuery = true)
    public int detachIncidentById(String teamname, String incidentId);


/*    @Modifying
    @Transactional
    @Query(value = """
        UPDATE responseteam 
        SET incidents = (
            SELECT jsonb_agg(
                CASE 
                    WHEN (incident->>'incidentId')::bigint = ?2 
                    THEN jsonb_set(incident, '{status}', to_jsonb(?3))
                    THEN jsonb_set(incident, '{assignee}', to_jsonb(?4))
                    ELSE incident
                END
            )
            FROM jsonb_array_elements(incidents) AS incident
        )
        WHERE teamname = ?1 AND incidents @> jsonb_build_array(jsonb_build_object('incidentId', ?2))
        """, nativeQuery = true)
        */
        @Modifying
        @Transactional
        @Query(value = """
        UPDATE responseteam
        SET incidents = (
        SELECT jsonb_agg(
            CASE
            WHEN (incident->>'incidentId') = :incidentId THEN
                incident
                || COALESCE(
                    CASE WHEN :newStatus IS NOT NULL THEN jsonb_build_object('status', :newStatus) END,
                    '{}'::jsonb
                )
                || COALESCE(
                    CASE WHEN :assignee IS NOT NULL THEN jsonb_build_object('assignee', :assignee) END,
                    '{}'::jsonb
                )
                || COALESCE(
                    CASE WHEN :activitytimestamp IS NOT NULL THEN jsonb_build_object('activitytimestampinUTCString', :activitytimestamp) END,
                    '{}'::jsonb
                )
            ELSE incident
            END
        )
        FROM jsonb_array_elements(responseteam.incidents) AS incident
    )
    WHERE teamname = :teamname
    AND incidents @> jsonb_build_array(jsonb_build_object('incidentId', :incidentId))
    """, nativeQuery = true)

    public int updateIncidentDetails(String teamname, String incidentId, String newStatus, String assignee, String activitytimestamp);        
}

