package org.kolmanfreecss.kfimapiresponseservice.application.services;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.Iterator;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;

public class RuleValidator {

        public static List<RuleStructure> loadRules(String resourcePath) {
        List<RuleStructure> rules = new ArrayList<>();
        try {
            ObjectMapper mapper = new ObjectMapper();
            InputStream is = RuleValidator.class.getResourceAsStream("/AssignmentRules.json");
            JsonNode root = mapper.readTree(is);

            Iterator<String> eventNames = root.fieldNames();
            while (eventNames.hasNext()) {
                String event = eventNames.next();
                JsonNode eventNode = root.get(event);
                List<String> currSts = new ArrayList<>();
                eventNode.get("prvSts").forEach(node -> currSts.add(node.asText()));
                List<String> mandatory = new ArrayList<>();
                eventNode.get("Mandatory").forEach(node -> mandatory.add(node.asText()));

                rules.add(new RuleStructure(event, currSts, mandatory));
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to load rules: " + e.getMessage(), e);
        }
        return rules;
    }
     
}

/*
 List<RuleStructure> rules = RuleLoader.loadRules("/AssignmentRules.json");
// Now you can use rules.stream().filter(r -> r.event().equals("ASSIGN")).findFirst()...
 */
