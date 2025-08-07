package com.johnreah.postgrestransactions6springdatajdbc.entities;

import lombok.Builder;
import lombok.Data;
import org.springframework.data.jdbc.core.mapping.AggregateReference;

import java.time.OffsetDateTime;

@Data
@Builder
public class AccountHistory {

    private OffsetDateTime timeStamp;
    private double account;
    private double balance;
    private String description;

}
