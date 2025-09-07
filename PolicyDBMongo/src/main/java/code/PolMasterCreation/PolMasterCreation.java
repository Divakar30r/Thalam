package code.PolMasterCreation;


import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import org.bson.Document;
import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.google.gson.Gson;
public class PolMasterCreation {




    // Method to insert a null-valued document into MongoDB
    public static void insertNullPolMaster() {
        MongoClient mongoClient = MongoClients.create("mongodb://localhost:27017");
        MongoDatabase db = mongoClient.getDatabase("PolDB");
       // Read PolRef rules for PolMaster
        MongoCollection<Document> polMasterCollection = db.getCollection("PolMaster");
     
         
        for (int i = 0; i < 15; i++) {
        Document lastPayment = new Document()
                .append("Amount", null)
                .append("Date", null)
                .append("BenfitCode", null);
        Document duePayment = new Document()
                .append("Amount", null)
                .append("Date", null)
                .append("BenefitCode", null);
        Document transaction = new Document()
                .append("LastPayment", lastPayment)
                .append("DuePayment", duePayment);

        Document doc = new Document()
                .append("PolicyType", null)
                .append("PolicyNumber", null)
                .append("SystemDate", null)
                .append("EffectiveDate", null)
                .append("ExpirationDate", null)
                .append("PolicyStatus", null)
                .append("Language", null)
                .append("Transaction", transaction)
                .append("SumInsured", null)
                .append("PendingCoverage", null)
                .append("ThirdParty", null)
                .append("JurisdictionState", null)
                .append("Term", null)
                .append("Frequency", null);

        polMasterCollection.insertOne(doc);
        
        }

     
    }
    // ...existing code...
}
