package com.johnreah.postgrestransactions6springdatajdbc.entities;

import lombok.Builder;
import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.MappedCollection;

import java.util.HashSet;
import java.util.Set;

@Data
@Builder
public class AccountType {

    @Id
    private long id;

    private String description;
    private String reference;

}
