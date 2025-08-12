package com.DRDiv.DocMgmt;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.Instant;
import java.util.Random;

import javax.sql.DataSource;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;

import com.DRDiv.DocMgmt.config.DocMS_Content_DBConfig;
import com.DRDiv.DocMgmt.dto.AppUserDTO;
import com.DRDiv.DocMgmt.dto.DocumentDTO;
import com.DRDiv.DocMgmt.service.AppUserService;
import com.DRDiv.DocMgmt.service.DocumentService;
import com.zaxxer.hikari.HikariDataSource;

@SpringBootTest
class RealtimeDocumentEditingApplicationTests {

	DocMS_Content_DBConfig docMS_Content_DBConfig=new DocMS_Content_DBConfig();

	/*
	@Autowired
    @Qualifier("DocMS_Content_DB_DataSource")
    private DataSource dataSource;
*/

	@Autowired
	AppUserService appUserService;

	@Autowired
	DocumentService documentService;

	AppUserDTO appUserDTO = new AppUserDTO();
	DocumentDTO documentDTO = new DocumentDTO();

	/* JUnit doesn't take constructor injections
	RealtimeDocumentEditingApplicationTests(AppUserDTO appUserDTO){
		this.appUserDTO = appUserDTO;
	}
	 
	
	@Test
	void printingDatasources(){

		 
		
		        assertNotNull(dataSource);
        
        // Check if it's a HikariDataSource and print its properties
        if (dataSource instanceof HikariDataSource) {
            HikariDataSource hikariDS = (HikariDataSource) dataSource;
            System.out.println("JDBC URL: " + hikariDS.getJdbcUrl());
            System.out.println("Username: " + hikariDS.getUsername());
            System.out.println("Driver Class: " + hikariDS.getDriverClassName());
            System.out.println("Pool Name: " + hikariDS.getPoolName());
        }
		else{
			System.out.println("not Hikari");
		}
        
		 

        // Test actual connection
        try (Connection connection = dataSource.getConnection()) {
            assertNotNull(connection);
            System.out.println("Connection successful!");
            System.out.println("Database Product Name: " + connection.getMetaData().getDatabaseProductName());
        }
		catch(SQLException e){ e.printStackTrace();};
	}
*/
	@Test
	void contextLoads() {
	}

	@Test
	void insertRec(){
		appUserDTO.setCreatedDate(Instant.now());
		appUserDTO.setFirstName("U1");
		appUserDTO.setEmail("U2@c.com" + (new Random().nextInt(9000) + 1000));
		appUserDTO.setLastName("U1L");
		appUserDTO.setPassword("N1Ds");
		appUserDTO.setCreatedBy("dssds");
		//appUserService.create(appUserDTO);

		
		documentDTO.setTitle("dDoc 1");
		documentDTO.setContent(("first conent \n text to read"));
		//documentService.save(documentDTO);
	}

}
