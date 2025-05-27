package com.example.app.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Document(collection = "AddressDetails")
public class Record {
    @Id
    private String id;
    private String name;
    private String address;
    private String landmark;
    private String taluk;
    private int pincode;
    private Geolocation geolocation;

    // Getters and Setters

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getLandmark() {
        return landmark;
    }

    public void setLandmark(String landmark) {
        this.landmark = landmark;
    }

    public String getTaluk() {
        return taluk;
    }

    public void setTaluk(String taluk) {
        this.taluk = taluk;
    }

    public int getPincode() {
        return pincode;
    }

    public void setPincode(int pincode) {
        this.pincode = pincode;
    }

    public Geolocation getGeolocation() {
        return geolocation;
    }

    public void setGeolocation(Geolocation geolocation) {
        this.geolocation = geolocation;
    }

    public static class Geolocation {
        private String collectioncentre;
        private String proximity;
        private Coordinates coordinates;

        // Getters and Setters

        public String getCollectioncentre() {
            return collectioncentre;
        }

        public void setCollectioncentre(String collectioncentre) {
            this.collectioncentre = collectioncentre;
        }

        public String getProximity() {
            return proximity;
        }

        public void setProximity(String proximity) {
            this.proximity = proximity;
        }

        public Coordinates getCoordinates() {
            return coordinates;
        }

        public void setCoordinates(Coordinates coordinates) {
            this.coordinates = coordinates;
        }

        public static class Coordinates {
            private double latitude;
            private double longitude;

            // Getters and Setters

            public double getLatitude() {
                return latitude;
            }

            public void setLatitude(double latitude) {
                this.latitude = latitude;
            }

            public double getLongitude() {
                return longitude;
            }

            public void setLongitude(double longitude) {
                this.longitude = longitude;
            }
        }
    }
}