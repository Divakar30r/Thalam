package com.blazenn.realtime_document_editing.controller.advice.errors;

public class InvalidPasswordException extends RuntimeException {
    public InvalidPasswordException(String message) {
        super(message);
    }
}
