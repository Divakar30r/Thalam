package com.johnreah.postgrestransactions6springdatajdbc.repositories;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CustomerRepository extends CrudRepository<Customer, Long>, CustomerRepositoryCustom {

    List<Customer> findByIdNotNull();

    Customer findByReference(String reference);

}
