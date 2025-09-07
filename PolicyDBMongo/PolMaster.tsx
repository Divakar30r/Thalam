    /*
    SystemDate is always before EffectiveDate and never in the future.
    No chnages for keys whose values are set as nulls
    Transaction.LastPayment.Date is always in the past.
    Transaction.LastPayment.Amount does not exceed SumInsured and in multiples of 100
    DuePayment.Amount does not exceed 1000 and in multiples of 100
    PendingCoverage is at least 10% of SumInsured.
    Suminsured is a  number in multiples of 10000
    */
    const docs = [];
    for (let i = 1; i <= 20; i++) {
    // SystemDate: 1-30 days ago
    const sysDaysAgo = Math.floor(Math.random() * 30) + 1;
    const systemDate = new Date(Date.now() - sysDaysAgo * 86400000);

    // EffectiveDate: 1-10 days after SystemDate
    const effDaysAhead = Math.floor(Math.random() * 10) + 1;
    const effectiveDate = new Date(systemDate.getTime() + effDaysAhead * 86400000);

    // SumInsured: 100,000 - 2,000,000 in multiples of 10,000
    const sumInsured = (Math.floor(Math.random() * 190) + 10) * 10000;

    // PendingCoverage: at least 10% of SumInsured
    const minPending = Math.ceil(sumInsured * 0.1 / 100) * 100; // round up to nearest 100
    const pendingCoverage = (Math.floor(Math.random() * ((sumInsured - minPending) / 100 + 1)) * 100) + minPending;

    // LastPayment.Amount: multiple of 100, ≤ SumInsured
    const lastPaymentAmount = (Math.floor(Math.random() * (sumInsured / 100)) + 1) * 100;

    // LastPayment.Date: between systemDate and now (always in past)
    const lastPaymentDaysAgo = Math.floor(Math.random() * sysDaysAgo) + 1;
    const lastPaymentDate = new Date(systemDate.getTime() - lastPaymentDaysAgo * 86400000);

    // DuePayment.Amount: multiple of 100, ≤ 1000
    const duePaymentAmount = (Math.floor(Math.random() * 10) + 1) * 100;

    // DuePayment.Date: 1-30 days after EffectiveDate
    const duePaymentDaysAhead = Math.floor(Math.random() * 30) + 1;
    const duePaymentDate = new Date(effectiveDate.getTime() + duePaymentDaysAhead * 86400000);

    docs.push({
        PolicyType:"TBD",
        PolicyNumber: `TBD${7000000 + i}`,
        SystemDate: systemDate,
        EffectiveDate: effectiveDate,
        ExpirationDate: null,
        PolicyStatus: null,
        Language: null,
        Transaction: {
        LastPayment: {
            Amount: lastPaymentAmount,
            Date: lastPaymentDate,
            BenfitCode: null
        },
        DuePayment: {
            Amount: duePaymentAmount,
            Date: duePaymentDate,
            BenefitCode: null
        }
        },
        SumInsured: sumInsured,
        PendingCoverage: pendingCoverage,
        ThirdParty: null,
        JurisdictionState: null,
        Term: null,
        Frequency: null
    });
    }

    db.getCollection('PolMaster').insertMany(docs);

