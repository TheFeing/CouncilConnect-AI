# --- SECURITY PERIMETER: KEY VAULT, REGISTRY & RBAC ---
# Isolates Identity, Permission, and Secret Storage logic.

# Define the Key Vault to store sensitive API keys
resource "azurerm_key_vault" "main" {
  name                        = "kv-${var.project_name}"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  enable_rbac_authorization   = true
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard" # Premium SKU provides HSM-protected (Hardware Security Module)
}

# Private repository for Docker images
resource "azurerm_container_registry" "acr" {
  name                = "acr${replace(var.project_name, "-", "")}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false # Security: Use Managed Identity for pulls
}

# Dedicated Identity for pulling images from ACR
resource "azurerm_user_assigned_identity" "acr_puller" {
  name                = "id-acr-puller"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# --- ROLE ASSIGNMENTS (RBAC) ---

# ACR Pull Role: Grants the pull identity permission to read from the registry
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.acr_puller.principal_id
}

# Admin Access Role: Grants the logged-in developer full access to manage data in Key Vault
resource "azurerm_role_assignment" "admin_access" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Vault Access Role: Grants the Backend App permission to read secrets from the Key Vault
resource "azurerm_role_assignment" "vault_access" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_container_app.app.identity[0].principal_id
}

# Automation Pipeline Access: Grants the CI/CD Service Principal permission to manage secrets
resource "azurerm_role_assignment" "sp_vault_access" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.pipeline_sp_object_id
}