package code.PolMaster;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import java.util.stream.Collectors;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public class PolMasterFieldThreadsv2 {

     
    private static Map<String, Object> lockMap = new HashMap<>();
    private static List<String> CollectionFieldList;
    private static Map<String,List<String>> KeysDeps;
    private static Map<String, CountDownLatch> latchMap = new HashMap<>();
    private static LinkedHashMap<String, List<Object>> LoaderFinal = new LinkedHashMap<>();
    private static HashMap<String , Object> LoaderFinalValueUnit = new HashMap<>();
    private static LinkedHashMap<String, List<String>> LoggerFinal = new LinkedHashMap<>();


    public static void executeThread(String field,ExecutorService executorObj) {

        executorObj.execute(() -> {

            // print LoaderFinalValueUnit
            
            List<Object> LoaderFinalValueUnitObj 
              = LoaderFinalValueUnit.entrySet()
                                    .stream()
                                    .map(e -> {
                                        Map<String, Object> map = new HashMap<>();
                                        if ("Parents".equals(e.getKey()) && e.getValue() instanceof LinkedList) 
                                            map.put("Parents", new LinkedList<>((List<?>) e.getValue()));
                                         
                                        if ("Completed?".equals(e.getKey()) && e.getValue() instanceof String) 
                                            map.put("Completed?", ( String) e.getValue());

                                        if ("Interrupted?".equals(e.getKey()) && e.getValue() instanceof Boolean) 
                                            map.put("Interrupted?", ( Boolean) e.getValue());

                                        return (Object) map;
                                    })
                                    .collect(Collectors.toList());

            LoaderFinal.put(field, LoaderFinalValueUnitObj);
            System.out.println("Thread started for : " + field + " " + Thread.currentThread().getName() + "             @ " + Instant.now());
             
            System.out.println("LoaderFinal on start of " + field + ": " + new Gson().toJson(LoaderFinal.get(field)));
            /* Gson gson = new GsonBuilder().setPrettyPrinting().create();
            String json = gson.toJson(LoaderFinal.get(field));
            System.out.println("LoaderFinal.get(" + field + "):\n" + json);
 */
            List<String> logList = new ArrayList<>();
            logList.add("Thread started for : " + field + Thread.currentThread().getName() + "             @ " + Instant.now());
            LoggerFinal.put(field, logList);
             try {
                    Thread.sleep(10_000); // Sleep for 30 seconds
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                if (latchMap.containsKey(field)) { // a child field
                    
                    try {
                        // Wait for the latch to reach zero
                        System.out.println( field+ " waiting for latch: " +
                        latchMap.get(field).getCount() + "@ " + Instant.now());
                        latchMap.get(field).await(100, TimeUnit.SECONDS);
                        if (latchMap.get(field).getCount() == 0) {
                            System.out.println(field + " All dependencies resolved, proceeding...@ " + Instant.now());
                            LoggerFinal.get(field).add(field + " All dependencies resolved, proceeding...@ " + Instant.now());
                            LoaderFinal.get(field)
                                            .stream()
                                            .filter(x -> x instanceof Map)
                                            .map(x -> (Map<String,Object>) x)
                                            .filter(x -> x.containsKey("Completed?"))
                                            .findFirst()
                                            .ifPresent(map -> map.replace("Completed?", "Done"));
                            
                            if (lockMap.containsKey(field)) notifyAllThreads(lockMap.get(field), field);
                                            
                            System.out.println("LoaderFinal after completion of " + field + ": " + new Gson().toJson(LoaderFinal.get(field)));

                         } else {
                            System.out.println(field + " Timeout reached while waiting for dependencies.@ " + Instant.now());
                            LoggerFinal.get(field).add(field + " Timeout reached while waiting for dependencies.@ " + Instant.now());
                        }
                    } catch (InterruptedException e) {
                        System.out.println("Thread interrupted while waiting for latch: " + e.getMessage());
                        Thread.currentThread().interrupt();
                    }
                }
                else if(KeysDeps.entrySet()
                                    .stream()
                                    .filter(x -> x.getValue().contains(field))
                                    .count() > 0) // a parent field
                {
                    // Notify all threads waiting on this field's lock
                    notifyAllThreads(lockMap.get(field), field);
                    LoaderFinal.get(field)
                                            .stream()
                                            .filter(x -> x instanceof Map)
                                            .map(x -> (Map<String,Object>) x)
                                            .filter(x -> x.containsKey("Completed?"))
                                            .findFirst()
                                            .ifPresent(map -> map.replace("Completed?", "Done"));
                            System.out.println("LoaderFinal after completion of " + field + ": " + new Gson().toJson(LoaderFinal.get(field)));
 

                }
                else{  // a standalone field
 

                    LoaderFinal.get(field)
                                            .stream()
                                            .filter(x -> x instanceof Map)
                                            .map(x -> (Map<String,Object>) x)
                                            .filter(x -> x.containsKey("Completed?"))
                                            .findFirst()
                                            .ifPresent(map -> map.replace("Completed?", "Done"));
                            System.out.println("LoaderFinal after completion of " + field + ": " + new Gson().toJson(LoaderFinal.get(field)));

                }

                System.out.println("Thread finished for : " + field + "           @ " + Instant.now());
                LoggerFinal.get(field).add("Thread finished for : " + field + "           @ " + Instant.now());
            });
       
    }

    public static void waitForCondition(Object lock, String parentfld, String childfld) throws InterruptedException {
    synchronized (lock) {
        try {
            System.out.println("Thread "+ childfld + " is waiting for "+ parentfld);
            lock.wait();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            // update the interrupted flag  in LoaderFinal
            LoaderFinal.get(childfld)
                        .stream()
                        .filter(x -> x instanceof Map)
                        .map(x -> (Map<String,Object>) x)
                        .filter(x -> x.containsKey("Interrupted?"))
                        .findFirst()
                        .ifPresent(map -> map.replace("Interrupted?", Boolean.TRUE));

            throw new InterruptedException();
        }
        }
    }

    public static void notifyAllThreads(Object lock, String parentfld) {
        synchronized (lock) {
            System.out.println("Notifying all waiting threads waiting for " + parentfld + "...");
            lock.notifyAll();
        }
    }

    public static void executeThreadDepDriver(Map.Entry<String, List<Object>> entry, ExecutorService executorObj) {

        
             
                String childfld = entry.getKey();

                for (String parentfld : KeysDeps.get(entry.getKey())) {
                    
                        // convert the below to runnable
                    
                        Runnable RunParents = (() -> {
                            System.out.println(Thread.currentThread().getName() +" Dependency thread started for : " + parentfld + " of child " + childfld + "           @ " + Instant.now());
                            LoggerFinal.get(childfld).add(Thread.currentThread().getName() +" Dependency thread started for : " + parentfld + " of child " + childfld + "           @ " + Instant.now());
                            try{
                                if (!LoaderFinal.containsKey(parentfld) || 

                                            LoaderFinal.get(parentfld)
                                                                    .stream()
                                                                    .filter(x -> x instanceof Map)
                                                                    .map(x -> (Map<String,Object>) x)
                                                                    .filter( x -> x.containsKey("Completed?") && x.get("Completed?")!="Done")
                                                                    .count() > 0
                                )
                                
                                {
                                System.out.println("Child " + childfld + " is waiting for parent " + parentfld + " to complete. @ " + Instant.now());
                                LoggerFinal.get(childfld).add("Child " + childfld + " is waiting for parent " + parentfld + " to complete. @ " + Instant.now());
                                waitForCondition(lockMap.get(parentfld), parentfld, childfld);
                                }
                            }catch(InterruptedException ie){
                                System.out.println("Dependency thread interrupted as shutdown initiated for " + parentfld + "-" + childfld + ": " + ie.getMessage());
                                Thread.currentThread().interrupt();
                                return;
                            }
                            catch(Exception e){
                                LoggerFinal.get(childfld).add("Exception in waiting for parent " + parentfld + " to complete for child " + childfld + ": " + e.getMessage() + " @ " + Instant.now());
                                System.out.println("Exception in waiting for parent " + parentfld + " to complete for child " + childfld + ": " + e.getMessage() + " @ " + Instant.now());
                            }   
                             
                     
    

                                // Update the LoaderFinal of childfld to add parentfld and gparentflds to the LinkedList "Parents"
                                if (latchMap.containsKey(childfld)) {
                                    List<String> gparentflds =   LoaderFinal.get(parentfld)
                                                                        .stream()
                                                                        .filter(x -> x instanceof Map)
                                                                        .map(x -> (Map<String,Object>) x)
                                                                        .filter( x -> x.containsKey("Parents") && x.get("Parents") instanceof LinkedList)
                                                                        .findFirst()
                                                                        .map(x -> (LinkedList<String>) x.get("Parents"))
                                                                        .orElseGet(LinkedList::new);

                                        if (gparentflds.size() > 0){
                                                LoaderFinal.get(childfld)
                                                    .stream()
                                                    .filter(x -> x instanceof Map)
                                                    .map(x -> (Map<String,Object>) x)
                                                    .filter( x -> x.containsKey("Parents") && x.get("Parents") instanceof LinkedList)
                                                    .findFirst()
                                                    .ifPresent(map -> {
                                                            // Add all gparentflds and parentfld to the "Parents" LinkedList
                                                            LinkedList<String> parentsList = (LinkedList<String>) map.get("Parents");
                                                            parentsList.addAll(gparentflds);
                                                            parentsList.add(parentfld);
                                                            map.replace("Parents", parentsList);
                                                    });

                                                    LoggerFinal.get(childfld).add("Child " + childfld + " loaded with grandparents into Linkedlist " + gparentflds + " @ " + Instant.now());
                                            }
                                            else {
                                                LoaderFinal.get(childfld)
                                                    .stream()
                                                    .filter(x -> x instanceof Map)
                                                    .map(x -> (Map<String,Object>) x)
                                                    .filter( x -> x.containsKey("Parents") && x.get("Parents") instanceof LinkedList)
                                                    .forEach(map -> {
                                                            LinkedList<String> parentsList = (LinkedList<String>) map.get("Parents");
                                                            if (!parentsList.contains(parentfld)) {
                                                                parentsList.add(parentfld);
                                                            }
                                                            map.replace("Parents", parentsList);
                                                        });
                                                    LoggerFinal.get(childfld).add("Child " + childfld + " loaded with parent into Linkedlist " + parentfld + " @ " + Instant.now());
                                        }

                                    
                                        latchMap.get(childfld).countDown();
                                        System.out.println("Parent  " + parentfld + " triggered for " + childfld + ", latch count: " +
                                            latchMap.get(childfld).getCount() + " @ " + Instant.now());
                                            LoggerFinal.get(childfld).add("Parent  " + parentfld + " triggered for " + childfld + ", latch count: " +
                                            latchMap.get(childfld).getCount() + " @ " + Instant.now());
                                    
                                
                               
                            }
                            System.out.println("Dependency thread finished for : " + parentfld + "           @ " + Instant.now());
                        });


                    // Execute the command as a thread    
                         executorObj.execute(RunParents);
           
                }
  
    }
    public static void getLinkedfieldsv2() {
        
        CollectionFieldList = PolMasterFieldThreads.getCollectionFieldList("PolDB", "PolMaster");
        
        KeysDeps = PolMasterFieldThreads.getKeysandDepedencies("PolDB", "PolMaster");

        // Create a CountDownLatch on all children
         for (String field : KeysDeps.keySet()) {
            if (KeysDeps.get(field).size()>0)
            latchMap.put(field, new CountDownLatch(KeysDeps.get(field).size()));
            
        }

        // lockMap on all Parents 
        for (String Parentfield: KeysDeps.entrySet()
                                    .stream()
                                    .filter(x-> x.getValue().size()>0)
                                    .flatMap(x-> x.getValue().stream())
                                    .distinct()
                                    .collect(Collectors.toList()) 
                                    )
        {
           // print parentfield that is being loaded in lockmap
            System.out.println("Loading lockMap for parentfield: " + Parentfield);  
            lockMap.put(Parentfield, new Object());
        }

        //get the values (List<String>) of KeysDeps and flatten it to a single list
        Set<String> flattenedParents = KeysDeps.entrySet().stream().flatMap(entry -> entry.getValue().stream().distinct()).collect(Collectors.toSet());
        // compare each values of flattenedParents with the latchMap values and if found,load it in map with flatterrnedDeps value as key and latchmap corresponding keys as value
        Map<String, Set<String>> reverseDeps = new HashMap<>();
        for (String dep : flattenedParents) {
            for (Map.Entry<String, CountDownLatch> entry : latchMap.entrySet()) {
                String key = entry.getKey();
                if (KeysDeps.get(key).contains(dep)) {
                    reverseDeps.computeIfAbsent(dep, k -> new HashSet<>()).add(key);
                }
            }
        }

        LoaderFinalValueUnit.put("Parents", new LinkedList<>());
        LoaderFinalValueUnit.put("Completed?", new String());
        LoaderFinalValueUnit.put("Interrupted?", Boolean.FALSE);
 
        // create a basic object delcaration with key value pair of field name and field value
        ExecutorService executorObj = Executors.newCachedThreadPool();
        // print the KeysDeps as json
        System.out.println("KeysDeps: " + new Gson().toJson(KeysDeps));

        List<String> HighDepList = KeysDeps.entrySet().stream()
        .filter(x -> x.getValue().size() > 0)
        .sorted((e1, e2) -> Integer.compare(e2.getValue().size(), e1.getValue().size()))
        .map(Map.Entry::getKey)
        .collect(Collectors.toList());

        try{
            for (String field : HighDepList) {

             
            executeThread(field, executorObj);
            Thread.sleep(2000); // Stagger different field thread starts slightly
            }
        } catch(Exception e){
            System.out.println("Exception in HighDeps threads creation: "+ e.getMessage());
        }
       
        // Thread pool for remaining fields
          
        try{
        // Start a thread for each field in CollectionFieldList
            for (String field : CollectionFieldList.stream().filter(x -> !HighDepList.contains(x) && !x.equals("PolicyType")).collect(Collectors.toList())) {
                Thread.sleep(2000); // Stagger different field thread starts slightly
                executeThread(field, executorObj);
            }
        }catch(Exception e){
            System.out.println("Exception in Parent threads creation: "+ e.getMessage());
        }

        

        Deque<Map.Entry<String, List<Object>>> LoaderFinalQ = 
                new ConcurrentLinkedDeque<>(new ArrayList<>(LoaderFinal.entrySet()
                                                                       .stream()
                                                                       .filter(e -> HighDepList.contains(e.getKey()))
                                                                       .collect(Collectors.toList()))     );
        List<String> DeferredList = new ArrayList<>();

        while (!LoaderFinalQ.isEmpty()) {
            Map.Entry<String, List<Object>> entry = LoaderFinalQ.pollFirst();
            
            if (   !LoaderFinal.keySet().contains(entry.getKey())  &&  !(DeferredList.contains(entry.getKey()))      ) 
             {
                    System.out.println("Deferring field: " + entry.getKey());
                    LoaderFinalQ.addLast(entry); // Re-add to the end of the queue
                    DeferredList.add(entry.getKey());
                    continue; // Skip processing for now
             }

                // execute the thread task
                System.out.println("Processing   field: " + entry.getKey());
                DeferredList.add(entry.getKey());
                executeThreadDepDriver(entry, executorObj);
         }
        
        try {
        Thread.sleep(5000); // Ensure all dependency threads are started before the last field
        executeThread("PolicyType", executorObj);  
        executorObj.shutdown();
         
            if (!executorObj.awaitTermination(20, TimeUnit.SECONDS)) {
                executorObj.shutdownNow(); // Force shutdown if not finished
            }
        } catch (InterruptedException e) {
            executorObj.shutdownNow();
            Thread.currentThread().interrupt();
        }

        // print LoaderFinal as json
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(LoaderFinal);
        System.out.println("Final LoaderFinal:\n" + json);

        gson = new GsonBuilder().setPrettyPrinting().create();
        json = gson.toJson(LoggerFinal);
        System.out.println("Final LoggerFinal:\n" + json);
        // Optionally, shutdown the executor after all tasks are submitted
        
         
         
    }
}
