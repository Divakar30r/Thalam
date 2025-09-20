package org.kolmanfreecss.kfimapiincidentservice.infrastructure.adapters.out.orm.hibernate;

import java.util.Optional;

import org.kolmanfreecss.kfimapiincidentservice.application.dto.IncidentDto;
import org.kolmanfreecss.kfimapiincidentservice.application.entity.Incident;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.rest.core.annotation.RepositoryRestResource;
import org.springframework.stereotype.Repository;

import reactor.core.publisher.Mono;

/**
 * IncidentHibernateRepository Hibernate Implementation
 * Used to define the methods that the IncidentHibernateRepository must implement.
 * 
 * @version 1.0
 */
@RepositoryRestResource(exported = false) // This annotation is used to disable the automatic prototype generation of the repository.
@Repository
public interface IncidentHibernateRepository extends JpaRepository<Incident, Long> {

    @Query(value = "SELECT * FROM incident WHERE ?1 = incidentId", nativeQuery = true)
    public Optional<Incident> findByIncidentId(String incidentId);

}
