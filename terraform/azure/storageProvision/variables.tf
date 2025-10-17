variable "resource_group_name" {
  description = "Name of the resource group to host storage resources."
  type        = string
  default     = "media-assets-rg"
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "East US"
}

variable "container_name" {
  description = "Blob container for incoming assets."
  type        = string
  default     = "game-assets"
}

variable "account_tier" {
  description = "Storage account performance tier (Standard or Premium)."
  type        = string
  default     = "Standard"
}

variable "replication_type" {
  description = "Storage account replication strategy (e.g., GRS, LRS)."
  type        = string
  default     = "GRS"
}

variable "allowed_ip_rules" {
  description = "Optional list of public IP addresses permitted to access the storage account."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
