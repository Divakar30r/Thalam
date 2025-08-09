package com.blazenn.realtime_document_editing.security;

import com.blazenn.realtime_document_editing.controller.advice.errors.JwtUnathorizedException;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;


import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.servlet.HandlerExceptionResolver;

import java.io.IOException;

@Component
public class JwtAuthorization extends OncePerRequestFilter {
    private final Jwt jwt;
    private final HandlerExceptionResolver handlerExceptionResolver;

    public JwtAuthorization(Jwt jwt, HandlerExceptionResolver handlerExceptionResolver) {
        this.jwt = jwt;
        this.handlerExceptionResolver = handlerExceptionResolver;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        try {
            String bearerToken = request.getHeader("Authorization");
            if (bearerToken == null || !bearerToken.startsWith("Bearer ")) {
                filterChain.doFilter(request, response);
                return;
            }
            String token = bearerToken.substring(7);
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
    }
}
