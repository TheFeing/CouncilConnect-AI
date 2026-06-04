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

# Financial budget to prevent runaway costs
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
    contact_emails = [var.alert_email]
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

# Application Insights for distributed performance tracking
resource "azurerm_application_insights" "app_insights" {
  name                = "ai-${var.project_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"
}

# Action Group for email notifications
resource "azurerm_monitor_action_group" "email" {
  name                = "ag-councilconnect-email"
  resource_group_name = azurerm_resource_group.rg.name
  short_name          = "council" # In email subject, must be <13 chars

  email_receiver {
    name          = "send_email"
    email_address = var.alert_email
  }
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

# Alert when backend container app replica count hits 5
resource "azurerm_monitor_metric_alert" "high_replica_count" {
  name                = "alert-high-replica-count"
  resource_group_name = azurerm_resource_group.rg.name
  scopes              = [azurerm_container_app.app.id]
  description         = "Alert when average replica count hits 5 over 5 minutes"
  severity            = 2      # 0-Critical, 1-Error, 2-Warning, 3-Informational, 4-Verbose
  frequency           = "PT1M" # Period of time = 1 minute, evaluation frequency
  window_size         = "PT5M" # Period of time = 5 minute, lookback window

  criteria {
    metric_namespace = "Microsoft.App/containerapps"
    metric_name      = "Requests"
    aggregation      = "Total" # Or "Average" for the past period of time window
    operator         = "GreaterThanOrEqual"
    threshold        = 500
  }

  action {
    action_group_id = azurerm_monitor_action_group.email.id
  }
}