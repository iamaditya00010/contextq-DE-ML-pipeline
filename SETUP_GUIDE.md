# Complete Setup Guide - From Local to Azure

This guide will walk you through:
1. Azure account setup and service enablement
2. Local development environment setup
3. Creating a GitHub repository
4. Building the solution locally
5. Deploying to Azure

---

## Part 1: Azure Account Setup

### Step 1: Verify Azure Subscription

```bash
# Login to Azure
az login

# List your subscriptions
az account list --output table

# Set the subscription you want to use
az account set --subscription "YOUR_SUBSCRIPTION_NAME_OR_ID"

# Verify current subscription
az account show --output table
```

### Step 2: Enable Required Azure Resource Providers

```bash
# Enable required resource providers (this is important!)
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.Databricks
az provider register --namespace Microsoft.DataFactory
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.Network
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.DBforPostgreSQL
az provider register --namespace Microsoft.OperationalInsights

# Check registration status (should show "Registered")
az provider show --namespace Microsoft.Storage --query "registrationState"
az provider show --namespace Microsoft.Databricks --query "registrationState"
az provider show --namespace Microsoft.DataFactory --query "registrationState"
```

**Note**: Registration can take 5-10 minutes. You can proceed while they register.

### Step 3: Set Up Service Principal for CI/CD

```bash
# Create a service principal with Contributor role
az ad sp create-for-rbac \
  --name "sp-data-pipeline-cicd" \
  --role Contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv) \
  --sdk-auth

# IMPORTANT: Save the entire JSON output! You'll need it for GitHub Actions
# It should look like:
# {
#   "clientId": "xxx",
#   "clientSecret": "xxx",
#   "subscriptionId": "xxx",
#   "tenantId": "xxx",
#   ...
# }
```

**Save this output** - you'll add it to GitHub secrets later!

### Step 4: Check Azure Quotas (Important!)

```bash
# Check compute quotas for your region
az vm list-usage --location eastus --output table

# Check if you have enough quota for:
# - Standard DSv3 Family vCPUs: Need at least 16 cores
# - Total Regional vCPUs: Need at least 20 cores
```

If you need more quota:
1. Go to Azure Portal → Subscriptions → Usage + quotas
2. Request quota increase for "Standard DSv3 Family vCPUs"

---

## Part 2: Local Development Environment Setup

### Step 1: Install Required Tools

#### macOS (using Homebrew)

```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Azure CLI
brew install azure-cli

# 3. Install Python 3.10
brew install python@3.10

# 4. Install Java (required for PySpark)
brew install openjdk@11

# Add to PATH (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 5. Install Terraform
brew install terraform

# 6. Install Git
brew install git

# 7. Install kubectl (for AKS)
brew install kubectl

# 8. Install Helm (for MLflow)
brew install helm

# Verify installations
az --version
python3.10 --version
java -version
terraform --version
git --version
```

### Step 2: Set Up Python Virtual Environment

```bash
# Navigate to your project directory
cd /Users/iamaditya010/Documents/Code/contextq

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PySpark and dependencies
pip install pyspark==3.4.1
pip install delta-spark==2.4.0
pip install pandas==2.1.3
pip install numpy==1.24.3

# Install testing tools
pip install pytest==7.4.3
pip install pytest-cov==4.1.0

# Install linting tools
pip install flake8==6.1.0
pip install black==23.11.0

# Install other utilities
pip install python-dotenv==1.0.0
pip install pyyaml==6.0.1

# Verify PySpark installation
python -c "import pyspark; print(f'PySpark {pyspark.__version__} installed successfully!')"
```

### Step 3: Configure Environment Variables

```bash
# Create .env file for local development
cat > .env << 'EOF'
# Local Development Environment Variables
ENVIRONMENT=local

# Azure Configuration (will be filled after Azure setup)
AZURE_SUBSCRIPTION_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# Storage Configuration
STORAGE_ACCOUNT_NAME=
STORAGE_ACCOUNT_KEY=
CONTAINER_NAME=data-pipeline

# Databricks Configuration (will be filled later)
DATABRICKS_HOST=
DATABRICKS_TOKEN=

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000

# Paths for local development
LOCAL_BRONZE_PATH=./data/bronze
LOCAL_SILVER_PATH=./data/silver
LOCAL_GOLD_PATH=./data/gold
LOCAL_MODELS_PATH=./data/models
EOF

# Add .env to .gitignore (IMPORTANT - don't commit secrets!)
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "*.log" >> .gitignore
echo "data/" >> .gitignore
echo ".DS_Store" >> .gitignore
```

---

## Part 3: Create GitHub Repository

### Option A: Using GitHub CLI (Recommended)

```bash
# 1. Install GitHub CLI
brew install gh

# 2. Authenticate with GitHub
gh auth login
# Follow the prompts to authenticate

# 3. Create a new public repository
gh repo create data-ai-pipeline \
  --public \
  --description "Azure-based ETL and ML Pipeline with CI/CD" \
  --gitignore Python \
  --license MIT

# 4. Clone the repository
cd ~/Documents/Code
gh repo clone YOUR_GITHUB_USERNAME/data-ai-pipeline

# 5. Copy files from contextq to new repo
cd data-ai-pipeline
cp -r /Users/iamaditya010/Documents/Code/contextq/AZURE_ARCHITECTURE_PLAN.md .
cp -r /Users/iamaditya010/Documents/Code/contextq/IMPLEMENTATION_GUIDE.md .
cp -r /Users/iamaditya010/Documents/Code/contextq/EXECUTIVE_SUMMARY.md .
```

### Option B: Using GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `data-ai-pipeline`
3. Description: "Azure-based ETL and ML Pipeline with CI/CD"
4. Select **Public**
5. Add .gitignore template: **Python**
6. Add license: **MIT License**
7. Click **Create repository**

Then clone it:
```bash
cd ~/Documents/Code
git clone https://github.com/YOUR_USERNAME/data-ai-pipeline.git
cd data-ai-pipeline
```

### Initialize Git Repository Structure

```bash
# Create project structure
mkdir -p src/{utils,data_quality}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p terraform/modules/{storage,databricks,data_factory,aks,networking,monitoring}
mkdir -p .github/workflows
mkdir -p docker
mkdir -p scripts
mkdir -p config
mkdir -p notebooks
mkdir -p data/{bronze,silver,gold,models}

# Create empty __init__.py files for Python packages
touch src/__init__.py
touch src/utils/__init__.py
touch src/data_quality/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Verify structure
tree -L 2 -I 'venv|__pycache__|*.pyc'
```

---

## Part 4: Local Development Setup

### Step 1: Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
# Core dependencies
pyspark==3.4.1
delta-spark==2.4.0
pandas==2.1.3
numpy==1.24.3

# Azure SDKs (for later Azure integration)
azure-storage-file-datalake==12.14.0
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0

# ML and MLflow
mlflow==2.9.2
scikit-learn==1.3.2

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Linting and formatting
flake8==6.1.0
black==23.11.0
mypy==1.7.1

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
click==8.1.7

# Development
ipython==8.18.1
jupyter==1.0.0
EOF

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Create pytest Configuration

```bash
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
EOF
```

### Step 3: Create Configuration Files

```bash
# Development config
cat > config/local.yaml << 'EOF'
environment: local

paths:
  bronze: ./data/bronze
  silver: ./data/silver
  gold: ./data/gold
  models: ./data/models

spark:
  app_name: "Data Pipeline - Local"
  master: "local[*]"
  executor_memory: "2g"
  driver_memory: "2g"

etl:
  batch_size: 1000
  partition_column: "processing_date"
  
ml:
  train_split: 0.8
  test_split: 0.2
  random_seed: 42

mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "/local-ml-pipeline"
EOF

# Production config (template)
cat > config/prod.yaml << 'EOF'
environment: production

paths:
  bronze: "abfss://data-pipeline@{storage_account}.dfs.core.windows.net/bronze"
  silver: "abfss://data-pipeline@{storage_account}.dfs.core.windows.net/silver"
  gold: "abfss://data-pipeline@{storage_account}.dfs.core.windows.net/gold"
  models: "abfss://data-pipeline@{storage_account}.dfs.core.windows.net/models"

spark:
  app_name: "Data Pipeline - Production"
  executor_memory: "8g"
  driver_memory: "4g"

etl:
  batch_size: 10000
  partition_column: "processing_date"
  
ml:
  train_split: 0.8
  test_split: 0.2
  random_seed: 42

mlflow:
  tracking_uri: "https://mlflow.internal.company.com"
  experiment_name: "/prod-ml-pipeline"
EOF
```

### Step 4: Create Helper Utilities

```bash
cat > src/utils/config.py << 'EOF'
"""Configuration management utilities"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration loader"""
    
    def __init__(self, env: str = "local"):
        self.env = env
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_file = config_dir / f"{self.env}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default=None):
        """Get configuration value by key (supports nested keys with dot notation)"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def __getitem__(self, key: str):
        """Allow dict-like access"""
        return self.get(key)


def load_config(env: str = None) -> Config:
    """Load configuration based on environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "local")
    
    return Config(env)
EOF

cat > src/utils/logger.py << 'EOF'
"""Logging utilities"""
import logging
import sys
from pathlib import Path


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logger with console and file handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / f"{name}.log")
    file_handler.setLevel(level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger
EOF
```

---

## Part 5: Quick Start - Local Development

### Step 1: Generate Sample Data

```bash
cat > scripts/generate_sample_data.py << 'EOF'
"""Generate sample log data for testing"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import gzip
import json
from pathlib import Path


def generate_log_data(num_rows: int = 10000) -> pd.DataFrame:
    """Generate sample log data"""
    
    np.random.seed(42)
    random.seed(42)
    
    # Generate timestamps
    start_date = datetime(2025, 10, 1)
    timestamps = [
        start_date + timedelta(minutes=random.randint(0, 43200))
        for _ in range(num_rows)
    ]
    
    # User IDs (with some nulls)
    user_ids = [
        f"user_{random.randint(1, 1000)}" if random.random() > 0.05 else None
        for _ in range(num_rows)
    ]
    
    # Event types
    event_types = ['page_view', 'click', 'purchase', 'logout', 'login', 'search']
    events = [random.choice(event_types) for _ in range(num_rows)]
    
    # Numeric features
    durations = np.random.exponential(scale=30, size=num_rows)
    values = np.random.normal(loc=50, scale=20, size=num_rows)
    high_value = [1 if v > 60 else 0 for v in values]
    
    # Session IDs
    session_ids = [f"session_{random.randint(1, 5000)}" for _ in range(num_rows)]
    
    # Device types
    devices = ['mobile', 'desktop', 'tablet']
    device_types = [random.choice(devices) for _ in range(num_rows)]
    
    df = pd.DataFrame({
        'user_id': user_ids,
        'session_id': session_ids,
        'event_type': events,
        'event_time': timestamps,
        'duration_seconds': durations,
        'value': values,
        'high_value': high_value,
        'device_type': device_types,
        'user_agent': ['Mozilla/5.0'] * num_rows,
        'ip_address': [f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}" 
                       for _ in range(num_rows)]
    })
    
    return df


def main():
    # Create output directories
    Path("data/bronze/logs/date=2025-10-16").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print("Generating sample data...")
    df = generate_log_data(num_rows=10000)
    
    # Save compressed for bronze layer
    output_file = "data/bronze/logs/date=2025-10-16/raw_logs.csv.gz"
    with gzip.open(output_file, 'wt', encoding='utf-8') as f:
        df.to_csv(f, index=False)
    print(f"✓ Saved {len(df)} rows to {output_file}")
    
    # Save smaller sample for tests
    sample_df = df.head(100)
    test_file = "tests/fixtures/sample_logs.csv"
    sample_df.to_csv(test_file, index=False)
    print(f"✓ Saved {len(sample_df)} rows to {test_file}")
    
    # Print statistics
    print(f"\nData Statistics:")
    print(f"  Total rows: {len(df)}")
    print(f"  Null user_ids: {df['user_id'].isna().sum()}")
    print(f"  High-value events: {df['high_value'].sum()}")
    print(f"  Date range: {df['event_time'].min()} to {df['event_time'].max()}")
    print(f"\nEvent type distribution:")
    print(df['event_type'].value_counts())


if __name__ == "__main__":
    main()
EOF

# Run the script
python scripts/generate_sample_data.py
```

### Step 2: Commit Initial Setup

```bash
# Stage all files
git add .

# Create initial commit
git commit -m "Initial project setup with local development environment"

# Push to GitHub
git push -u origin main
```

---

## Next Steps

Now you have:
✅ Azure account configured  
✅ Local development environment set up  
✅ GitHub repository created  
✅ Project structure initialized  
✅ Sample data generated  

### What's Next?

1. **Implement ETL Pipeline** (I'll help you create this next)
2. **Implement ML Pipeline** 
3. **Write Unit Tests**
4. **Test Everything Locally**
5. **Set Up Azure Resources**
6. **Deploy to Azure**
7. **Configure CI/CD**

Would you like me to help you with the next step (implementing the ETL pipeline)?

---

## Verification Checklist

Before proceeding, verify:

```bash
# Check Azure CLI
az account show

# Check Python environment
python --version
which python  # Should be in your venv

# Check PySpark
python -c "import pyspark; print(pyspark.__version__)"

# Check project structure
ls -la

# Check Git remote
git remote -v

# Check sample data
ls -lh data/bronze/logs/date=2025-10-16/
```

All checks passed? Great! You're ready to start development! 🚀

