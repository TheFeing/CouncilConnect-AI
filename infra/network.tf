# Container App Environment: The secure virtual boundary for compute resources
resource "azurerm_container_app_environment" "env" {
  name                       = "env-${var.project_name}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
  # Connects Dapr sidecar telemetry to Application Insights for end-to-end distributed tracing.
  dapr_application_insights_connection_string = azurerm_application_insights.app_insights.connection_string
}