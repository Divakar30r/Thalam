package code.PolMaster;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import java.util.stream.Collectors;

import org.bson.Document;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;

public class PolMasterFieldThreads {

    private static final MongoClient mongoClient = MongoClients.create("mongodb://localhost:27017");

     

    public static List<String> getCollectionFieldList(String DBname, String  CollectionName) {

        MongoDatabase db = mongoClient.getDatabase(DBname);

        MongoCollection<Document> recordCollectionMongo = db.getCollection(CollectionName);
        // from the first document of the recordCollectionMongo pick all the keys (including sub nodes) and load it to fieldslist list<String>
        Document firstDoc = recordCollectionMongo.find().first();

        List<String> PolMasterFieldList = new ArrayList<>();
        if (firstDoc != null)
            extractKeysRecursive("", firstDoc, PolMasterFieldList);

        // PolMasterFieldList now contains all keys (including nested) in dot notation
        // Example: "Transaction.LastPayment.Amount"

        // Print or use the list as needed
        //PolMasterFieldList.forEach(System.out::println);
        return PolMasterFieldList;
    }

    // Helper method to extract keys recursively in dot notation
    private static void extractKeysRecursive(String prefix, Document doc, List<String> fieldList) {
        for (String key : doc.keySet()) {
            Object value = doc.get(key);
            String fullKey = prefix.isEmpty() ? key : prefix + "." + key;
            if (value instanceof Document) {
                extractKeysRecursive(fullKey, (Document) value, fieldList);
            } else {
                fieldList.add(fullKey);
            }
        }
    }

    public static void getLinkedfields() {

        MongoDatabase db = mongoClient.getDatabase("PolDB");

        // Read PolRef rules for PolMaster
        MongoCollection<Document> polRef = db.getCollection("PolRef");
        List<Document> mongoDocList = polRef.find(new Document("PolicyTable", "PolMaster")).into(new ArrayList<>());
        List<String>  Ref_fieldKeysList = new ArrayList<>();
        List<Map<String, Object>> mainDocs = new ArrayList<>();

        // put MongoDocList in an iteration
         for (Document mongoDoc : mongoDocList) {
             

            String policyField = mongoDoc.getString("PolicyField");
            Document description = mongoDoc.get("Description", Document.class);
            List<Document> allowedValues = description.getList("AllowedValues", Document.class);

            List<Document> outputSinglefieldRuleList = new ArrayList<>();
            if (allowedValues != null) {
                for (Document allowed : allowedValues) {
                    Document entry = new Document();
                    for (String key : allowed.keySet()) {
                        entry.put(key, allowed.get(key));
                    }
                    outputSinglefieldRuleList.add(entry);
                }
            } else {
                // Handle case where AllowedValues is not a list of Document (e.g., ListStr)
                Object allowed = description.get("AllowedValues");
                if (allowed instanceof Document) {
                    outputSinglefieldRuleList.add((Document) allowed);
                }
            }

            Document result = new Document();
            result.put(policyField, outputSinglefieldRuleList);
            Ref_fieldKeysList.add(policyField);
            mainDocs.add(Map.of(policyField, outputSinglefieldRuleList));
              
        }

        // Step 2: Convert to HashMap for ordered insertion
        Map<String, List<Document>> resultMap = new HashMap<>();

        for (Map<String, Object> mainDoc : mainDocs) {
            for (Map.Entry<String, Object> entry : mainDoc.entrySet()) {
                String fieldKey = entry.getKey();
                List<Document> ruleDocItrList = new ArrayList<>();
     
                Object rulesObj = entry.getValue();

                if (rulesObj instanceof List) {
                    List<?> rulesList = (List<?>) rulesObj;
                    for (Object ruleObj : rulesList) {
                        Document ruleDoc = new Document((Map<String, Object>) ruleObj);

                        // Check for keys that don't contain "List" or "Range"
                        boolean hasDependentKey = false;
                        for (String ruleKey : ruleDoc.keySet()) {
                            if (!ruleKey.contains("List") && !ruleKey.contains("Range")) {
                                if (Ref_fieldKeysList.contains(ruleKey)) {
                                    hasDependentKey = true;
                                    // Rearrangement: push below referenced FieldKey
                                    // Remove current and add after referenced key
                                    // We'll handle this after initial pass
                                    break;
                                }
                            }
                        }
                        ruleDocItrList.add(ruleDoc);
                    }
                }
                resultMap.put(fieldKey, ruleDocItrList);
            }
            
        }
  
        // Step 4: Rearrangement logic
        // For each entry, if any RuleDocItr references another FieldKey, move this entry after the referenced FieldKey
        List<String> unorderedKeys = new ArrayList<>(resultMap.keySet());
        Set<String> uniqueKeys = new LinkedHashSet<>();

        // create a new List<String> unique using Set
        Map<String, List<String>> KeysDeps = new LinkedHashMap<>();
         
        // Organize dependencies in KeysDeps
        //"Key1" : ["DepKey1_Key4", "DepKey1_Key3"]
        //"Key2" : ["DepKey1_Key3"]
        //"Key3" : []
        //"Key4" : ["DepKey1_Key2"]
        for (String key : new ArrayList<>(unorderedKeys)) {
            List<Document> ruleDocs = resultMap.get(key);
            for (Document ruleDoc : ruleDocs) {
                for (String ruleKey : ruleDoc.keySet()) {
                    if (!ruleKey.contains("List") && !ruleKey.contains("Range")) {
                         
                        if (Ref_fieldKeysList.contains(ruleKey) && !ruleKey.equals(key)) {
                            // Get the dependent field and load it into unique key
                            int Dep_idx = unorderedKeys.indexOf(ruleKey);
                            if (KeysDeps.get(key)!=null){
                                if (!KeysDeps.get(key).contains(unorderedKeys.get(Dep_idx)))
                                  {KeysDeps.get(key).add(unorderedKeys.get(Dep_idx));}
                            } else {
                                KeysDeps.put(key, new ArrayList<>(Collections.singletonList(unorderedKeys.get(Dep_idx))));
                            }
                             
                        }
                    }
                }
            }

            if (KeysDeps.get(key)==null) KeysDeps.put(key, new ArrayList<>());
             
        }

        // print the KeysDeps
        String jsonArrayStr2 = new Gson().toJson(KeysDeps);
        System.out.println("KeysDeps JSON: " + jsonArrayStr2);

        List<String> CollectionFieldList = getCollectionFieldList("PolDB", "PolMaster"); 

        // Create a CountDownLatch for each field in KeysDeps.keySet()
        Map<String, CountDownLatch> latchMap = new HashMap<>();
        for (String field : KeysDeps.keySet()) {
            if (KeysDeps.get(field).size()>0)
            latchMap.put(field, new CountDownLatch(KeysDeps.get(field).size()));
            
        }

        LinkedHashMap<String, List<String>> LoadedFinal = new LinkedHashMap<>();
        LinkedHashMap<String, List<String>> LoggerFinal = new LinkedHashMap<>();
        // Create a thread pool
        ExecutorService executor = Executors.newCachedThreadPool();
        try{
        // Start a thread for each field in CollectionFieldList
        for (String field : CollectionFieldList) {

            executor.execute(() -> {
                LoggerFinal.put(field, new ArrayList<>());
                System.out.println("Thread started for : " + field + "             @ " + Instant.now());
                LoggerFinal.get(field).add("Thread started for : " + field + "             @ " + Instant.now());
                try {
                    Thread.sleep(10_000); // Sleep for 30 seconds
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                if (latchMap.containsKey(field)) {
                    
                    try {
                        // Wait for the latch to reach zero
                        System.out.println( field+ " waiting for latch: " +
                        latchMap.get(field).getCount() + "@ " + Instant.now());
                        latchMap.get(field).await(50, TimeUnit.SECONDS);
                        if (latchMap.get(field).getCount() == 0) {
                            System.out.println(field + " All dependencies resolved, proceeding...@ " + Instant.now());
                            LoggerFinal.get(field).add(field + " All dependencies resolved, proceeding...@ " + Instant.now());
                         } else {
                            System.out.println(field + " Timeout reached while waiting for dependencies.@ " + Instant.now());
                            LoggerFinal.get(field).add(field + " Timeout reached while waiting for dependencies.@ " + Instant.now());
                        }
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                }
                else{
                    LoadedFinal.put(field, new ArrayList<>());

                }

                System.out.println("Thread finished for : " + field + "           @ " + Instant.now());
                LoggerFinal.get(field).add("Thread finished for : " + field + "           @ " + Instant.now());
            });
            Thread.sleep(2000); // Stagger different field thread starts slightly
        }
        
        }
        catch(Exception e){
            System.out.println("Exception in threads: "+ e.getMessage());
        }
        
        // get the values (List<String>) of KeysDeps and flatten it to a single list
        Set<String> flattenedDeps = KeysDeps.entrySet().stream().flatMap(entry -> entry.getValue().stream().distinct()).collect(Collectors.toSet());
        // compare each values of flattenedDeps with the latchMap values and if found,load it in map with flatterrnedDeps value as key and latchmap corresponding keys as value
        Map<String, Set<String>> reverseDeps = new HashMap<>();
        for (String dep : flattenedDeps) {
            for (Map.Entry<String, CountDownLatch> entry : latchMap.entrySet()) {
                String key = entry.getKey();
                if (KeysDeps.get(key).contains(dep)) {
                    reverseDeps.computeIfAbsent(dep, k -> new HashSet<>()).add(key);
                }
            }
        }

        // print the reverseDeps
        String jsonArrayStr3 = new Gson().toJson(reverseDeps);
        System.out.println("reverseDeps JSON: " + jsonArrayStr3);

        // read flattenDeps key, create a thread for each using executor.execute , within thread print each of its values
        try{
        for (String parentfld : flattenedDeps) {
            executor.execute(() -> {
                System.out.println("Dependency thread triggered by Parent " + parentfld + " started              @ " + Instant.now());
                try {
                    Thread.sleep(15_000); // Sleep for 15 seconds
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }

                if (reverseDeps.containsKey(parentfld)) {
                    for (String childfld : reverseDeps.get(parentfld)) {
                        if (latchMap.containsKey(childfld)) {
                              List<String> gparentflds = LoadedFinal.entrySet().stream()
                                                            .filter(x -> x.getKey().contains(parentfld))
                                                            .flatMap(x-> x.getValue().stream())
                                                            .distinct()
                                                            .collect(Collectors.toList());

                            if (!LoadedFinal.keySet().contains(childfld)){
                                  if (gparentflds.size() > 0) {//  if both a parent & a child
                                     LinkedList<String> tempParentsList = new LinkedList<>();
                                     tempParentsList.addAll(gparentflds);
                                     tempParentsList.add(0, parentfld); // add parentfld as the first element
                                     LoadedFinal.put(childfld, tempParentsList);
                                     LoggerFinal.get(childfld).add("Child " + childfld + " loaded with grandparents as Linkedlist " + gparentflds + " @ " + Instant.now());
                                 }
                                 else{
                                     List<String> tempParentsList = new ArrayList<>();
                                     tempParentsList.add(parentfld);
                                     LoadedFinal.put(childfld, tempParentsList);
                                     LoggerFinal.get(childfld).add("Child " + childfld + " loaded with parent as Arraylist " + parentfld + " @ " + Instant.now());
                                 }
                            } else{
                                if (gparentflds.size() > 0){
                                    if (LoadedFinal.get(childfld) instanceof LinkedList){
                                            LoadedFinal.get(childfld).addAll(gparentflds);
                                            LoadedFinal.get(childfld).add(parentfld);
                                            LoggerFinal.get(childfld).add("Child " + childfld + " loaded with grandparents into exisitng  Linkedlist " + gparentflds + " @ " + Instant.now());
                                    }
                                    else {
                                        LinkedList<String> tempParentsList = new LinkedList<>();
                                        tempParentsList.addAll(LoadedFinal.get(childfld));
                                        tempParentsList.addAll(gparentflds);
                                        tempParentsList.add(parentfld);
                                        LoadedFinal.replace(childfld, tempParentsList);
                                        LoggerFinal.get(childfld).add("Child " + childfld + " loaded with parent converted to an existing LinkedList " + parentfld + " @ " + Instant.now());
                                    }
                                }
                                else {
                                     
                                    LoadedFinal.get(childfld).add(parentfld);
                                    LoggerFinal.get(childfld).add("Child " + childfld + " loaded with parent as Arraylist " + parentfld + " @ " + Instant.now());
                                }

                            }
                            latchMap.get(childfld).countDown();
                            System.out.println("Parent  " + parentfld + " triggered for " + childfld + ", latch count: " +
                                    latchMap.get(childfld).getCount() + " @ " + Instant.now());
                                    LoggerFinal.get(childfld).add("Parent  " + parentfld + " triggered for " + childfld + ", latch count: " +
                                    latchMap.get(childfld).getCount() + " @ " + Instant.now());
                            
                        }
                        }
                    }
                
                System.out.println("Dependency thread finished for : " + parentfld + "           @ " + Instant.now());
            });
            Thread.sleep(1000); // Stagger different field thread starts slightly
        }

        Thread.sleep(120_000); // Main thread sleeps to allow all tasks to complete
        }
        catch(Exception e){
            System.out.println("Exception in dependency threads: "+ e.getMessage());
            
        }

        LoadedFinal.entrySet().forEach(x -> {
            System.out.print("\n" + " ChildKey: " + x.getKey() + " Parents: ");
            x.getValue().forEach(y -> System.out.print(y + "/ "));
             
        });

        LoggerFinal.entrySet().forEach(x -> {
            System.out.print("\n" + " ChildKey: " + x.getKey() +  "\n"+  "Logs: ");
            x.getValue().forEach(y -> System.out.println("      " + y + " "));
            System.out.println();
        });
        // Optionally, shutdown the executor after all tasks are submitted
        

        executor.shutdown();
    }
}