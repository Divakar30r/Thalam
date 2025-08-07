package com.johnreah.postgrestransactions6springdatajdbc.entities;

import lombok.Builder;
import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.MappedCollection;

import java.util.HashSet;
import java.util.Set;

@Data
@Builder
public class Customer {

    @Id
    private long id;

    private String lastName;
    private String firstName;
    private String email;
    private String reference;

    @Builder.Default
    @MappedCollection(idColumn = "customer_id")
    Set<LinkCustomerAccount> linkCustomerAccounts = new HashSet<>();
}
