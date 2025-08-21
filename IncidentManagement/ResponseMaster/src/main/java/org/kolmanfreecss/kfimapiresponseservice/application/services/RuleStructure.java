package org.kolmanfreecss.kfimapiresponseservice.application.services;

 
import java.util.List;

public record RuleStructure(String event, List<String> CurrSts, List<String> Mandatory){
 

    public boolean isValidStatus(String Status) {
        return CurrSts.contains(Status);
    };
    public boolean isMandatory(String fieldName) {
        return Mandatory.contains(fieldName);
    };

     
}
