package code;

import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.function.Supplier;
import java.util.stream.Collector;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

public class StreamLearner {

    //load a string  array with value "123",'ABC","s$"',"1323"
    public static void main(String[] args) {

        int arrint[] = {1,2,3,4,5};
        //print the sum of the array using streams
        System.out.println("Sum of array using streams: " + Arrays.stream(arrint).sum());
        // if input is a list of integers - math functions are easy on primitives
        List<Integer> arrint_list = Arrays.asList(12,12,132);
        System.out.println("Sum of array list using streams: " + arrint_list.stream().mapToInt(Integer::intValue).sum());


        String[] arr = {"123", "ABC", "s$", "1323"};
        // using regex filter the array to print only numeric values
        Arrays.stream(arr).filter(s -> s.matches("\\d+")).forEach(System.out::println);

        String[] polprefixes = {"PN", "CI", "DI"};
        String polString = "find the policynumberPN1A2345 in this context assume policy number always starts with PN followed by 5 digits";
       // Split into words and use streams to find the policy number
        Arrays.stream(polString.split("\\s+"))
        .filter(word -> word.matches(".*PN\\d{5}.*"))
        .map(word -> {
            // Extract PN and 5 digits using regex
            java.util.regex.Matcher m = java.util.regex.Pattern.compile("PN\\d{5}").matcher(word);
            return m.find() ? m.group() : null;
        })
        .filter(s -> s != null)
        .forEach(policyNumber -> System.out.println("Policy Number w/ exact regex: " + policyNumber));
 
    

    Arrays.stream(polString.split("\\s+"))
    .filter(s -> s.matches(".*\\d{5}.*"))
    .forEach(s -> {
        System.out.println("Found policy number w/ 5 digits: " + s);
        Arrays.stream(polprefixes)
            .filter(prefix -> polString.contains(prefix + s.replaceAll("[^\\d]", "")))
            .forEach(prefix -> System.out.println("Found policy number w/ multiple prefixes " + prefix + s));
        }); 


    String multipleOccurences = "list each words in the string and categorize each word as numeric or alphabetic or alphanumeric";
    Map<String, Long> oMap = Arrays.stream(multipleOccurences.split("\\s+")). collect(Collectors.groupingBy(Function.identity(),Collectors.counting()));
    System.out.println(oMap);
    
    String findtwovowels = "find words with atleast two vowels in the string";
    List<String> twoVowels=Arrays.stream(findtwovowels.split("\\s+")).filter(s -> s.matches(".*[aeiouAEIOU].*[aeiouAEIOU].*")).collect(Collectors.toList());
    System.out.println("TwoVowels using regex double pattern"+twoVowels);

    twoVowels=Arrays.stream(findtwovowels.split("\\s+")).filter(s -> s.replaceAll("[^aeiouAEIOU]","").length()>=2).collect(Collectors.toList());
    System.out.println("TwoVowels using Replace w/ regex pattern"+twoVowels);

    String alphanumeric = "find words with atleast one alphabet and one numeric in the string";

    int arrgroupdigitlengthroundoff[] = {1121, 2113, 43435,2199, 3121, 1, 99,41232};
    List<Integer> arrgroupdigitlengthroundoff_list = Arrays.stream(arrgroupdigitlengthroundoff).boxed().collect(Collectors.toList());
    Map<Integer, List<Integer>> o_Map_arrgroupdigitlengthroundoff= arrgroupdigitlengthroundoff_list.stream().
        collect(Collectors.groupingBy(x->{
                    int factor = (int) Math.pow(10, Integer.toString(x).length() - 2 > 0 ? Integer.toString(x).length() - 2 : 0);
                    return (x / factor) * factor;
        }));
   Map<Integer, Long> o_Map_arrgroupdigitlengthroundoff_withCount= arrgroupdigitlengthroundoff_list.stream().
        collect(Collectors.groupingBy(x->{
                    int factor = (int) Math.pow(10, Integer.toString(x).length() - 2 > 0 ? Integer.toString(x).length() - 2 : 0);
                    return (x / factor) * factor;
                    }, Collectors.counting()));
    System.out.println("Input array: " + Arrays.toString(arrgroupdigitlengthroundoff));
    System.out.println("for the input " + "Group by digit length roundoff 2 digits:" +o_Map_arrgroupdigitlengthroundoff);
    System.out.println("for the input " + "Group by digit length roundoff 2 digits just count:" +o_Map_arrgroupdigitlengthroundoff_withCount);

    int arrproductof2elements[] = {9,2,3,4};
    int o_arrproductof2elements= Arrays.stream(arrproductof2elements).boxed().collect(Collectors.toList()).stream().limit(arrproductof2elements.length>=2 ? 2: arrproductof2elements.length)
        //.reduce((a,b)->a*b); 


        .reduce(1,(a,b)->a*b); 
    System.out.println("Input array: " + Arrays.toString(arrproductof2elements) + " Product of first two elements: " + o_arrproductof2elements);

    String[] arrpairanagrams = {"reap","pear","rape","one","neo"};
    Map<Object, List<String>> o_arrpairanagrams  =    Arrays.asList(arrpairanagrams)
        .stream().collect(Collectors.groupingBy(s->Arrays.stream(s.toLowerCase().split("")).sorted().collect(Collectors.toList())));
    System.out.println("Input array: " + Arrays.toString(arrpairanagrams) + " Anagram pairs: " + o_arrpairanagrams);        
    //to print only values pair i.e. the pair of anagrams
    Collection<List<String>> o_arrpairanagrams_collections  =    Arrays.asList(arrpairanagrams)
        .stream().collect(Collectors.groupingBy(s->Arrays.stream(s.toLowerCase().split("")).sorted().collect(Collectors.toList()))).values();
    System.out.println("Input array: " + Arrays.toString(arrpairanagrams) + " Anagram pairs: " + o_arrpairanagrams_collections);        
    

    int arrmultipleevenindexes[]={1,2,3,4,5,6,7,8,9,10,11};
    Integer o_arrmultipleevenindexes= IntStream.range(1, arrmultipleevenindexes.length)
        .filter(i -> i % 2 == 0)
        .map(i -> arrmultipleevenindexes[i])
        .reduce(1, (a,b)->a*b);
        
    System.out.println("Input array: " + Arrays.toString(arrmultipleevenindexes) + " Product of elements at even indexes: " + Integer.toString(o_arrmultipleevenindexes));
         

    int arrmultiplicationmovinginside[]={1,2,3,4,5,6,7,8,9,10,11};
    
    List<Integer> arrmultiplicationmovinginside_pairedlist = IntStream.range(0, arrmultiplicationmovinginside.length /2 )
            .map(i -> arrmultiplicationmovinginside[i] * arrmultiplicationmovinginside[arrmultiplicationmovinginside.length - 1 - i])
            .boxed().collect(Collectors.toList());
    if (arrmultiplicationmovinginside.length % 2 != 0) 
        arrmultiplicationmovinginside_pairedlist.add(arrmultiplicationmovinginside[arrmultiplicationmovinginside.length / 2 ]);
    
    System.out.println("Input array: " + Arrays.toString(arrmultiplicationmovinginside) + " Multiplication moving inside: " + arrmultiplicationmovinginside_pairedlist);

    int arrsort[] = {1,5,3,7,2,8,4,6};
    Arrays.stream(arrsort).mapToObj(x->x).sorted(Collections.reverseOrder()).forEach(System.out::print);
    Arrays.stream(arrsort).mapToObj(x->x).sorted().forEach(System.out::print);

    int pushzerosend[] = {1,0,2,0,3,0,4,0,5};
     
    //print input array
    System.out.println("Input array for pushzerosend: " + Arrays.toString(pushzerosend) + " Push zeros to end: ");
     Arrays.stream(pushzerosend).boxed().collect(Collectors.partitioningBy(x->x!=0))
    .values().stream().flatMap(List::stream).forEach(System.out::print);
            
    //noneMatch on streams

    // determine whether it's an distinct array
    int checkdistinctarray[] = {1,2,3,4,5,6,7,8,9,10,1};
    // Method 1: loading the stram to Set and comparing the size of set to array length
    boolean isDistinct = Arrays.stream(checkdistinctarray).boxed().collect(Collectors.toSet()).size() == checkdistinctarray.length;
    // Method 2: using indexof to determine if first and last index of an element is same
     // ** First need to convert int[] to list as IndexOf is an object level operaiton ***
    List<Integer> checkdistinctarray_list = Arrays.stream(checkdistinctarray).boxed().collect(Collectors.toList());
     
    System.out.println("Input array for distinct check: " + Arrays.toString(checkdistinctarray) + " isDistinct: " + 
    checkdistinctarray_list.stream().noneMatch(i->checkdistinctarray_list.indexOf(i)!=checkdistinctarray_list.lastIndexOf(i))
    );

    // Group based on middle character
    String[] groupbymiddlechar = {"abc","bcd","cde","def","abcd","bcde","cdef","abcde"};
    // print input array groupbymiddlechar
    System.out.println("Input array for group by middle char: " + Arrays.toString(groupbymiddlechar) + " Group by middle char: ");
    Arrays.asList(groupbymiddlechar).stream()
    .filter(s->s.length()%2!=0) // consider only odd length strings to have a middle character
    .collect(Collectors.groupingBy(s->s.charAt(s.length()/2)))
    .forEach((k,v)->System.out.println(k + " : " + v));

    //sort List of strings based on alphabetic order
    List<String> sortlistofstrings = Arrays.asList("Pineapple","banana","ornage","kiwi","sortlistofstrings","apple");
    System.out.println("Input list for sortlistofstrings: " +    sortlistofstrings + " Sorted list: " );
    sortlistofstrings.stream().map(s->s.toUpperCase()).sorted().map(s-> s+" / ").forEach(System.out::print);                 

    // intersection of 2 lists
    List<String> list1 = Arrays.asList("A","B","C","D","E");
    List<String> list2 = Arrays.asList("D","E","F","G","H");
    // print the input arrays
    System.out.print("\nInput list1 for intersection: " +    list1 + "Input list2 for intersection: " +    list2 + " Intersection: " );
    list1.stream().filter(list2::contains).forEach(s -> System.out.print(s + " / "));
    
    // list of string containing all types of string - alphabets, amounts and alphanuemrickeys
    List<String> wcomparinglist = Arrays.asList("A","B","C","D","E","100","200","300","400","500","A100","B200","C300"); 
    // convert each element in the list as object and filter the type using instance of

    /*You cannot directly filter numeric strings using instanceof Integer because all elements in your list are String objects. However, you can attempt to convert each string to an Integer and filter those that succeed, handling exceptions for non-numeric strings. */
     System.out.print("\nInput list for comparinglist: " +    wcomparinglist + " Amounts: " );
      wcomparinglist.stream().map(s->{
            try{
                return Integer.valueOf(s);
            }catch(NumberFormatException e){return null;}
        })
        .filter(Integer.class::isInstance)
        .forEach(s -> System.out.print(s + " / "));


    // transforming custom objects using Collector
    List<CustomObject> customObjects = Arrays.asList(
        new CustomObject("A", 10),
        new CustomObject("B", 20),
        new CustomObject("C", 30),
        new CustomObject("A", 40),
        new CustomObject("B", 50)
    );
    Collector<CustomObject, ?, Map<String, List<CustomObject>>> collector = Collectors.groupingBy(CustomObject::getName);
    // get the Map as separate variable from Collector and print
    Map<String, List<CustomObject>> groupedByName = customObjects.stream().collect(collector);
    System.out.println("\nInput list for custom objects: " +    customObjects + " Grouped by name: " + groupedByName);
 
    // another example
    Collector<CustomObject, StringBuilder, String> NameConcatenation = 
        Collector.of(
                () -> new StringBuilder(), // Supplier
                (sb, co) -> {
                    if (sb.length() > 0) sb.append(", ");
                    sb.append(co.name);
                }, // Accumulator
                (sb1, sb2) -> {
                    if (sb1.length() > 0 && sb2.length() > 0) sb1.append(", ");
                    sb1.append(sb2);
                    return sb1;
                }, // Combiner
                StringBuilder::toString // Finisher
        );
     
    System.out.println("Concatenated Names: " + customObjects.stream().collect(NameConcatenation) );


    // iterate example - FIBONACCI
    Stream.iterate
            (new int[]{0, 1} // initializer
           , p -> new int[]{p[1], p[0] + p[1]} // function to generate next element
            )
        .limit(10) // ensure a limit is set, else it goes into infinitie 
        .map(p -> p[0]) // extract the Fibonacci number
        .forEach(n -> System.out.print(n + " / "));


    // Suppliers and stream reuse
    int streamsreusearr[] = {1,2,3,4,5,6,7,8,9,10};
    Stream<Integer> streamsreuse_stream = Arrays.stream(streamsreusearr).boxed();
    System.out.println(" Print the sum "+ streamsreuse_stream.mapToInt(x->x).sum());
    try{
     streamsreuse_stream.forEach(s->System.out.print(s+" / ")); // this will throw IllegalStateException
    }catch(IllegalStateException e){
        System.out.println(" Exception caught on consuming stream twice: " + e.toString());
    }
    Supplier<Stream<Integer>> streamsreuse_supplier = () -> Arrays.stream(streamsreusearr).boxed();
    System.out.println(" Print the sum "+ streamsreuse_supplier.get().mapToInt(x->x).sum());
    streamsreuse_supplier.get().forEach(s->System.out.print(s+" / ")); // this will now throw IllegalStateException: stream has already been operated upon or closed.
    
    // concatenation of streams 
    Stream<String> stream1 = Stream.of("A", "B", "C");
    Stream<String> stream2 = Stream.of("D", "E", "F");  
    Stream<String> concatenatedStream = Stream.concat(stream1, stream2);
    System.out.println("\n Concatenated Stream: "); 
    concatenatedStream.forEach(s->System.out.print(s+" / "));


    Product p1 = new Product(1, "Lifeboy", 24, "Soap");
    Product p2 = new Product(2, "Portronics", 200, "Adapter");
    Product p3 = new Product(3, "SurfExcel", 90, "Washing Powder");
    Product p4 = new Product(4, "Yamaha", 8000, "Guitar");
    Product p5 = new Product(5, "Tikapi", 50, "Muesli");

    List<Product> productList = Arrays.asList(p1, p2, p3, p4, p5);

    // #1 - print products price less than 100
    List<String> filteredProducts = productList.stream()
        .filter(p -> p.getPrice() < 100)
        .map(Product::getName)
        .collect(Collectors.toList());

    System.out.println(filteredProducts);

    //#2- Reduce products by 20% and create new list w/o disturbing original list
    List<Product> newProductList = productList.stream().map(p-> {
        // clone each product object to avoid disturbing original list
        Product newP = new Product(p.getI(), p.getName(), p.getPrice(), p.getDesc());
        newP.setPrice(p.getPrice()*.70);
        return newP;
        }).collect(Collectors.toList());

    newProductList.forEach(p->System.out.println("NewProductSet:" + p.getName() + " " + p.getPrice())) ;
     
    //#2a- Reduce products by 20% and print the entire product object
    productList.stream().map(p-> {
        p.setPrice(p.getPrice()*.80);
        return p;
    }).collect(Collectors.toList());
    // print the productList objects listing each attributes
    productList.forEach(p->System.out.println("ProductSet:" + p.getName() + " " + p.getPrice())) ;

    // #3 - Average price of products
    productList.stream().map(Product::getPrice).mapToDouble(p->p).average().ifPresent(avg->System.out.println("Average price of products: " + avg));

    // #4
         productList.stream().map(
        Product::getPrice).mapToDouble(p->p).
        reduce((pCurrentPrice, pNextPrice)-> Math.min(pCurrentPrice,pNextPrice))
        .ifPresent(min->System.out.println("Minimum price of products using reduce : " + min));;
      
        productList.stream().min((a,b)-> Double.compare(a.getPrice(), b.getPrice())).ifPresent(min->System.out.println("Minimum price of products using min on streams : " + min.getPrice()));
   
    // Next question - use streams generate for getting current date on DD/MM/YY format 
    Stream.generate(()->java.time.LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("dd/MM/yy"))).limit(1)
        .forEach(s->System.out.println("Current date using streams generate: " + s));


    // create an int arr with 10 random numbers of heterogenrous range 1-1000 with atleast 5 starting with 1,  


    int randomarrheterogeneous[] = new java.util.Random().ints(10, 1, 1000).toArray();
    Arrays.stream(randomarrheterogeneous).distinct().filter(x -> String.valueOf(x).startsWith("1")).sorted().boxed().collect(Collectors.toList()).reversed().forEach(s->System.out.print(s + " / "));

    // comparing products with same price
     List<Product> productList2 = Arrays.asList(
        new Product(6, "Lifeboy", 24, "Soap"),
        new Product(7, "Portronics", 200, "Adapter"),
        new Product(8, "SurfExcel", 90, "Washing Powder"),
        new Product(9, "Yamaha", 8000, "Guitar"),
        new Product(10, "Tikapi", 50, "Muesli"),
        new Product(8, "Rin", 110, "Washing Powder")
    );

    productList2.stream().sorted(Comparator.comparing(Product::getName).thenComparing(Product::getDesc)).forEach(p->System.out.println("Sorted products: " + p.getName() + " " + p.getDesc()));


    // Method 1 (group to Map) comparing repetitve words and their count 
    String repetitivewords = "list each words in the string and categorize each word as numeric or alphabetic or alphanumeric list each words in the string and categorize each word as numeric or alphabetic or alphanumeric"; 
    //print input string
    System.out.println("Input string for repetitive words: " + repetitivewords);
    Map<String, Long> repetitivewords_map = Arrays.stream(repetitivewords.split("\\s+")).collect(Collectors.groupingBy(Function.identity(),Collectors.counting()));
    System.out.println("Repetitive words and their count: " + repetitivewords_map);

    // Method 2(group to Map and comparingByValue) - comparing repetitve words splitting with spaces and filter words > 2 characters and removing spaces
    System.out.println("Repetitive words > 2 characters without spaces: ");
    Map<String, Long> repetitivewords_Map= Arrays.stream(repetitivewords.split("\\s+"))
        .filter(s-> s.length()>2)
        .map(s->s.replace(" ",""))
        .collect(Collectors.groupingBy(Function.identity(),Collectors.counting()));
     
    Map.Entry<String, Long> maxEntry = repetitivewords_Map.entrySet().stream()
        .max(Map.Entry.comparingByValue())
        .orElse(null);
    
    if (maxEntry != null) 
    System.out.println("Word with highest count: " + maxEntry.getKey() + " -> " + maxEntry.getValue());


    //Method 3 (using IntStresm and specific search string) Input string with no spaces and filter words > 2 characters and removing spaces
    String longstringwospaces = Arrays.stream(repetitivewords.split("\\s+"))
    .filter(s -> s.length() > 2)
    .map(s -> s.replace(" ", ""))
    .collect(Collectors.joining(""));
    //generated the input string
    System.out.println("Input string after filtering words > 2 characters and removing spaces: " + longstringwospaces); 

    String searchstr ="word";
    long searchstroccurencecount = IntStream.range(0, longstringwospaces.length()-1-searchstr.length())
             .filter(i-> longstringwospaces.substring(i, i+searchstr.length()).equals(searchstr)).count();
    // print the occurence count of searchstr in longstringwospaces
    System.out.println("Occurence count of '" + searchstr + " in longstringwospaces: " + searchstroccurencecount);
     
    // Method 4 (using nested loops) - most repeatedword of length > 3 characters
        int minLen = 3;
         
                 
         Map<String, Long> freq = IntStream.range(0, longstringwospaces.length())
            .boxed()
            .flatMap(i -> 
                IntStream.range(i + minLen, longstringwospaces.length() + 1).mapToObj(j -> longstringwospaces.substring(i, j)))
            .collect(Collectors.groupingBy(sub -> sub, Collectors.counting()));
        System.out.println("All substrings of length > " + minLen + " and their counts: " + freq);

        String mostRepeated = freq.entrySet().stream()
            .filter(e -> e.getValue() > 1)
            .max(Map.Entry.comparingByValue())
            .map(Map.Entry::getKey)
            .orElse("No repeats");

        System.out.println("Most repeated substring using nested methods: " + mostRepeated);


        


    // Log message sorting
    //"HH":"MM":"SS":idnumber: Logmessage
    // generate above pattern as a single message and load into List<string> for 5 such messages
     

    List<String> logmessages = Arrays.asList(
    "12:32:15:1004:Password changed",
    "12:30:45:1001:User login successful",
    "12:34:45:1005:File deleted",
    "12:31:00:1002:File uploaded",
    "12:33:30:1003:User logout"
);

    logmessages.stream()
        .sorted(Comparator
            .comparing((String wlog) -> {
                // Extract time part
                java.util.regex.Matcher matcher = java.util.regex.Pattern.compile("\\b\\d{2}:\\d{2}:\\d{2}\\b").matcher(wlog);
                String time = matcher.find() ? matcher.group() : "";
                // Parse to LocalTime for proper comparison
                return java.time.LocalTime.parse(time, java.time.format.DateTimeFormatter.ofPattern("HH:mm:ss"));
            })
            .thenComparing(wlog -> {
                // Extract ID part (after time, before next colon)
                String[] parts = wlog.split(":");
                return parts.length > 3 ? Integer.parseInt(parts[3]) : 0;
            })
        )
    .forEach(s -> System.out.println("Sorted log messages: " + s));
     

    // Merge key conflicts handled in Collectors.toMap
    // create a list of fruites
    List<String> fruits = Arrays.asList("apple", "banana", "orange", "apple", "kiwi", "banana", "apple");
    fruits.stream().collect(Collectors.toMap(
        Function.identity(), // key is the fruit name
        v -> 1,              // initial count is 1
        Integer::sum         // merge function to sum counts for duplicate keys - without this any deuplicates leads to IllegalStateException

        // alternative function
        // (existing, replacement) -> existing + 1
    )).forEach((fruit, count) -> System.out.println(fruit + ": " + count));
    
    /* 
    NOTES
    -----

    only non string arrays need to be boxed to convert to list, for string arrays -> Arrays.asList(arr) is sufficient

    Here Object could be string, long, integer or any custom object based on the actual process
    Map<Object, List<Objects> = collectors.groupingBy(actual process) by default loads the process output as key and all entities matching the process given into List<Objects>
                            = collectors.groupingBy(actual process, count/length/min/max...)    loads the process output as key and all entities matching the process aggregated by count/length/sum/avg/min/max into
                            List<Objects>

    if a list formed using integer array, no new elements allowed as it's actually a primitive array converted to list of integers

    reduce((a,b)->a*b) -> takes two elements at a time and applies the function to reduce to single value. This returns Optional<>
    reduce(1,(a,b)->a*b) -> takes two elements at a time and applies the function to reduce to single value with initial value 1
    1 is the initial value, if the array is empty it returns 1

    IntStreams are used whereved index based operations are needed and then loaded values using map

    mapTo... is used to convert streams into an primitive stream of int,long,double

    You cannot use .collect(Collectors.groupingBy(...)) directly on an IntStream
    : You need to box the IntStream to a Stream<Integer> before collecting:

    flatmap isList<list<object>> to List<object> conversion

    Collectors.partitioningBy is a special case of Collectors.groupingBy that groups elements into two categories based on a predicate(true/false). (not any key)

    Flexibility of bulk operations and row wise operations
     row wise: forEach(s -> System.out.print(s + " / ")); or filter (x -> x != 0) or map(x -> x * 2)
     bulk: forEach(System.out::print); or sum() or collect(Collectors.toList()) or filter(wcomparinglist::contains) )

    The map does not modify the original stream; it creates a new stream with the transformed elements.(Immmutability)

    ForEach, Reduce, count,... are terminal operators and cannot be chained further. Streams cannot be used again leading to IllegalStateException: stream has already been operated upon or closed. however this can be overcome with use of suppliers


    primitive streams (IntStream, LongStream, DoubleStream) are specialized streams for handling primitive data types. They provide methods that are optimized for performance and memory usage when working with primitive values. Primitive streams avoid the overhead of boxing and unboxing that occurs when using wrapper classes like Integer, Long, and Double in regular streams.



    streams.allMatch(predicate) - returns true if all elements match the given predicate.
    streams.anyMatch(predicate) - returns true if any element matches the given predicate.
    streams.noneMatch(predicate) - returns true if no elements match the given predicate.
                             
    String ConcatenatedString = Arrays.stream(repetitivewords.split("\\s+"))
    .filter(s -> s.length() > 2)
    .map(s -> s.replace(" ", ""))
    .collect(Collectors.joining(""));


    Map also combine with streams, comparingByValue is comparison on the value list
    Map.Entry<String, Long> maxEntry = repetitivewords_Map.entrySet().stream()
        .max(Map.Entry.comparingByValue())
    */
 
}  
}

   

   class CustomObject{
     
        public String name;
        public int value;
        public double amount;
        
        public CustomObject(String name, int value){
            this.name = name;
            this.value = value;
        }

        public CustomObject(String name, int value, double amount){
            this.name = name;
            this.value = value;
            this.amount = amount;
        }

        @Override
        public String toString(){
            return "CustomObject{name='" + name + "', value=" + value + "}";
        }

        public String getName() {
            return name;
        }
        public int getValue() {
            return value;
        }
        public double getAmount() {
            return amount;
        }
    }