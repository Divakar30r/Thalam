package com.example.builder.serializer;

import com.example.entity.AccountEntity;
import com.example.model.Account;
import com.example.service.AccountTransactionService;

import org.apache.commons.lang3.RandomStringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
public class AccountDetailsSerializer {

    @Value("${SERVICE_ACCOUNT}")
    private String serviceAccount;

    AccountTransactionService accountTransactionService;
    public AccountDetailsSerializer(AccountTransactionService accountTransactionService){
        this.accountTransactionService = accountTransactionService;
    }

    public AccountEntity serializeAccount(Account Wrkaccount) {
        return AccountEntity.builder()
                .accNo(Integer.valueOf(RandomStringUtils.randomNumeric(5, 5)))
                .holderName(Wrkaccount.getAccountHolderName())
                .startDate(new Date())
                .branch(Wrkaccount.getAccountBranch())
                .balance(0L)
                .transactions(accountTransactionService.createAccountSuccessfulEvent(Wrkaccount))
                .createdBy(this.serviceAccount)
                .createdDate(new Date())
                .build();
    }
}
