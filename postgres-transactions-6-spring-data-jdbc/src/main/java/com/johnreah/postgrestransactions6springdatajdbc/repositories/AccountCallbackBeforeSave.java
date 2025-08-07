package com.johnreah.postgrestransactions6springdatajdbc.repositories;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.relational.core.conversion.MutableAggregateChange;
import org.springframework.data.relational.core.mapping.event.BeforeSaveCallback;
import org.springframework.stereotype.Component;

@Component
public class AccountCallbackBeforeSave implements BeforeSaveCallback<Account> {

    private static Logger log = LoggerFactory.getLogger(AccountCallbackBeforeSave.class);

    @Override
    public Account onBeforeSave(Account aggregate, MutableAggregateChange<Account> aggregateChange) {
        log.info("Before save: " + aggregateChange.toString());
        return aggregate;
    }
}
