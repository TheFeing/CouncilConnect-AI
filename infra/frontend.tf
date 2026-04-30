# Provisioning the Public-Facing UI Container App

resource "azurerm_container_app" "frontend" {
  name                         = "ui-${var.project_name}"
  container_app_environment_id = azurerm_container_app_environment.env.id   # Defined in network.tf
  resource_group_name          = azurerm_resource_group.rg.name             # Defined in main.tf
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "ui-service"
      image  = "${azurerm_container_registry.acr.login_server}/councilconnect-ui:latest"
      cpu    = 0.25
      memory = "0.5Gi"
      
      # Injecting the Backend FQDN as an environment variable (Service Discovery)
      env {
        name  = "BACKEND_URL"
        # Explicitly referencing the backend container app created in compute.tf
        value = "https://${azurerm_container_app.app.ingress[0].fqdn}"
      }
      
      # Deployment metadata for Sprint 9 Blue/Green logic
      env {
        name  = "APP_VERSION"
        value = "v1.0-stable"
      }
    }
    
    min_replicas = 0    # Scale to zero when inactive (K4)
    max_replicas = 3
  }

  ingress {
    external_enabled = true     # Public internet access
    target_port      = 8501
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

# Output the public URL for verification
output "frontend_url" {
  value = azurerm_container_app.frontend.ingress[0].fqdn
}