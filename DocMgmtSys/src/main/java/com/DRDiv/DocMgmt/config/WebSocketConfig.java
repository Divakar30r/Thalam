package com.DRDiv.DocMgmt.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

import com.DRDiv.DocMgmt.controller.rest.AppUserController;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
Logger log = LoggerFactory.getLogger(WebSocketConfig.class); 

    @Override
    
    public void configureMessageBroker(MessageBrokerRegistry config) {
        log.info("Attempting to config broker");
        config.enableSimpleBroker("/topic");
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        log.info(("attempting to config endpoints "));
        registry.addEndpoint("/ws")
                //.setAllowedOriginPatterns("http://localhost:5173")
                .setAllowedOriginPatterns("*") // ✅ use this instead
                .withSockJS();
    }
}
