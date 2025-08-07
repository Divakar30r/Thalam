package com.johnreah.postgrestransactions6springdatajdbc;

import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountType;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.AccountTypeRepository;
import com.johnreah.postgrestransactions6springdatajdbc.support.AbstractIntegrationTest;
import com.johnreah.postgrestransactions6springdatajdbc.support.DatabaseUtils;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class AccountTypeRepositoryIntegrationTest extends AbstractIntegrationTest {

    private Logger log = LoggerFactory.getLogger(AccountTypeRepositoryIntegrationTest.class);

    @Autowired
    private AccountTypeRepository accountTypeRepository;

    @Test
    public void testPersistence() {
        long countBefore = accountTypeRepository.count();
        AccountType accountType = AccountType.builder()
                .description(UUID.randomUUID().toString())
                .reference(UUID.randomUUID().toString())
                .build();
        accountTypeRepository.save(accountType);
        long countAfter = accountTypeRepository.count();
        log.debug(String.format("Count before = %d, count after = %d", countBefore, countAfter));
        assertTrue(countAfter == countBefore + 1, "Count should have incremented by 1");
    }
}
