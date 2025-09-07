package code.mongo;


import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import org.bson.Document;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class MongoService {

    private final MongoCollection<Document> collection;

    public MongoService(
            MongoDatabase mongoDatabase,
            @Value("${mongodb.collection.name:defaultCollection}") String collectionName) {
        this.collection = mongoDatabase.getCollection(collectionName); // Replace with your collection name
    }

    public void insertDocument(Document document) {
        collection.insertOne(document);
    }

    public List<Document> getAllDocuments() {
        List<Document> documents = new ArrayList<>();
        collection.find().into(documents);
        return documents;
    }

    public Document findDocument(String key, String value) {
        return collection.find(new Document(key, value)).first();
    }

    public void updateDocument(String key, String oldValue, Document updateDocument) {
        collection.updateOne(new Document(key, oldValue), new Document("$set", updateDocument));
    }

    public void deleteDocument(String key, String value) {
        collection.deleteOne(new Document(key, value));
    }

    public MongoCollection<Document> collection(){
        return collection;
    }
}