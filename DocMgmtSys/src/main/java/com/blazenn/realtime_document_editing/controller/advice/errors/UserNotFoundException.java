package com.blazenn.realtime_document_editing.controller.advice.errors;

public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException (String message) {
        super(message);
    }
}
