package com.johnreah.postgrestransactions6springdatajdbc.repositories;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.relational.core.conversion.MutableAggregateChange;
import org.springframework.data.relational.core.mapping.event.BeforeDeleteCallback;
import org.springframework.stereotype.Component;

@Component
public class AccountCallbackBeforeDelete implements BeforeDeleteCallback<Account> {

    private static final Logger log = LoggerFactory.getLogger(AccountCallbackBeforeDelete.class);
    @Override
    public Account onBeforeDelete(Account aggregate, MutableAggregateChange<Account> aggregateChange) {
        log.info("Before delete");
        return aggregate;
    }
}
