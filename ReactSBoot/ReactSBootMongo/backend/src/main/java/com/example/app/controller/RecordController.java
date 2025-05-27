package com.example.app.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
// class RecordRepository resides in package com.example.app.repository;
import com.example.app.repository.*;
import com.example.app.model.Record;

import java.util.List;

@RestController
@RequestMapping("/api/records")
public class RecordController {

    @Autowired
    private RecordRepository recordRepository;

    @GetMapping
    public List<com.example.app.model.Record> getAllRecords() {
        return recordRepository.findAll();
    }

    @GetMapping("/{id}")
    public ResponseEntity<com.example.app.model.Record> getRecordById(@PathVariable String id) {
        return recordRepository.findById(id)
                .map(record -> ResponseEntity.ok().body(record))
                .orElse(new ResponseEntity<>(HttpStatus.NOT_FOUND));
    }

    @PostMapping
    public ResponseEntity<com.example.app.model.Record> createRecord(@RequestBody com.example.app.model.Record record) {
        // convert the incoming record from "org.springframework.web.bind.annotation.RequestBody.Record" to "com.example.app.model.Record"


       
        if (record.getId() != null) {
            // is the "record" object from app.model.Record class?
       
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(null);
        }
        // Ensure that the ID is not set, as MongoDB will generate it automatically
        if (record.getName() == null || record.getAddress() == null || record.getLandmark() == null ||
            record.getTaluk() == null || record.getPincode() <= 0 || record.getGeolocation() == null) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(null);
        }
        // Validate the geolocation object if necessary
        //getLatitude method is inside class Coordinates which is inside Geolocation class inside Record class
  
        if (record.getGeolocation().getCoordinates().getLatitude()  == 0.0 || record.getGeolocation().getCoordinates().getLongitude() == 0.0) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(null);
        }
        // Save the record to the database
        record.setId(null); // Ensure ID is null for new records
        // This will allow MongoDB to generate a new ID
         
        com.example.app.model.Record savedRecord = recordRepository.save(record);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedRecord);
    }

    @PutMapping("/{id}")
    public ResponseEntity<com.example.app.model.Record> updateRecord(@PathVariable String id, @RequestBody com.example.app.model.Record recordDetails) {
        return recordRepository.findById(id)
                .map(record -> {
                    record.setName(recordDetails.getName());
                    record.setAddress(recordDetails.getAddress());
                    record.setLandmark(recordDetails.getLandmark());
                    record.setTaluk(recordDetails.getTaluk());
                    record.setPincode(recordDetails.getPincode());
                    record.setGeolocation(recordDetails.getGeolocation());
                    Record updatedRecord = recordRepository.save(record);
                    return ResponseEntity.ok().body(updatedRecord);
                })
                .orElse(new ResponseEntity<>(HttpStatus.NOT_FOUND));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Object> deleteRecord(@PathVariable String id) {
        return recordRepository.findById(id)
                .map(record -> {
                    recordRepository.delete(record);
                    return ResponseEntity.noContent().build();
                })
                .orElse(new ResponseEntity<>(HttpStatus.NOT_FOUND));
    }
}