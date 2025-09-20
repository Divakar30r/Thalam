package org.kolmanfreecss.kfimapiresponseservice.application.services;

import java.util.concurrent.Callable;

import org.kolmanfreecss.kfimapiresponseservice.shared.exceptions.InvalidInputException;
import org.kolmanfreecss.kfimapiresponseservice.shared.exceptions.UpdFailureException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ResponseTransactionService {
    
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public <T> T RunTransactional(Callable<T> task) throws InvalidInputException, UpdFailureException, Exception {

        Logger log = LoggerFactory.getLogger(ResponseService.class);
        try{
            return task.call();
        }
        catch(InvalidInputException iie){
            log.error("InvalidInputException in RunTransactional: " + iie.getMessage());
            throw iie;
        }
        catch(UpdFailureException ufe){
            log.error("UpdFailureException in RunTransactional: " + ufe.getMessage());
            throw ufe;
        }
        catch(Exception e){
            log.error("Exception in RunTransactional: " + e.getMessage());
            throw e;
        }
        //return task.call();
    }
    
 

}
