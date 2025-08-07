package com.johnreah.postgrestransactions6springdatajdbc.support;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountHistory;
import com.johnreah.postgrestransactions6springdatajdbc.entities.AccountType;
import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.AccountRepository;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.AccountTypeRepository;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.CustomerRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.jdbc.core.mapping.AggregateReference;
import org.springframework.stereotype.Component;

import java.time.OffsetDateTime;
import java.util.UUID;

@Component
public class DatabaseUtils {

    @Autowired
    private DatabaseUtilsHelperRepository databaseUtilsHelperRepository;

    @Autowired
    private AccountTypeRepository accountTypeRepository;

    @Autowired
    private AccountRepository accountRepository;

    @Autowired
    private CustomerRepository customerRepository;

    public void deleteEverything() {
        databaseUtilsHelperRepository.deleteLinkCustomerAccount();
        databaseUtilsHelperRepository.deleteAccountHistory();
        databaseUtilsHelperRepository.deleteCustomer();
        databaseUtilsHelperRepository.deleteAccount();
        databaseUtilsHelperRepository.deleteAccountType();
    }

    public AccountType createAndSaveRandomAccountType() {
        AccountType accountType = AccountType.builder()
                .description("Test account type")
                .reference(UUID.randomUUID().toString())
                .build();
        return accountTypeRepository.save(accountType);
    }

    public Account createAndSaveRandomAccount(AccountType accountType) {
        Account account = Account.builder()
                .description("Test account")
                .accountTypeId(AggregateReference.to(accountType.getId()))
                .build();
        for (int i = 0; i < 3; i++) {
            account.getAccountHistories().add(AccountHistory.builder()
                    .description(UUID.randomUUID().toString())
                    .timeStamp(OffsetDateTime.now())
                    .build());
        }
        return accountRepository.save(account);
    }

    public Customer createAndSaveRandomCustomer() {
        Customer customer = Customer.builder()
                .firstName("Test")
                .lastName("Customer")
                .reference("TEST_CUSTOMER_" + UUID.randomUUID().toString())
                .build();
        return customerRepository.save(customer);
    }

    public long countLinkCustomerAccounts() {
        return databaseUtilsHelperRepository.countLinkCustomerAccounts();
    }

    public void setAccountHistoryDescriptionNotNull() {
        databaseUtilsHelperRepository.setAccountHistoryDescriptionNotNull();
    }

    public void dropAccountHistoryDescriptionNotNull() {
        databaseUtilsHelperRepository.dropAccountHistoryDescriptionNotNull();
    }

    public long countAccountHistories() {
        return databaseUtilsHelperRepository.countAccountHistories();
    }

}
