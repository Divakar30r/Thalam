package com.johnreah.postgrestransactions6springdatajdbc.repositories;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import com.johnreah.postgrestransactions6springdatajdbc.entities.LinkCustomerAccount;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.jdbc.core.mapping.AggregateReference;

public class CustomerRepositoryCustomImpl implements CustomerRepositoryCustom {

    private static Logger log = LoggerFactory.getLogger(CustomerRepositoryCustomImpl.class);

    public void linkAccountToCustomer(Account account, Customer customer) {
        customer.getLinkCustomerAccounts().add(new LinkCustomerAccount(AggregateReference.to(customer.getId()), AggregateReference.to(account.getId())));
        account.getLinkCustomerAccounts().add(new LinkCustomerAccount(AggregateReference.to(customer.getId()), AggregateReference.to(account.getId())));
    }

    public void unlinkAccountFromCustomer(Account account, Customer customer) {
        customer.getLinkCustomerAccounts().remove(new LinkCustomerAccount(AggregateReference.to(customer.getId()), AggregateReference.to(account.getId())));
        account.getLinkCustomerAccounts().remove(new LinkCustomerAccount(AggregateReference.to(customer.getId()), AggregateReference.to(account.getId())));
    }

}
