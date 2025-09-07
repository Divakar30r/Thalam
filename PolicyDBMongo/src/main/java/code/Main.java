package code;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Random;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;

import com.mongodb.client.*;
import com.mongodb.client.model.Updates;
import org.bson.Document;
import java.util.*;



@SpringBootApplication
public class Main {
    public static void main(String[] args) {

        
        //code.PolMasterCreation.PolMasterCreation.insertNullPolMaster();
        code.PolMasterCreation.PolMasterMocker.UpdatePolTest();
        //PolDBtables.UpdatePolTest();
     //ConfigurableApplicationContext context = SpringApplication.run(Main.class, args);

    }
}