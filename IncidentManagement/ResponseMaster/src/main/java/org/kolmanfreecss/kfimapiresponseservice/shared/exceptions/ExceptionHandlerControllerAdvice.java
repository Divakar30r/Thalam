package org.kolmanfreecss.kfimapiresponseservice.shared.exceptions;

import jakarta.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.http.HttpStatus;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.services.ResponseService;
import org.kolmanfreecss.kfimapiresponseservice.infrastructure.rest.model.ResponseWrapper;

import java.time.LocalDateTime;

@RestControllerAdvice
public class ExceptionHandlerControllerAdvice {


    
    
    @ExceptionHandler(InvalidInputException.class)
    @ResponseStatus(value = HttpStatus.BAD_REQUEST)
    public ResponseWrapper<ResponseTeamDto> InvalidInputsexcmethod(final InvalidInputException exception) {
        System.out.println("Inside InvalidInputsexcmethod of ExceptionHandlerControllerAdvice");
        return new ResponseWrapper<ResponseTeamDto>(exception.getMessage(),exception.responseTeamDto);
    }

    @ExceptionHandler(UpdFailureException.class)
    @ResponseStatus(value = HttpStatus.EXPECTATION_FAILED)
    public  ResponseWrapper<ResponseTeamDto> UpdateIncidentexcmethod(final UpdFailureException exception) {
        System.out.println("Inside UpdateIncidentexcmethod of ExceptionHandlerControllerAdvice");
        return new ResponseWrapper<ResponseTeamDto>(exception.getMessage(),exception.responseTeamDto);
    }

    @ExceptionHandler(TeamNotFoundException.class)
    @ResponseStatus(value = HttpStatus.EXPECTATION_FAILED)
    public  ResponseWrapper<ResponseTeamDto> TeamNotfoundexcmethod(final TeamNotFoundException exception) {
        System.out.println("Inside TeamNotfoundexcmethod of ExceptionHandlerControllerAdvice");
        return new ResponseWrapper<ResponseTeamDto>(exception.getMessage(),exception.responseTeamDto);
    }    
     
    /* */
    @ExceptionHandler(Exception.class)
    @ResponseStatus(value = HttpStatus.EXPECTATION_FAILED)
    public  ResponseWrapper<ResponseTeamDto> Exception(final Exception exception) {
        System.out.println("Inside general exception of ExceptionHandlerControllerAdvice");
        return new ResponseWrapper<ResponseTeamDto>(exception.getMessage());
    }
}
