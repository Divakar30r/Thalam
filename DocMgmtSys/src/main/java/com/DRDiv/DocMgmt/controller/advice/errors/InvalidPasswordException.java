package com.DRDiv.DocMgmt.controller.advice.errors;

public class InvalidPasswordException extends RuntimeException {
    public InvalidPasswordException(String message) {
        super(message);
    }
}
