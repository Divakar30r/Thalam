package code.PolMasterCreation;

import code.PolMasterCreation.PolMasterTransaction;
import lombok.Data;

@Data
public   class PolMaster {

        public String PolicyType = null;
        public String PolicyNumber = null;
        public String SystemDate = null;
        public String EffectiveDate = null;
        public String ExpirationDate = null;
        public String PolicyStatus = null;
        public String Language = null;
        public PolMasterTransaction Transaction = new PolMasterTransaction();
        public Double SumInsured = null;
        public Double PendingCoverage = null;
        public String ThirdParty = null;
        public String JurisdictionState = null;
        public Integer Term = null;
        public String Frequency = null;
    }
