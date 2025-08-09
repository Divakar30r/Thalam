package com.blazenn.realtime_document_editing.repository;


import com.blazenn.realtime_document_editing.model.AppUser;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface AppUserRepository extends JpaRepository<AppUser, Long> {
    AppUser findAppUserByEmail(String email);
}
