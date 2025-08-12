package com.DRDiv.DocMgmt.controller.advice.errors;

public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException (String message) {
        super(message);
    }
}
