package com.blazenn.realtime_document_editing.controller.advice.errors;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.UNAUTHORIZED)
public class JwtUnathorizedException extends RuntimeException {
    public JwtUnathorizedException(String message) {
        super(message);
    }
    public JwtUnathorizedException(String message, Throwable cause) { super(message, cause); }
}
