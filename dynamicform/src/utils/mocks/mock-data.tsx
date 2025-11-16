// --- MOCK DATA ---
// This data is a stand-in for what would be fetched from the
// 'CP_OrderManagement.RoleDetails' collection in MongoDB.

export const INDUSTRY_DATA = [
  {
    "Industry":"Pharma",
    "Scale":"Retail",
    "factors": {
      "Brand":["GSK","SunPharma"],
      "^Dosage":["mg","ml"],
      "Storage":"ColdPacking",
      "RouteForm":{"Oral":["Tablet","Capsule","Syrup"],"External":["Injection","Ointment","Cream","Capsule"]},
      "^Age":["months","Years"],
      "Unit*":["Strips","Numbers","Bottles"],
      "Size":["XS","S","M","L","XL","XLS"]
    }
  },
  {
    "Industry":"Biscuits",
    "Scale":"Cottage",
    "factors": {
      "Specifics":"*/*NoMaida*/*Nuts*/*Chocochips*/*GlutenFree*/*",
      "Sugarlevel":["0-5%","5-15%",">15%"],
      "flavour":["Ragi","Wheat","Oats","Multigrain","Jowar"],
      "Unit*":["Pack of 10","Pack of 5","Pack of 2","Pack of 20"],
    }
  },
  {
    "Industry":"Footwear",
    "Scale":"Cotage",
    "factors": {
      "SoulType":["Rexin","Leather"],
      "Gender*":["Male","Female"],
      "Model":["Loafers","Flipflops","Shoes","Belts","Sockspair"],
      "Size*": ["footsize","hip size"],
      "Unit*":["numbers"]
    }
  },
  {
    "Industry":"Groceries",
    "Scale":"Retail",
    "factors":
    {
      "Storage":"ColdPacking",
      "^Unit*":["Kg","g","mg","ml","l","numbers"],
      "Pack":["Bottle","Sachet"], 
      "Type":["ReadyToEat","FoodIngredient","Cleaning"],
      "Form":["Solid/Bar","Liquid/Detergent"]
    }
  }
];