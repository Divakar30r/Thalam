package com.DRDiv.keycloakMicroservice.config;

import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.ILoggerFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {


    Logger log = LoggerFactory.getLogger(SecurityConfig.class);
    @Bean
    public SecurityFilterChain authenticatedChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable) // Disable CSRF for testing purposes
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/Forward/GetDatafromOther").permitAll()
                        .requestMatchers("/error").permitAll()
                        .anyRequest().authenticated()
                ).sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
                // exception handling for Unauthorised or access denied issue
                .exceptionHandling(ex ->
                        ex.authenticationEntryPoint((request, response, authException) -> {
                                    log.error("Unauthorized error: {}", authException.getMessage() + " "+ request.getRequestURL()+ " " +authException.getClass().getName());
                                    response.sendError(
                                            HttpServletResponse.SC_UNAUTHORIZED,
                                            "Unauthorized: " + authException.getMessage()
                                    );
                                })
                                .accessDeniedHandler((request, response, accessDeniedException) -> {
                                    log.error("Access denied error: {}", accessDeniedException.getMessage());
                                    log.error("Request URL: {}", request.getRequestURL());
                                    log.error("User authorities: {}",
                                            SecurityContextHolder.getContext().getAuthentication().getAuthorities());
                                    response.sendError(HttpServletResponse.SC_FORBIDDEN,
                                            "Access Denied: " + accessDeniedException.getMessage());
                                })
                );

        return http.build();
    }

}

