# --- FOUNDATIONAL INFRASTRUCTURE ---

# Access current client configuration for Tenant ID
data "azurerm_client_config" "current" {}

# 1. Logical container for all project-related assets
resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.project_name}"
  location = var.location
}

# 2. Log Analytics Workspace: Central hub for all telemetry and logs (K11)
resource "azurerm_log_analytics_workspace" "law" {
  name                = "logs-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# --- SECURITY & SECRETS MANAGEMENT ---

# 3. Define the Key Vault to store sensitive API keys (K15)
resource "azurerm_key_vault" "main" {
  name                        = "kv-${var.project_name}"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  enable_rbac_authorization   = true
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  sku_name = "standard"
}