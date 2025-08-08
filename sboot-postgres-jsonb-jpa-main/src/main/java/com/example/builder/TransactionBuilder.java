package com.example.builder;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

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
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.java.Log;

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
    AccountRepository accountRepository;

    @Autowired
    AccountDetailsDeserializer accountDetailsDeserializer;
/*
    public TransactionBuilder(AccountService accountService, AccountDetailsDeserializer accountDetailsDeserializer, AccountRepository accountRepository ){
        this.accountService = accountService;
        this.accountDetailsDeserializer = accountDetailsDeserializer;
        this.accountRepository = accountRepository;
    }
*/
    public List<Transaction> generate (Account account_n, Optional<Transaction> InpTr){
        Optional<AccountEntity> account_o = Optional.ofNullable(this.accountRepository.findByAccNo(account_n.getAccountNumber()));
        
    
        /*
         * if account_o.empty -> then new record
         *   do not set current bal and transaction amount
         * if account_o.isPresent but InpTr.empty -> Update account
         *   do not set current bal and transaction amount
         *
         * 
         */
        //Account account_o =  this.accountService.getAccountInformation(String.valueOf(account_n.getAccountNumber()));
        Transaction transaction_n = new Transaction();
        Account account_dtl_o = new Account();
        List<Transaction> transaction_o = new ArrayList();

        if (account_o.isPresent())  {
             account_dtl_o = accountDetailsDeserializer.deserializeAccount(account_o.get());
             transaction_o = account_dtl_o.getAccountTransactions();
             transaction_o.sort(Comparator.comparing(Transaction::getTs).reversed());
              
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
            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> map_o = mapper.convertValue(account_dtl_o, new TypeReference<Map<String, Object>>() {});
            map_o.remove("accountTransactions");
            Map<String, Object> map_n = mapper.convertValue(account_n, new TypeReference<Map<String, Object>>() {});
            map_n.remove("accountTransactions");
   
            try {
                eventdesc =  AccountConstants.EVENT_ACCOUNT_UPDATE.getMessage()  + 
                " / " + " Old Details: \" :" + mapper.writeValueAsString(map_o) +
                " / " + " New Details: \" :" + mapper.writeValueAsString(map_n);
            } catch (JsonProcessingException e) {
                // TODO Auto-generated catch block
                eventdesc =  AccountConstants.EVENT_ACCOUNT_UPDATE.getMessage();
            }
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

}
