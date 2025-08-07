package com.johnreah.postgrestransactions6springdatajdbc.services;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.AccountRepository;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.CustomerRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class BankingService {

    @Autowired
    private CustomerRepository customerRepository;

    @Autowired
    private AccountRepository accountRepository;

    public long countAllCustomers() {
        return customerRepository.count();
    }

    public List<Customer> getAllCustomers() {
        return customerRepository.findByIdNotNull();
    }

    public long countAllAccounts() {
        return accountRepository.count();
    }

    public List<Account> getAllAccounts() {
        return accountRepository.findByIdNotNull();
    }

    public void save(Account account) {
        accountRepository.save(account);
    }

    public Customer findCustomerByReference(String reference) {
        return customerRepository.findByReference(reference);
    }

    public void linkAccountToCustomerAndSave(Account account, Customer customer) {
        customerRepository.linkAccountToCustomer(account, customer);
        customerRepository.save(customer);
    }
    public void RunTransactional(Runnable runnable) throws Exception {
        runnable.run();
    }

    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void RunNonTransactional(Runnable runnable) throws Exception {
        runnable.run();
    }
}
