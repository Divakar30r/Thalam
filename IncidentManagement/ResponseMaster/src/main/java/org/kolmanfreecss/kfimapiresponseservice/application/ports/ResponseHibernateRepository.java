package org.kolmanfreecss.kfimapiresponseservice.application.ports;

import org.kolmanfreecss.kfimapiresponseservice.application.entity.ResponseTeam;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.rest.core.annotation.RepositoryRestResource;
import org.springframework.stereotype.Repository;

 
@RepositoryRestResource(exported = false) // This annotation is used to disable the automatic prototype generation of the repository.
@Repository
public interface ResponseHibernateRepository extends JpaRepository<ResponseTeam, Long> {
}

