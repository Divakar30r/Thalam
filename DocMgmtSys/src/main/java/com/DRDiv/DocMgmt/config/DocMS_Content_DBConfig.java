package com.DRDiv.DocMgmt.config;

import java.util.HashMap;
import java.util.Map;

import javax.sql.DataSource;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.autoconfigure.orm.jpa.JpaProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.boot.orm.jpa.EntityManagerFactoryBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.orm.jpa.JpaVendorAdapter;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import com.zaxxer.hikari.HikariDataSource;

import jakarta.persistence.EntityManagerFactory;

@Configuration
@EnableTransactionManagement
@EnableJpaRepositories(
    basePackages = "com.DRDiv.DocMgmt.repository.document",
    entityManagerFactoryRef = "DocMS_Content_DB_Entity_Manager_Factory",
    transactionManagerRef = "DocMS_Content_DB_Transaction_Manager_Factory"
)
public class DocMS_Content_DBConfig {

    @Autowired
    private JpaProperties DocMS_Content_DB_jpaProperties;
    
    
    @Bean
    @ConfigurationProperties(prefix = "docmscontent.datasource")
    public DataSourceProperties DocMS_Content_DB_DataSourceProperties() {
        return new DataSourceProperties();
    }
        


    @Bean
    //@ConfigurationProperties(prefix = "docmscontent.datasource")
    public DataSource DocMS_Content_DB_DataSource()  {
        return DocMS_Content_DB_DataSourceProperties().initializeDataSourceBuilder().type(HikariDataSource.class).build();
        //return DataSourceBuilder.  create().build();
    }

    @Bean
    public LocalContainerEntityManagerFactoryBean DocMS_Content_DB_Entity_Manager_Factory(      
         @Qualifier("DocMS_Content_DB_EntityManagerFactoryBuilder") EntityManagerFactoryBuilder DocMS_Content_DB_EntityManagerFactoryBuilder) {

        Map<String, Object> DocMS_Content_DB_props = new HashMap<>(DocMS_Content_DB_jpaProperties.getProperties());
        DocMS_Content_DB_props.put("hibernate.dialect", "org.hibernate.dialect.PostgreSQLDialect");

        return DocMS_Content_DB_EntityManagerFactoryBuilder
                .dataSource(DocMS_Content_DB_DataSource())
                .packages("com.DRDiv.DocMgmt.entity.document")
                .persistenceUnit("DocMS_Content_DB_Persisent")
                .properties(DocMS_Content_DB_props)
                .build();
    }

    @Bean(name="DocMS_Content_DB_EntityManagerFactoryBuilder")
    public EntityManagerFactoryBuilder DocMS_Content_DB_EntityManagerFactoryBuilder(JpaVendorAdapter DocMS_Content_DB_jpaVendorAdapter) {
        return new EntityManagerFactoryBuilder(DocMS_Content_DB_jpaVendorAdapter, new HashMap<>(), null);
    }

    @Bean
    public JpaVendorAdapter DocMS_Content_DB_jpaVendorAdapter() {
        return new HibernateJpaVendorAdapter();
    }
    
    @Bean
    public PlatformTransactionManager DocMS_Content_DB_Transaction_Manager_Factory(
            @Qualifier("DocMS_Content_DB_Entity_Manager_Factory") EntityManagerFactory DocMS_Content_DB_emf) {
        return new JpaTransactionManager(DocMS_Content_DB_emf);
    }


}
