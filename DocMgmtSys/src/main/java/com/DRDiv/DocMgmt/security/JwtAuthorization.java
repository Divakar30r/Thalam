package com.DRDiv.DocMgmt.security;

import com.DRDiv.DocMgmt.controller.advice.errors.JwtUnathorizedException;
import com.DRDiv.DocMgmt.controller.rest.AppUserController;
import com.nimbusds.jwt.JWTClaimsSet;

import io.jsonwebtoken.Claims;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.web.authentication.WebAuthenticationDetails;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.servlet.HandlerExceptionResolver;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;
import java.util.Map;

@Component
public class JwtAuthorization extends OncePerRequestFilter {
    private final Jwt jwt;
    private final HandlerExceptionResolver handlerExceptionResolver;
    Logger log = LoggerFactory.getLogger(AppUserController.class);

    public JwtAuthorization(Jwt jwt, HandlerExceptionResolver handlerExceptionResolver) {
        this.jwt = jwt;
        this.handlerExceptionResolver = handlerExceptionResolver;
    }

    @Autowired
    KeycloakJwtValidator keycloakJwtValidatorobj;
/* 
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        try {
            log.info("Request header" + request.getHeader(ALREADY_FILTERED_SUFFIX));
            
            Enumeration<String> headerNames = request.getHeaderNames();
            while (headerNames.hasMoreElements()) {
            String headerName = headerNames.nextElement();
            String headerValue = request.getHeader(headerName);
            log.info("Header: " + headerName + " = " + headerValue);
            }

     
            String bearerToken = request.getHeader("Authorization");
            if (bearerToken == null || !bearerToken.startsWith("Bearer ")) {
                filterChain.doFilter(request, response);
                return;
            }
            log.info("Bearer details: ", bearerToken);
            String token = bearerToken.substring(7);
            log.info("token details: ", token);
            if (Boolean.FALSE.equals(jwt.validateToken(token))) {
                throw new JwtUnathorizedException("Invalid JWT token found.");
            }
            String email = jwt.getEmailFromToken(token);
            UsernamePasswordAuthenticationToken authenticationToken = new UsernamePasswordAuthenticationToken(email, null, null);
            SecurityContextHolder.getContext().setAuthentication(authenticationToken);
            filterChain.doFilter(request, response);
        } catch (JwtUnathorizedException e) {
            handlerExceptionResolver.resolveException(request, response, null, e);
        }
    } */

@Override
protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
    try {
         
        String bearerToken = request.getHeader("Authorization");
 
        if (bearerToken == null || !bearerToken.startsWith("Bearer ")) {
            log.warn("No bearer token found or invalid format");
            filterChain.doFilter(request, response);
            return;
        }

        String token = bearerToken.substring(7);
        log.info("Extracted token: {}", token);

        

        if (Boolean.FALSE.equals(jwt.validateToken(token))) {
            throw new JwtUnathorizedException("Invalid JWT token found.");
        
        }

         
        // Add authorities to the authentication token
        List<SimpleGrantedAuthority> authorities = Collections.singletonList(
            new SimpleGrantedAuthority("ROLE_USER")
        );

        try{
        String email = jwt.getEmailFromToken(token);
        UsernamePasswordAuthenticationToken authenticationToken = 
            new UsernamePasswordAuthenticationToken(email, token, authorities);
        //log.info(" Authentication token "+ authenticationToken.toString());
            
        SecurityContextHolder.getContext().setAuthentication(authenticationToken)  ;
        }
        catch(Exception e){
        System.out.println(" Authentication conetext for JWT");     
           Map<String,Object> JWTClaimsInfo =        keycloakJwtValidatorobj.getJWTClaimsInfo((String) token);
           JWTClaimsInfo.entrySet().forEach(obj ->System.out.println(obj.getKey()+":"+obj.getValue()));
           String username =  JWTClaimsInfo.get("subject").toString();
           List<String> JWTroles = new ArrayList<>();
           JWTroles.add(JWTClaimsInfo.get("roles").toString());
           authorities = JWTroles.stream().map(role -> new SimpleGrantedAuthority("ROLE_" + role)).toList();
           UsernamePasswordAuthenticationToken auth =  new UsernamePasswordAuthenticationToken(username, null, authorities);
           SecurityContextHolder.getContext().setAuthentication(auth);
        }
    
        

        filterChain.doFilter(request, response);
    } catch (JwtUnathorizedException e) {
        log.error("JWT Authorization failed: {}", e.getMessage());
        handlerExceptionResolver.resolveException(request, response, null, e);
    }
}
}
