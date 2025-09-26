package com.example.signup.controller;

import com.example.signup.dto.SignupRequest;
import com.example.signup.dto.CreateGroupRequest;
import com.example.signup.dto.LinkUserRequest;
import com.example.signup.dto.SigninRequest;
import com.example.signup.dto.SigninResponse;
import com.example.signup.dto.DelinkUserRequest;
import com.example.signup.service.SignupService;
import com.example.signup.exception.AlreadyExistsException;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
public class SignupController {
    private final SignupService signupService;

    @PostMapping("/signup")
    public ResponseEntity<?> signup(@Valid @RequestBody SignupRequest request) {
        try {
            signupService.signup(request);
            return ResponseEntity.status(HttpStatus.CREATED).body("User registered successfully");
        } catch (AlreadyExistsException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(e.getMessage());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(e.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Signup failed");
        }
    }

    @PostMapping("/groups")
    public ResponseEntity<?> createGroup(@Valid @RequestBody CreateGroupRequest request) {
        try {
            signupService.CreateGroup(request);
            return ResponseEntity.status(HttpStatus.CREATED).body("Group created successfully");
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(e.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Group creation failed");
        }
    }

    @PostMapping("/linkuser")
    public ResponseEntity<?> linkUser(@Valid @RequestBody LinkUserRequest request) {
        try {
            var result = signupService.linkuser(request);
            return ResponseEntity.status(result.status()).body(result.body());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(e.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Linking failed");
        }
    }

    @PostMapping("/delinkuser")
    public ResponseEntity<?> delinkUser(@Valid @RequestBody DelinkUserRequest request) {
        try {
            var result = signupService.delinkuser(request);
            return ResponseEntity.status(result.status()).body(result.body());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(e.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Delinking failed");
        }
    }
}
