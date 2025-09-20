package org.kolmanfreecss.kfimapiincidentservice.application.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.Date;

/**
 * Incident
 * Used to define the Incident object.
 * 
 * @version 1.0
 * @uthor Kolman-Freecss
 */
@AllArgsConstructor
@NoArgsConstructor
@ToString
@Getter
@Setter
@Entity
public class Incident {
    
    public enum Status {
        REPORTED,
        IN_PROGRESS,
        RESOLVED,
        CLOSED,
        OPEN,
        ASSIGNED
    }
    
    public enum Priority {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    
    @Column(nullable = false, unique = true, name = "incidentid")
    String incidentId;
    
    
    @Column(nullable = false)
    String title;
    
    String description;

    String keydata;

    String complexitylevel;
    
    @Enumerated(EnumType.STRING)
    Status status;
    
    @Enumerated(EnumType.STRING)
    Priority priority;
    
    @Column(name = "reportdate")
    Date reportDate;
    
    @Column(name = "resolutiondate")
    Date resolutionDate;
    
}
