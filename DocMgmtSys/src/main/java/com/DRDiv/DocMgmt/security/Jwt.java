package com.DRDiv.DocMgmt.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
public class Jwt {
    Logger log = LoggerFactory.getLogger(Jwt.class);
    @Value("${jwt.secret}")
    private String secret;
    @Value("${jwt.expiration}")
    private String expiration;


    @Autowired
    JwtSigner jwtSigner;


    public String createToken(String email) {
        Claims claims = Jwts.claims().setSubject(email);
        return Jwts.builder().setClaims(claims).setSubject(email).setExpiration(new Date(System.currentTimeMillis() + Long.parseLong(expiration))).signWith(SignatureAlgorithm.HS256, secret).compact();
    }

    public Boolean validateToken(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(secret).build().parse(token);
            return true;
        } catch (Exception e) {
            // validate from keystore
            if (jwtSigner.validateJWTtoken(token)) return true;
                try{
                    System.out.println(" starting JWT validation");
                    if (jwtSigner.validateJWTtoken(token)) return true;
                    
                }catch(Exception e1){
                    log.error("Exception while validating token", e.fillInStackTrace());
                    log.error("Exception while validating JWTtoken", e1.fillInStackTrace());
                }
                return false;
            }
        
    }

    public String getEmailFromToken(String token) {
        return Jwts.parserBuilder().setSigningKey(secret).build().parseClaimsJws(token).getBody().getSubject();
    }
}
