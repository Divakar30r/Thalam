package com.johnreah.postgrestransactions6springdatajdbc;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Account;
import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import com.johnreah.postgrestransactions6springdatajdbc.services.BankingService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.data.jdbc.core.mapping.AggregateReference;
import org.springframework.stereotype.Component;

import java.time.OffsetDateTime;

@Component
@Profile("!test")
public class CommandLineRunnerImpl implements CommandLineRunner {

    private static Logger log = LoggerFactory.getLogger(CommandLineRunnerImpl.class);

    @Autowired
    BankingService bankingService;

	@Override
	public void run(String... args) {
		bankingService.getAllCustomers().stream().forEach(c -> log.debug(String.format("Customer %d: %s", c.getId(), c.toString())));
		bankingService.getAllAccounts().stream().forEach(a -> log.debug(String.format("Account %d: %s", a.getId(), a.toString())));

		Customer customer = bankingService.findCustomerByReference("TEST_CUSTOMER_01");
		log.debug(String.format("Customer %d: %s", customer.getId(), customer.toString()));

		Account newAccount = Account.builder()
				.description("desc")
				.balance(0.0)
				.balanceTimestamp(OffsetDateTime.now())
				.reference("ref")
				.accountTypeId(AggregateReference.to(2L))
				.build();
		bankingService.save(newAccount);
		bankingService.getAllAccounts().stream().forEach(a -> log.debug(String.format("Account %d: %s", a.getId(), a.toString())));
	}

}
