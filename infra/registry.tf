resource "azurerm_container_registry" "acr" {
  name                = "acr${replace(var.project_name, "-", "")}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false # Security: Use Managed Identity for pulls
}

resource "azurerm_user_assigned_identity" "acr_puller" {
  name                = "id-acr-puller"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# Grant Container App Permission to pull from the registry
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.acr_puller.principal_id
}