# --- APPLICATION SERVICES (BACKEND AI ENGINE & RESIDENT UI) ---
# Manages the Frontend and Backend connection logic.

# Fetches the Gemma API key from Key Vault
data "azurerm_key_vault_secret" "gemma_key" {
  name         = "GEMMA-API-KEY"
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

  # Maps the secret fetched via the data source into the app configuration
  secret {
    name  = "gemma-api-key"
    value = data.azurerm_key_vault_secret.gemma_key.value
  }

  # Desired state: Container blueprint
  template {
    container {
      name   = "api-gateway"
      image  = "${azurerm_container_registry.acr.login_server}/councilconnect-backend:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "VAULT_URL" # Must match the name Python code looks for
        value = azurerm_key_vault.main.vault_uri
      }

      # Inject the secret alias into the actual environment variable
      env {
        name        = "GEMMA_API_KEY"
        secret_name = "gemma-api-key"
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.app_insights.connection_string
      }
    }

    # KEDA Scaling: Logic to manage replicas based on traffic
    min_replicas = 0 # Scale-to-Zero: Cost is £0 when not in use
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
      percentage = 100
      # revision_name = "app-v1-blue"
      latest_revision = true
    }
    # traffic_weight {
    #   revision_name = "app-v2-green"
    #   percentage    = 10
    # }
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
        name = "BACKEND_URL"
        # Explicitly referencing the backend container app created in compute.tf
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