# Implementation Guide - Quick Start

## 🚀 Getting Started

This guide provides step-by-step instructions to implement the Data & AI Engineering pipeline on Azure.

---

## Prerequisites

### Required Tools
```bash
# Install Azure CLI
brew install azure-cli

# Install Terraform
brew install terraform

# Install Python 3.10
brew install python@3.10

# Install kubectl (for AKS)
brew install kubectl

# Install Helm (for MLflow)
brew install helm

# Install Databricks CLI
pip install databricks-cli
```

### Azure Setup
```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Create a service principal for Terraform
az ad sp create-for-rbac --name "terraform-sp" --role="Contributor" --scopes="/subscriptions/YOUR_SUBSCRIPTION_ID"
# Save the output - you'll need it for GitHub Actions
```

---

## Step 1: Project Setup

### Create Project Structure
```bash
# Clone or create your repository
mkdir data-ai-pipeline
cd data-ai-pipeline

# Create directory structure
mkdir -p src/{utils,data_quality}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p terraform/modules/{storage,databricks,data_factory,aks,networking,monitoring}
mkdir -p adf docker helm/mlflow/{templates,} notebooks scripts config
mkdir -p .github/workflows

# Initialize git
git init
git remote add origin YOUR_GITHUB_REPO_URL
```

### Create requirements.txt
```bash
cat > requirements.txt << 'EOF'
# Core dependencies
pyspark==3.4.1
delta-spark==2.4.0
pandas==2.1.3
numpy==1.24.3

# ML and MLflow
mlflow==2.9.2
scikit-learn==1.3.2

# Azure SDKs
azure-storage-file-datalake==12.14.0
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-spark==0.6.0

# Linting and formatting
flake8==6.1.0
black==23.11.0

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1

# Databricks
databricks-cli==0.18.0

# OpenLineage (for data lineage)
openlineage-python==1.7.0
EOF
```

---

## Step 2: Generate Sample Data

Create a script to generate sample log data using AI (or manually):

```python
# scripts/generate_sample_data.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import gzip
import json
import random

def generate_log_data(num_rows=10000):
    """Generate sample log data for the pipeline"""
    
    np.random.seed(42)
    
    # Generate timestamps
    start_date = datetime(2025, 10, 1)
    timestamps = [
        start_date + timedelta(minutes=random.randint(0, 43200))  # 30 days
        for _ in range(num_rows)
    ]
    
    # User IDs (with some nulls to test validation)
    user_ids = [f"user_{random.randint(1, 1000)}" if random.random() > 0.05 else None 
                for _ in range(num_rows)]
    
    # Event types
    event_types = ['page_view', 'click', 'purchase', 'logout', 'login', 'search']
    events = [random.choice(event_types) for _ in range(num_rows)]
    
    # Event duration (seconds)
    durations = np.random.exponential(scale=30, size=num_rows)
    
    # Event values (for ML prediction)
    values = np.random.normal(loc=50, scale=20, size=num_rows)
    
    # High-value flag (target variable for ML)
    high_value = [1 if v > 60 else 0 for v in values]
    
    # Session IDs
    session_ids = [f"session_{random.randint(1, 5000)}" for _ in range(num_rows)]
    
    # Device types
    devices = ['mobile', 'desktop', 'tablet']
    device_types = [random.choice(devices) for _ in range(num_rows)]
    
    # Create DataFrame
    df = pd.DataFrame({
        'user_id': user_ids,
        'session_id': session_ids,
        'event_type': events,
        'event_time': timestamps,
        'duration_seconds': durations,
        'value': values,
        'high_value': high_value,
        'device_type': device_types,
        'user_agent': ['Mozilla/5.0'] * num_rows,  # Simplified
        'ip_address': [f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}" 
                       for _ in range(num_rows)]
    })
    
    return df

def save_compressed_csv(df, output_path):
    """Save DataFrame as compressed CSV"""
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        df.to_csv(f, index=False)
    print(f"Saved {len(df)} rows to {output_path}")

def save_compressed_json(df, output_path):
    """Save DataFrame as compressed JSONL"""
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        for record in df.to_dict('records'):
            f.write(json.dumps(record, default=str) + '\n')
    print(f"Saved {len(df)} rows to {output_path}")

if __name__ == "__main__":
    # Generate data
    df = generate_log_data(num_rows=10000)
    
    # Save in multiple formats
    save_compressed_csv(df, 'tests/fixtures/sample_logs.csv.gz')
    save_compressed_json(df, 'tests/fixtures/sample_logs.json.gz')
    
    # Also save uncompressed for testing
    df.to_csv('tests/fixtures/sample_logs.csv', index=False)
    
    print("\nData generation complete!")
    print(f"Shape: {df.shape}")
    print(f"\nNull user_ids: {df['user_id'].isna().sum()}")
    print(f"High-value events: {df['high_value'].sum()}")
```

Run it:
```bash
python scripts/generate_sample_data.py
```

---

## Step 3: Implement ETL Pipeline

### Create ETL Pipeline Script

```python
# src/etl_pipeline.py

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType
from delta import configure_spark_with_delta_pip
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL Pipeline for processing log data"""
    
    def __init__(self, config):
        self.config = config
        self.spark = self._create_spark_session()
        
    def _create_spark_session(self):
        """Create Spark session with Delta Lake support"""
        builder = SparkSession.builder \
            .appName("ETL Pipeline") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", 
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        
        spark = configure_spark_with_delta_pip(builder).getOrCreate()
        return spark
    
    def get_expected_schema(self):
        """Define expected schema for raw data"""
        return StructType([
            StructField("user_id", StringType(), True),
            StructField("session_id", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("event_time", TimestampType(), True),
            StructField("duration_seconds", DoubleType(), True),
            StructField("value", DoubleType(), True),
            StructField("high_value", StringType(), True),
            StructField("device_type", StringType(), True),
            StructField("user_agent", StringType(), True),
            StructField("ip_address", StringType(), True),
        ])
    
    def extract(self, input_path):
        """
        Extract data from ADLS Gen2 bronze layer
        Supports both CSV and JSON formats (compressed or uncompressed)
        """
        logger.info(f"Extracting data from: {input_path}")
        
        if input_path.endswith('.csv') or input_path.endswith('.csv.gz'):
            df = self.spark.read.csv(
                input_path,
                header=True,
                inferSchema=True,
                schema=self.get_expected_schema()
            )
        elif input_path.endswith('.json') or input_path.endswith('.json.gz'):
            df = self.spark.read.json(input_path, schema=self.get_expected_schema())
        else:
            raise ValueError(f"Unsupported file format: {input_path}")
        
        logger.info(f"Extracted {df.count()} rows")
        return df
    
    def validate_schema(self, df):
        """Validate that DataFrame matches expected schema"""
        expected_schema = self.get_expected_schema()
        
        # Check if all expected columns exist
        expected_cols = set([field.name for field in expected_schema.fields])
        actual_cols = set(df.columns)
        
        missing_cols = expected_cols - actual_cols
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")
        
        logger.info("Schema validation passed")
        return True
    
    def cleanse_data(self, df):
        """
        Cleanse data:
        - Fill nulls with defaults
        - Standardize strings
        - Cast data types
        """
        logger.info("Cleansing data...")
        
        df_clean = df \
            .withColumn("event_type", F.lower(F.trim(F.col("event_type")))) \
            .withColumn("device_type", F.lower(F.trim(F.col("device_type")))) \
            .fillna({
                "event_type": "unknown",
                "duration_seconds": 0.0,
                "value": 0.0,
                "device_type": "unknown"
            })
        
        logger.info("Data cleansing complete")
        return df_clean
    
    def filter_valid_rows(self, df):
        """
        Filter out invalid rows:
        - user_id must not be null
        - event_time must be a valid timestamp
        """
        logger.info("Filtering invalid rows...")
        
        initial_count = df.count()
        
        df_valid = df.filter(
            (F.col("user_id").isNotNull()) &
            (F.col("event_time").isNotNull())
        )
        
        filtered_count = initial_count - df_valid.count()
        logger.info(f"Filtered out {filtered_count} invalid rows")
        
        return df_valid
    
    def add_derived_columns(self, df):
        """
        Add derived columns:
        - processing_date: Date when data was processed
        - event_category: Categorize events
        - hour_of_day: Extract hour from event_time
        """
        logger.info("Adding derived columns...")
        
        df_derived = df \
            .withColumn("processing_date", F.lit(datetime.now().strftime("%Y-%m-%d"))) \
            .withColumn("event_category", 
                       F.when(F.col("event_type").isin(["purchase", "checkout"]), "transaction")
                        .when(F.col("event_type").isin(["page_view", "click"]), "engagement")
                        .when(F.col("event_type").isin(["login", "logout"]), "authentication")
                        .otherwise("other")) \
            .withColumn("hour_of_day", F.hour(F.col("event_time"))) \
            .withColumn("is_mobile", 
                       F.when(F.col("device_type") == "mobile", 1).otherwise(0))
        
        logger.info("Derived columns added")
        return df_derived
    
    def transform(self, df):
        """
        Main transformation logic
        """
        logger.info("Starting transformation...")
        
        # Validate schema
        self.validate_schema(df)
        
        # Cleanse data
        df_clean = self.cleanse_data(df)
        
        # Filter valid rows
        df_valid = self.filter_valid_rows(df_clean)
        
        # Add derived columns
        df_transformed = self.add_derived_columns(df_valid)
        
        logger.info(f"Transformation complete. Final row count: {df_transformed.count()}")
        return df_transformed
    
    def load(self, df, output_path, partition_cols=["processing_date"]):
        """
        Load data to ADLS Gen2 silver layer
        Save as Delta Lake format with partitioning
        """
        logger.info(f"Loading data to: {output_path}")
        
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .partitionBy(*partition_cols) \
            .option("overwriteSchema", "true") \
            .save(output_path)
        
        logger.info("Data loaded successfully")
        
        # Enable Delta Lake history for lineage
        logger.info("Delta Lake history enabled for lineage tracking")
    
    def run(self, input_path, output_path):
        """
        Run the complete ETL pipeline
        """
        logger.info("=" * 60)
        logger.info("Starting ETL Pipeline")
        logger.info("=" * 60)
        
        try:
            # Extract
            raw_df = self.extract(input_path)
            
            # Transform
            transformed_df = self.transform(raw_df)
            
            # Load
            self.load(transformed_df, output_path)
            
            logger.info("=" * 60)
            logger.info("ETL Pipeline completed successfully!")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {str(e)}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ETL Pipeline')
    parser.add_argument('--input', required=True, help='Input path (bronze layer)')
    parser.add_argument('--output', required=True, help='Output path (silver layer)')
    parser.add_argument('--date', default=datetime.now().strftime("%Y-%m-%d"), 
                       help='Processing date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    config = {
        'processing_date': args.date
    }
    
    pipeline = ETLPipeline(config)
    pipeline.run(args.input, args.output)


if __name__ == "__main__":
    main()
```

---

## Step 4: Implement ML Pipeline

```python
# src/ml_pipeline.py

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
import mlflow
import mlflow.spark
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLTrainingPipeline:
    """ML Pipeline for training classification models"""
    
    def __init__(self, config):
        self.config = config
        self.spark = SparkSession.builder \
            .appName("ML Training Pipeline") \
            .getOrCreate()
        
        # Configure MLflow
        mlflow.set_tracking_uri(config.get('mlflow_tracking_uri', 'http://mlflow-service:5000'))
        mlflow.set_experiment(config.get('experiment_name', '/ml-pipeline-experiment'))
    
    def load_features(self, input_path):
        """Load cleaned data from silver layer"""
        logger.info(f"Loading features from: {input_path}")
        
        df = self.spark.read.format("delta").load(input_path)
        
        logger.info(f"Loaded {df.count()} rows")
        return df
    
    def prepare_features(self, df):
        """
        Prepare features for ML:
        - Select relevant columns
        - Handle categorical variables
        - Create label column
        """
        logger.info("Preparing features...")
        
        # Select features and label
        feature_df = df.select(
            "user_id",
            "event_type",
            "duration_seconds",
            "value",
            "device_type",
            "event_category",
            "hour_of_day",
            "is_mobile",
            "high_value"
        )
        
        # Convert label to integer
        feature_df = feature_df.withColumn("label", 
                                          feature_df["high_value"].cast("integer"))
        
        logger.info(f"Features prepared. Shape: {feature_df.count()} rows")
        return feature_df
    
    def build_pipeline(self):
        """
        Build Spark ML Pipeline with:
        - StringIndexer for categorical features
        - VectorAssembler to combine features
        - StandardScaler for normalization
        - LogisticRegression classifier
        """
        logger.info("Building ML pipeline...")
        
        # Index categorical features
        indexer_event = StringIndexer(
            inputCol="event_type",
            outputCol="event_type_idx",
            handleInvalid="keep"
        )
        
        indexer_device = StringIndexer(
            inputCol="device_type",
            outputCol="device_type_idx",
            handleInvalid="keep"
        )
        
        indexer_category = StringIndexer(
            inputCol="event_category",
            outputCol="event_category_idx",
            handleInvalid="keep"
        )
        
        # Assemble features into a vector
        assembler = VectorAssembler(
            inputCols=[
                "event_type_idx",
                "device_type_idx",
                "event_category_idx",
                "duration_seconds",
                "value",
                "hour_of_day",
                "is_mobile"
            ],
            outputCol="features",
            handleInvalid="skip"
        )
        
        # Scale features
        scaler = StandardScaler(
            inputCol="features",
            outputCol="scaled_features",
            withStd=True,
            withMean=True
        )
        
        # Logistic Regression classifier
        lr = LogisticRegression(
            featuresCol="scaled_features",
            labelCol="label",
            maxIter=100,
            regParam=0.01
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[
            indexer_event,
            indexer_device,
            indexer_category,
            assembler,
            scaler,
            lr
        ])
        
        logger.info("ML pipeline built successfully")
        return pipeline
    
    def train_and_evaluate(self, pipeline, train_df, test_df):
        """
        Train the model and evaluate performance
        """
        logger.info("Training model...")
        
        with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Log parameters
            mlflow.log_param("model_type", "LogisticRegression")
            mlflow.log_param("train_size", train_df.count())
            mlflow.log_param("test_size", test_df.count())
            
            # Train model
            model = pipeline.fit(train_df)
            
            # Make predictions
            predictions = model.transform(test_df)
            
            # Evaluate
            evaluator = BinaryClassificationEvaluator(
                labelCol="label",
                rawPredictionCol="rawPrediction",
                metricName="areaUnderROC"
            )
            
            auc = evaluator.evaluate(predictions)
            
            # Log metrics
            mlflow.log_metric("auc_roc", auc)
            
            # Log model
            mlflow.spark.log_model(model, "model")
            
            logger.info(f"Model trained. AUC-ROC: {auc:.4f}")
            
            return model, auc
    
    def save_model(self, model, output_path):
        """Save model artifact to ADLS Gen2"""
        logger.info(f"Saving model to: {output_path}")
        
        model.write().overwrite().save(output_path)
        
        logger.info("Model saved successfully")
    
    def run(self, input_path, model_output_path):
        """
        Run the complete ML training pipeline
        """
        logger.info("=" * 60)
        logger.info("Starting ML Training Pipeline")
        logger.info("=" * 60)
        
        try:
            # Load features
            df = self.load_features(input_path)
            
            # Prepare features
            feature_df = self.prepare_features(df)
            
            # Split data
            train_df, test_df = feature_df.randomSplit([0.8, 0.2], seed=42)
            
            # Build pipeline
            pipeline = self.build_pipeline()
            
            # Train and evaluate
            model, auc = self.train_and_evaluate(pipeline, train_df, test_df)
            
            # Save model
            self.save_model(model, model_output_path)
            
            logger.info("=" * 60)
            logger.info("ML Training Pipeline completed successfully!")
            logger.info(f"Final AUC-ROC: {auc:.4f}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"ML Training Pipeline failed: {str(e)}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ML Training Pipeline')
    parser.add_argument('--input', required=True, 
                       help='Input path (silver layer)')
    parser.add_argument('--output', required=True, 
                       help='Output path for model')
    parser.add_argument('--mlflow-uri', default='http://mlflow-service:5000',
                       help='MLflow tracking URI')
    
    args = parser.parse_args()
    
    config = {
        'mlflow_tracking_uri': args.mlflow_uri,
        'experiment_name': '/ml-pipeline-experiment'
    }
    
    pipeline = MLTrainingPipeline(config)
    pipeline.run(args.input, args.output)


if __name__ == "__main__":
    main()
```

---

## Step 5: Write Unit Tests

```python
# tests/unit/test_etl_pipeline.py

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from etl_pipeline import ETLPipeline


@pytest.fixture(scope="session")
def spark():
    """Create Spark session for testing"""
    spark = SparkSession.builder \
        .master("local[2]") \
        .appName("unit-tests") \
        .getOrCreate()
    
    yield spark
    spark.stop()


@pytest.fixture
def etl_pipeline(spark):
    """Create ETL pipeline instance"""
    config = {'processing_date': '2025-10-16'}
    pipeline = ETLPipeline(config)
    return pipeline


@pytest.fixture
def sample_data(spark):
    """Create sample data for testing"""
    data = [
        ("user1", "session1", "page_view", datetime(2025, 10, 16, 10, 0, 0), 
         30.5, 45.0, "0", "desktop", "Mozilla/5.0", "192.168.1.1"),
        ("user2", "session2", "CLICK", datetime(2025, 10, 16, 11, 0, 0), 
         15.0, 70.0, "1", "Mobile", "Mozilla/5.0", "192.168.1.2"),
        (None, "session3", "purchase", datetime(2025, 10, 16, 12, 0, 0), 
         60.0, 100.0, "1", "tablet", "Mozilla/5.0", "192.168.1.3"),
    ]
    
    schema = StructType([
        StructField("user_id", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("event_time", TimestampType(), True),
        StructField("duration_seconds", DoubleType(), True),
        StructField("value", DoubleType(), True),
        StructField("high_value", StringType(), True),
        StructField("device_type", StringType(), True),
        StructField("user_agent", StringType(), True),
        StructField("ip_address", StringType(), True),
    ])
    
    df = spark.createDataFrame(data, schema)
    return df


def test_validate_schema(etl_pipeline, sample_data):
    """Test schema validation"""
    assert etl_pipeline.validate_schema(sample_data) == True


def test_cleanse_data(etl_pipeline, sample_data):
    """Test data cleansing"""
    result = etl_pipeline.cleanse_data(sample_data)
    
    # Check that strings are lowercase
    assert result.filter(result.event_type == "click").count() == 1
    assert result.filter(result.device_type == "mobile").count() == 1


def test_filter_valid_rows(etl_pipeline, sample_data):
    """Test filtering of invalid rows"""
    result = etl_pipeline.filter_valid_rows(sample_data)
    
    # Should filter out row with null user_id
    assert result.count() == 2
    assert result.filter(result.user_id.isNull()).count() == 0


def test_add_derived_columns(etl_pipeline, sample_data):
    """Test adding derived columns"""
    result = etl_pipeline.add_derived_columns(sample_data)
    
    # Check that derived columns exist
    assert "processing_date" in result.columns
    assert "event_category" in result.columns
    assert "hour_of_day" in result.columns
    assert "is_mobile" in result.columns
    
    # Check categorization
    engagement_count = result.filter(result.event_category == "engagement").count()
    assert engagement_count == 2  # page_view and click


def test_transform_pipeline(etl_pipeline, sample_data):
    """Test complete transformation pipeline"""
    result = etl_pipeline.transform(sample_data)
    
    # Should have filtered invalid rows
    assert result.count() == 2
    
    # Should have derived columns
    assert "event_category" in result.columns
    
    # Event types should be lowercase
    uppercase_events = result.filter(result.event_type != result.event_type.lower()).count()
    assert uppercase_events == 0
```

Run tests:
```bash
pytest tests/unit/ -v --cov=src --cov-report=html
```

---

## Step 6: Deploy Infrastructure with Terraform

### Initialize Terraform

```bash
cd terraform

# Create backend storage for Terraform state
az group create --name rg-terraform-state --location eastus
az storage account create --name tfstate$RANDOM --resource-group rg-terraform-state --sku Standard_LRS
az storage container create --name tfstate --account-name YOUR_STORAGE_ACCOUNT

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file=environments/dev.tfvars -out=tfplan

# Apply (deploy infrastructure)
terraform apply tfplan
```

### Key Terraform Commands

```bash
# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Show planned changes
terraform plan

# Apply changes
terraform apply -auto-approve

# Destroy infrastructure (when done)
terraform destroy
```

---

## Step 7: Configure CI/CD Pipeline

### Set up GitHub Secrets

```bash
# In your GitHub repository settings, add these secrets:

# Azure credentials (from service principal)
AZURE_CREDENTIALS='{ 
  "clientId": "xxx",
  "clientSecret": "xxx",
  "subscriptionId": "xxx",
  "tenantId": "xxx"
}'

AZURE_SUBSCRIPTION_ID='your-subscription-id'

# Databricks credentials
DATABRICKS_HOST='https://adb-xxxxx.azuredatabricks.net'
DATABRICKS_TOKEN='dapi-xxxxx'

# Storage account key
STORAGE_ACCOUNT_KEY='your-storage-key'
```

### Trigger Pipeline

```bash
# Create feature branch
git checkout -b feature/implement-etl

# Make changes and commit
git add .
git commit -m "Implement ETL pipeline"
git push origin feature/implement-etl

# This will trigger CI (tests)

# Create PR and merge to main
# This will trigger CD (deployment)
```

---

## Step 8: Deploy and Test

### Upload Sample Data to ADLS Gen2

```bash
# Using Azure CLI
az storage blob upload \
  --account-name YOUR_STORAGE_ACCOUNT \
  --container-name data-pipeline \
  --name bronze/logs/date=2025-10-16/raw_logs.csv.gz \
  --file tests/fixtures/sample_logs.csv.gz
```

### Trigger ADF Pipeline Manually

```bash
# Using Azure CLI
az datafactory pipeline create-run \
  --resource-group rg-data-pipeline-prod \
  --factory-name adf-data-pipeline \
  --name ETL_ML_Pipeline
```

### Monitor Pipeline Execution

```bash
# Check ADF pipeline run status
az datafactory pipeline-run show \
  --resource-group rg-data-pipeline-prod \
  --factory-name adf-data-pipeline \
  --run-id YOUR_RUN_ID
```

### Query Delta Lake Table

```python
# In Databricks notebook
df = spark.read.format("delta").load("abfss://data-pipeline@xxx.dfs.core.windows.net/silver/logs_processed")
display(df)

# View Delta history (lineage)
spark.sql("DESCRIBE HISTORY delta.`abfss://data-pipeline@xxx.dfs.core.windows.net/silver/logs_processed`")
```

### Access MLflow UI

```bash
# Port forward MLflow service (if on AKS)
kubectl port-forward -n mlflow svc/mlflow-service 5000:5000

# Open browser
open http://localhost:5000
```

---

## Step 9: Monitoring & Troubleshooting

### View Databricks Logs

```bash
# Access Databricks workspace
# Navigate to: Workspace > Jobs > Your Job > Runs
# Click on run to view logs
```

### View Azure Monitor Logs

```bash
# Query Log Analytics
az monitor log-analytics query \
  --workspace YOUR_WORKSPACE_ID \
  --analytics-query "AzureDiagnostics | where ResourceType == 'DATAFACTORIES' | take 10"
```

### Common Issues & Solutions

1. **Authentication Errors**
   ```bash
   # Check service principal permissions
   az role assignment list --assignee YOUR_SERVICE_PRINCIPAL_ID
   ```

2. **Network Connectivity Issues**
   ```bash
   # Verify private endpoints
   az network private-endpoint list --resource-group rg-data-pipeline-prod
   ```

3. **Spark Job Failures**
   ```bash
   # Check Databricks cluster logs
   # Navigate to: Compute > Your Cluster > Event Log
   ```

---

## 📚 Additional Resources

### Useful Commands Cheatsheet

```bash
# Azure CLI
az account show                    # Show current subscription
az group list                      # List resource groups
az resource list --resource-group  # List resources in group

# Databricks CLI
databricks workspace ls /          # List workspace files
databricks jobs list               # List jobs
databricks runs list               # List job runs

# Terraform
terraform state list               # List resources in state
terraform state show RESOURCE      # Show resource details
terraform output                   # Show outputs

# kubectl (for AKS/MLflow)
kubectl get pods -n mlflow         # List pods
kubectl logs POD_NAME -n mlflow    # View logs
kubectl describe pod POD_NAME      # Pod details

# pytest
pytest -v                          # Verbose mode
pytest --cov=src                   # With coverage
pytest -k test_name                # Run specific test
```

---

## Final Checklist

Before submitting:

- [ ] All infrastructure deployed via Terraform
- [ ] Sample data generated and uploaded to ADLS Gen2
- [ ] ETL pipeline tested locally and on Databricks
- [ ] ML pipeline tested and model registered in MLflow
- [ ] Unit tests passing with >80% coverage
- [ ] CI/CD pipeline configured and tested
- [ ] ADF pipeline scheduled and running
- [ ] README.md documented with setup instructions
- [ ] Architecture diagrams created
- [ ] All secrets stored in Key Vault (not hardcoded)
- [ ] Monitoring and alerting configured
- [ ] Data lineage verified (Delta Lake history)

---

##  Next Steps

1. Review the architecture plan
2. Set up Azure account and install prerequisites
3. Generate sample data
4. Implement ETL and ML pipelines locally
5. Write and run unit tests
6. Deploy infrastructure with Terraform
7. Configure CI/CD pipeline
8. Test end-to-end pipeline
9. Document everything in README.md
10. Submit assignment!

Good luck! 🚀

