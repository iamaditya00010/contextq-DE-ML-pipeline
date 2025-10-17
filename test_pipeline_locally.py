#!/usr/bin/env python3
"""
Simple Pipeline Execution Script
Author: Aditya Padhi

This script executes the data pipeline locally to verify it works,
then provides instructions for Databricks execution.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - SUCCESS")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"✅ {description} - EXISTS")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def main():
    print("=" * 70)
    print("🚀 SIMPLE PIPELINE EXECUTION VERIFICATION")
    print("=" * 70)
    
    # Check if we're in the right directory
    if not Path("logs/OpenSSH_2k.log").exists():
        print("❌ Error: logs/OpenSSH_2k.log not found!")
        print("Please run this script from the project root directory.")
        return False
    
    # Check Python environment
    print(f"\n🐍 Python Environment:")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Check required files
    print(f"\n📁 Checking Required Files:")
    required_files = [
        ("logs/OpenSSH_2k.log", "Source log file"),
        ("scripts/run_pipeline_pandas.py", "Pandas pipeline script"),
        ("scripts/ml_anomaly_detection.py", "ML anomaly detection script")
    ]
    
    all_files_exist = True
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Missing required files. Please ensure all files are present.")
        return False
    
    # Create data directories
    print(f"\n📂 Creating Data Directories:")
    directories = ["data/bronze", "data/silver", "data/gold", "data/ml_output", "models"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Run the pipeline
    print(f"\n🔄 EXECUTING DATA PIPELINE:")
    
    # Step 1: Run Pandas pipeline
    if not run_command("python scripts/run_pipeline_pandas.py", "Running Pandas Pipeline"):
        print("❌ Pandas pipeline failed!")
        return False
    
    # Step 2: Run ML anomaly detection
    if not run_command("python scripts/ml_anomaly_detection.py", "Running ML Anomaly Detection"):
        print("❌ ML pipeline failed!")
        return False
    
    # Verify outputs
    print(f"\n📊 VERIFYING OUTPUTS:")
    output_files = [
        ("data/bronze/raw_logs.parquet", "Bronze layer data"),
        ("data/silver/structured_logs.json", "Silver layer data"),
        ("data/gold/openssh_logs_final.csv", "Gold layer data"),
        ("data/ml_output/anomaly_predictions.csv", "ML predictions"),
        ("models/anomaly_model.pkl", "Trained ML model")
    ]
    
    all_outputs_exist = True
    for file_path, description in output_files:
        if not check_file_exists(file_path, description):
            all_outputs_exist = False
    
    if all_outputs_exist:
        print(f"\n🎉 PIPELINE EXECUTION SUCCESSFUL!")
        print(f"✅ All data layers processed successfully")
        print(f"✅ ML model trained and saved")
        print(f"✅ Anomaly detection completed")
        
        # Show file sizes
        print(f"\n📈 OUTPUT FILE SIZES:")
        for file_path, description in output_files:
            if Path(file_path).exists():
                size = Path(file_path).stat().st_size
                print(f"  {description}: {size:,} bytes")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. ✅ Local pipeline works correctly")
        print(f"2. 🔧 Fix Databricks job execution in GitHub Actions")
        print(f"3. 📊 Verify data in Azure Storage after Databricks execution")
        print(f"4. 🎯 Test manual Databricks job execution")
        
        return True
    else:
        print(f"\n❌ PIPELINE EXECUTION FAILED!")
        print(f"Some output files are missing.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
