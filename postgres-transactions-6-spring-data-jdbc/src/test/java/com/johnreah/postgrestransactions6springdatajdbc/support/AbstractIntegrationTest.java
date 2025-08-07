package com.johnreah.postgrestransactions6springdatajdbc.support;

import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.containers.wait.strategy.LogMessageWaitStrategy;
import org.testcontainers.utility.DockerImageName;

import java.time.Duration;
import java.time.temporal.ChronoUnit;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
public abstract class AbstractIntegrationTest {

	private static DockerImageName postgresImageName = DockerImageName.parse("fastlight/postgres-transaction-test").asCompatibleSubstituteFor("postgres");

	protected static final PostgreSQLContainer postgreSQLContainer;

	static {
		postgreSQLContainer = new PostgreSQLContainer<>(postgresImageName)
				.withUsername("postgres")
				.withPassword("postgres")
				.waitingFor(new LogMessageWaitStrategy()
						.withRegEx(".*database system is ready to accept connections.*\\s")
						.withTimes(1)
						.withStartupTimeout(Duration.of(60L, ChronoUnit.SECONDS)));
		postgreSQLContainer.start();
	}

	@DynamicPropertySource
	public static void configure(DynamicPropertyRegistry registry) {
		registry.add("spring.datasource.url", postgreSQLContainer::getJdbcUrl);
		registry.add("spring.datasource.username", postgreSQLContainer::getUsername);
		registry.add("spring.datasource.password", postgreSQLContainer::getPassword);
	}

	@Autowired
	protected DatabaseUtils databaseUtils;

	@BeforeEach
	public void beforeEach() {
		databaseUtils.deleteEverything();
	}

}
