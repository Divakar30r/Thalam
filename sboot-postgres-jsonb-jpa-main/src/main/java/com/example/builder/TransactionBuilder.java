package com.example.builder;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import com.example.constant.AccountConstants;
import com.example.deserializer.AccountDetailsDeserializer;
import com.example.entity.AccountEntity;
import com.example.exception.BadRequestException;
import com.example.exception.ResourceNotFoundException;
import com.example.model.Account;
import com.example.model.Transaction;
import com.example.repository.AccountRepository;
import com.example.service.AccountService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.java.Log;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Field;

@Component
public class TransactionBuilder {

    private String eventdesc = "";
    Long totalTrAmt_o=0L;
    Long CurrentBal_n = 0L;
  
/*
    AccountService accountService;
    AccountDetailsDeserializer accountDetailsDeserializer;
    AccountRepository accountRepository;
*/
    @Autowired
    @Lazy
    AccountService accountService;

    @Autowired
    @Lazy
    AccountRepository accountRepository_2;

    @Autowired
    @Lazy
    AccountDetailsDeserializer accountDetailsDeserializer_2;
/*
    public TransactionBuilder(AccountService accountService, AccountDetailsDeserializer accountDetailsDeserializer, AccountRepository accountRepository ){
        this.accountService = accountService;
        this.accountDetailsDeserializer = accountDetailsDeserializer;
        this.accountRepository = accountRepository;
    }
*/
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public List<Transaction> generate (Account account_n, Optional<Transaction> InpTr){
        Optional<AccountEntity> account_o = Optional.ofNullable(this.accountRepository_2.findByAccNo(account_n.getAccountNumber()));

        
    
        /*
         * if account_o.empty -> then new record
         *   do not set current bal and transaction amount
         * if account_o.isPresent but InpTr.empty -> Update account
         *   do not set current bal and transaction amount
         *
         * 
         */
        
        Transaction transaction_n = new Transaction();
        Account account_dtl_o = new Account();

        List<Transaction> transaction_o = new ArrayList<>();

        if (account_o.isPresent())  {
             account_dtl_o = accountDetailsDeserializer_2.deserializeAccount(account_o.get());
             transaction_o = account_dtl_o.getAccountTransactions();
             transaction_o.sort(Comparator.comparing(Transaction::getTs).reversed());
            // final ObjectMapper o1 = new ObjectMapper();
            // System.out.println(" Old string: " + (((ObjectNode) (o1.valueToTree((Object) account_dtl_o) )).required("accountBranch")).toPrettyString());   
            // System.out.println(" New string: " + (((ObjectNode) (o1.valueToTree((Object) account_n) )).required("accountBranch")).toPrettyString());
              
        }
        if (account_o.isEmpty() && InpTr.isEmpty()) {
            eventdesc =  AccountConstants.EVENT_CREATE_ACCOUNT.getMessage()  + " @Branch:" + account_n.getAccountBranch();
            transaction_n =Transaction.builder()
                .type(eventdesc)
                .ts(LocalDateTime.now().toString())
                .build();
        }
        else if (account_o.isPresent() && InpTr.isEmpty())
        {   
            eventdesc =  AccountConstants.EVENT_ACCOUNT_UPDATE.getMessage();

            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> map_o = mapper.convertValue(account_dtl_o, new TypeReference<Map<String, Object>>() {});
            map_o.remove("accountTransactions");
            Map<String, Object> map_n = mapper.convertValue(account_n, new TypeReference<Map<String, Object>>() {});
            map_n.remove("accountTransactions");
            /*
            try {
            
                " / " + " Old Details: \" :" + mapper.writeValueAsString(map_o) +
                " / " + " New Details: \" :" + mapper.writeValueAsString(map_n);
            } catch (JsonProcessingException e) {
                 
                eventdesc =  AccountConstants.EVENT_ACCOUNT_UPDATE.getMessage();
            }
            */
            
            (compareObjectsViaJson((Object) account_dtl_o, (Object) account_n)).entrySet().forEach(ObjCompItr ->{
                eventdesc += " / " +  ObjCompItr.getKey() + " : " +  ObjCompItr.getValue();
            });
            /* The above can also be written as  
            (compareObjectsViaJson((Object) account_dtl_o, (Object) account_n)).forEach((ObjCompItr_key, ObjCompItr_Value) -> {
                eventdesc = "Field:" + ObjCompItr_key + " " + " Value change: "+ ObjCompItr_Value;
            });
            */
             

            transaction_n =Transaction.builder()
                .type(eventdesc)
                .ts(LocalDateTime.now().toString())
                .build();
        }    
        else if (account_o.isPresent() && InpTr.isPresent())
        {      
            

            totalTrAmt_o = transaction_o.stream().filter(trItr -> trItr.getType().toLowerCase().contains("transaction"))
                    .mapToLong(Transaction ::getTransactionAmt).sum();

            CurrentBal_n = totalTrAmt_o + (InpTr.get()).getTransactionAmt();
            eventdesc = (InpTr.get()).getType()+ " / " +   " Old Bal:" +account_dtl_o.getAccountCurrentBalance() + " Current Balance:" + account_n.getAccountCurrentBalance() 
                            + " / " + " Old TrAmt:" + String.valueOf(totalTrAmt_o) +  " New TrAmt:" +  String.valueOf(CurrentBal_n);
            transaction_n =Transaction.builder()
                .type(eventdesc)
                .ts(LocalDateTime.now().toString())
                .transactionAmt((InpTr.get()).getTransactionAmt())
                .balance(CurrentBal_n)
                .build();                          
                         
        }

        transaction_o.add(transaction_n);
        return transaction_o;
    
            
     }

    public static Map<String, String> compareObjectsViaJson(Object oldObj, Object newObj) {
        
        final ObjectMapper objectMapper = new ObjectMapper();
        Map<String, String> differences = new HashMap<>();
        
        try {
            JsonNode oldNode = objectMapper.valueToTree(oldObj);
            JsonNode newNode = objectMapper.valueToTree(newObj);
            
            
            // Get all field names from both objects
            Set<String> fieldNames = new HashSet<>();
            oldNode.fieldNames().forEachRemaining(fieldNames::add);
            newNode.fieldNames().forEachRemaining(fieldNames::add);
            
            for (String fieldName : fieldNames) {
                if (fieldName == "accountTransactions") continue;
                JsonNode oldValue = oldNode.get(fieldName);
                JsonNode newValue = newNode.get(fieldName);
                
                // Handle null values
                String oldStr = (oldValue == null || oldValue.isNull()) ? "null" : oldValue.asText();
                String newStr = (newValue == null || newValue.isNull()) ? "null" : newValue.asText();
                //differences.put(fieldName, oldStr + " -> " + newStr);

             if (!Objects.equals(oldStr, newStr)) {
                    differences.put(fieldName, oldStr + " -> " + newStr);
                }
            
            }
            
                        
        } catch (Exception e) {
            throw new RuntimeException("Error comparing objects", e);
        }
        
        return differences;
    }

}
