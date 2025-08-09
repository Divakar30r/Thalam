--liquibase formatted sql
--changeset Hamza:creation-of-document-entity.sql endDelimiter:#


CREATE TABLE document (
    id BIGINT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT DEFAULT '',
    created_date TIMESTAMP,
    created_by VARCHAR(255),
    last_modified_by VARCHAR(255),
    last_modified_date VARCHAR(255)
);#

CREATE SEQUENCE document_seq
    INCREMENT BY 1
    START WITH 1
    OWNED BY document.id;#