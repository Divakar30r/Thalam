package com.blazenn.realtime_document_editing;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
public class RealtimeDocumentEditingApplication {

	public static void main(String[] args) {
		SpringApplication.run(RealtimeDocumentEditingApplication.class, args);
	}

}
