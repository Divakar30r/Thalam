package com.johnreah.postgrestransactions6springdatajdbc.repositories;

import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountType;
import org.springframework.data.jdbc.repository.query.Modifying;
import org.springframework.data.jdbc.repository.query.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.stream.Stream;

@Repository
public interface AccountTypeRepository extends CrudRepository<AccountType, Long> {
    public List<AccountType> findByIdNotNull();
    public Stream<AccountType> findByReference(String reference);

    @Modifying
    @Query("delete from link_customer_account")
    public void deleteLinks();
}
