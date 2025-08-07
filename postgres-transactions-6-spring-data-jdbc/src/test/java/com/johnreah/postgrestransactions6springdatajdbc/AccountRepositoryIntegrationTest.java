package com.johnreah.postgrestransactions6springdatajdbc;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountHistory;
import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountType;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.AccountRepository;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.AccountTypeRepository;
import com.johnreah.postgrestransactions6springdatajdbc.support.AbstractIntegrationTest;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.jdbc.core.mapping.AggregateReference;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.util.List;
import java.util.NoSuchElementException;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

public class AccountRepositoryIntegrationTest extends AbstractIntegrationTest {

    private Logger log = LoggerFactory.getLogger(AccountRepositoryIntegrationTest.class);

    @Autowired
    AccountRepository accountRepository;

    @Autowired
    AccountTypeRepository accountTypeRepository;

    @Test
    public void testPersistence() {
        AccountType accountType = AccountType.builder()
                .description("Test account type")
                .reference("TEST_REF")
                .build();
        accountType = accountTypeRepository.save(accountType);
        assertTrue(accountType != null && accountType.getId() != 0, "AccountType should have saved");

        Account account = Account.builder()
                .description("Test account")
                .accountTypeId(AggregateReference.to(accountType.getId()))
                .build();

        long countBeforeSave = accountRepository.count();
        long id = accountRepository.save(account).getId();
        assertTrue(id != 0, "ID should be non-zero after save");
        long countAfterSave = accountRepository.count();
        assertTrue(countAfterSave == countBeforeSave + 1, "Count should have incremented by 1");

        AccountHistory accountHistory1 = AccountHistory.builder()
                .description("Test account history one")
                .build();
        AccountHistory accountHistory2 = AccountHistory.builder()
                .description("Test account history two")
                .build();
        AccountHistory accountHistory3 = AccountHistory.builder()
                .description("Test account history three")
                .build();
        account.getAccountHistories().add(accountHistory1);
        account.getAccountHistories().add(accountHistory2);
        account.getAccountHistories().add(accountHistory3);
        accountRepository.save(account);
        long countAfterUpdate = accountRepository.count();
        assertTrue(countAfterUpdate == countAfterSave, "Update should keep count the same");

        Optional<Account> accountReloaded = accountRepository.findById(id);
        assertTrue(accountReloaded.isPresent() && accountReloaded.get().getAccountHistories().size() == 3, "All history records should have persisted");
    }

    @Test
    public void createAndDeleteMultiple() {
        AccountType accountType = databaseUtils.createAndSaveRandomAccountType();
        Account account1 = databaseUtils.createAndSaveRandomAccount(accountType);
        Account account2 = databaseUtils.createAndSaveRandomAccount(accountType);
        Account account3 = databaseUtils.createAndSaveRandomAccount(accountType);
        accountRepository.saveAll(List.of(account1, account2, account3));
        assertTrue(accountRepository.count() == 3);

//        accountRepository.deleteAll(); // this won't trigger the pre-delete callbacks
        accountRepository.findAll().forEach(a -> accountRepository.delete(a)); // this one will
        assertTrue(accountRepository.count() == 0, "Accounts should all be gone");
    }

    @Test
    public void isAggregatePersistenceTransactional() {
        assertFalse(TransactionSynchronizationManager.isActualTransactionActive(), "No transaction for this test");

        AccountType accountType = AccountType.builder()
                .description("Test account type")
                .reference("TEST_REF")
                .build();
        accountType = accountTypeRepository.save(accountType);
        assertTrue(accountType != null && accountType.getId() != 0, "AccountType should have saved");

        final Account account = Account.builder()
                .description("Test account")
                .accountTypeId(AggregateReference.to(accountType.getId()))
                .build();

        AccountHistory accountHistory1 = AccountHistory.builder()
                .description("Test account history one")
                .build();
        AccountHistory accountHistory2 = AccountHistory.builder()
                .description(null) // this will violate a not-null constraint
                .build();
        AccountHistory accountHistory3 = AccountHistory.builder()
                .description("Test account history three")
                .build();
        account.getAccountHistories().add(accountHistory1);
        account.getAccountHistories().add(accountHistory2);
        account.getAccountHistories().add(accountHistory3);

        databaseUtils.setAccountHistoryDescriptionNotNull(); // create an error condition
        assertThrows(RuntimeException.class, () -> {
            accountRepository.save(account); // this would normally save the account then its account histories
        });
        databaseUtils.dropAccountHistoryDescriptionNotNull(); // revert our change

        assertTrue(databaseUtils.countAccountHistories() == 0, "Account histories should have rolled back");
        assertTrue(accountRepository.count() == 0, "Account should have rolled back");

        assertThrows(NoSuchElementException.class, () -> {
            Account retrievedAccount = accountRepository.findById(account.getId()).get();
            log.debug(retrievedAccount.toString());
        });
    }
}
