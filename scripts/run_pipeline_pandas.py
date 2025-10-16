"""
Master Pipeline Runner (Pandas Version for Local Testing)
==========================================================
This script runs the complete data pipeline using Pandas (no Java required).
The PySpark versions in bronze/, silver/, gold/ are for Azure Databricks.

This pandas version is for local testing only.

Usage:
    python scripts/run_pipeline_pandas.py
"""

import pandas as pd
import json
import os
import gzip
from datetime import datetime
from pathlib import Path


def print_header(message):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")


def bronze_layer():
    """Bronze Layer: Load raw logs to Parquet"""
    print_header("BRONZE LAYER - Raw Load")
    
    input_file = "logs/OpenSSH_2k.log"
    output_file = "data/bronze/raw_logs.parquet"
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return False
    
    # Read raw log file
    print(f"Reading: {input_file}")
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Create DataFrame
    df = pd.DataFrame({
        'LineId': range(1, len(lines) + 1),
        'raw_log': [line.strip() for line in lines],
        'ingestion_timestamp': pd.Timestamp.now(),
        'source_file': input_file
    })
    
    # Save as Parquet
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_parquet(output_file, index=False)
    
    print(f"Saved {len(df)} records to {output_file}")
    return True


def silver_layer():
    """Silver Layer: Parse and transform"""
    print_header("SILVER LAYER - Parse & Transform")
    
    input_file = "data/bronze/raw_logs.parquet"
    output_dir = "data/silver"
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return False
    
    # Read Bronze data
    print(f"Reading: {input_file}")
    df = pd.read_parquet(input_file)
    
    # Parse log entries
    print("Parsing log format...")
    df['parts'] = df['raw_log'].str.split(r'\s+', n=4)
    df['Date'] = df['parts'].str[0]
    df['Day'] = df['parts'].str[1]
    df['Time'] = df['parts'].str[2]
    df['Component'] = df['parts'].str[3]
    
    # Extract PID
    df['Pid'] = df['raw_log'].str.extract(r'sshd\[(\d+)\]')[0]
    
    # Extract Content
    df['Content'] = df['raw_log'].str.extract(r'sshd\[\d+\]:\s*(.+)')[0]
    
    # Generate EventId
    df['EventId'] = 'E0'
    df.loc[df['Content'].str.contains('reverse mapping checking', na=False), 'EventId'] = 'E27'
    df.loc[df['Content'].str.contains('Invalid user', na=False), 'EventId'] = 'E13'
    df.loc[df['Content'].str.contains('input_userauth_request: invalid user', na=False), 'EventId'] = 'E12'
    df.loc[df['Content'].str.contains('check pass; user unknown', na=False), 'EventId'] = 'E21'
    df.loc[df['Content'].str.contains('authentication failure', na=False), 'EventId'] = 'E19'
    df.loc[df['Content'].str.contains('Failed password for invalid user', na=False), 'EventId'] = 'E10'
    df.loc[df['Content'].str.contains('Connection closed by', na=False), 'EventId'] = 'E2'
    df.loc[df['Content'].str.contains('Received disconnect', na=False), 'EventId'] = 'E24'
    
    # Generate EventTemplate
    df['EventTemplate'] = df['Content'].str.replace(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<*>', regex=True)
    df['EventTemplate'] = df['EventTemplate'].str.replace(r'\bport\s+\d+\b', 'port <*>', regex=True)
    df['EventTemplate'] = df['EventTemplate'].str.replace(r'\buser\s+\w+', 'user <*>', regex=True)
    df['EventTemplate'] = df['EventTemplate'].str.replace(r'\buid=\d+', 'uid=<*>', regex=True)
    df['EventTemplate'] = df['EventTemplate'].str.replace(r'\beuid=\d+', 'euid=<*>', regex=True)
    
    # Quality checks
    print("Applying quality checks...")
    df['quality_completeness'] = 'PASS'
    df.loc[(df['Date'].isna()) | (df['Day'].isna()) | (df['Time'].isna()) | (df['Content'].isna()), 
           'quality_completeness'] = 'FAIL'
    
    df['quality_time_format'] = df['Time'].str.match(r'^\d{2}:\d{2}:\d{2}$').map({True: 'PASS', False: 'FAIL'})
    df['quality_pid_valid'] = df['Pid'].notna().map({True: 'PASS', False: 'FAIL'})
    
    valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df['quality_month_valid'] = df['Date'].isin(valid_months).map({True: 'PASS', False: 'FAIL'})
    
    df['overall_quality'] = 'PASS'
    df.loc[(df['quality_completeness'] == 'FAIL') | 
           (df['quality_time_format'] == 'FAIL') | 
           (df['quality_pid_valid'] == 'FAIL') | 
           (df['quality_month_valid'] == 'FAIL'), 
           'overall_quality'] = 'FAIL'
    
    # Standardize Day to 2 digits
    df['Day'] = df['Day'].str.zfill(2)
    
    passed = (df['overall_quality'] == 'PASS').sum()
    failed = (df['overall_quality'] == 'FAIL').sum()
    print(f"Quality: {passed} passed, {failed} failed")
    
    # Select final columns
    silver_df = df[['LineId', 'Date', 'Day', 'Time', 'Component', 'Pid', 
                    'Content', 'EventId', 'EventTemplate', 'overall_quality', 'ingestion_timestamp']]
    
    # Save as JSON
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'structured_logs.json')
    silver_df.to_json(output_file, orient='records', lines=True)
    
    print(f"Saved {len(silver_df)} records to {output_file}")
    return True


def gold_layer():
    """Gold Layer: Final curated data"""
    print_header("GOLD LAYER - Final Curated")
    
    input_file = "data/silver/structured_logs.json"
    output_dir = "data/gold"
    output_file = os.path.join(output_dir, "openssh_logs_final.csv")
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return False
    
    # Read Silver data
    print(f"Reading: {input_file}")
    df = pd.read_json(input_file, lines=True)
    
    # Filter quality data
    print("Filtering quality data...")
    total_before = len(df)
    df = df[df['overall_quality'] == 'PASS']
    total_after = len(df)
    print(f"Kept {total_after}/{total_before} quality-passed records")
    
    # Combine datetime
    print("Creating datetime column...")
    df['datetime'] = df['Day'].astype(str) + '-' + df['Date'].astype(str) + '-2024 : ' + df['Time'].astype(str)
    
    # Select final columns (remove Date, Day, Time)
    gold_df = df[['LineId', 'datetime', 'Component', 'Pid', 'EventId', 'EventTemplate', 'Content']]
    gold_df = gold_df.sort_values('LineId')
    
    # Save as CSV
    os.makedirs(output_dir, exist_ok=True)
    gold_df.to_csv(output_file, index=False)
    
    print(f"Saved {len(gold_df)} records to {output_file}")
    
    # Show sample
    print("\nSample data (first 3 records):")
    print(gold_df.head(3).to_string(index=False))
    
    return True


def main():
    """Main execution"""
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  OpenSSH Log Processing Pipeline (Pandas Version)".center(78) + "█")
    print("█" + "  Bronze → Silver → Gold".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    start_time = datetime.now()
    print(f"\nPipeline started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nNote: This is the Pandas version for local testing.")
    print("      PySpark versions are in scripts/bronze/, silver/, gold/ for Databricks.\n")
    
    success = True
    
    # Run Bronze
    if not bronze_layer():
        success = False
    
    # Run Silver
    if success:
        if not silver_layer():
            success = False
    
    # Run Gold
    if success:
        if not gold_layer():
            success = False
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("  PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Start Time:    {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End Time:      {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:      {duration}")
    print(f"Status:        {'SUCCESS' if success else 'FAILED'}")
    print("=" * 80)
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print("\nOutput locations:")
        print("  Bronze: data/bronze/raw_logs.parquet")
        print("  Silver: data/silver/structured_logs.json")
        print("  Gold:   data/gold/openssh_logs_final.csv")
        print("\n")
    else:
        print("\n⚠️ Pipeline completed with errors.\n")


if __name__ == "__main__":
    main()

