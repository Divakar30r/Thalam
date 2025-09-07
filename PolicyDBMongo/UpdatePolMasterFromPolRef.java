import com.mongodb.client.*;
import com.mongodb.client.model.Updates;
import org.bson.Document;
import java.util.*;

public class UpdatePolMasterFromPolRef {
    public static void main(String[] args) {
        // Connect to MongoDB
        MongoClient mongoClient = MongoClients.create("mongodb://localhost:27017");
        MongoDatabase db = mongoClient.getDatabase("PolDB");

        // Read PolRef rules for PolMaster
        MongoCollection<Document> polRef = db.getCollection("PolRef");
        List<Document> rules = polRef.find(new Document("PolicyTable", "PolMaster")).into(new ArrayList<>());

        // Prepare field-to-allowed-values map
        Map<String, List<String>> fieldAllowedValues = new HashMap<>();
        for (Document rule : rules) {
            Document desc = rule.get("Description", Document.class);
            if (desc != null && "List<String>".equals(desc.getString("Type"))) {
                List<String> allowed = desc.getList("AllowedValues", String.class);
                if (allowed != null && !allowed.isEmpty()) {
                    fieldAllowedValues.put(rule.getString("PolicyField"), allowed);
                }
            }
        }

        // Update PolMaster documents
        MongoCollection<Document> polMaster = db.getCollection("PolMaster");
        FindIterable<Document> docs = polMaster.find();
        Random rand = new Random();

        for (Document doc : docs) {
            Document updateFields = new Document();
            for (Map.Entry<String, List<String>> entry : fieldAllowedValues.entrySet()) {
                String field = entry.getKey();
                List<String> allowed = entry.getValue();
                String randomValue = allowed.get(rand.nextInt(allowed.size()));
                // Currently vaue of  key 'PolicyType' is set as 'TBD' and value of key 'PolicyNumber' also has the prefix 'TBD'  when the entry.getKey() ="PolicyType", can you also replace the literal 'TBD' in the policynumber with PolicyType
                //  when the entry.getKey() ="PolicyType", do add this policytype random value as prefix to the value of entry.getKey() ="PolicyNumber"


                
                updateFields.append(field, randomValue);
                //if (field == "PolicyType"){updateFields.append("PolicyNumber", randomValue);}

            }
            if (!updateFields.isEmpty()) {
                polMaster.updateOne(
                    new Document("_id", doc.getObjectId("_id")),
                    new Document("$set", updateFields)
                );
            }
        }

        mongoClient.close();
        System.out.println("PolMaster documents updated based on PolRef rules.");
    }
}