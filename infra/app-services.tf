# --- APPLICATION SERVICES (BACKEND AI ENGINE & RESIDENT UI) ---
# Manages the Frontend and Backend connection logic.

# Fetches the Gemma API key from Key Vault
data "azurerm_key_vault_secret" "gemma_key" {
  name         = "GEMMA-API-KEY"
  key_vault_id = azurerm_key_vault.main.id
}

# Fetches the authenticated Qdrant cluster access token from Key Vault
data "azurerm_key_vault_secret" "qdrant_key" {
  name         = "QDRANT-API-KEY"
  key_vault_id = azurerm_key_vault.main.id
}

# Fetches the external Qdrant Cloud SaaS cluster URL endpoint from Key Vault
data "azurerm_key_vault_secret" "qdrant_url" {
  name         = "QDRANT-URL"
  key_vault_id = azurerm_key_vault.main.id
}

# Backend Container App: Scraping and Vector engine
resource "azurerm_container_app" "app" {
  name                         = "app-${var.project_name}"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Multiple" # Use "Single" for no Blue/Green deployments

  identity {
    type         = "SystemAssigned, UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.acr_puller.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.acr_puller.id
  }

  # Retaining existing secrets declarations to satisfy the Azure API constraint
  secret {
    name  = "gemma-api-key"
    value = data.azurerm_key_vault_secret.gemma_key.value
  }

  secret {
    name  = "qdrant-url"
    value = data.azurerm_key_vault_secret.qdrant_url.value
  }

  secret {
    name  = "qdrant-api-key"
    value = data.azurerm_key_vault_secret.qdrant_key.value
  }

  # Desired state: Container blueprint
  template {
    container {
      name   = "api-gateway"
      image  = "${azurerm_container_registry.acr.login_server}/councilconnect-backend:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "AZURE_KEY_VAULT_ENDPOINT" # Matches what Python code scans for
        value = azurerm_key_vault.main.vault_uri
      }

      # Inject values directly as explicit deployment string inputs to avoid look-up delays
      env {
        name  = "GEMMA_API_KEY"
        value = data.azurerm_key_vault_secret.gemma_key.value
      }

      env {
        name  = "QDRANT_URL"
        value = data.azurerm_key_vault_secret.qdrant_url.value
      }

      env {
        name  = "QDRANT_API_KEY"
        value = data.azurerm_key_vault_secret.qdrant_key.value
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.app_insights.connection_string
      }
    }

    # KEDA Scaling: Logic to manage replicas based on traffic
    min_replicas = 0  # Scale-to-Zero: Cost is £0 when not in use
    max_replicas = 10

    http_scale_rule {
      name                = "scale-on-requests"
      concurrent_requests = "10" # New instance spins up for every 10 concurrent users
    }
  }

  ingress {
    allow_insecure_connections = false # Enforces HTTPS (K16)
    external_enabled           = true
    target_port                = 8000

    # Routing instruction (e.g., Blue/Green deployment traffic)
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  # Makes sure Role Assignment is ready first
  depends_on = [azurerm_role_assignment.acr_pull]
}

# Frontend UI Container App: Resident & Admin Portal
resource "azurerm_container_app" "frontend" {
  name                         = "ui-${var.project_name}"
  container_app_environment_id = azurerm_container_app_environment.env.id # Defined in other .tf files
  resource_group_name          = azurerm_resource_group.rg.name           # Defined in other .tf files
  revision_mode                = "Single"

  # ACR Puller identity
  identity {
    type         = "SystemAssigned, UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.acr_puller.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.acr_puller.id
  }

  template {
    container {
      name   = "ui-service"
      image  = "${azurerm_container_registry.acr.login_server}/councilconnect-frontend:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      # Injecting the Backend FQDN as an environment variable (Service Discovery)
      env {
        name  = "BACKEND_URL"
        value = "https://${azurerm_container_app.app.ingress[0].fqdn}"
      }

      # Deployment metadata for Sprint 9 Blue/Green logic
      env {
        name  = "APP_VERSION"
        value = "v1.0-stable"
      }
    }

    min_replicas = 0  # Scale to zero when inactive (K4)
    max_replicas = 10 # Should match backend's ceiling

    # Scaling logic to prevent bottlenecks
    http_scale_rule {
      name                = "scale-on-requests"
      concurrent_requests = "20"
    }
  }

  ingress {
    external_enabled = true # Public internet access
    target_port      = 8501
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  # Ensure role assignment exists before deployment
  depends_on = [azurerm_role_assignment.acr_pull]
}