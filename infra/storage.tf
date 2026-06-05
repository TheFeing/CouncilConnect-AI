# --- BLOB STORAGE FOR DISASTER RECOVERY BACKUPS ---
# Acts as a backup storage for council knowledge

# Random suffix for globally unique storage account name
resource "random_string" "storage_suffix" {
  length  = 6
  special = false
  upper   = false
}

# Storage account (Cool tier – low cost for infrequent access)
resource "azurerm_storage_account" "backup" {
  name                     = "sacouncilconnect${random_string.storage_suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  access_tier              = "Cool"
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = false
  }
}

# Private container for backup JSON files
resource "azurerm_storage_container" "backup" {
  name                  = "knowledge-base-backups"
  storage_account_name  = azurerm_storage_account.backup.name
  container_access_type = "private"
}

# Grant the backend app’s managed identity write access to the container
resource "azurerm_role_assignment" "backend_blob_writer" {
  scope                = azurerm_storage_account.backup.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_container_app.app.identity[0].principal_id
}