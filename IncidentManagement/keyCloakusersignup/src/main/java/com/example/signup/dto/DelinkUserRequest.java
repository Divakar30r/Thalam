package com.example.signup.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class DelinkUserRequest {
    @NotBlank
    private String userId;
    @NotBlank
    private String groupName;
}