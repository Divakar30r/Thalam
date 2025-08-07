package com.johnreah.postgrestransactions6springdatajdbc.repositories;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;

public interface CustomerRepositoryCustom {
    void linkAccountToCustomer(Account a, Customer customer);
    void unlinkAccountFromCustomer(Account a, Customer customer);

}
