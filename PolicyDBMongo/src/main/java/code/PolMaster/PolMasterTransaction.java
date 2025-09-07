package code.PolMasterCreation;

public class PolMasterTransaction {

        // Java class representing the JSON structure
    
        public static class Payment {
            public Double Amount = null;
            public String Date = null;
            public String BenfitCode = null; // Note: typo as in original JSON
            public String BenefitCode = null;
        }
        public Payment LastPayment = new Payment();
        public Payment DuePayment = new Payment();
    }

