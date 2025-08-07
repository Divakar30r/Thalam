package com.johnreah.postgrestransactions6springdatajdbc;

import com.johnreah.postgrestransactions6springdatajdbc.entities.Customer;
import com.johnreah.postgrestransactions6springdatajdbc.repositories.CustomerRepository;
import com.johnreah.postgrestransactions6springdatajdbc.support.AbstractIntegrationTest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;

class App6Tests extends AbstractIntegrationTest {

	Logger log = LoggerFactory.getLogger("com.johnreah.postgrestransactions6springdatajdbc.App6Tests");

	@Autowired
	CustomerRepository customerRepository;

	@BeforeEach
	public void beforeEach() {

	}

	@Test
	void contextLoads() {
	}

	@Test
	void testContainerRuns() throws InterruptedException {
		assertTrue(postgreSQLContainer.isRunning());
	}

	@Test
	public void testCustomersExist() {
		List<Customer> customerList = customerRepository.findByIdNotNull();
		assertTrue(customerList.size() > 0, "Num customers should be > 0");
	}

	@Test
	public void whenNewCustomerSaved_thenSavedOk() {
		Customer customer = Customer.builder()
				.firstName("firstName")
				.lastName("lastName")
				.email("email")
				.reference("reference")
				.build();
		long numBefore = customerRepository.count();
		log.debug("Count before = " + numBefore);
		customerRepository.save(customer);
		long numAfter = customerRepository.count();
		log.debug("Count after = " + numAfter);
		assertTrue(numAfter == numBefore + 1, "Num customers should have incremented by one");
	}
}
