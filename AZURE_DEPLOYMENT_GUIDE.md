# Azure Deployment Guide - DE Log Processing & ML Pipeline

**Author:** Aditya Padhi

This guide provides step-by-step instructions for deploying the DE Log Processing & ML Pipeline to Azure using Databricks, ADLS Gen2, AKS, and MLflow.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Azure Databricks Configuration](#azure-databricks-configuration)
5. [ADLS Gen2 Setup](#adls-gen2-setup)
6. [MLflow Integration](#mlflow-integration)
7. [AKS Services](#aks-services)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Deployment Steps](#deployment-steps)
10. [Monitoring & Validation](#monitoring--validation)

---

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │    │  Azure Data     │    │  Azure MLflow   │
│   (Source Code) │───▶│  Factory        │───▶│  (Model Registry)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ADLS Gen2     │◀───│ Azure Databricks│───▶│   AKS Cluster   │
│   (Data Lake)   │    │  (PySpark/ML)   │    │  (Services)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components:
- **Azure Databricks**: PySpark ETL and ML pipeline execution
- **ADLS Gen2**: Data lake storage (Bronze/Silver/Gold layers)
- **Azure Data Factory**: Orchestration and scheduling
- **MLflow**: Model tracking and registration
- **AKS**: Additional services and APIs
- **GitHub Actions**: CI/CD pipeline

---

## Prerequisites

### Azure Account Setup
1. **Azure Subscription** with appropriate permissions
2. **Azure CLI** installed and configured
3. **Terraform** (for Infrastructure as Code)
4. **GitHub Account** with repository access

### Required Azure Services
- Azure Databricks
- Azure Data Lake Storage Gen2
- Azure Data Factory
- Azure Kubernetes Service (AKS)
- Azure Container Registry (ACR)
- Azure Key Vault
- Azure Monitor

---

## Infrastructure Setup

### 1. Terraform Configuration

Create `infrastructure/main.tf`:

```hcl
# Configure the Azure Provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "de-log-processing-rg"
  location = "East US"
}

# Storage Account for ADLS Gen2
resource "azurerm_storage_account" "datalake" {
  name                     = "delogprocessingdatalake"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
}

# ADLS Gen2 File System
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
  name                = "de-log-processing-databricks"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "standard"
}

# Data Factory
resource "azurerm_data_factory" "main" {
  name                = "de-log-processing-adf"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = "de-log-processing-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "delogprocessing"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2s_v3"
  }

  identity {
    type = "SystemAssigned"
  }
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "delogprocessingacr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "de-log-processing-kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
}

data "azurerm_client_config" "current" {}
```

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
cd infrastructure
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply
```

---

## Azure Databricks Configuration

### 1. Databricks Workspace Setup

1. **Access Databricks Workspace**:
   - Navigate to Azure Portal → Databricks workspace
   - Click "Launch Workspace"

2. **Create Cluster**:
   ```json
   {
     "cluster_name": "de-log-processing-cluster",
     "spark_version": "13.3.x-scala2.12",
     "node_type_id": "Standard_DS3_v2",
     "driver_node_type_id": "Standard_DS3_v2",
     "num_workers": 2,
     "autotermination_minutes": 30,
     "spark_conf": {
       "spark.sql.adaptive.enabled": "true",
       "spark.sql.adaptive.coalescePartitions.enabled": "true"
     }
   }
   ```

3. **Install Libraries**:
   - PySpark (included)
   - MLflow
   - Azure Storage libraries

### 2. Mount ADLS Gen2

Create `databricks/mount_adls.py`:

```python
# Mount ADLS Gen2 to Databricks
def mount_adls_gen2():
    configs = {
        "fs.azure.account.auth.type": "OAuth",
        "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.MsiTokenProvider",
        "fs.azure.account.oauth2.client.id": "<client-id>",
        "fs.azure.account.oauth2.credential": "<credential>",
        "fs.azure.account.oauth2.msi.tenant": "<tenant-id>",
        "fs.azure.account.oauth2.msi.endpoint": "https://login.microsoftonline.com/<tenant-id>/oauth2/token"
    }
    
    # Mount bronze layer
    dbutils.fs.mount(
        source = "abfss://bronze@delogprocessingdatalake.dfs.core.windows.net/",
        mount_point = "/mnt/bronze",
        extra_configs = configs
    )
    
    # Mount silver layer
    dbutils.fs.mount(
        source = "abfss://silver@delogprocessingdatalake.dfs.core.windows.net/",
        mount_point = "/mnt/silver",
        extra_configs = configs
    )
    
    # Mount gold layer
    dbutils.fs.mount(
        source = "abfss://gold@delogprocessingdatalake.dfs.core.windows.net/",
        mount_point = "/mnt/gold",
        extra_configs = configs
    )
    
    # Mount models
    dbutils.fs.mount(
        source = "abfss://models@delogprocessingdatalake.dfs.core.windows.net/",
        mount_point = "/mnt/models",
        extra_configs = configs
    )

mount_adls_gen2()
```

---

## ADLS Gen2 Setup

### 1. Upload Source Data

```bash
# Upload source log file to ADLS Gen2
az storage blob upload \
  --account-name delogprocessingdatalake \
  --container-name bronze \
  --file logs/OpenSSH_2k.log \
  --name raw_logs/OpenSSH_2k.log
```

### 2. Directory Structure

```
bronze/
├── raw_logs/
│   └── OpenSSH_2k.log
└── processed/
    └── raw_logs.parquet

silver/
├── structured_logs/
│   └── structured_logs.json
└── quality_reports/

gold/
├── final_data/
│   └── openssh_logs_final.csv
└── business_reports/

models/
├── anomaly_model.pkl
├── label_encoders.pkl
└── mlflow_artifacts/
```

---

## MLflow Integration

### 1. MLflow Server Setup

Create `mlflow/mlflow_server.py`:

```python
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

# Configure MLflow
mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("ssh-anomaly-detection")

def log_model_to_mlflow(model, model_name, metrics, features):
    """Log model to MLflow registry"""
    
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("algorithm", "IsolationForest")
        mlflow.log_param("features", features)
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Log model
        mlflow.sklearn.log_model(
            model, 
            "model",
            registered_model_name=model_name
        )
        
        # Log artifacts
        mlflow.log_artifacts("data/ml_output/", "ml_output")
        
        print(f"Model {model_name} logged to MLflow")

def register_model_version(model_name, stage="Production"):
    """Register model version"""
    client = MlflowClient()
    
    # Get latest version
    latest_version = client.get_latest_versions(model_name)[0]
    
    # Transition to stage
    client.transition_model_version_stage(
        name=model_name,
        version=latest_version.version,
        stage=stage
    )
    
    print(f"Model {model_name} version {latest_version.version} moved to {stage}")
```

### 2. Deploy MLflow Server to AKS

Create `kubernetes/mlflow-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlflow-server
  template:
    metadata:
      labels:
        app: mlflow-server
    spec:
      containers:
      - name: mlflow-server
        image: python:3.9-slim
        command: ["mlflow", "server"]
        args: ["--host", "0.0.0.0", "--port", "5000"]
        ports:
        - containerPort: 5000
        env:
        - name: MLFLOW_BACKEND_STORE_URI
          value: "sqlite:///mlflow.db"
        - name: MLFLOW_DEFAULT_ARTIFACT_ROOT
          value: "/mlflow/artifacts"
        volumeMounts:
        - name: mlflow-storage
          mountPath: /mlflow
      volumes:
      - name: mlflow-storage
        persistentVolumeClaim:
          claimName: mlflow-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-service
spec:
  selector:
    app: mlflow-server
  ports:
  - port: 5000
    targetPort: 5000
  type: LoadBalancer
```

---

## AKS Services

### 1. Deploy Services to AKS

Create `kubernetes/services-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pipeline-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pipeline-api
  template:
    metadata:
      labels:
        app: pipeline-api
    spec:
      containers:
      - name: pipeline-api
        image: delogprocessingacr.azurecr.io/pipeline-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABRICKS_URL
          value: "https://de-log-processing-databricks.azuredatabricks.net"
        - name: MLFLOW_URL
          value: "http://mlflow-service:5000"
---
apiVersion: v1
kind: Service
metadata:
  name: pipeline-api-service
spec:
  selector:
    app: pipeline-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 2. Build and Push Container Images

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "api/main.py"]
```

Build and push:

```bash
# Build image
docker build -t delogprocessingacr.azurecr.io/pipeline-api:latest .

# Push to ACR
az acr login --name delogprocessingacr
docker push delogprocessingacr.azurecr.io/pipeline-api:latest
```

---

## CI/CD Pipeline

### 1. GitHub Actions Workflow

Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Azure Deployment Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        python -m pytest tests/test_pipeline.py --cov=scripts --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  deploy-infrastructure:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy Infrastructure
      run: |
        cd infrastructure
        terraform init
        terraform plan
        terraform apply -auto-approve

  deploy-databricks:
    needs: deploy-infrastructure
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Databricks
      uses: databricks/upload-dbfs@v1
      with:
        host: ${{ secrets.DATABRICKS_HOST }}
        token: ${{ secrets.DATABRICKS_TOKEN }}
        local-path: scripts/
        dbfs-path: /FileStore/de-log-processing/

  deploy-aks:
    needs: deploy-databricks
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Build and Push Container
      run: |
        az acr login --name delogprocessingacr
        docker build -t delogprocessingacr.azurecr.io/pipeline-api:${{ github.sha }} .
        docker push delogprocessingacr.azurecr.io/pipeline-api:${{ github.sha }}
    
    - name: Deploy to AKS
      run: |
        az aks get-credentials --resource-group de-log-processing-rg --name de-log-processing-aks
        kubectl apply -f kubernetes/
```

### 2. Azure Data Factory Pipeline

Create `adf/pipeline.json`:

```json
{
  "name": "DE_Log_Processing_Pipeline",
  "properties": {
    "activities": [
      {
        "name": "Bronze_Layer_Processing",
        "type": "DatabricksNotebook",
        "dependsOn": [],
        "policy": {
          "timeout": "7.00:00:00",
          "retry": 0,
          "retryIntervalInSeconds": 30,
          "secureOutput": false,
          "secureInput": false
        },
        "userProperties": [],
        "typeProperties": {
          "notebookPath": "/FileStore/de-log-processing/bronze/raw_load"
        },
        "linkedServiceName": {
          "referenceName": "AzureDatabricks1",
          "type": "LinkedServiceReference"
        }
      },
      {
        "name": "Silver_Layer_Processing",
        "type": "DatabricksNotebook",
        "dependsOn": [
          {
            "activity": "Bronze_Layer_Processing",
            "dependencyConditions": [
              "Succeeded"
            ]
          }
        ],
        "policy": {
          "timeout": "7.00:00:00",
          "retry": 0,
          "retryIntervalInSeconds": 30,
          "secureOutput": false,
          "secureInput": false
        },
        "userProperties": [],
        "typeProperties": {
          "notebookPath": "/FileStore/de-log-processing/silver/silver_load"
        },
        "linkedServiceName": {
          "referenceName": "AzureDatabricks1",
          "type": "LinkedServiceReference"
        }
      },
      {
        "name": "Gold_Layer_Processing",
        "type": "DatabricksNotebook",
        "dependsOn": [
          {
            "activity": "Silver_Layer_Processing",
            "dependencyConditions": [
              "Succeeded"
            ]
          }
        ],
        "policy": {
          "timeout": "7.00:00:00",
          "retry": 0,
          "retryIntervalInSeconds": 30,
          "secureOutput": false,
          "secureInput": false
        },
        "userProperties": [],
        "typeProperties": {
          "notebookPath": "/FileStore/de-log-processing/gold/gold_load"
        },
        "linkedServiceName": {
          "referenceName": "AzureDatabricks1",
          "type": "LinkedServiceReference"
        }
      },
      {
        "name": "ML_Model_Training",
        "type": "DatabricksNotebook",
        "dependsOn": [
          {
            "activity": "Gold_Layer_Processing",
            "dependencyConditions": [
              "Succeeded"
            ]
          }
        ],
        "policy": {
          "timeout": "7.00:00:00",
          "retry": 0,
          "retryIntervalInSeconds": 30,
          "secureOutput": false,
          "secureInput": false
        },
        "userProperties": [],
        "typeProperties": {
          "notebookPath": "/FileStore/de-log-processing/ml_anomaly_detection"
        },
        "linkedServiceName": {
          "referenceName": "AzureDatabricks1",
          "type": "LinkedServiceReference"
        }
      }
    ],
    "folder": {
      "name": "DE_Log_Processing"
    }
  }
}
```

---

## Deployment Steps

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/iamaditya00010/contextq-DE-ML-pipeline.git
cd contextq-DE-ML-pipeline

# Set up Azure CLI
az login
az account set --subscription "your-subscription-id"

# Create service principal
az ad sp create-for-rbac --name "de-log-processing-sp" \
  --role contributor \
  --scopes /subscriptions/your-subscription-id \
  --sdk-auth
```

### 2. Deploy Infrastructure

```bash
# Deploy with Terraform
cd infrastructure
terraform init
terraform plan
terraform apply

# Note down outputs:
# - Databricks workspace URL
# - Storage account name
# - AKS cluster name
```

### 3. Configure Databricks

```bash
# Get Databricks token
# Go to Databricks workspace → User Settings → Access Tokens → Generate New Token

# Upload notebooks
databricks workspace import scripts/bronze/raw_load.py /FileStore/de-log-processing/bronze/raw_load --language PYTHON
databricks workspace import scripts/silver/silver_load.py /FileStore/de-log-processing/silver/silver_load --language PYTHON
databricks workspace import scripts/gold/gold_load.py /FileStore/de-log-processing/gold/gold_load --language PYTHON
databricks workspace import scripts/ml_anomaly_detection.py /FileStore/de-log-processing/ml_anomaly_detection --language PYTHON
```

### 4. Deploy AKS Services

```bash
# Get AKS credentials
az aks get-credentials --resource-group de-log-processing-rg --name de-log-processing-aks

# Deploy MLflow server
kubectl apply -f kubernetes/mlflow-deployment.yaml

# Deploy pipeline API
kubectl apply -f kubernetes/services-deployment.yaml
```

### 5. Configure Data Factory

```bash
# Import Data Factory pipeline
az datafactory pipeline create \
  --resource-group de-log-processing-rg \
  --factory-name de-log-processing-adf \
  --name DE_Log_Processing_Pipeline \
  --pipeline adf/pipeline.json
```

---

## Monitoring & Validation

### 1. Monitor Pipeline Execution

- **Azure Data Factory**: Monitor pipeline runs in ADF portal
- **Databricks**: Check job execution in Databricks workspace
- **MLflow**: View model metrics and artifacts
- **AKS**: Monitor service health with kubectl

### 2. Validate Data Quality

```python
# Data quality validation script
def validate_pipeline_output():
    # Check Bronze layer
    bronze_df = spark.read.parquet("/mnt/bronze/processed/raw_logs.parquet")
    assert bronze_df.count() > 0, "Bronze layer is empty"
    
    # Check Silver layer
    silver_df = spark.read.json("/mnt/silver/structured_logs/structured_logs.json")
    assert silver_df.count() > 0, "Silver layer is empty"
    
    # Check Gold layer
    gold_df = spark.read.csv("/mnt/gold/final_data/openssh_logs_final.csv", header=True)
    assert gold_df.count() > 0, "Gold layer is empty"
    
    print("All data layers validated successfully!")
```

### 3. Model Performance Monitoring

```python
# Model monitoring script
def monitor_model_performance():
    client = MlflowClient()
    
    # Get latest model
    latest_model = client.get_latest_versions("ssh-anomaly-model")[0]
    
    # Load model
    model = mlflow.sklearn.load_model(f"models:/ssh-anomaly-model/{latest_model.version}")
    
    # Test on new data
    test_data = spark.read.csv("/mnt/gold/final_data/openssh_logs_final.csv", header=True)
    predictions = model.predict(test_data)
    
    # Log performance metrics
    mlflow.log_metric("prediction_count", len(predictions))
    mlflow.log_metric("anomaly_rate", sum(predictions) / len(predictions))
    
    print(f"Model {latest_model.version} performance logged")
```

---

## Troubleshooting

### Common Issues:

1. **Databricks Mount Issues**: Check service principal permissions
2. **MLflow Connection**: Verify MLflow server is running
3. **ADLS Gen2 Access**: Check storage account permissions
4. **AKS Pod Issues**: Check pod logs with `kubectl logs`

### Useful Commands:

```bash
# Check Databricks cluster status
databricks clusters list

# Check AKS pods
kubectl get pods

# Check MLflow server
kubectl logs deployment/mlflow-server

# Check Data Factory runs
az datafactory pipeline-run query-by-factory \
  --resource-group de-log-processing-rg \
  --factory-name de-log-processing-adf
```

---

## Cost Optimization

### Recommendations:

1. **Databricks**: Use auto-termination and spot instances
2. **ADLS Gen2**: Use cool storage for archived data
3. **AKS**: Use spot node pools for non-critical workloads
4. **Data Factory**: Optimize pipeline scheduling

### Estimated Monthly Costs:
- Databricks: ~$200-400
- ADLS Gen2: ~$50-100
- AKS: ~$150-300
- Data Factory: ~$50-100
- **Total**: ~$450-900/month

---

**Last Updated:** October 16, 2025  
**Author:** Aditya Padhi  
**Version:** 1.0
