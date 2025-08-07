package com.johnreah.postgrestransactions6springdatajdbc;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountType;
import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import com.johnreah.postgrestransactions6springdatajdbc.services.BankingService;
import com.johnreah.postgrestransactions6springdatajdbc.support.AbstractIntegrationTest;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import static org.junit.jupiter.api.Assertions.*;

public class BankingServiceIntegrationTest extends AbstractIntegrationTest {

    private static final Logger log = LoggerFactory.getLogger(BankingServiceIntegrationTest.class);

    @Autowired
    BankingService bankingService;

    @Test
    public void testTransactions() {
        assertThrows(RuntimeException.class, () -> {
            bankingService.RunTransactional(() -> {
                log.debug("Transaction active: " + TransactionSynchronizationManager.isActualTransactionActive());
                throw new RuntimeException("cak");
            });
        });
        assertThrows(RuntimeException.class, () -> {
            bankingService.RunNonTransactional(() -> {
                log.debug("Transaction active: " + TransactionSynchronizationManager.isActualTransactionActive());
                throw new RuntimeException("cak");
            });
        });
    }

    @Test
    public void givenTransactionActive_whenMultipleOperations_andNoError_thenSavedOkWithNoRollback() {
        assertDoesNotThrow(() -> {
            bankingService.RunTransactional(() -> {
                assertTrue(TransactionSynchronizationManager.isActualTransactionActive(), "Transaction required for this test");
                AccountType accountType = databaseUtils.createAndSaveRandomAccountType();
                Account account = databaseUtils.createAndSaveRandomAccount(accountType);
                Customer customer = databaseUtils.createAndSaveRandomCustomer();
                bankingService.linkAccountToCustomerAndSave(account, customer);
            });
        });
        assertTrue(bankingService.countAllAccounts() == 1, "Account should have persisted");
        assertTrue(bankingService.countAllCustomers() == 1, "Customer should have persisted");
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 1, "Customer and account should be linked");
    }

    @Test
    public void givenTransactionActive_whenMultipleOperations_andError_thenExceptionAndRollback() {
        assertThrows(RuntimeException.class, () -> {
            bankingService.RunTransactional(() -> {
                assertTrue(TransactionSynchronizationManager.isActualTransactionActive(), "Transaction required for this test");
                AccountType accountType = databaseUtils.createAndSaveRandomAccountType();
                Account account = databaseUtils.createAndSaveRandomAccount(accountType);
                Customer customer = databaseUtils.createAndSaveRandomCustomer();
                assertTrue(bankingService.countAllAccounts() == 1, "Account should have persisted so far");
                assertTrue(bankingService.countAllCustomers() == 1, "Customer should have persisted so far");
                assertTrue(databaseUtils.countLinkCustomerAccounts() == 0, "No links at this point");
                customer.setId(-1);
                bankingService.linkAccountToCustomerAndSave(account, customer); // generate error
                assertTrue(false, "We should never get here");
            });
        });
        assertTrue(bankingService.countAllAccounts() == 0, "Account should have been rolled back");
        assertTrue(bankingService.countAllCustomers() == 0, "Customer should have been rolled back");
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 0, "Still no links");
    }

    @Test
    public void givenTransactionNotActive_whenMultipleOperations_andError_thenExceptionButNoRollback_andDebrisLeftBehind() {
        assertThrows(RuntimeException.class, () -> {
            bankingService.RunNonTransactional(() -> {
                assertFalse(TransactionSynchronizationManager.isActualTransactionActive(), "No transaction in this test");
                AccountType accountType = databaseUtils.createAndSaveRandomAccountType();
                Account account = databaseUtils.createAndSaveRandomAccount(accountType);
                Customer customer = databaseUtils.createAndSaveRandomCustomer();
                assertTrue(bankingService.countAllAccounts() == 1, "Account should have persisted so far");
                assertTrue(bankingService.countAllCustomers() == 1, "Customer should have persisted so far");
                assertTrue(databaseUtils.countLinkCustomerAccounts() == 0, "No links at this point");
                customer.setId(-1);
                bankingService.linkAccountToCustomerAndSave(account, customer); // generate error
                assertTrue(false, "We should never get here");
            });
        });
        assertTrue(bankingService.countAllAccounts() == 1, "Account should not have been rolled back");
        assertTrue(bankingService.countAllCustomers() == 1, "Customer should not have been rolled back");
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 0, "Links never changed");
    }

}
