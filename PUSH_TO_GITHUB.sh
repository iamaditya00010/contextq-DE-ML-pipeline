#!/bin/bash

# Quick GitHub Push Script
# Run this after creating your GitHub repository

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    PUSH TO GITHUB                                    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Not in project directory"
    exit 1
fi

echo "Step 1: Creating commit..."
git commit -m "Initial commit: Complete 3-layer data pipeline with ML anomaly detection

Features:
- Bronze layer: Raw log loading to Parquet
- Silver layer: Parsing, transformation, quality checks (4 validations)
- Gold layer: Combined datetime, final curated CSV
- ML Model: Isolation Forest anomaly detection (170 anomalies detected)
- Complete PySpark implementation (Databricks-ready)
- Pandas version for local testing
- Comprehensive documentation

Tech Stack: PySpark, Pandas, scikit-learn, Azure-ready"

echo "✅ Commit created!"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Step 2: Now you need to:"
echo ""
echo "1️⃣  Go to: https://github.com/new"
echo ""
echo "2️⃣  Create repository:"
echo "    - Name: openssh-data-pipeline"
echo "    - Description: 3-Layer Data Pipeline with ML Anomaly Detection"
echo "    - Public or Private (your choice)"
echo "    - DON'T add README or .gitignore (we have them)"
echo ""
echo "3️⃣  Copy your repository URL (will look like):"
echo "    https://github.com/YOUR_USERNAME/openssh-data-pipeline.git"
echo ""
echo "4️⃣  Run these commands (replace YOUR_USERNAME):"
echo ""
echo "    git remote add origin https://github.com/YOUR_USERNAME/openssh-data-pipeline.git"
echo "    git branch -M main"
echo "    git push -u origin main"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tip: If git asks for password, use a Personal Access Token"
echo "   Create one at: https://github.com/settings/tokens"
echo ""
echo "📚 Full guide: Read GITHUB_PUSH_GUIDE.md"
echo ""

