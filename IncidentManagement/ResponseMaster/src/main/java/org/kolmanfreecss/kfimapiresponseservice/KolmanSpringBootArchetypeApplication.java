package org.kolmanfreecss.kfimapiresponseservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
 
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

 
@SpringBootApplication
@EnableJpaRepositories(basePackages = "org.kolmanfreecss.kfimapiresponseservice.application.ports")
public class KolmanSpringBootArchetypeApplication {

	public static void main(String[] args) {
		SpringApplication.run(KolmanSpringBootArchetypeApplication.class, args);
	}

}
