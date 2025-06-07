package com.example.app;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;

@Configuration
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // Permit public access to the root, error, and OAuth2 endpoints.
            // Notice that "/welcome" is no longer in the permitAll list.
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers("/", "/error", "/oauth2/**").permitAll()
                .anyRequest().authenticated()
            )
            // Return 401 for unauthorized REST API calls instead of redirecting
            //.exceptionHandling(exception -> exception
            //    .authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED))
            //)
            // Configure OAuth2 login
            .oauth2Login(oauth2 -> oauth2
                // On successful authentication, always redirect to "/api/records"
                .defaultSuccessUrl("/api/records", true)
            )
            // Disable CSRF for stateless REST APIs
            .csrf(csrf -> csrf.disable());
        
        return http.build();
    }
}