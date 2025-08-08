package com.example.repository;

import com.example.entity.AccountEntity;
//import jakarta.transaction.Transactional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.annotation.Propagation;
@Repository
public interface AccountRepository extends JpaRepository<AccountEntity, Long> {

    @Query(value = "select * from account where acc_no = ?1", nativeQuery = true)
    @Transactional
    AccountEntity findByAccNo(Integer accountNumber);

    @Modifying
    @Transactional
    @Query(value = "delete from account where acc_no = ?1", nativeQuery = true)
    void deleteByAccNo(Integer accountNumber);
}
