package org.kolmanfreecss.kfimapiresponseservice.shared.exceptions;

import jakarta.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.http.HttpStatus;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.kolmanfreecss.kfimapiresponseservice.application.services.ResponseService;
import org.kolmanfreecss.kfimapiresponseservice.infrastructure.rest.model.ResponseWrapper;

import java.time.LocalDateTime;

@ControllerAdvice
public class ExceptionHandlerControllerAdvice {


    
    
    @ExceptionHandler(InvalidInputException.class)
    @ResponseStatus(value = HttpStatus.BAD_REQUEST)
    public ResponseWrapper<ResponseTeamDto> InvalidInputsexcmethod(final InvalidInputException exception) {

        return new ResponseWrapper<ResponseTeamDto>(exception.getMessage(),exception.responseTeamDto);
    }

    @ExceptionHandler(UpdFailureException.class)
    @ResponseStatus(value = HttpStatus.EXPECTATION_FAILED)
    public  ResponseWrapper<ResponseTeamDto> UpdateIncidentexcmethod(final UpdFailureException exception) {
        return new ResponseWrapper<ResponseTeamDto>(exception.getMessage(),exception.responseTeamDto);
    }

    @ExceptionHandler(TeamNotFoundException.class)
    @ResponseStatus(value = HttpStatus.EXPECTATION_FAILED)
    public  ResponseWrapper<ResponseTeamDto> TeamNotfoundexcmethod(final UpdFailureException exception) {
        return new ResponseWrapper<ResponseTeamDto>(exception.getMessage(),exception.responseTeamDto);
    }    
    /*
    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    @ResponseStatus(value = HttpStatus.BAD_REQUEST)
    public @ResponseBody ExceptionResponse handleHttpMediaTypeNotSupportedException(final HttpMediaTypeNotSupportedException exception,
                                                                                    final HttpServletRequest request) {

        return ExceptionResponse.builder()
                .errorMessage(exception.getMessage())
                .requestedURI(request.getRequestURI())
                .timestamp(LocalDateTime.now())
                .build();
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    @ResponseStatus(value = HttpStatus.BAD_REQUEST)
    public @ResponseBody ExceptionResponse handleMissingServletRequestParameterException(final MissingServletRequestParameterException exception,
                                                                                         final HttpServletRequest request) {

        return ExceptionResponse.builder()
                .errorMessage(exception.getMessage())
                .requestedURI(request.getRequestURI())
                .timestamp(LocalDateTime.now())
                .build();
    }

    @ExceptionHandler(InsufficientAccountBalanceException.class)
    @ResponseStatus(value = HttpStatus.BAD_REQUEST)
    public @ResponseBody ExceptionResponse handleInsufficientAccountBalanceException(final InsufficientAccountBalanceException exception,
                                                                                     final HttpServletRequest request) {

        return ExceptionResponse.builder()
                .errorMessage(exception.getMessage())
                .requestedURI(request.getRequestURI())
                .timestamp(LocalDateTime.now())
                .build();
    }


    @ExceptionHandler(Exception.class)
    @ResponseStatus(value = HttpStatus.INTERNAL_SERVER_ERROR)
    public @ResponseBody ExceptionResponse handleException(final Exception exception,
                                                           final HttpServletRequest request) {
        exception.printStackTrace();
        return ExceptionResponse.builder()
                .errorMessage(exception.getMessage())
                .requestedURI(request.getRequestURI())
                .timestamp(LocalDateTime.now())
                .build();
    }
                */
}
