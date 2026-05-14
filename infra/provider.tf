# --- TERRAFORM & AZURE PROVIDER CONFIGURATION ---
# Establishes the connection and versioning for the Azure Cloud API.

# Terraform Block: Configures the requirements for the Terraform binary
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0" # Prevents breaking changes from newer provider releases
    }
  }
  # Remote Backend: State file is stored in Azure Blob Storage rather than locally
  backend "azurerm" {}
}

# Provider Block: Configures the specific instance of the AzureRM provider
provider "azurerm" {
  features {
    resource_group {
      # Allow RG deletion even if it contains resources
      prevent_deletion_if_contains_resources = false
    }
  }
}