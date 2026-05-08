# --- FOUNDATIONAL INFRASTRUCTURE ---

# Access current client configuration for Tenant ID
data "azurerm_client_config" "current" {}

# Logical container for all project-related assets
resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.project_name}"
  location = var.location
}

# Log Analytics Workspace: Central hub for all telemetry and logs (K11)
resource "azurerm_log_analytics_workspace" "law" {
  name                = "logs-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# --- SECURITY & SECRETS MANAGEMENT ---

# Define the Key Vault to store sensitive API keys (K15)
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

# --- RESOURCE MONITORING ---

# Application Insights for distributed tracing and P95 latency (200ms)
resource "azurerm_application_insights" "app_insights" {
  name                = "ai-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"
}

# Automate the registration of the Alerts Management provider
resource "azurerm_resource_provider_registration" "alerts_management" {
  name = "Microsoft.AlertsManagement"
}

# Financial budget to prevent runaway costs from scaling (K4)
resource "azurerm_consumption_budget_resource_group" "safety_budget" {
  name              = "budget-${var.project_name}"
  resource_group_id = azurerm_resource_group.rg.id
  amount            = 10 # Monthly limit in GBP
  time_grain        = "Monthly"
  time_period {
    start_date = "${formatdate("YYYY-MM-01", timestamp())}T00:00:00Z" # Must be the first of a month
    # end_date   = "2028-04-01T00:00:00Z" # Optional: When the budget expires
  }

  notification {
    enabled        = true
    threshold      = 90.0
    operator       = "GreaterThanOrEqualTo"
    contact_emails = ["ngfeilik@gmail.com"]
  }
}