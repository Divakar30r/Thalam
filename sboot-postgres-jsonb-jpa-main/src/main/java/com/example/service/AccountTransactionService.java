package com.example.service;

import java.util.List;

import com.example.model.Account;
import com.example.model.Transaction;

public interface AccountTransactionService {

   public List<Transaction> createAccountSuccessfulEvent(Account newAccount) ;
   public List<Transaction> updateAccountSuccessfulEvent(Account Account);
   public List<Transaction> createTransactionSuccessfulEvent(Account newAccount, Long trnAmt); 
    
   
}
