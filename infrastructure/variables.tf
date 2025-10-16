# Terraform variables for Azure deployment
# Author: Aditya Padhi

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "Production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "DE-Log-Processing"
}

variable "author" {
  description = "Author name"
  type        = string
  default     = "Aditya Padhi"
}

variable "aks_node_count" {
  description = "Number of nodes in AKS cluster"
  type        = number
  default     = 2
}

variable "aks_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "databricks_sku" {
  description = "Databricks SKU"
  type        = string
  default     = "standard"
}

variable "storage_account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
}

variable "storage_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
}

variable "acr_sku" {
  description = "Container Registry SKU"
  type        = string
  default     = "Basic"
}

variable "key_vault_sku" {
  description = "Key Vault SKU"
  type        = string
  default     = "standard"
}

variable "log_analytics_sku" {
  description = "Log Analytics SKU"
  type        = string
  default     = "PerGB2018"
}

variable "log_retention_days" {
  description = "Log retention days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
    ManagedBy   = "Terraform"
  }
}
