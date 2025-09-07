package code.mongo;

import com.mongodb.client.MongoDatabase;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.bson.Document;
import java.util.List;

@RestController
@RequestMapping("/mongo")
public class MongoController {

    private final MongoService feeds;
    private final MongoService tokens;
    private final MongoService users;

    @Autowired
    public MongoController(MongoDatabase mongoDatabase) {
        this.feeds = new MongoService(mongoDatabase, "feeds");
        this.tokens = new MongoService(mongoDatabase, "tokens");
        this.users = new MongoService(mongoDatabase, "users");
    }

    @PostMapping("/insert")
    public String insert(@RequestBody Document document) {
        feeds.insertDocument(document);
        return "Document inserted";
    }

    @GetMapping("/all")
    public List<Document> getAll() {
        return feeds.getAllDocuments();
    }

    @GetMapping("/all-tokens")
    public List<Document> getAllTokens() {
        return tokens.getAllDocuments();
    }

    @GetMapping("/all-users")
    public List<Document> getAllUsers() {
        return users.getAllDocuments();
    }

    @GetMapping("/find")
    public Document find(@RequestParam String key, @RequestParam String value) {
        return feeds.findDocument(key, value);
    }

    @PutMapping("/update")
    public String update(@RequestParam String key, @RequestParam String oldValue, @RequestBody Document updateDocument) {
        feeds.updateDocument(key, oldValue, updateDocument);
        return "Document updated";
    }

    @DeleteMapping("/delete")
    public String delete(@RequestParam String key, @RequestParam String value) {
        feeds.deleteDocument(key, value);
        return "Document deleted";
    }
}


/*

@PostMapping("/insert")
public String insert(@RequestBody Document document) {
    // Example document to insert (from request body):
    // { "name": "John Doe", "age": 30, "city": "New York" }
    mongoService.insertDocument(document);
    return "Document inserted";
}

@GetMapping("/all")
public List<Document> getAll() {
    // Example: Returns a list of all documents in the "myCollection" collection.
    return mongoService.getAllDocuments();
}

@GetMapping("/find")
public Document find(@RequestParam String key, @RequestParam String value) {
    // Example: /mongo/find?key=name&value=John Doe
    // Returns the document where "name" is "John Doe".
    return mongoService.findDocument(key, value);
}

@PutMapping("/update")
public String update(@RequestParam String key, @RequestParam String oldValue, @RequestBody Document updateDocument) {
    // Example: /mongo/update?key=age&oldValue=30
    // Request body: { "city": "London", "occupation":"Developer"}
    // Updates the document where "age" is 30, adding/updating "city" and "occupation" fields.
    mongoService.updateDocument(key, oldValue, updateDocument);
    return "Document updated";
}

@DeleteMapping("/delete")
public String delete(@RequestParam String key, @RequestParam String value) {
    // Example: /mongo/delete?key=name&value=John Doe
    // Deletes the document where "name" is "John Doe".
    mongoService.deleteDocument(key, value);
    return "Document deleted";
}

@PostMapping("/insertExample")
public String insertExample() {
    //Example of inserting a document directly from the controller.
    Document exampleDoc = new Document("exampleField", "exampleValue").append("numberField", 123).append("arrayField", List.of("a", "b", "c"));
    mongoService.insertDocument(exampleDoc);
    return "Example document inserted";
}

 @GetMapping("/findExample")
public Document findExample() {
    //Example of finding a document.
    return mongoService.findDocument("exampleField", "exampleValue");
}

@PutMapping("/updateExample")
public String updateExample(){
    //Example of updating a document.
    Document update = new Document("newField", "newValue");
    mongoService.updateDocument("exampleField", "exampleValue", update);
    return "Example document updated";
}

@DeleteMapping("/deleteExample")
public String deleteExample(){
    //Example of deleting a document.
    mongoService.deleteDocument("exampleField", "newValue");
    return "Example document deleted";
}

 */