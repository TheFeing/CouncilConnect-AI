# Fetch the secret value from Key Vault at plan/apply time
data "azurerm_key_vault_secret" "gemma_key" {
  name         = "GEMMA-API-KEY"
  key_vault_id = azurerm_key_vault.main.id
}

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
      image  = "${azurerm_container_registry.acr.login_server}/councilconnect-ai:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "VAULT_URL"
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
    min_replicas = 0  # Scale-to-Zero: Cost is £0 when not in use
    max_replicas = 10

    http_scale_rule {
      name                = "scale-on-requests"
      concurrent_requests = "10"  # New instance spins up for every 10 concurrent users
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
  depends_on = [
    azurerm_role_assignment.acr_pull
  ]
}

# The Managed Identity only receives 'Read' permissions (Least-Privilege)
resource "azurerm_role_assignment" "vault_access" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_container_app.app.identity[0].principal_id
}