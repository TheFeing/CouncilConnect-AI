# --- CORE INFRASTRUCTURE, MONITORING & NETWORKING ---
# Establishes the foundational "World" including financial safety and observability.

# Tenant and Subscription ID context
data "azurerm_client_config" "current" {}

# Resource Group: The logical container for all project-related assets
resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.project_name}"
  location = var.location
}

# Provider Registration: Automates the registration of the Alerts Management provider
resource "azurerm_resource_provider_registration" "alerts_management" {
  name = "Microsoft.AlertsManagement"
}

# Financial budget to prevent runaway costs from scaling
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

  # Ensures the provider is registered before attempting to create the budget alerts
  depends_on = [azurerm_resource_provider_registration.alerts_management]
}

# Log Analytics Workspace: Central hub for all telemetry and logs
resource "azurerm_log_analytics_workspace" "law" {
  name                = "logs-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Application Insights for distributed performance tracking (e.g., P95 latency 200ms)
resource "azurerm_application_insights" "app_insights" {
  name                = "ai-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"
}

# Container App Environment: The secure virtual boundary for compute resources
resource "azurerm_container_app_environment" "env" {
  name                       = "env-${var.project_name}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
  # Connects Dapr sidecar telemetry to Application Insights for end-to-end distributed tracing.
  dapr_application_insights_connection_string = azurerm_application_insights.app_insights.connection_string
}