# Azure Services Setup Guide - Step by Step
**Author:** Aditya Padhi

This guide will walk you through creating all necessary Azure services for your DE Log Processing & ML Pipeline deployment.

---

## Prerequisites

**Azure Account:** You have a fresh Azure account  
**Subscription:** Active Azure subscription  
**Permissions:** Owner or Contributor access  

---

## Step 1: Create Resource Group

**Purpose:** Organize all your resources in one place

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource" (plus icon)
   - Search for "Resource group"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group Name: de-log-processing-rg
   Region: East US
   ```

3. **Click "Review + create" → "Create"**

---

## Step 2: Create Storage Account (ADLS Gen2)

**Purpose:** Data lake storage for Bronze/Silver/Gold layers

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Storage account"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Storage Account Name: delogprocessingdatalake[random4digits]
   Region: East US
   Performance: Standard
   Redundancy: LRS (Locally-redundant storage)
   ```

3. **IMPORTANT - Enable ADLS Gen2:**
   - Go to "Advanced" tab
   - Check "Enable hierarchical namespace"
   - This converts it to ADLS Gen2

4. **Click "Review + create" → "Create"**

### After Creation:
1. Go to your storage account
2. Create containers:
   - `bronze`
   - `silver` 
   - `gold`
   - `models`

---

## Step 3: Create Databricks Workspace

**Purpose:** Run PySpark ETL and ML scripts

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Azure Databricks"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Workspace Name: de-log-processing-databricks
   Region: East US
   Pricing Tier: Standard
   ```

3. **Click "Review + create" → "Create"**

### After Creation:
1. Click "Launch Workspace"
2. Create a cluster:
   ```
   Cluster Name: de-log-processing-cluster
   Runtime: 13.3.x-scala2.12
   Node Type: Standard_DS3_v2
   Driver Type: Standard_DS3_v2
   Min Workers: 1
   Max Workers: 3
   Auto Termination: 30 minutes
   ```

---

## Step 4: Create Azure Kubernetes Service (AKS)

**Purpose:** Deploy API services and MLflow server

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Kubernetes service"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Cluster Name: de-log-processing-aks
   Region: East US
   Kubernetes Version: 1.28
   Node Count: 2
   Node Size: Standard_D2s_v3
   ```

3. **Click "Review + create" → "Create"**

---

## Step 5: Create Azure Data Factory

**Purpose:** Orchestrate ETL pipeline execution

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Data Factory"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Name: de-log-processing-adf
   Region: East US
   Version: V2
   ```

3. **Click "Review + create" → "Create"**

---

## Step 6: Create Container Registry

**Purpose:** Store Docker images for AKS

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Container Registry"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Registry Name: delogprocessingacr[random4digits]
   Region: East US
   SKU: Basic
   Admin User: Enable
   ```

3. **Click "Review + create" → "Create"**

---

## Step 7: Create Key Vault

**Purpose:** Store secrets and connection strings

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Key Vault"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Vault Name: de-log-processing-kv[random4digits]
   Region: East US
   Pricing Tier: Standard
   ```

3. **Click "Review + create" → "Create"**

---

## Step 8: Create Application Insights

**Purpose:** Monitor application performance

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Application Insights"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Name: de-log-processing-insights
   Region: East US
   Application Type: Web
   ```

3. **Click "Review + create" → "Create"**

---

## Step 9: Create Log Analytics Workspace

**Purpose:** Centralized logging

### Steps:
1. **In Azure Portal:**
   - Click "Create a resource"
   - Search for "Log Analytics workspace"
   - Click "Create"

2. **Configuration:**
   ```
   Resource Group: de-log-processing-rg
   Name: de-log-processing-logs
   Region: East US
   Pricing Tier: Pay-as-you-go
   ```

3. **Click "Review + create" → "Create"**

---

## Step 10: Configure Permissions

### Databricks → Storage Account:
1. Go to Storage Account → Access Control (IAM)
2. Add role assignment:
   ```
   Role: Storage Blob Data Contributor
   Assign access to: Managed Identity
   Select: Databricks workspace
   ```

### AKS → Storage Account:
1. Go to Storage Account → Access Control (IAM)
2. Add role assignment:
   ```
   Role: Storage Blob Data Contributor
   Assign access to: Managed Identity
   Select: AKS cluster
   ```

---

## Step 11: Get Connection Information

### Databricks:
1. Go to Databricks workspace
2. Click user icon → User Settings
3. Go to "Access tokens" → Generate new token
4. **Save this token - you'll need it for GitHub Actions**

### Storage Account:
1. Go to Storage Account → Access keys
2. Copy "Connection string" (you'll need this)

### AKS:
1. Go to AKS cluster → Connect
2. Copy the kubectl command

---

## Step 12: Upload Source Data

### Upload OpenSSH_2k.log:
1. Go to Storage Account → Containers → bronze
2. Click "Upload" → Select your `logs/OpenSSH_2k.log` file
3. Upload to path: `raw_logs/OpenSSH_2k.log`

---

## Step 13: Configure GitHub Secrets

### In your GitHub repository:
1. Go to Settings → Secrets and variables → Actions
2. Add these secrets:

```
AZURE_CREDENTIALS: [Service Principal JSON]
DATABRICKS_TOKEN: [Your Databricks token]
STORAGE_ACCOUNT_NAME: [Your storage account name]
CONTAINER_REGISTRY: [Your ACR name]
```

### Create Service Principal:
```bash
az ad sp create-for-rbac --name "de-log-processing-sp" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

---

## Step 14: Deploy Infrastructure

### Option 1: Using Terraform (Recommended)
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

### Option 2: Using GitHub Actions
1. Push code to main branch
2. GitHub Actions will automatically deploy

---

## Step 15: Verify Deployment

### Check all services are running:
1. **Resource Group:** All 9 services should be present
2. **Storage Account:** Containers created
3. **Databricks:** Workspace accessible
4. **AKS:** Cluster running
5. **Data Factory:** Service available

---

## Troubleshooting

### Common Issues:

1. **Storage Account Name Conflict:**
   - Add random numbers: `delogprocessingdatalake1234`

2. **Databricks Launch Issues:**
   - Wait 5-10 minutes after creation
   - Check if workspace is fully provisioned

3. **AKS Cluster Issues:**
   - Ensure you have sufficient quota
   - Try different region if needed

4. **Permission Errors:**
   - Check IAM assignments
   - Ensure you're Owner/Contributor

---

## Cost Optimization Tips

1. **Stop AKS when not in use:**
   ```bash
   az aks stop --name de-log-processing-aks --resource-group de-log-processing-rg
   ```

2. **Use Spot Instances for AKS:**
   - Configure spot node pools

3. **Set up Budget Alerts:**
   - Go to Cost Management → Budgets
   - Set monthly budget limit

---

## Next Steps After Setup

1. **Deploy Pipeline Code:**
   - Upload notebooks to Databricks
   - Deploy services to AKS

2. **Configure Data Factory:**
   - Create pipeline
   - Set up triggers

3. **Monitor Pipeline:**
   - Check Application Insights
   - Monitor costs

---

**Estimated Total Setup Time:** 30-45 minutes  
**Estimated Monthly Cost:** $450-900  
**Author:** Aditya Padhi

---

## Quick Reference Commands

```bash
# List all resources
az resource list --resource-group de-log-processing-rg --output table

# Get AKS credentials
az aks get-credentials --resource-group de-log-processing-rg --name de-log-processing-aks

# Check storage account
az storage account show --name delogprocessingdatalake --resource-group de-log-processing-rg

# List Databricks workspaces
az databricks workspace list --resource-group de-log-processing-rg
```
