package com.example.signup.exception;

public class AlreadyExistsException extends RuntimeException {
    public AlreadyExistsException(String message) { super(message); }
}