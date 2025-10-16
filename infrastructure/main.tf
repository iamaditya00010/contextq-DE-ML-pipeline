# Configure the Azure Provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
  backend "azurerm" {
    resource_group_name  = "de-log-processing-tfstate-rg"
    storage_account_name = "delogprocessingtfstate"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# Data sources
data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "de-log-processing-rg"
  location = "East US"
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Storage Account for ADLS Gen2
resource "azurerm_storage_account" "datalake" {
  name                     = "delogprocessingdatalake${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Random string for unique naming
resource "random_string" "suffix" {
  length  = 4
  special = false
  upper   = false
}

# ADLS Gen2 File Systems
resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gold" {
  name               = "gold"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "models" {
  name               = "models"
  storage_account_id = azurerm_storage_account.datalake.id
}

# Databricks Workspace
resource "azurerm_databricks_workspace" "main" {
  name                = "de-log-processing-databricks-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "standard"
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Data Factory
resource "azurerm_data_factory" "main" {
  name                = "de-log-processing-adf-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "de-log-processing-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Subnet for AKS
resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = "de-log-processing-aks-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "delogprocessing"
  kubernetes_version  = "1.28"
  
  default_node_pool {
    name                = "default"
    node_count          = 2
    vm_size             = "Standard_D2s_v3"
    vnet_subnet_id      = azurerm_subnet.aks.id
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 5
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  network_profile {
    network_plugin = "azure"
    service_cidr   = "10.1.0.0/16"
    dns_service_ip = "10.1.0.10"
  }
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "delogprocessingacr${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "de-log-processing-kv-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    
    key_permissions = [
      "Get", "List", "Create", "Delete", "Update"
    ]
    
    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Purge"
    ]
  }
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "de-log-processing-insights-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "de-log-processing-logs-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days  = 30
  
  tags = {
    Environment = "Production"
    Project     = "DE-Log-Processing"
    Author      = "Aditya Padhi"
  }
}

# Role assignments for AKS to access storage
resource "azurerm_role_assignment" "aks_storage" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_kubernetes_cluster.main.identity[0].principal_id
}

# Role assignments for Databricks to access storage
resource "azurerm_role_assignment" "databricks_storage" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_workspace.main.managed_resource_group_id
}

# Outputs
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.main.workspace_url
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "container_registry_name" {
  value = azurerm_container_registry.main.name
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "application_insights_key" {
  value = azurerm_application_insights.main.instrumentation_key
}

output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.main.workspace_id
}
