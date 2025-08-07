package com.johnreah.postgrestransactions6springdatajdbc.entities;

import lombok.Builder;
import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.jdbc.core.mapping.AggregateReference;
import org.springframework.data.relational.core.mapping.MappedCollection;

import java.time.OffsetDateTime;
import java.util.HashSet;
import java.util.Set;

@Data
@Builder
public class Account {

    @Id
    private long id;

    private String description;
    private double balance;
    private OffsetDateTime balanceTimestamp;
    private String reference;

    AggregateReference<Account, Long> accountTypeId;

    @Builder.Default
    @MappedCollection(idColumn = "account_id")
    Set<AccountHistory> accountHistories = new HashSet<>();

    @Builder.Default
    @MappedCollection(idColumn = "account_id")
    Set<LinkCustomerAccount> linkCustomerAccounts = new HashSet<>();
}
