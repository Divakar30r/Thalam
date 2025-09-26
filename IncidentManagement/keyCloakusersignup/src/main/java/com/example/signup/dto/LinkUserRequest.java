package com.example.signup.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class LinkUserRequest {
    @NotBlank
    private String userId; // Keycloak internal user UUID
    @NotBlank
    private String groupName; // Desired group to link
}
