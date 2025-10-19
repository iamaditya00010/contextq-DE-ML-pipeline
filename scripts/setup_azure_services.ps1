# Azure Services Setup Script
# Author: Aditya Padhi
# Description: Automated setup script for Azure services

# Login to Azure (run this first)
# az login

# Set variables
$resourceGroupName = "de-log-processing-rg"
$location = "East US"
$storageAccountName = "delogprocessingdatalake" + (Get-Random -Minimum 1000 -Maximum 9999)
$databricksName = "de-log-processing-databricks"
$aksName = "de-log-processing-aks"
$dataFactoryName = "de-log-processing-adf"
$acrName = "delogprocessingacr" + (Get-Random -Minimum 1000 -Maximum 9999)
$keyVaultName = "de-log-processing-kv" + (Get-Random -Minimum 1000 -Maximum 9999)
$appInsightsName = "de-log-processing-insights"
$logAnalyticsName = "de-log-processing-logs"

Write-Host "Creating Azure services for DE Log Processing Pipeline..." -ForegroundColor Green
Write-Host "Resource Group: $resourceGroupName" -ForegroundColor Yellow
Write-Host "Location: $location" -ForegroundColor Yellow

# 1. Create Resource Group
Write-Host "`n1. Creating Resource Group..." -ForegroundColor Cyan
az group create --name $resourceGroupName --location $location

# 2. Create Storage Account with ADLS Gen2
Write-Host "`n2. Creating Storage Account with ADLS Gen2..." -ForegroundColor Cyan
az storage account create `
    --name $storageAccountName `
    --resource-group $resourceGroupName `
    --location $location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --enable-hierarchical-namespace true

# Create containers
Write-Host "Creating containers..." -ForegroundColor Yellow
az storage container create --name "bronze" --account-name $storageAccountName
az storage container create --name "silver" --account-name $storageAccountName
az storage container create --name "gold" --account-name $storageAccountName
az storage container create --name "models" --account-name $storageAccountName

# 3. Create Databricks Workspace
Write-Host "`n3. Creating Databricks Workspace..." -ForegroundColor Cyan
az databricks workspace create `
    --name $databricksName `
    --resource-group $resourceGroupName `
    --location $location `
    --sku standard

# 4. Create AKS Cluster
Write-Host "`n4. Creating AKS Cluster..." -ForegroundColor Cyan
az aks create `
    --name $aksName `
    --resource-group $resourceGroupName `
    --location $location `
    --node-count 2 `
    --node-vm-size Standard_D2s_v3 `
    --generate-ssh-keys

# 5. Create Data Factory
Write-Host "`n5. Creating Data Factory..." -ForegroundColor Cyan
az datafactory create `
    --name $dataFactoryName `
    --resource-group $resourceGroupName `
    --location $location

# 6. Create Container Registry
Write-Host "`n6. Creating Container Registry..." -ForegroundColor Cyan
az acr create `
    --name $acrName `
    --resource-group $resourceGroupName `
    --location $location `
    --sku Basic `
    --admin-enabled true

# 7. Create Key Vault
Write-Host "`n7. Creating Key Vault..." -ForegroundColor Cyan
az keyvault create `
    --name $keyVaultName `
    --resource-group $resourceGroupName `
    --location $location `
    --sku standard

# 8. Create Application Insights
Write-Host "`n8. Creating Application Insights..." -ForegroundColor Cyan
az monitor app-insights component create `
    --app $appInsightsName `
    --location $location `
    --resource-group $resourceGroupName

# 9. Create Log Analytics Workspace
Write-Host "`n9. Creating Log Analytics Workspace..." -ForegroundColor Cyan
az monitor log-analytics workspace create `
    --resource-group $resourceGroupName `
    --workspace-name $logAnalyticsName `
    --location $location

Write-Host "`nAll Azure services created successfully!" -ForegroundColor Green

# Display created resources
Write-Host "`n📋 Created Resources:" -ForegroundColor Yellow
Write-Host "Resource Group: $resourceGroupName"
Write-Host "Storage Account: $storageAccountName"
Write-Host "Databricks: $databricksName"
Write-Host "AKS: $aksName"
Write-Host "Data Factory: $dataFactoryName"
Write-Host "Container Registry: $acrName"
Write-Host "Key Vault: $keyVaultName"
Write-Host "Application Insights: $appInsightsName"
Write-Host "Log Analytics: $logAnalyticsName"

# Get connection information
Write-Host "`n🔗 Connection Information:" -ForegroundColor Yellow

# Get Databricks workspace URL
$databricksUrl = az databricks workspace show --name $databricksName --resource-group $resourceGroupName --query "workspaceUrl" -o tsv
Write-Host "Databricks URL: $databricksUrl"

# Get AKS credentials
Write-Host "`nGetting AKS credentials..."
az aks get-credentials --name $aksName --resource-group $resourceGroupName

# Get storage account connection string
$storageConnectionString = az storage account show-connection-string --name $storageAccountName --resource-group $resourceGroupName --query "connectionString" -o tsv
Write-Host "Storage Connection String: $storageConnectionString"

Write-Host "`n📝 Next Steps:" -ForegroundColor Green
Write-Host "1. Go to Databricks workspace and create access token"
Write-Host "2. Upload source data to storage account"
Write-Host "3. Configure GitHub secrets"
Write-Host "4. Deploy pipeline code"

Write-Host "`n🎉 Setup Complete! Your Azure infrastructure is ready." -ForegroundColor Green
