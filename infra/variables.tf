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

# gemma_api_key: Sensitive placeholder for the AI model authentication
# This value should be provided via GitHub Secrets or CLI at runtime
variable "gemma_api_key" {
  type        = string
  description = "API Key for the Gemma Inference Engine"
  sensitive   = true
}