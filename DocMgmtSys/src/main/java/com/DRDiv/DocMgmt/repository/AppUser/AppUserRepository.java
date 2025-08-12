package com.DRDiv.DocMgmt.repository.AppUser;


import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.DRDiv.DocMgmt.entity.AppUser.AppUserEntity;

@Repository
public interface AppUserRepository extends JpaRepository<AppUserEntity, Long> {
    AppUserEntity findAppUserByEmail(String email);
}
