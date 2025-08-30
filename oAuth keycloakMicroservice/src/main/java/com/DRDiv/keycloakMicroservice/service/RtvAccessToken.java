package com.DRDiv.keycloakMicroservice.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.security.oauth2.client.*;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.stereotype.Service;


import java.util.HashMap;
import java.util.Map;


@Service
public class RtvAccessToken {

        public OAuth2AuthorizedClientService auth2AuthorizedClientService(ClientRegistrationRepository
                                                                              clientRegistrationRepository){
        return new InMemoryOAuth2AuthorizedClientService(clientRegistrationRepository);
    }

    //  Creating a manager (helps manage token request)

    public OAuth2AuthorizedClientManager auth2AuthorizedClientManager(ClientRegistrationRepository repos, OAuth2AuthorizedClientService clientService) {

        AuthorizedClientServiceOAuth2AuthorizedClientManager manager = new AuthorizedClientServiceOAuth2AuthorizedClientManager(repos, clientService);
        OAuth2AuthorizedClientProvider provider = OAuth2AuthorizedClientProviderBuilder.builder().clientCredentials().build();
        manager.setAuthorizedClientProvider(provider);
        System.out.println("Manager build ");
        return manager;
    }

    @Autowired
    OAuth2AuthorizedClientManager oAuth2AuthorizedClientManager1;


    public String retreiver(){
        //keycloakprops is the suffix used in the property
        var authRequest = OAuth2AuthorizeRequest.withClientRegistrationId ("keycloakprops").principal("TEST").build();

        OAuth2AuthorizedClient oAuth2AuthorizedClient =  oAuth2AuthorizedClientManager1.authorize(authRequest);
        return oAuth2AuthorizedClient.getAccessToken().getTokenValue();

    }
}
