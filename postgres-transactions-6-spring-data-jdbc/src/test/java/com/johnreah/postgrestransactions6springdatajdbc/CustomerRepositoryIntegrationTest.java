package com.johnreah.postgrestransactions6springdatajdbc;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountType;
import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.AccountRepository;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.CustomerRepository;
import com.johnreah.postgrestransactions6springdatajdbc.support.AbstractIntegrationTest;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

import static org.junit.jupiter.api.Assertions.*;

public class CustomerRepositoryIntegrationTest extends AbstractIntegrationTest {

    private static final Logger log = LoggerFactory.getLogger(CustomerRepositoryIntegrationTest.class);

    @Autowired
    private CustomerRepository customerRepository;

    @Autowired
    private AccountRepository accountRepository;

    @Test
    public void testPersistence() {
        Customer customer = Customer.builder()
                .firstName("Test")
                .lastName("Customer")
                .reference("TEST_CUSTOMER")
                .build();
        customer = customerRepository.save(customer);
        assertTrue(customer.getId() != 0, "Customer ID after save should be non-zero");
    }

    @Test
    public void testCustomerAccountLinking() {
        Customer customer = databaseUtils.createAndSaveRandomCustomer();
        assertNotNull(customer, "Customer should not be null");

        AccountType accountType = databaseUtils.createAndSaveRandomAccountType();
        assertNotNull(accountType, "Account type should not be null");

        Account account = databaseUtils.createAndSaveRandomAccount(accountType);
        assertNotNull(account, "Account should not be null");

        customerRepository.linkAccountToCustomer(account, customer);
        customer = customerRepository.save(customer);
        assertTrue(customer.getLinkCustomerAccounts().size() == 1, "Customer should have an account");

        // AT THIS POINT account and customer are inconsistent even though the link table has joined them.
        assertTrue(customer.getLinkCustomerAccounts().size() == 1, "Customer has been updated");
        assertTrue(account.getLinkCustomerAccounts().size() == 1, "Account has been updated in memory only");
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 1, "Link table should have 1 link");

        account = accountRepository.findById(account.getId()).get();
        assertTrue(account.getLinkCustomerAccounts().size() == 1, "Account's links should now be 1");

//        accountRepository.delete(account);
//        customer = customerRepository.findById(customer.getId()).get();
//        assertTrue(customer.getLinkCustomerAccounts().size() == 0, "Customer's accounts should be reduced by deleting account");
        customerRepository.delete(customer);
        account = accountRepository.findById(account.getId()).get();
        assertTrue(account.getLinkCustomerAccounts().size() == 0, "Account's customers should be reduced by deleting customer");
    }

    @Test
    public void createAndDeleteMultiple() {
        // Create 3 accounts
        AccountType accountType = databaseUtils.createAndSaveRandomAccountType();
        Account account1 = databaseUtils.createAndSaveRandomAccount(accountType);
        Account account2 = databaseUtils.createAndSaveRandomAccount(accountType);
        Account account3 = databaseUtils.createAndSaveRandomAccount(accountType);
        assertTrue(accountRepository.count() == 3);

        // Create a customer and link to all 3 accounts
        Customer customer = databaseUtils.createAndSaveRandomCustomer();
        customerRepository.linkAccountToCustomer(account1, customer);
        customerRepository.linkAccountToCustomer(account2, customer);
        customerRepository.linkAccountToCustomer(account3, customer);
        assertEquals(3, customer.getLinkCustomerAccounts().size());
        assertEquals(1, account1.getLinkCustomerAccounts().size());
        assertEquals(1, account2.getLinkCustomerAccounts().size());
        assertEquals(1, account3.getLinkCustomerAccounts().size());
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 0); // no links in database yet
        accountRepository.save(account2);
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 1); // saving the account adds 1 link
        customerRepository.save(customer);
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 3); // saving the customer adds all 3

        // Unlink one of the accounts but don't persist yet - the database is out of sync
        customerRepository.unlinkAccountFromCustomer(account2, customer);
        assertTrue(account1.getLinkCustomerAccounts().size() == 1);
        assertTrue(account2.getLinkCustomerAccounts().size() == 0);
        assertTrue(account3.getLinkCustomerAccounts().size() == 1);
        assertTrue(customer.getLinkCustomerAccounts().size() == 2);
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 3);

        // Now persist the unlinked account - the database is synced again
        accountRepository.save(account2);
        assertTrue(account1.getLinkCustomerAccounts().size() == 1);
        assertTrue(account2.getLinkCustomerAccounts().size() == 0);
        assertTrue(account3.getLinkCustomerAccounts().size() == 1);
        assertTrue(customer.getLinkCustomerAccounts().size() == 2);
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 2);

        // Now delete one of the remaining linked accounts
        accountRepository.delete(account1);
        assertTrue(account1.getLinkCustomerAccounts().size() == 1); // this is out of date but we've just deleted it from the database
        assertTrue(account2.getLinkCustomerAccounts().size() == 0); // this was unlinked previously
        assertTrue(account3.getLinkCustomerAccounts().size() == 1); // this is still linked
        assertTrue(customer.getLinkCustomerAccounts().size() == 2); // this is out of date
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 1); // this was updated in the database by the account deletion

        // Now refresh the customer
        customer = customerRepository.findById(customer.getId()).get();
        assertTrue(customer.getLinkCustomerAccounts().size() == 1); // re-read from database

        // Now delete the customer
        customerRepository.delete(customer);
        assertTrue(databaseUtils.countLinkCustomerAccounts() == 0); // all the database links have now gone
        assertTrue(account3.getLinkCustomerAccounts().size() == 1); // but the account still thinks it's linked

        // Refresh the last remaining account
        account3 = accountRepository.findById(account3.getId()).get();
        assertTrue(account3.getLinkCustomerAccounts().size() == 0); // it's no longer linked
    }

}
