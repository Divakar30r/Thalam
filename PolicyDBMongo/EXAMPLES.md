# MongoDB Java Examples

## Complex Queries

```java
// Find documents with multiple criteria
public List<Document> findByMultipleCriteria(String key1, Object value1, String key2, Object value2) {
    Document query = new Document(key1, value1).append(key2, value2);
    List<Document> results = new ArrayList<>();
    collection.find(query).into(results);
    return results;
}

// Find with sorting
public List<Document> findWithSorting(String key, Object value, String sortField, int sortOrder) {
    Document query = new Document(key, value);
    List<Document> results = new ArrayList<>();
    collection.find(query)
            .sort(new Document(sortField, sortOrder)) // 1 for ascending, -1 for descending
            .into(results);
    return results;
}

// Find with projection (selecting specific fields)
public List<Document> findWithProjection(String key, Object value, String... fields) {
    Document query = new Document(key, value);
    Document projection = new Document();
    for (String field : fields) {
        projection.append(field, 1);
    }
    
    List<Document> results = new ArrayList<>();
    collection.find(query).projection(projection).into(results);
    return results;
}

// Find with limit and skip (pagination)
public List<Document> findWithPagination(int pageNumber, int pageSize) {
    int skip = (pageNumber - 1) * pageSize;
    List<Document> results = new ArrayList<>();
    collection.find()
            .skip(skip)
            .limit(pageSize)
            .into(results);
    return results;
}
```

## Aggregation Operations

```java
public List<Document> runAggregation(List<Document> pipeline) {
    List<Document> results = new ArrayList<>();
    collection.aggregate(pipeline).into(results);
    return results;
}

// Sample specific aggregation operation - grouping by field
public List<Document> groupByField(String groupField, String sumField) {
    List<Document> pipeline = new ArrayList<>();
    
    // Group stage
    Document groupStage = new Document("$group", 
        new Document("_id", "$" + groupField)
            .append("count", new Document("$sum", 1))
            .append("total", new Document("$sum", "$" + sumField))
    );
    pipeline.add(groupStage);
    
    // Sort stage (optional)
    Document sortStage = new Document("$sort", 
        new Document("count", -1)
    );
    pipeline.add(sortStage);
    
    return runAggregation(pipeline);
}

// Sample lookup (join) aggregation
public List<Document> lookupCollection(String foreignCollection, String localField, 
                                      String foreignField, String as) {
    List<Document> pipeline = new ArrayList<>();
    
    Document lookupStage = new Document("$lookup",
        new Document("from", foreignCollection)
            .append("localField", localField)
            .append("foreignField", foreignField)
            .append("as", as)
    );
    pipeline.add(lookupStage);
    
    return runAggregation(pipeline);
}
```

## Example Usage in Controller

```java
@GetMapping("/complex-query")
public List<Document> complexQuery(@RequestParam String categoryName, @RequestParam double minPrice) {
    return feeds.findByMultipleCriteria("category", categoryName, "price", new Document("$gte", minPrice));
}

@GetMapping("/user-stats")
public List<Document> userStats() {
    List<Document> pipeline = new ArrayList<>();
    
    // Group users by country and count them
    pipeline.add(new Document("$group", 
        new Document("_id", "$country")
            .append("userCount", new Document("$sum", 1))
            .append("averageAge", new Document("$avg", "$age"))
    ));
    
    // Sort by user count descending
    pipeline.add(new Document("$sort", new Document("userCount", -1)));
    
    return users.runAggregation(pipeline);
}

@GetMapping("/users-with-feeds")
public List<Document> usersWithFeeds() {
    return users.lookupCollection("feeds", "userId", "createdBy", "userFeeds");
}
```

## Working with Filters

```java
import static com.mongodb.client.model.Filters.*;
import static com.mongodb.client.model.Projections.*;
import static com.mongodb.client.model.Sorts.*;

public List<Document> findWithComplexFilters(String category, double minPrice, double maxPrice) {
    List<Document> results = new ArrayList<>();
    collection.find(and(
            eq("category", category),
            gte("price", minPrice),
            lte("price", maxPrice),
            exists("description")
        ))
        .sort(descending("price"))
        .into(results);
    return results;
}
```

## Additional Aggregation Examples

### Pipeline Stages

```java
// Example with multiple pipeline stages
public List<Document> complexAggregation(String matchField, Object matchValue, String groupField) {
    List<Document> pipeline = new ArrayList<>();
    
    // Match stage
    pipeline.add(new Document("$match", 
        new Document(matchField, matchValue)
    ));
    
    // Group stage
    pipeline.add(new Document("$group", 
        new Document("_id", "$" + groupField)
            .append("count", new Document("$sum", 1))
    ));
    
    // Project stage
    pipeline.add(new Document("$project", 
        new Document("_id", 0)
            .append("category", "$_id")
            .append("count", 1)
    ));
    
    // Sort stage
    pipeline.add(new Document("$sort", 
        new Document("count", -1)
    ));
    
    // Limit stage
    pipeline.add(new Document("$limit", 10));
    
    return runAggregation(pipeline);
}
```

### Working with Arrays

```java
// Unwind arrays
public List<Document> unwindArrays(String arrayField) {
    List<Document> pipeline = new ArrayList<>();
    
    pipeline.add(new Document("$unwind", "$" + arrayField));
    
    pipeline.add(new Document("$group", 
        new Document("_id", "$" + arrayField)
            .append("count", new Document("$sum", 1))
    ));
    
    pipeline.add(new Document("$sort", 
        new Document("count", -1)
    ));
    
    return runAggregation(pipeline);
}
```

### Date Operations

```java
// Group by date parts
public List<Document> groupByDateParts(String dateField) {
    List<Document> pipeline = new ArrayList<>();
    
    pipeline.add(new Document("$group", 
        new Document("_id", 
            new Document("year", new Document("$year", "$" + dateField))
                .append("month", new Document("$month", "$" + dateField))
        )
        .append("count", new Document("$sum", 1))
    ));
    
    pipeline.add(new Document("$sort", 
        new Document("_id.year", 1).append("_id.month", 1)
    ));
    
    return runAggregation(pipeline);
}
```
