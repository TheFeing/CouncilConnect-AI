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