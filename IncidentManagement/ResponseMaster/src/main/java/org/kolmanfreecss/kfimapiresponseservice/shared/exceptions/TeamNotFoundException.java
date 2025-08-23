package org.kolmanfreecss.kfimapiresponseservice.shared.exceptions;

import java.io.Serial;

import org.kolmanfreecss.kfimapiresponseservice.application.dto.ResponseTeamDto;
import org.springframework.beans.factory.annotation.Autowired;


public class TeamNotFoundException  extends Exception{

    @Serial
    private static final long serialVersionUID = 523016048628748232L;

    @Autowired
    ResponseTeamDto responseTeamDto;

    public TeamNotFoundException() {
        super();
    }

    public TeamNotFoundException(final String message, ResponseTeamDto responseTeamDto  ) {
        super(message);
        this.responseTeamDto = responseTeamDto;

    }


}


