# Azure-Based Data & AI Engineering Pipeline - Architecture Plan

## 📋 Executive Summary

This document outlines a comprehensive Azure-based solution for building a scalable ETL and ML pipeline with CI/CD automation. The architecture leverages Azure's native services to meet all assignment requirements.

---

## 🏗️ Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CI/CD Layer (GitHub Actions)                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Code Push    │ -> │ Unit Tests   │ -> │ Terraform    │              │
│  │ (GitHub)     │    │ (pytest)     │    │ Deploy       │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer (Azure Data Factory)              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Pipeline Trigger (Scheduled/Event-based)                        │   │
│  │    ↓                    ↓                      ↓                 │   │
│  │  [ETL Job]  ──────→  [ML Training]  ──────→  [Model Registry]   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     Data Layer (ADLS Gen2)                               │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐                    │
│  │  Bronze    │ -> │  Silver    │ -> │   Gold     │                    │
│  │  (Raw)     │    │ (Cleaned)  │    │ (Curated)  │                    │
│  └────────────┘    └────────────┘    └────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              Processing Layer (Azure Databricks + PySpark)               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  • Data Cleansing & Validation                                   │   │
│  │  • Schema Validation                                             │   │
│  │  • Feature Engineering                                           │   │
│  │  │  • ML Model Training (Spark MLlib)                            │   │
│  │  • Data Lineage Tracking                                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                  ML Ops Layer (MLflow on AKS)                            │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐        │
│  │ Model Tracking │    │ Model Registry │    │ Model Serving  │        │
│  │ (Experiments)  │    │ (Versions)     │    │ (REST API)     │        │
│  └────────────────┘    └────────────────┘    └────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│          Monitoring & Security (Azure Monitor + Key Vault)               │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐        │
│  │ Log Analytics  │    │ App Insights   │    │ Key Vault      │        │
│  │ (Monitoring)   │    │ (Metrics)      │    │ (Secrets)      │        │
│  └────────────────┘    └────────────────┘    └────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Azure Services Mapping

| Requirement | Azure Service | Rationale |
|-------------|--------------|-----------|
| **Data Storage (Bronze/Silver/Gold)** | **Azure Data Lake Storage Gen2** | Hierarchical namespace, cost-effective, supports Delta Lake format |
| **ETL Processing** | **Azure Databricks** | Native PySpark support, optimized Spark runtime, collaborative notebooks |
| **Orchestration** | **Azure Data Factory** | Managed service, built-in scheduling, visual designer, ADF pipelines |
| **ML Model Registry** | **MLflow on AKS** | Open-source, integrates with Databricks, flexible deployment |
| **Container Orchestration** | **Azure Kubernetes Service (AKS)** | For hosting MLflow server and model serving APIs |
| **CI/CD** | **GitHub Actions** | Code-native, easy integration, free for public repos |
| **Container Registry** | **Azure Container Registry (ACR)** | Private Docker image storage, geo-replication |
| **Secrets Management** | **Azure Key Vault** | Secure credential storage, integrated with all Azure services |
| **Monitoring** | **Azure Monitor + Log Analytics** | Centralized logging, custom dashboards, alerts |
| **IaC** | **Terraform** | Cloud-agnostic, modular, state management |
| **Networking** | **Azure Virtual Network + Private Endpoints** | Secure communication, no public internet exposure |

---

## 📊 Detailed Component Design

### 1. **Data Storage Layer (ADLS Gen2)**

#### Structure:
```
adls-container/
├── bronze/                    # Raw data (compressed CSV/JSON)
│   └── logs/
│       └── date=2025-10-16/
│           └── raw_logs.csv.gz
├── silver/                    # Cleaned & validated data
│   └── logs_processed/
│       └── date=2025-10-16/
│           └── part-00000.parquet
├── gold/                      # Curated/aggregated data
│   └── features/
│       └── date=2025-10-16/
│           └── feature_vectors.parquet
└── models/                    # ML model artifacts
    └── logistic_regression/
        └── version_1/
            ├── model/
            └── metadata.json
```

#### Configuration:
- **Account**: `adlsgen2datapipeline` (example name)
- **Container**: `data-pipeline`
- **Features**: 
  - Hierarchical namespace enabled
  - Lifecycle management for cost optimization
  - Private endpoint for secure access
  - RBAC enabled

---

### 2. **Processing Layer (Azure Databricks)**

#### Cluster Configuration:

**For ETL Jobs:**
```yaml
Cluster Type: Standard (Job Cluster - auto-terminated)
Databricks Runtime: 13.3 LTS ML (includes Spark 3.4.1, Python 3.10)
Node Type: 
  - Driver: Standard_D8s_v3 (8 cores, 32 GB RAM)
  - Workers: Standard_D8s_v3 (8 cores, 32 GB RAM)
Min Workers: 2
Max Workers: 8
Auto-scaling: Enabled
Auto-termination: 30 minutes
```

**Rationale:**
- **D8s_v3**: Cost-effective for general-purpose workloads
- **Auto-scaling**: Handles variable data volumes efficiently
- **Job Cluster**: Spins up for job execution, terminates automatically (cost-efficient)
- **ML Runtime**: Includes MLflow, scikit-learn, and PySpark MLlib pre-installed

#### Network Configuration:
```yaml
Virtual Network: vnet-databricks-prod
Subnets:
  - Private Subnet (for cluster nodes)
  - Public Subnet (for control plane - minimal exposure)
Network Security Groups: 
  - Allow inbound from ADF private endpoint only
  - Allow outbound to ADLS Gen2 private endpoint
No Public IP: Enabled (Secure Cluster Connectivity)
```

---

### 3. **ETL Pipeline Design**

#### PySpark Script Structure:

**File: `etl_pipeline.py`**
```python
# Pseudo-code structure

class ETLPipeline:
    def __init__(self, spark, config):
        self.spark = spark
        self.config = config
    
    def extract(self):
        """
        Extract compressed data from ADLS Gen2 Bronze layer
        - Read gzip CSV/JSON from bronze/logs/date=YYYY-MM-DD/
        """
        pass
    
    def transform(self, df):
        """
        Transform and validate data
        - Cleanse: Fill nulls, standardize strings
        - Validate: Check user_id, event_time
        - Derive: Add processing_date, event_category
        - Lineage: Track transformations using Delta Lake history
        """
        pass
    
    def load(self, df):
        """
        Load to Silver layer as Parquet/Delta Lake
        - Partition by date
        - Write to silver/logs_processed/
        """
        pass
    
    def run(self):
        raw_df = self.extract()
        clean_df = self.transform(raw_df)
        self.load(clean_df)
```

#### Data Quality Checks:
1. **Schema Validation**: Enforce expected schema using PySpark schema
2. **Null Checks**: Reject rows with missing critical fields (user_id, event_time)
3. **Data Type Validation**: Ensure timestamps are valid
4. **Referential Integrity**: Check foreign key constraints if applicable
5. **Statistical Validation**: Detect outliers using z-score or IQR

#### Lineage Implementation:
**Option 1: Delta Lake Lineage (Recommended)**
- Use Delta Lake's built-in versioning and history
- Query `DESCRIBE HISTORY table_name` for lineage
- Store metadata in Delta Lake transaction log

**Option 2: Custom Lineage with OpenLineage**
- Integrate OpenLineage SDK
- Emit lineage events to Marquez or custom backend

---

### 4. **ML Pipeline Design**

#### PySpark ML Pipeline Structure:

**File: `ml_pipeline.py`**
```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import mlflow

class MLTrainingPipeline:
    def __init__(self, spark, config):
        self.spark = spark
        self.config = config
    
    def load_features(self):
        """Load cleaned data from Silver layer"""
        pass
    
    def build_pipeline(self):
        """
        Build Spark ML Pipeline
        - StringIndexer for categorical features
        - VectorAssembler to combine features
        - StandardScaler for normalization
        - LogisticRegression classifier
        """
        indexer = StringIndexer(inputCol="event_category", outputCol="category_index")
        assembler = VectorAssembler(
            inputCols=["category_index", "duration", "value"],
            outputCol="features"
        )
        scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
        lr = LogisticRegression(featuresCol="scaled_features", labelCol="label")
        
        pipeline = Pipeline(stages=[indexer, assembler, scaler, lr])
        return pipeline
    
    def train_and_register(self, pipeline, train_df, test_df):
        """
        Train model and register with MLflow
        """
        with mlflow.start_run():
            model = pipeline.fit(train_df)
            predictions = model.transform(test_df)
            
            # Evaluate
            evaluator = BinaryClassificationEvaluator()
            auc = evaluator.evaluate(predictions)
            
            # Log to MLflow
            mlflow.log_param("model_type", "LogisticRegression")
            mlflow.log_metric("auc", auc)
            mlflow.spark.log_model(model, "model")
            
            # Save to ADLS Gen2
            model_path = f"abfss://data-pipeline@{storage_account}.dfs.core.windows.net/models/lr_model"
            model.write().overwrite().save(model_path)
            
            return model
    
    def run(self):
        df = self.load_features()
        train_df, test_df = df.randomSplit([0.8, 0.2])
        pipeline = self.build_pipeline()
        model = self.train_and_register(pipeline, train_df, test_df)
```

---

### 5. **Orchestration Layer (Azure Data Factory)**

#### ADF Pipeline Structure:

```json
{
  "name": "ETL_ML_Pipeline",
  "properties": {
    "activities": [
      {
        "name": "Run_ETL_Job",
        "type": "DatabricksSparkPython",
        "dependsOn": [],
        "policy": {
          "timeout": "1:00:00",
          "retry": 2
        },
        "typeProperties": {
          "pythonFile": "dbfs:/mnt/scripts/etl_pipeline.py",
          "parameters": ["--date", "@{formatDateTime(utcnow(), 'yyyy-MM-dd')}"]
        },
        "linkedServiceName": {
          "referenceName": "AzureDatabricks_LinkedService",
          "type": "LinkedServiceReference"
        }
      },
      {
        "name": "Run_ML_Training",
        "type": "DatabricksSparkPython",
        "dependsOn": [
          {
            "activity": "Run_ETL_Job",
            "dependencyConditions": ["Succeeded"]
          }
        ],
        "typeProperties": {
          "pythonFile": "dbfs:/mnt/scripts/ml_pipeline.py",
          "parameters": ["--date", "@{formatDateTime(utcnow(), 'yyyy-MM-dd')}"]
        }
      },
      {
        "name": "Data_Quality_Check",
        "type": "DatabricksNotebook",
        "dependsOn": [
          {
            "activity": "Run_ETL_Job",
            "dependencyConditions": ["Succeeded"]
          }
        ],
        "typeProperties": {
          "notebookPath": "/Workspace/notebooks/data_quality_check"
        }
      }
    ],
    "triggers": [
      {
        "name": "DailyScheduleTrigger",
        "type": "ScheduleTrigger",
        "properties": {
          "recurrence": {
            "frequency": "Day",
            "interval": 1,
            "startTime": "2025-01-01T02:00:00Z",
            "timeZone": "UTC"
          }
        }
      }
    ]
  }
}
```

#### Alternative: Apache Airflow on AKS

If you prefer Airflow:
- Deploy Airflow using Helm chart on AKS
- Use DatabricksSubmitRunOperator for job submission
- Store DAGs in Azure Container Registry

---

### 6. **MLflow Deployment on AKS**

#### Cluster Configuration:

```yaml
AKS Cluster:
  Name: aks-mlflow-prod
  Node Pool:
    VM Size: Standard_D4s_v3 (4 cores, 16 GB RAM)
    Node Count: 3
    Auto-scaling: Enabled (min: 2, max: 5)
  Networking:
    Network Plugin: Azure CNI
    Network Policy: Calico
    Load Balancer: Standard (Internal)
    Private Cluster: Enabled
```

#### MLflow Deployment:

**Helm Chart Configuration:**
```yaml
# values.yaml
replicaCount: 2
image:
  repository: <acr-name>.azurecr.io/mlflow
  tag: "2.9.2"

service:
  type: LoadBalancer
  port: 5000

backendStore:
  type: postgresql  # Azure Database for PostgreSQL
  connectionString: "postgresql://user:pass@mlflow-db.postgres.database.azure.com/mlflow"

artifactStore:
  type: azureblob
  connectionString: "DefaultEndpointsProtocol=https;AccountName=..."
  containerName: "mlflow-artifacts"

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: mlflow.internal.company.com
      paths:
        - path: /
          pathType: Prefix
```

---

### 7. **CI/CD Pipeline (GitHub Actions)**

#### Workflow Structure:

**File: `.github/workflows/ci-cd-pipeline.yml`**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [feature/*, develop]
  pull_request:
    branches: [main]

env:
  AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  RESOURCE_GROUP: rg-data-pipeline-prod
  ACR_NAME: acrdatapipeline

jobs:
  # ============================================
  # CI: Continuous Integration
  # ============================================
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pyspark==3.4.1
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=src --cov-report=xml
      
      - name: Run data validation tests
        run: |
          pytest tests/integration/test_data_validation.py
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run flake8
        run: |
          pip install flake8
          flake8 src/ --max-line-length=100

  # ============================================
  # CD: Continuous Deployment (Main branch only)
  # ============================================
  deploy:
    runs-on: ubuntu-latest
    needs: [test, lint]
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy infrastructure with Terraform
        run: |
          cd terraform
          terraform init
          terraform plan -out=tfplan
          terraform apply -auto-approve tfplan
      
      - name: Upload scripts to Databricks
        run: |
          pip install databricks-cli
          databricks workspace import_dir src/ /Workspace/production/ --overwrite
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
      
      - name: Deploy ADF Pipeline
        run: |
          az datafactory pipeline create \
            --resource-group $RESOURCE_GROUP \
            --factory-name adf-data-pipeline \
            --name ETL_ML_Pipeline \
            --pipeline @adf/pipeline.json
      
      - name: Build and push Docker image (for MLflow)
        run: |
          az acr build \
            --registry $ACR_NAME \
            --image mlflow:${{ github.sha }} \
            --file docker/Dockerfile .
      
      - name: Deploy MLflow to AKS
        run: |
          az aks get-credentials --resource-group $RESOURCE_GROUP --name aks-mlflow-prod
          helm upgrade --install mlflow ./helm/mlflow \
            --set image.tag=${{ github.sha }} \
            --namespace mlflow
```

---

### 8. **Testing Strategy**

#### Unit Tests (`tests/unit/test_transformations.py`):

```python
import pytest
from pyspark.sql import SparkSession
from src.etl_pipeline import ETLPipeline

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .master("local[2]") \
        .appName("unit-tests") \
        .getOrCreate()

def test_cleanse_nulls(spark):
    """Test that null values are filled correctly"""
    data = [
        ("user1", "event1", None),
        ("user2", None, "2025-10-16")
    ]
    df = spark.createDataFrame(data, ["user_id", "event_type", "event_time"])
    
    etl = ETLPipeline(spark, {})
    result = etl.cleanse_data(df)
    
    assert result.filter(result.event_type.isNull()).count() == 0

def test_validate_schema(spark):
    """Test schema validation"""
    data = [("user1", "event1", "2025-10-16")]
    df = spark.createDataFrame(data, ["user_id", "event_type", "event_time"])
    
    etl = ETLPipeline(spark, {})
    is_valid = etl.validate_schema(df)
    
    assert is_valid == True

def test_reject_invalid_rows(spark):
    """Test that rows with missing user_id are rejected"""
    data = [
        ("user1", "event1", "2025-10-16"),
        (None, "event2", "2025-10-16")
    ]
    df = spark.createDataFrame(data, ["user_id", "event_type", "event_time"])
    
    etl = ETLPipeline(spark, {})
    result = etl.filter_valid_rows(df)
    
    assert result.count() == 1
```

#### Integration Tests (`tests/integration/test_data_validation.py`):

```python
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

def test_output_schema():
    """Validate that the output schema matches expected structure"""
    spark = SparkSession.builder.master("local[2]").getOrCreate()
    
    expected_schema = StructType([
        StructField("user_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("event_time", TimestampType(), False),
        StructField("processing_date", StringType(), False),
        StructField("event_category", StringType(), False)
    ])
    
    # Read output from local test data
    df = spark.read.parquet("tests/fixtures/sample_output.parquet")
    
    assert df.schema == expected_schema
```

---

## 🛠️ Infrastructure as Code (Terraform)

### Directory Structure:

```
terraform/
├── main.tf                 # Main configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── providers.tf            # Provider configuration
├── modules/
│   ├── storage/            # ADLS Gen2
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── databricks/         # Databricks workspace
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── data_factory/       # Azure Data Factory
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── aks/                # AKS for MLflow
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── networking/         # VNet, Subnets, NSGs
│   │   ├── main.tf
│   │   └── variables.tf
│   └── monitoring/         # Azure Monitor, Log Analytics
│       ├── main.tf
│       └── variables.tf
└── environments/
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

### Key Terraform Resources:

#### `terraform/main.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.75.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.30.0"
    }
  }
  
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "tfstatestorage"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
  tags     = var.tags
}

# Networking Module
module "networking" {
  source              = "./modules/networking"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  vnet_name           = "vnet-${var.project_name}"
  address_space       = ["10.0.0.0/16"]
}

# Storage Module (ADLS Gen2)
module "storage" {
  source              = "./modules/storage"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  storage_account_name = "adls${var.project_name}${var.environment}"
  containers          = ["bronze", "silver", "gold", "models"]
  subnet_id           = module.networking.private_subnet_id
}

# Databricks Module
module "databricks" {
  source              = "./modules/databricks"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  workspace_name      = "dbw-${var.project_name}-${var.environment}"
  sku                 = "premium"
  vnet_id             = module.networking.vnet_id
  private_subnet_name = module.networking.databricks_private_subnet_name
  public_subnet_name  = module.networking.databricks_public_subnet_name
}

# Data Factory Module
module "data_factory" {
  source              = "./modules/data_factory"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  factory_name        = "adf-${var.project_name}-${var.environment}"
  databricks_workspace_url = module.databricks.workspace_url
}

# AKS Module (for MLflow)
module "aks" {
  source              = "./modules/aks"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  cluster_name        = "aks-mlflow-${var.environment}"
  node_count          = 3
  vm_size             = "Standard_D4s_v3"
  subnet_id           = module.networking.aks_subnet_id
}

# Monitoring Module
module "monitoring" {
  source              = "./modules/monitoring"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  log_analytics_name  = "law-${var.project_name}-${var.environment}"
}
```

#### `terraform/modules/storage/main.tf`:

```hcl
resource "azurerm_storage_account" "adls" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true  # Enable hierarchical namespace for ADLS Gen2
  
  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    virtual_network_subnet_ids = [var.subnet_id]
  }
  
  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
  }
  
  tags = var.tags
}

resource "azurerm_storage_container" "containers" {
  for_each              = toset(var.containers)
  name                  = each.value
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_private_endpoint" "adls_pe" {
  name                = "${var.storage_account_name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id
  
  private_service_connection {
    name                           = "${var.storage_account_name}-psc"
    private_connection_resource_id = azurerm_storage_account.adls.id
    subresource_names              = ["dfs"]
    is_manual_connection           = false
  }
}
```

---

## 📁 Project Structure

```
data-ai-pipeline/
├── .github/
│   └── workflows/
│       └── ci-cd-pipeline.yml
├── src/
│   ├── etl_pipeline.py          # Main ETL logic
│   ├── ml_pipeline.py           # ML training pipeline
│   ├── utils/
│   │   ├── config.py            # Configuration management
│   │   ├── logger.py            # Logging utilities
│   │   └── lineage.py           # Lineage tracking
│   └── data_quality/
│       ├── validators.py        # Schema and data validators
│       └── checks.py            # Quality check functions
├── tests/
│   ├── unit/
│   │   ├── test_transformations.py
│   │   ├── test_validators.py
│   │   └── test_ml_pipeline.py
│   ├── integration/
│   │   └── test_data_validation.py
│   └── fixtures/
│       └── sample_data.csv
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── modules/
│       ├── storage/
│       ├── databricks/
│       ├── data_factory/
│       ├── aks/
│       └── networking/
├── adf/
│   └── pipeline.json            # ADF pipeline definition
├── docker/
│   ├── Dockerfile               # MLflow Docker image
│   └── requirements.txt
├── helm/
│   └── mlflow/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── notebooks/
│   ├── data_exploration.ipynb
│   └── data_quality_check.ipynb
├── scripts/
│   ├── generate_sample_data.py  # AI-generated sample data
│   └── deploy.sh                # Deployment helper script
├── config/
│   ├── dev.yaml
│   ├── staging.yaml
│   └── prod.yaml
├── requirements.txt
├── setup.py
├── pytest.ini
├── .gitignore
└── README.md
```

---

## 🚀 Implementation Roadmap

### Phase 1: Infrastructure Setup (Week 1)
1. ✅ Set up Azure subscription and resource groups
2. ✅ Configure Terraform backend (Azure Storage for state)
3. ✅ Deploy base infrastructure (VNet, ADLS Gen2, Key Vault)
4. ✅ Deploy Azure Databricks workspace
5. ✅ Configure networking (Private Endpoints, NSGs)

### Phase 2: ETL Pipeline Development (Week 2)
1. ✅ Generate sample log data using AI (ChatGPT/Claude)
2. ✅ Develop PySpark ETL script
   - Extract from ADLS Gen2
   - Transform with cleansing and validation
   - Load to Parquet/Delta Lake format
3. ✅ Implement data lineage tracking (Delta Lake history)
4. ✅ Write unit tests for transformations
5. ✅ Test locally with PySpark

### Phase 3: ML Pipeline Development (Week 2)
1. ✅ Design feature engineering logic
2. ✅ Build Spark ML Pipeline (VectorAssembler + Model)
3. ✅ Integrate MLflow for experiment tracking
4. ✅ Train and evaluate model
5. ✅ Write unit tests for ML pipeline
6. ✅ Save model artifacts to ADLS Gen2

### Phase 4: Orchestration Setup (Week 3)
1. ✅ Deploy Azure Data Factory
2. ✅ Create ADF pipeline with activities:
   - ETL Databricks job
   - ML training Databricks job
   - Data quality check
3. ✅ Configure scheduling trigger (daily)
4. ✅ Test end-to-end pipeline execution

### Phase 5: MLflow Deployment (Week 3)
1. ✅ Deploy AKS cluster
2. ✅ Set up Azure Database for PostgreSQL (MLflow backend)
3. ✅ Deploy MLflow using Helm chart
4. ✅ Configure artifact storage (ADLS Gen2)
5. ✅ Test model registration and retrieval

### Phase 6: CI/CD Pipeline (Week 4)
1. ✅ Set up GitHub repository
2. ✅ Create GitHub Actions workflow
   - CI: Run pytest, linting
   - CD: Deploy Terraform, upload scripts, deploy ADF pipeline
3. ✅ Configure Azure service principal for authentication
4. ✅ Test CI/CD pipeline with feature branch

### Phase 7: Testing & Documentation (Week 4)
1. ✅ Write comprehensive README.md
2. ✅ Document architecture and design decisions
3. ✅ Create setup and deployment instructions
4. ✅ Add monitoring and alerting dashboards
5. ✅ Final end-to-end testing

---

## 🔐 Security Best Practices

1. **Network Security**
   - Private endpoints for all PaaS services (no public internet exposure)
   - Network Security Groups (NSGs) with least-privilege rules
   - Azure Firewall for outbound traffic control

2. **Identity & Access Management**
   - Managed Identities for Azure services (no hardcoded credentials)
   - RBAC with principle of least privilege
   - Azure AD authentication for Databricks and ADF

3. **Secrets Management**
   - All credentials stored in Azure Key Vault
   - Key Vault integrated with Databricks using secret scopes
   - Rotate secrets regularly

4. **Data Protection**
   - Encryption at rest (Azure Storage encryption)
   - Encryption in transit (TLS 1.2+)
   - Data masking for sensitive fields

---

## 📊 Monitoring & Alerting

### Metrics to Track:
1. **Pipeline Metrics**
   - Job execution time
   - Success/failure rate
   - Data volume processed

2. **Model Metrics**
   - Model performance (AUC, F1-score)
   - Training time
   - Prediction latency

3. **Infrastructure Metrics**
   - Databricks cluster utilization
   - ADLS storage usage
   - AKS pod health

### Azure Monitor Dashboards:
- Real-time pipeline status
- Cost tracking
- Resource utilization
- Error logs and alerts

---

## 💰 Cost Optimization

1. **Databricks**
   - Use job clusters (auto-terminate)
   - Enable autoscaling
   - Use Spot instances for non-critical workloads

2. **ADLS Gen2**
   - Lifecycle management (move cold data to Archive tier)
   - Data compression (Parquet format)

3. **AKS**
   - Use Reserved Instances for production
   - Enable cluster autoscaler

4. **Estimated Monthly Cost (Production)**
   - ADLS Gen2: ~$50-100
   - Databricks: ~$500-1000 (depends on usage)
   - AKS: ~$200-400
   - Azure Data Factory: ~$50-100
   - **Total: ~$800-1600/month**

---

## 📚 Key Documentation

1. **Setup Guide**: Instructions for deploying infrastructure
2. **Developer Guide**: How to develop and test locally
3. **Operations Guide**: How to monitor and troubleshoot
4. **Architecture Decision Records (ADR)**: Design decisions and rationale

---

## ✅ Success Criteria

- ✅ ETL pipeline successfully processes raw data and outputs to Silver layer
- ✅ ML model trains successfully and is registered in MLflow
- ✅ All unit tests pass with >80% code coverage
- ✅ CI/CD pipeline deploys infrastructure and code automatically
- ✅ Pipeline executes on schedule without manual intervention
- ✅ Data lineage is traceable
- ✅ All resources deployed via Terraform (IaC)
- ✅ Comprehensive documentation provided

---

## 🎯 Next Steps

1. **Review this plan** and confirm alignment with assignment requirements
2. **Set up Azure account** and obtain necessary credentials
3. **Create GitHub repository** for version control
4. **Start with Phase 1** (Infrastructure Setup)
5. **Iterate and test** each component incrementally

---

## 📞 Support & Resources

- **Azure Documentation**: https://docs.microsoft.com/azure
- **Databricks Documentation**: https://docs.databricks.com
- **MLflow Documentation**: https://mlflow.org/docs
- **Terraform Azure Provider**: https://registry.terraform.io/providers/hashicorp/azurerm

---

**Author**: Aditya  
**Date**: October 16, 2025  
**Version**: 1.0

