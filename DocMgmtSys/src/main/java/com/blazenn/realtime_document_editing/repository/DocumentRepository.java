package com.blazenn.realtime_document_editing.repository;

import com.blazenn.realtime_document_editing.model.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DocumentRepository extends JpaRepository<Document, Long> {
}
