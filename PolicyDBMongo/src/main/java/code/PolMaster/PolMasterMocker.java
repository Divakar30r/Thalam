package code.PolMasterCreation;

 
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

import org.bson.Document;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;

import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.google.gson.Gson;

public class PolMasterMocker {

    private static final List<String> configTypes = Arrays.asList("RangeInt", "ListStr", "ListInt","RangeDateYYYYMM","RangeDate*:>:D:10"); 
    
    public static   List<Document> convertPolicyConfig(String wCollectionName) {

        MongoClient mongoClient = MongoClients.create("mongodb://localhost:27017");
        MongoDatabase db = mongoClient.getDatabase("PolDB");

        // Read PolRef rules for PolMaster
        MongoCollection<Document> polRef = db.getCollection("PolRef");
        List<Document> mongoDocList = polRef.find(new Document("PolicyTable", wCollectionName)).into(new ArrayList<>());

        // put MongoDocList in an iteration
        List<Document> outputAllfieldRuleList = new ArrayList<>();
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
            outputAllfieldRuleList.add(result);
             
        }
        // print the outputAllfieldRuleList showinf the json format
        String jsonArrayStr = new Gson().toJson(outputAllfieldRuleList);
        System.out.println("Converted JSON: " + jsonArrayStr);
        return outputAllfieldRuleList;
     }

    public static LinkedHashMap<String, List<Document>> convertAndRearrange(String jsonArrayStr) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        List<Map<String, Object>> mainDocs = mapper.readValue(jsonArrayStr, new TypeReference<List<Map<String, Object>>>(){});

        // Step 1: Load all FieldKeys into FieldKeysList
        List<String> fieldKeysList = new ArrayList<>();
        for (Map<String, Object> mainDoc : mainDocs) {
            fieldKeysList.addAll(mainDoc.keySet());
        }
 
        // Step 2: Convert to LinkedHashMap for ordered insertion
        LinkedHashMap<String, List<Document>> resultMap = new LinkedHashMap<>();

        // Step 3: Prepare a list to hold docs to be pushed to the end
        List<Map.Entry<String, List<Document>>> pushToEnd = new ArrayList<>();

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
                                if (fieldKeysList.contains(ruleKey)) {
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
                         
                        if (fieldKeysList.contains(ruleKey) && !ruleKey.equals(key)) {
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

        // based on the sample sequence 
        //"Key1" : ["DepKey1_Key4", "DepKey1_Key3"]
        //"Key2" : ["DepKey1_Key3"]
        //"Key3" : []
        //"Key4" : ["DepKey1_Key2"]

        //has to be seqeunced as Key3, Key2, Key4, Key1

        String jsonArrayStr2 = new Gson().toJson(KeysDeps);
        System.out.println("KeysDeps JSON: " + jsonArrayStr2);
        // Now rearrange unorderedKeys based on dependencies in KeysDeps
        while(uniqueKeys.size() != KeysDeps.size()){
            for (String key : KeysDeps.keySet()) {
                int DepCount = KeysDeps.get(key).size();
                while(DepCount>0){
                    String dep = KeysDeps.get(key).get(DepCount-1);
                    if (uniqueKeys.contains(dep))
                            KeysDeps.get(key).remove(dep);
                    DepCount--;
                }
                DepCount = KeysDeps.get(key).size();
                if (DepCount==0) uniqueKeys.add(key);

            } 
        }
 

        // Rebuild LinkedHashMap in new order
        LinkedHashMap<String, List<Document>> finalMap = new LinkedHashMap<>();
        for (String key : uniqueKeys) {
            if (resultMap.containsKey(key)) {
                finalMap.put(key, resultMap.get(key));
            }
        }

        // print the resultMap in json format
            String jsonArrayStr1 = new Gson().toJson(finalMap);
            System.out.println("ResultMap JSON: " + jsonArrayStr1);
        return finalMap;
        
    }
    
    
    public static void UpdatePolTest() {
        // Implementation for updating PolMaster documents
        MongoClient mongoClient = MongoClients.create("mongodb://localhost:27017");
        MongoDatabase db = mongoClient.getDatabase("PolDB");

        // Read PolRef rules for PolStakes
        MongoCollection<Document> polRef = db.getCollection("PolRef");
        List<Document> rules = polRef.find(new Document("PolicyTable", "PolMaster")).into(new ArrayList<>());


        // Update PolStakes documents
        MongoCollection<Document> recordCollectionMongo = db.getCollection("PolMaster");
        FindIterable<Document> recordCollection = recordCollectionMongo.find();
        Map<String, List<Document>> finalConfigs = new LinkedHashMap<>();
         // convert the output of convertPolicyConfig to LinkedHashMap
        try{
             finalConfigs
          = convertAndRearrange((new ObjectMapper()).writeValueAsString(convertPolicyConfig("PolMaster")));
        }catch(Exception jpe){jpe.printStackTrace(); return;}
         
        
         // Iterate through each record in PolStakes
       try{ 
        for (Map.Entry<String, List<Document>> fc : finalConfigs.entrySet()) {
            
            //if (fc.getKey()!="StakerAge") continue;
            HashMap<String, List<Document>> singleConfig = new HashMap<>();
            singleConfig.put(fc.getKey(), fc.getValue());

            for (Document recordDoc : recordCollection) { 
             
                Map<String,List<Object>> possibleCondFieldLevel1 
                    =  LoadPossibleValuesbasedonDep(singleConfig,recordDoc);

             // print possibleCondFieldLevel list in json format
                String jsonArrayStr = new Gson().toJson(possibleCondFieldLevel1);
                System.out.println("PossibleCondFieldLevel JSON: " + jsonArrayStr);

                    possibleCondFieldLevel1.entrySet().forEach(entry -> entry.getValue().forEach(System.out::println));
                  
                    Object randomValue = getRandomIntersectedValueForFieldKey(  possibleCondFieldLevel1.get(fc.getKey())); 
                        System.out.println("Setting " + fc.getKey() + " to " + randomValue);
                    if (randomValue != null) {
                        // set this random value in the recordDoc at the correct nested position
                        // print the key and random value
                    
                        setNestedValue(recordDoc, fc.getKey(), randomValue);
                    
                    }
                
                    // After processing all variable fields, update the document in MongoDB
                    recordCollectionMongo.updateOne(
                    new Document("_id", recordDoc.getObjectId("_id")),
                    new Document("$set", recordDoc)
                );
             break;
         }
        }
    }catch(Exception e){e.printStackTrace();}

    }


private static Map<String,List<Object>> LoadPossibleValuesbasedonDep(
       HashMap<String, List<Document>> configLinkedHashMap,
        Document recordDoc
) {
    
    Map<String, List<Object>> possibleCondFieldLevel = new HashMap<>();
    // print configLinkedHashMap in json format
        String jsonArrayStr = new Gson().toJson(configLinkedHashMap);
        System.out.println("ConfigLinkedHashMap JSON: " + jsonArrayStr);

      
         // Iterate through each entry in configLinkedHashMap
    for (Map.Entry<String, List<Document>> entry : configLinkedHashMap.entrySet()) {
     
        String configKey = entry.getKey();
         
        List<Document> configLinkedHashMapValueList = entry.getValue();
        // print the configLinkedHashMapValueList in json format
        String jsonArrayStr2 = new Gson().toJson(configLinkedHashMapValueList);
        System.out.println("ConfigLinkedHashMapValueList JSON: " + jsonArrayStr2);

        for (Document configLinkedHashMapValueInstance : configLinkedHashMapValueList) {
              String matchingConfigType, DependentConditionskey;
            // print configLinkedHashMapValueInstance in json format



                 matchingConfigType = configTypes.stream()
                        .filter(configLinkedHashMapValueInstance::containsKey)
                        .findFirst()
                        .orElse(null);

                if (matchingConfigType == null) continue;
                            
                    // Condition type fo
                    List<Object> condList = possibleCondFieldLevel.getOrDefault(configKey, new ArrayList<>());
                    Map<String, Object> condMap = new HashMap<>();
                    condMap.put("ConfigLinkedHashMapValueInstanceCondType", matchingConfigType);
                    condMap.put("ConfigLinkedHashMapValueInstanceCondValue", configLinkedHashMapValueInstance.get(matchingConfigType));
                    condList.add(condMap);
                    possibleCondFieldLevel.put(configKey,condList);
                // print possibleCondFieldLevelin json format
                String jsonArrayStr3 = new Gson().toJson(possibleCondFieldLevel);
                System.out.println("PossibleCondFieldLevel Intermediate JSON: " + jsonArrayStr3);
                // compare configLinkedHashMapValueInstance.keySet() with configtypes and filter non matching records alone
                DependentConditionskey = configLinkedHashMapValueInstance.keySet().stream()
                        .filter(key -> !configTypes.contains(key))
                        .findFirst()
                        .orElse(null);

                 if (DependentConditionskey == null) continue; // skipping if no dependents else below process
                
                // print DependentConditionskey
                System.out.println("DependentConditionskey: " + DependentConditionskey); 
                { 
                      // Dependent key
                    String depKey = DependentConditionskey;
                    Object depValue = configLinkedHashMapValueInstance.get(DependentConditionskey);

                    // Handle nested keys (dot notation)
                    // print recordDoc in json format
                    String jsonArrayStr4 = new Gson().toJson(recordDoc);
                    System.out.println("RecordDoc JSON: " + jsonArrayStr4);

                    Object recordDocDepValue = getNestedValue(recordDoc, depKey);
                    boolean matchDepValRecVal = false;
                    
                    if (recordDocDepValue != null) {

                        // Convert to List<String> if value is a list
                        List<String> recordDocDepValueList = new ArrayList<>();
                        if (recordDocDepValue instanceof List) {
                            for (Object obj : (List<?>) recordDocDepValue) {
                                recordDocDepValueList.add(obj.toString());
                            }
                        } else if (recordDocDepValue != null) {
                            recordDocDepValueList.add(recordDocDepValue.toString());
                        }
                        System.out.println("Printing RecordDep:");
                        recordDocDepValueList.stream().forEach(System.out::println);

                        // Compare values  
                        if (depValue instanceof List) {
                            List<String> depValueList = new ArrayList<>();
                            for (Object obj : (List<?>) depValue) {
                                depValueList.add(obj.toString());
                            }
                            // if depValueList contains all has "*" then match is true

                            if (depValueList.contains("*"))  matchDepValRecVal = true;
                            else matchDepValRecVal = recordDocDepValueList.containsAll(depValueList);
                            System.out.println("Dep val in PolRefList: " + depValueList);
                        } else {
                            if (depValue.toString().equals("*")) matchDepValRecVal = true;
                            else matchDepValRecVal = recordDocDepValueList.contains(depValue.toString());
                            System.out.println("Dep val in PolRef: " + depValue);
                        }
                        

                    }

                    if ((!matchDepValRecVal || recordDocDepValue==null)  && matchingConfigType != null){

                    // print the matchingConfigType, configKey, depKey, depValue, recordDocDepValue
                    System.out.println("No Match - Removing Config: " + configKey + ", DepKey: " + depKey + ", DepValue: " + depValue + ", RecordDepValue: " + recordDocDepValue);
                        /*
                        final String configTypeToRemove = matchingConfigType;
                        possibleCondFieldLevel.get(configKey).remove("ConfigLinkedHashMapValueInstanceCondType", configTypeToRemove);
                        possibleCondFieldLevel.get(configKey).remove("ConfigLinkedHashMapValueInstanceCondValue", configLinkedHashMapValueInstance.get(configTypeToRemove));
                       */
                      // print possibleCondFieldLevel in json format
                      String jsonArrayStr4a = new Gson().toJson(possibleCondFieldLevel);
                        System.out.println("Before Removal PossibleCondFieldLevel JSON: " + jsonArrayStr4a);

                      // print possibleCondFieldLevel.get(matchingConfigType) in json format
                      String jsonArrayStr5 = new Gson().toJson(possibleCondFieldLevel.get(matchingConfigType));
                          System.out.println("Before Removal PossibleCondFieldLevelValueList JSON: " + jsonArrayStr5);
                       
                        possibleCondFieldLevel.get(configKey).removeLast();
                    }

                    if (depValue.toString().equals("*")) {
                        //in the map's key possibleCondFieldLevel.get(configKey) has a list of objects and each object has keys
                        //"ConfigLinkedHashMapValueInstanceCondType" and "ConfigLinkedHashMapValueInstanceCondValue", need to replace one of these value
                        //where "ConfigLinkedHashMapValueInstanceCondValue" = matchingConfigType with the recordDocDepValue
                        if (possibleCondFieldLevel.get(configKey) != null) {
                          possibleCondFieldLevel.get(configKey).stream()
                                                .filter(obj -> obj instanceof Map)
                                                .map(obj -> (Map<String, Object>) obj)
                                                .filter(map -> matchingConfigType.equals(map.get("ConfigLinkedHashMapValueInstanceCondType")))
                                                .findFirst()
                                                .ifPresent(map -> map.put("ConfigLinkedHashMapValueInstanceCondValue", recordDocDepValue));
                            }
                        }                        
                         
                    }
                }
            
            }
        
          
        
        

    // print the final possibleCondFieldLevel in json format
   
    return possibleCondFieldLevel;
}

private static Object getNestedValue(Document doc, String key) {
    String[] keyParts = key.split("\\.");
    return getNestedValueRecursive(doc, keyParts, 0);
}

private static Object getNestedValueRecursive(Object current, String[] keyParts, int index) {
    if (current == null || index >= keyParts.length) {
        return current;
    }
    String key = keyParts[index];

    if (current instanceof Document) {
        Object next = ((Document) current).get(key);
        return getNestedValueRecursive(next, keyParts, index + 1);
    } else if (current instanceof List) {
        List<Object> results = new ArrayList<>();
        for (Object item : (List<?>) current) {
            Object result = getNestedValueRecursive(item, keyParts, index);
            if (result != null) {
                if (result instanceof List) {
                    results.addAll((List<?>) result);
                } else {
                    results.add(result);
                }
            }
        }
        return results.isEmpty() ? null : results;
    } else {
        return null;
    }
}
 
private static void setNestedValue(Document doc, String key, Object value) {
    String[] keyParts = key.split("\\.");
    setNestedValueRecursive(doc, keyParts, 0, value);
}

@SuppressWarnings("unchecked")
private static void setNestedValueRecursive(Object current, String[] keyParts, int index, Object value) {
    if (current == null || index >= keyParts.length) return;
    String key = keyParts[index];

    if (current instanceof Document) {
        Document currDoc = (Document) current;
        if (index == keyParts.length - 1) {
            currDoc.put(key, value);
        } else {
            Object next = currDoc.get(key);
            if (next == null) {
                // If next is not present, create a new Document
                Document newDoc = new Document();
                currDoc.put(key, newDoc);
                setNestedValueRecursive(newDoc, keyParts, index + 1, value);
            } else if (next instanceof Document) {
                setNestedValueRecursive(next, keyParts, index + 1, value);
            } else if (next instanceof List) {
                for (Object item : (List<?>) next) {
                    setNestedValueRecursive(item, keyParts, index + 1, value);
                }
            }
        }
    } else if (current instanceof List) {
        for (Object item : (List<?>) current) {
            setNestedValueRecursive(item, keyParts, index, value);
        }
    }
}

private static <T> T getRandomIntersectedValueForFieldKey(
        
        Object possibleCondFieldLevelValueList
) {
    Random rand = new Random();
    List<Set<T>> allPossibleValues = new ArrayList<>();
    String detectedType = null;


     
             // print possibleCondFieldLevelValueList in json format
            String jsonArrayStr = new Gson().toJson(possibleCondFieldLevelValueList);
            System.out.println("PossibleCondFieldLevelValueList JSON: " + jsonArrayStr);

            // Iterate through each entry in configLinkedHashMap
                
            
            for (Object possibleCondFieldLevelValueListIterator: (List<Object>) possibleCondFieldLevelValueList) {
                 
                // this possibleCondFieldLevelValueListIterator also has keys "ConfigLinkedHashMapValueIterationCondType" and
                // "ConfigLinkedHashMapValueIterationCondValue" like as below 
                // {"ConfigLinkedHashMapValueIterationCondValue":"[19, 65]", "ConfigLinkedHashMapValueIterationCondType":"RangeInt"},
                // need to extract these 2 keys and values



                if (!(possibleCondFieldLevelValueListIterator instanceof Map)) continue;
                // print the possibleCondFieldLevelValueListIterator in json format
                String jsonArrayStr1 = new Gson().toJson(possibleCondFieldLevelValueListIterator);
                System.out.println("PossibleCondFieldLevelValueListIterator JSON: " + jsonArrayStr1);

                Map<String, Object> cond = (Map<String, Object>) possibleCondFieldLevelValueListIterator;

                cond.entrySet().forEach(entry -> System.out.println(entry.getKey() + ": " + entry.getValue()));
                
                String condType = (String) cond.get("ConfigLinkedHashMapValueInstanceCondType");
                Object condValue = cond.get("ConfigLinkedHashMapValueInstanceCondValue");
                Set<T> possibleValues = new HashSet<>();
                detectedType = condType;

                switch (condType) {
                    case "RangeInt":
                        if (condValue instanceof List) {
                            List<?> range = (List<?>) condValue;
                            if (range.size() == 2) {
                                int min = ((Number) range.get(0)).intValue();
                                int max = ((Number) range.get(1)).intValue();
                                for (int i = min; i <= max; i++) {
                                    possibleValues.add((T) Integer.valueOf(i));
                                }
                            }
                        }
                        break;
                    case "ListInt":
                        if (condValue instanceof List) {
                            for (Object obj : (List<?>) condValue) {
                                possibleValues.add((T) Integer.valueOf(((Number) obj).intValue()));
                            }
                        }
                        break;
                    case "ListStr":
                        if (condValue instanceof List) {
                            for (Object obj : (List<?>) condValue) {
                                possibleValues.add((T) obj.toString());
                            }
                        }
                        break;

                    case "RangeDateYYYYMM":
                    List<?> range = (List<?>) condValue;
                            if (range.size() == 2) {
                                
                                // create minYear as first 4 digits of minYYYYMM
                                int minYear = ((Number) range.get(0)).intValue() / 100;
                                int minMonth = ((Number) range.get(0)).intValue() % 100;
                                
                                int maxYear = ((Number) range.get(1)).intValue() / 100;
                                int maxMonth = ((Number) range.get(1)).intValue() % 100;

                                // load a list of dates  with 1st  day of each month betwween  range (minYear, minMonth) and (maxTear, maxMonth
                                // e.g., if min is 202201 and max is 202212, then the list should be 20220101, 20220201, ..., 20221201
                                //print the minYear, minMonth, maxYear, maxMonth
                                System.out.println("Min Year: " + minYear + ", Min Month: " + minMonth + ", Max Year: " + maxYear + ", Max Month: " + maxMonth);    
                                java.time.LocalDate RangeDatestart = java.time.LocalDate.of(minYear, minMonth, 1);
                                java.time.LocalDate RangeDateend = java.time.LocalDate.of(maxYear, maxMonth, 1);

                                // print the RangeDatestart and RangeDateMonth

                                List<java.time.LocalDate> dateList = new ArrayList<>();
                                java.time.LocalDate current = RangeDatestart;
                                System.out.println("RangeDatestart: " + RangeDatestart + ", RangeDateend: " + RangeDateend
                                    + " condition:"+ current.isBefore(RangeDateend));
                                while (current.isBefore(RangeDateend)) {
                                    dateList.add(current);
                                    current = current.plusMonths(1);
                                    possibleValues.add((T) current.toString());
                                }
                            }
                            break;
         
                    default:
                      if (condType.contains("RangeDate*")){// look for subsrtring of switch case in this condition whether first 10 char match
                                 

                                String dateStr = condValue.toString();
                                System.out.println("Date String: " + dateStr);
                                java.time.LocalDate singleDate = java.time.LocalDate.parse(dateStr, java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd"));

                                // Parse condType: DateRange*:<:M:5
                                String[] parts = condType.split(":");
                                // print the parts
                                System.out.println("CondType Parts: " + Arrays.toString(parts));
                                if (parts.length == 4) {
                                    String directionStr = parts[1]; // ">" or "<"
                                    String freqUnitStr = parts[2];  // "D", "M", or "Y"
                                    int rangeFrequency = Integer.parseInt(parts[3]);

                                    int direction = directionStr.equals(">") ? 1 : -1;
                                    java.time.Period period;
                                    switch (freqUnitStr) {
                                        case "D": period = java.time.Period.ofDays(1); break;
                                        case "M": period = java.time.Period.ofMonths(1); break;
                                        case "Y": period = java.time.Period.ofYears(1); break;
                                        default: period = java.time.Period.ofDays(1); // fallback
                                    }

                                    List<java.time.LocalDate> dateList = new ArrayList<>();
                                    java.time.LocalDate current = singleDate;
                                    for (int i = 1; i <= rangeFrequency; i++) {
                                        current = direction > 0 ? current.plus(period) : current.minus(period);
                                        dateList.add(current);
                                        possibleValues.add((T) current.toString());
                                          
                                        if (i >= 50) break; // safety break to avoid infinite loops
                                    }
                                        }

                               }
                               break;
                }
              if (!possibleValues.isEmpty())   allPossibleValues.add(possibleValues);
                                
            }

            allPossibleValues.forEach(set -> System.out.println("Possible Values Set: " + set));
            // Find intersection of all possible values
            Set<T> intersection = null;
            for (Set<T> values : allPossibleValues) {
                if (intersection == null) {
                    intersection = new HashSet<>(values);
                } else {
                    intersection.retainAll(values);
                }
            }

            if (intersection != null && !intersection.isEmpty()) {
                List<T> intersectedList = new ArrayList<>(intersection);
                return intersectedList.get(rand.nextInt(intersectedList.size()));
            }
    return null;    
    }
}
