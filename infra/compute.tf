resource "azurerm_container_app" "app" {
  name                         = "app-${var.project_name}"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single" # No Blue/Green deployments

  identity {
    type = "SystemAssigned"
  }

  # Desired state: Container blueprint
  template {
    container {
      name   = "api-gateway"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      # Commented out in Sprint 6
      # env {
      #   name  = "GEMMA_API_KEY"
      #   value = var.gemma_api_key
      # }

      env {
        name  = "VAULT_URL"
        value = azurerm_key_vault.main.vault_uri
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
      percentage      = 100
      latest_revision = true
    }
  }
}

# The Managed Identity only receives 'Read' permissions (Least-Privilege)
resource "azurerm_role_assignment" "vault_access" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_container_app.app.identity[0].principal_id
}