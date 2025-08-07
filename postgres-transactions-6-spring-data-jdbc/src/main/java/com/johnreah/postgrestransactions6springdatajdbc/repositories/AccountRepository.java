package com.johnreah.postgrestransactions6springdatajdbc.repositories;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AccountRepository extends CrudRepository<Account, Long> {

    public List<Account> findByIdNotNull();

}
