package com.example.app.repository;

import org.springframework.data.mongodb.repository.MongoRepository;
import com.example.app.model.Record;

public interface RecordRepository extends MongoRepository<Record, String> {
}