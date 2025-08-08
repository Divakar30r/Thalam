package com.example.service.impl;

import com.example.constant.AccountConstants;
import com.example.deserializer.AccountDetailsDeserializer;
import com.example.entity.AccountEntity;
import com.example.model.Account;
import com.example.model.Transaction;
import com.example.service.AccountTransactionService;
import com.example.builder.*;

import jakarta.annotation.PostConstruct;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class AccountTransactionServiceImpl implements AccountTransactionService {
    
    @Autowired
    AccountDetailsDeserializer accountDetailsDeserializer;

    TransactionBuilder transactionBuilder;
    public AccountTransactionServiceImpl(TransactionBuilder transactionBuilder){
        this.transactionBuilder = transactionBuilder;
    }

    @PostConstruct
public void init() {
    System.out.println(" AccountTransactionServiceImpl bean initialized");
}

    @Override
    public List<Transaction> createAccountSuccessfulEvent(Account newAccount) {
         return (transactionBuilder.generate(newAccount, Optional.empty()));  
         //(transactionBuilder.generate(accountDetailsDeserializer.deserializeAccount(newAccount), Optional.empty()));  
         /* return Collections.singletonList(Transaction.builder()
                .type(AccountConstants.EVENT_CREATE_ACCOUNT.getMessage())
                .ts(LocalDateTime.now().toString())
                .balance(0L)
                .build());
        */
    }

    @Override
    public List<Transaction> updateAccountSuccessfulEvent(Account newAccount) {
        // existingTransactions.sort(Comparator.comparing(Transaction::getTs).reversed());
        /*Transaction accountUpdateNewEvent = Transaction.builder()
                .type(AccountConstants.EVENT_ACCOUNT_UPDATE.getMessage())
                .ts(LocalDateTime.now().toString())
                .build();
        */
        
         
        //existingTransactions.add(accountUpdateNewEvent);
        return (transactionBuilder.generate(newAccount, Optional.empty()));
    }

    @Override
    public List<Transaction> createTransactionSuccessfulEvent(Account newAccount, Long trnAmt) {
        /*
        existingTransactions.sort(Comparator.comparing(Transaction::getTs).reversed());
        Long newBalance = ((existingTransactions.get(0).getBalance() != null) ? existingTransactions.get(0).getBalance() : 0L) + deposit;
        Transaction depositNewEvent = Transaction.builder()
                .type(AccountConstants.EVENT_DEPOSIT.getMessage())
                .ts(LocalDateTime.now().toString())
                .balance(newBalance)
                .transactionAmt(Long.valueOf(deposit))
                .build();
        existingTransactions.add(depositNewEvent);
        return existingTransactions;
        */
        Optional<Transaction> TransactionEvent = Optional.empty();
        if (trnAmt > 0)
        { TransactionEvent = Optional.of(Transaction.builder()
                                         .type(AccountConstants.EVENT_DEPOSIT.getMessage())
                                         .transactionAmt(trnAmt)
                                         .build());}
        else if(trnAmt < 0)
        { TransactionEvent = Optional.of(Transaction.builder()
                                            .type(AccountConstants.EVENT_WITHDRAWAL.getMessage())
                                            .transactionAmt(trnAmt)
                                            .build());}
        return (transactionBuilder.generate(newAccount, TransactionEvent));
    }
    
/*
    @Override
    public  List<Transaction> createWithdrawalSuccessfulEvent(Account newAccount, Integer deposit) {
 
        existingTransactions.sort(Comparator.comparing(Transaction::getTs).reversed());
        Long newBalance = ((existingTransactions.get(0).getBalance() != null) ? existingTransactions.get(0).getBalance() : 0L) - withdrawal;
        Transaction depositCurrentEvent = Transaction.builder()
                .type(AccountConstants.EVENT_WITHDRAWAL.getMessage())
                .ts(LocalDateTime.now().toString())
                .balance(newBalance)
                .transactionAmt(Long.valueOf(withdrawal))
                .build();
        existingTransactions.add(depositCurrentEvent);
        return existingTransactions;
         Optional<Transaction> depositNewEvent = Optional.of(Transaction.builder().type(AccountConstants.EVENT_WITHDRAWAL.getMessage()).build());
        return (transactionBuilder.generate(newAccount, depositNewEvent));
    }
*/
}
