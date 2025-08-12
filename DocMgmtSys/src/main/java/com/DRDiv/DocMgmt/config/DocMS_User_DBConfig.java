package  com.DRDiv.DocMgmt.config;

import java.util.HashMap;
import java.util.Map;

import javax.sql.DataSource;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.autoconfigure.orm.jpa.JpaProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
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
/*
 * org.springframework.orm.jpa.JpaTransactionManager
org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean
jakarta.persistence.EntityManagerFactory (for Spring Boot 3+)
javax.sql.DataSource
org.springframework.boot.autoconfigure.jdbc.DataSourceProperties
org.springframework.boot.orm.jpa.EntityManagerFactoryBuilder
org.springframework.transaction.PlatformTransactionManager
org.springframework.context.annotation.Bean
org.springframework.context.annotation.Configuration
org.springframework.data.jpa.repository.config.EnableJpaRepositories
org.springframework.transaction.annotation.EnableTransactionManagement
org.springframework.beans.factory.annotation.Qualifier
org.springframework.boot.context.properties.ConfigurationProperties
 */

import jakarta.persistence.EntityManagerFactory;
  
@Configuration
@EnableTransactionManagement
@EnableJpaRepositories(
    basePackages = "com.DRDiv.DocMgmt.repository.AppUser",
    entityManagerFactoryRef = "DocMS_User_DB_Entity_Manager_Factory",
    transactionManagerRef = "DocMS_User_DB_Transaction_Manager_Factory"
)
public class DocMS_User_DBConfig {


    @Autowired
    private JpaProperties DocMS_User_DB_jpaProperties;
    

 
    // Define DataSource, EntityManagerFactory, TransactionManager for DB1
    @Bean
    @ConfigurationProperties(prefix = "docms-user-db-property.datasource")
    public DataSourceProperties docMS_User_DB_DataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    public DataSource DocMS_User_DB_DataSource() {
        return docMS_User_DB_DataSourceProperties().initializeDataSourceBuilder().build();
    }


    @Bean
    public LocalContainerEntityManagerFactoryBean DocMS_User_DB_Entity_Manager_Factory(
           @Qualifier("DocMS_User_DB_EntityManagerFactoryBuilder") EntityManagerFactoryBuilder docMS_User_DB_EntityManagerFactoryBuilder) {

        Map<String, Object> DocMS_User_DB_props = new HashMap<>(DocMS_User_DB_jpaProperties.getProperties());
        DocMS_User_DB_props.put("hibernate.dialect", "org.hibernate.dialect.PostgreSQLDialect");
            
        return docMS_User_DB_EntityManagerFactoryBuilder
                .dataSource(DocMS_User_DB_DataSource())
                .packages("com.DRDiv.DocMgmt.entity.AppUser")
                .persistenceUnit("DocMS_User_DB_Persistent")
                .properties(DocMS_User_DB_props)
                .build();
    }

    @Bean(name = "DocMS_User_DB_EntityManagerFactoryBuilder")
    public EntityManagerFactoryBuilder DocMS_User_DB_EntityManagerFactoryBuilder(JpaVendorAdapter DocMS_User_DB_jpaVendorAdapter) {
        return new EntityManagerFactoryBuilder(DocMS_User_DB_jpaVendorAdapter, new HashMap<>(), null);
    }

    @Bean
    public JpaVendorAdapter DocMS_User_DB_jpaVendorAdapter() {
        return new HibernateJpaVendorAdapter();
    }
    @Bean
    public PlatformTransactionManager DocMS_User_DB_Transaction_Manager_Factory(
            @Qualifier("DocMS_User_DB_Entity_Manager_Factory") EntityManagerFactory DocMS_User_DB_emf) {
        return new JpaTransactionManager(DocMS_User_DB_emf);
    }
}
