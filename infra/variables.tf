# --- INPUT VARIABLES & OUTPUT ENDPOINTS ---
# Centralises all configurable inputs and surfaces critical endpoint URLs.

# project_name: Used as a prefix for all resources to ensure naming consistency
variable "project_name" {
  type        = string
  description = "The base name for all CouncilConnect resources"
  default     = "councilconnect-ai"
}

# location: Regional default set to France Central for quota compatibility
variable "location" {
  type        = string
  description = "The Azure region where resources will be provisioned"
  default     = "francecentral"
}

# Output: The public URL for the resident interface
output "frontend_url" {
  value = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

# Output: The internal Vault URI for visibility
output "vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

# The Object ID of the CI/CD Service Principal (GitHub actions)
variable "pipeline_sp_object_id" {
  type        = string
  description = "The Object ID of the sp-councilconnect service principal"
  default     = "df68d97e-bcff-4c54-9d79-f1e5cdd5c999"
}