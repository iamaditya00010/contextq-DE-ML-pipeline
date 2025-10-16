# Terraform outputs for Azure deployment
# Author: Aditya Padhi

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.datalake.name
}

output "storage_account_primary_dfs_endpoint" {
  description = "Primary DFS endpoint of the storage account"
  value       = azurerm_storage_account.datalake.primary_dfs_endpoint
}

output "databricks_workspace_name" {
  description = "Name of the Databricks workspace"
  value       = azurerm_databricks_workspace.main.name
}

output "databricks_workspace_url" {
  description = "URL of the Databricks workspace"
  value       = azurerm_databricks_workspace.main.workspace_url
}

output "data_factory_name" {
  description = "Name of the Data Factory"
  value       = azurerm_data_factory.main.name
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.name
}

output "aks_cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.fqdn
}

output "aks_cluster_kube_config" {
  description = "Kube config for the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "container_registry_name" {
  description = "Name of the Container Registry"
  value       = azurerm_container_registry.main.name
}

output "container_registry_login_server" {
  description = "Login server of the Container Registry"
  value       = azurerm_container_registry.main.login_server
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "application_insights_name" {
  description = "Name of the Application Insights"
  value       = azurerm_application_insights.main.name
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key of Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.name
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.workspace_id
}

output "virtual_network_name" {
  description = "Name of the virtual network"
  value       = azurerm_virtual_network.main.name
}

output "virtual_network_address_space" {
  description = "Address space of the virtual network"
  value       = azurerm_virtual_network.main.address_space
}

output "aks_subnet_id" {
  description = "ID of the AKS subnet"
  value       = azurerm_subnet.aks.id
}

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    resource_group     = azurerm_resource_group.main.name
    storage_account    = azurerm_storage_account.datalake.name
    databricks_workspace = azurerm_databricks_workspace.main.name
    data_factory      = azurerm_data_factory.main.name
    aks_cluster       = azurerm_kubernetes_cluster.main.name
    container_registry = azurerm_container_registry.main.name
    key_vault         = azurerm_key_vault.main.name
    application_insights = azurerm_application_insights.main.name
    log_analytics     = azurerm_log_analytics_workspace.main.name
  }
}
