<#-- Minimal Keycloak login template customization for 26.4.0 -->
<#assign ctx = kc">
<!DOCTYPE html>
<html lang="${locale}">
<head>
  <meta charset="utf-8" />
  <title>Sign in - Order Management</title>
  <link rel="stylesheet" href="${url.resourcesPath}/css/login.css" />
</head>
<body>
  <div class="kc-login-wrapper">
    <div class="kc-login-logo">OrderMgmt</div>
    <div class="kc-login-box">
      <h1>Sign in to Order Management</h1>
      <#-- include Keycloak login form -->
      <@loginForm />
    </div>
    <div class="kc-login-footer">&copy; ${now?date?string["yyyy"]} Acme Corp</div>
  </div>
</body>
</html>
