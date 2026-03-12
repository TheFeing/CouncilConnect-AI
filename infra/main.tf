# Logical container for all project-related assets
resource "azurerm_resource_group" "rg" { # resource type + local name
  name     = "rg-${var.project_name}"    # physical name on Azure
  location = var.location
}

# Log Analytics Workspace: Central hub for all telemetry and logs (K11)
resource "azurerm_log_analytics_workspace" "law" {
  name                = "logs-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018" # Current Pay-as-you-go model
  retention_in_days   = 30
}