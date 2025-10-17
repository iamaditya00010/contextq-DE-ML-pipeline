# Pipeline Execution Workflow (No Terraform)
**Author:** Aditya Padhi

This workflow executes the DE Log Processing & ML Pipeline directly on existing Azure infrastructure, skipping Terraform deployment.

## Overview

This workflow is designed for scenarios where:
- Azure infrastructure is already created
- You want to execute the pipeline without infrastructure changes
- You need faster deployment cycles
- You want to test pipeline execution independently

## Prerequisites

### Existing Azure Resources
The following resources must already exist in your Azure subscription:
- **Resource Group:** `de-log-processing-rg`
- **Storage Account:** `delogprocessingdatalake`
- **Databricks Workspace:** `de-log-processing-databricks`
- **AKS Cluster:** `de-log-processing-aks`
- **Container Registry:** `delogprocessingacr`
- **Key Vault:** `de-log-processing-kv`

### GitHub Secrets Required
Configure these secrets in your GitHub repository:
- `AZURE_CREDENTIALS` - Service Principal credentials
- `STORAGE_ACCOUNT_KEY` - Storage account access key
- `DATABRICKS_TOKEN` - Databricks access token

## Workflow Jobs

### 1. lint-and-validate
- Code linting with flake8
- Python structure validation
- Dependency installation

### 2. upload-source-data
- Creates Azure Storage containers (bronze, silver, gold)
- Uploads source log file (`logs/OpenSSH_2k.log`) to bronze container
- Uses existing storage account

### 3. deploy-databricks-pipeline
- Creates Databricks workspace directories
- Uploads PySpark scripts to Databricks
- Sets up notebook structure

### 4. deploy-aks-services
- Gets AKS cluster credentials
- Deploys MLflow and API services to AKS
- Waits for services to be ready

### 5. execute-pipeline
- **Bronze Layer:** Raw data processing
- **Silver Layer:** Data transformation
- **Gold Layer:** Final data processing
- **ML Pipeline:** Anomaly detection

### 6. validate-pipeline-execution
- Validates pipeline outputs in Azure Storage
- Checks AKS service status
- Confirms data processing completion

### 7. test-pipeline
- Runs comprehensive pytest tests
- Generates code coverage reports
- Validates pipeline functionality

## Usage

### Automatic Execution
The workflow runs automatically on:
- Push to `main` branch
- Pull requests to `main` branch

### Manual Execution
You can trigger the workflow manually:
1. Go to GitHub Actions tab
2. Select "Pipeline Execution (No Terraform)"
3. Click "Run workflow"

## Environment Variables

The workflow uses these environment variables:
```yaml
AZURE_RESOURCE_GROUP: "de-log-processing-rg"
STORAGE_ACCOUNT_NAME: "delogprocessingdatalake"
DATABRICKS_WORKSPACE: "de-log-processing-databricks"
AKS_CLUSTER_NAME: "de-log-processing-aks"
CONTAINER_REGISTRY: "delogprocessingacr"
KEY_VAULT_NAME: "de-log-processing-kv"
```

## Databricks Job Configuration

Each pipeline layer runs as a separate Databricks job with:
- **Spark Version:** 13.3.x-scala2.12
- **Node Type:** Standard_DS3_v2
- **Workers:** 2 nodes
- **Auto-termination:** Enabled

## Expected Outputs

After successful execution, you'll have:
- **Bronze Layer:** Raw log data in Parquet format
- **Silver Layer:** Structured data in JSON format
- **Gold Layer:** Final processed data in CSV format
- **ML Output:** Anomaly detection results and model artifacts

## Monitoring

### GitHub Actions
Monitor execution progress in the GitHub Actions tab:
- Real-time logs for each job
- Success/failure status
- Execution duration

### Azure Portal
Check resource status in Azure Portal:
- Storage account containers and blobs
- Databricks workspace notebooks
- AKS cluster pods and services

### Databricks UI
Access Databricks workspace to:
- View job execution logs
- Monitor Spark job progress
- Debug any issues

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify GitHub secrets are correctly configured
   - Check Service Principal permissions
   - Ensure Databricks token is valid

2. **Resource Not Found**
   - Confirm all Azure resources exist
   - Check resource names match environment variables
   - Verify resource group and subscription

3. **Databricks Job Failures**
   - Check Spark cluster configuration
   - Review notebook syntax
   - Monitor cluster resource usage

4. **AKS Deployment Issues**
   - Verify cluster credentials
   - Check Kubernetes manifests
   - Monitor pod status

### Debug Steps

1. **Check GitHub Actions Logs**
   - Review detailed execution logs
   - Look for error messages
   - Check environment variable values

2. **Verify Azure Resources**
   - Confirm resources exist in Azure Portal
   - Check resource status and health
   - Verify access permissions

3. **Test Databricks Connectivity**
   - Use Databricks CLI to test connection
   - Verify workspace access
   - Check notebook uploads

## Benefits

### Speed
- No Terraform deployment time
- Direct pipeline execution
- Faster iteration cycles

### Simplicity
- Fewer moving parts
- Direct resource usage
- Easier debugging

### Flexibility
- Independent of infrastructure changes
- Focus on data processing
- Easy testing and validation

## Comparison with Terraform Workflow

| Aspect | Pipeline Execution | Terraform Workflow |
|--------|-------------------|-------------------|
| **Speed** | Fast (5-15 minutes) | Slow (15-35 minutes) |
| **Complexity** | Simple | Complex |
| **Infrastructure** | Uses existing | Creates new |
| **Use Case** | Pipeline testing | Full deployment |
| **Dependencies** | Minimal | Many |

## Next Steps

After successful pipeline execution:
1. Review pipeline outputs
2. Analyze ML model performance
3. Optimize pipeline performance
4. Schedule regular executions
5. Monitor data quality metrics

---

**Last Updated:** October 16, 2025  
**Author:** Aditya Padhi  
**Version:** 1.0
