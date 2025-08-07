package com.johnreah.postgrestransactions6springdatajdbc.entities;

import lombok.AllArgsConstructor;
import lombok.Data;
import org.springframework.data.jdbc.core.mapping.AggregateReference;

@Data
@AllArgsConstructor
public class LinkCustomerAccount {
    private AggregateReference<Customer, Long> customerId;
    private AggregateReference<Account, Long> accountId;
}
