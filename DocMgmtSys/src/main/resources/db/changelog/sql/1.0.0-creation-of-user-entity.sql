--liquibase formatted sql
--changeset Hamza:creation-of-user-entity.sql endDelimiter:#


CREATE TABLE app_user (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE ,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    password TEXT NOT NULL,
    activated BOOLEAN DEFAULT false,
    created_date TIMESTAMP,
    created_by VARCHAR(255),
    last_modified_by VARCHAR(255),
    last_modified_date VARCHAR(255)
);#

CREATE SEQUENCE app_user_seq
    INCREMENT BY 1
    START WITH 1
    OWNED BY app_user.id;#