#!/bin/bash

# Quick Start Script for Local Development Setup
# This script automates the local environment setup

set -e  # Exit on error

echo "🚀 Data & AI Pipeline - Quick Start Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if we're in the right directory
echo -e "${BLUE}Step 1: Checking directory...${NC}"
if [ ! -f "SETUP_GUIDE.md" ]; then
    echo -e "${YELLOW}Warning: SETUP_GUIDE.md not found. Are you in the project root?${NC}"
    exit 1
fi
echo -e "${GREEN}✓ In project directory${NC}"
echo ""

# Step 2: Check Python version
echo -e "${BLUE}Step 2: Checking Python version...${NC}"
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD=python3.10
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo -e "${GREEN}✓ Found: $PYTHON_VERSION${NC}"
echo ""

# Step 3: Create virtual environment
echo -e "${BLUE}Step 3: Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping...${NC}"
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Step 4: Activate virtual environment and install dependencies
echo -e "${BLUE}Step 4: Installing dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 5: Create project structure
echo -e "${BLUE}Step 5: Creating project structure...${NC}"
mkdir -p src/{utils,data_quality}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p data/{bronze,silver,gold,models}/logs/date=2025-10-16
mkdir -p scripts
mkdir -p config
mkdir -p logs

# Create __init__.py files
touch src/__init__.py
touch src/utils/__init__.py
touch src/data_quality/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

echo -e "${GREEN}✓ Project structure created${NC}"
echo ""

# Step 6: Create .gitignore
echo -e "${BLUE}Step 6: Creating .gitignore...${NC}"
cat > .gitignore << 'EOF'
# Python
venv/
*.pyc
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/

# Environment
.env
.env.local
*.log

# Data
data/
*.csv
*.csv.gz
*.parquet
*.json.gz

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Terraform
*.tfstate
*.tfstate.*
.terraform/
*.tfvars
!*.tfvars.example

# MLflow
mlruns/
mlartifacts/
EOF
echo -e "${GREEN}✓ .gitignore created${NC}"
echo ""

# Step 7: Verify Java installation (required for PySpark)
echo -e "${BLUE}Step 7: Checking Java installation...${NC}"
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}✓ Found: $JAVA_VERSION${NC}"
else
    echo -e "${YELLOW}⚠ Java not found. PySpark requires Java 8 or 11.${NC}"
    echo "Install with: brew install openjdk@11"
fi
echo ""

# Step 8: Test PySpark installation
echo -e "${BLUE}Step 8: Testing PySpark installation...${NC}"
$PYTHON_CMD -c "import pyspark; print('PySpark', pyspark.__version__, 'installed successfully!')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PySpark working${NC}"
else
    echo -e "${YELLOW}⚠ PySpark test failed. Check Java installation.${NC}"
fi
echo ""

# Step 9: Summary
echo "=========================================="
echo -e "${GREEN}✅ Local setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo "2. Generate sample data:"
echo -e "   ${YELLOW}python scripts/generate_sample_data.py${NC}"
echo ""
echo "3. Run ETL pipeline:"
echo -e "   ${YELLOW}python src/etl_pipeline.py --input data/bronze/logs/date=2025-10-16/raw_logs.csv.gz --output data/silver/logs_processed${NC}"
echo ""
echo "4. Run tests:"
echo -e "   ${YELLOW}pytest tests/unit/ -v${NC}"
echo ""
echo "Happy coding! 🎉"

