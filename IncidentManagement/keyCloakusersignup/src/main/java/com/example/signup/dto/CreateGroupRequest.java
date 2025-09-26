package com.example.signup.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CreateGroupRequest {
    @NotBlank
    private String name;
    private String path; // optional explicit path (Keycloak can derive if null)
}
