import Keycloak from 'keycloak-js';

const fnkeycloak = new Keycloak({
  url: 'http://localhost:9090', // base URL for your realm
  realm: 'DivRealm',                             // your realm name
  clientId: 'ReactSBootMongo-ClientID-FE'           // your client ID as configured in Keycloak
});

export default fnkeycloak;