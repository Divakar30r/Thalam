package org.kolmanfreecss.kfimapiresponseservice.infrastructure.rest.model;

    public record ResponseWrapper<T>(String message,T dtoData) {
              public ResponseWrapper(final T dtoData, final String message) {
                    this(message, dtoData);
              }
            
              public ResponseWrapper(final String message) {
                        this(null,message);
                }
                        
    }

     

