"""
Silver Layer: Transformation and Quality Script
===============================================
This script reads Bronze layer data, parses OpenSSH log format,
extracts structured fields, applies quality checks and transformations,
and saves to Silver layer as JSON.

Author: Aditya Padhi

Input: data/bronze/raw_logs.parquet
Output: data/silver/structured_logs.json
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    regexp_extract, split, trim, col, when, length,
    regexp_replace, udf, lit
)
from pyspark.sql.types import StringType
from datetime import datetime
import os


def create_spark_session():
    """Create Spark session for Silver layer processing"""
    return SparkSession.builder \
        .appName("Silver Layer - Parse and Transform") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()


def load_bronze_data(spark, bronze_path):
    """
    Load data from Bronze layer
    
    Args:
        spark: SparkSession
        bronze_path: Path to Bronze Parquet file
        
    Returns:
        DataFrame with Bronze data
    """
    print(f"[SILVER] Loading Bronze data from: {bronze_path}")
    
    df = spark.read.parquet(bronze_path)
    record_count = df.count()
    
    print(f"[SILVER] Bronze records loaded: {record_count}")
    
    return df


def parse_openssh_logs(df):
    """
    Parse OpenSSH log format and extract structured fields
    
    Log format: Dec 10 06:55:46 LabSZ sshd[24200]: <content>
    
    Extracted fields:
    - Date (Month): Dec
    - Day: 10
    - Time: 06:55:46
    - Component: LabSZ
    - Pid: 24200 (extracted from sshd[24200])
    - Content: The actual log message
    
    Args:
        df: DataFrame with raw logs
        
    Returns:
        DataFrame with parsed fields
    """
    print("[SILVER] Parsing log entries...")
    
    # Extract Date (Month) - First token
    parsed_df = df.withColumn(
        "Date",
        trim(split(col("raw_log"), " ").getItem(0))
    )
    
    # Extract Day - Second token
    parsed_df = parsed_df.withColumn(
        "Day",
        trim(split(col("raw_log"), " ").getItem(1))
    )
    
    # Extract Time - Third token
    parsed_df = parsed_df.withColumn(
        "Time",
        trim(split(col("raw_log"), " ").getItem(2))
    )
    
    # Extract Component - Fourth token
    parsed_df = parsed_df.withColumn(
        "Component",
        trim(split(col("raw_log"), " ").getItem(3))
    )
    
    # Extract Pid from pattern sshd[12345]:
    # Pattern: find number inside square brackets
    parsed_df = parsed_df.withColumn(
        "Pid",
        regexp_extract(col("raw_log"), r"sshd\[(\d+)\]", 1)
    )
    
    # Extract Content - everything after sshd[pid]:
    # Split by ': ' and take everything after first occurrence
    parsed_df = parsed_df.withColumn(
        "Content",
        regexp_extract(col("raw_log"), r"sshd\[\d+\]:\s*(.+)", 1)
    )
    
    print(f"[SILVER] Parsing complete")
    
    return parsed_df


def generate_event_templates(df):
    """
    Generate EventId and EventTemplate by pattern matching
    
    Common SSH log patterns:
    - Invalid user -> E13
    - Failed password -> E10
    - Connection closed -> E2
    - etc.
    
    Args:
        df: DataFrame with Content column
        
    Returns:
        DataFrame with EventId and EventTemplate columns
    """
    print("[SILVER] Generating event templates...")
    
    # Define event patterns and their IDs
    df = df.withColumn(
        "EventId",
        when(col("Content").contains("reverse mapping checking"), "E27")
        .when(col("Content").contains("Invalid user"), "E13")
        .when(col("Content").contains("input_userauth_request: invalid user"), "E12")
        .when(col("Content").contains("check pass; user unknown"), "E21")
        .when(col("Content").contains("authentication failure"), "E19")
        .when(col("Content").contains("Failed password for invalid user"), "E10")
        .when(col("Content").contains("Connection closed by"), "E2")
        .when(col("Content").contains("Received disconnect"), "E24")
        .when(col("Content").contains("Failed password for"), "E9")
        .when(col("Content").contains("Accepted password for"), "E18")
        .when(col("Content").contains("pam_unix(sshd:session): session opened"), "E7")
        .when(col("Content").contains("pam_unix(sshd:session): session closed"), "E8")
        .otherwise("E0")
    )
    
    # Generate EventTemplate - replace variables with <*>
    df = df.withColumn(
        "EventTemplate",
        # Replace IP addresses
        regexp_replace(col("Content"), r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "<*>")
    )
    
    df = df.withColumn(
        "EventTemplate",
        # Replace port numbers
        regexp_replace(col("EventTemplate"), r"\bport\s+\d+\b", "port <*>")
    )
    
    df = df.withColumn(
        "EventTemplate",
        # Replace usernames (word after "user")
        regexp_replace(col("EventTemplate"), r"\buser\s+\w+", "user <*>")
    )
    
    df = df.withColumn(
        "EventTemplate",
        # Replace UIDs
        regexp_replace(col("EventTemplate"), r"\buid=\d+", "uid=<*>")
    )
    
    df = df.withColumn(
        "EventTemplate",
        # Replace EUIDs
        regexp_replace(col("EventTemplate"), r"\beuid=\d+", "euid=<*>")
    )
    
    df = df.withColumn(
        "EventTemplate",
        # Replace hostnames/domains
        regexp_replace(col("EventTemplate"), r"for\s+[\w\.\-]+\s+\[", "for <*> [")
    )
    
    df = df.withColumn(
        "EventTemplate",
        # Replace disconnect codes
        regexp_replace(col("EventTemplate"), r"from\s+<\*>:\s+\d+:", "from <*>: <*>:")
    )
    
    print("[SILVER] Event templates generated")
    
    return df


def apply_quality_checks(df):
    """
    DATA QUALITY CHECKS
    ===================
    Apply various quality checks and validations:
    
    1. Completeness Check: Ensure required fields are not null/empty
    2. Format Validation: Validate time format, PID is numeric
    3. Consistency Check: Ensure Date values are valid months
    4. Data Standardization: Trim whitespace, standardize formats
    
    Args:
        df: DataFrame to validate
        
    Returns:
        DataFrame with quality flags and cleaned data
    """
    print("[SILVER] Applying quality checks...")
    
    # QUALITY CHECK 1: Completeness - Flag records with missing critical fields
    df = df.withColumn(
        "quality_completeness",
        when(
            (col("Date").isNull()) | (col("Date") == "") |
            (col("Day").isNull()) | (col("Day") == "") |
            (col("Time").isNull()) | (col("Time") == "") |
            (col("Content").isNull()) | (col("Content") == ""),
            "FAIL"
        ).otherwise("PASS")
    )
    
    # QUALITY CHECK 2: Format Validation - Validate time format (HH:MM:SS)
    df = df.withColumn(
        "quality_time_format",
        when(
            col("Time").rlike(r"^\d{2}:\d{2}:\d{2}$"),
            "PASS"
        ).otherwise("FAIL")
    )
    
    # QUALITY CHECK 3: PID Validation - Ensure PID is numeric and not empty
    df = df.withColumn(
        "quality_pid_valid",
        when(
            (col("Pid").isNull()) | (col("Pid") == "") | (~col("Pid").rlike(r"^\d+$")),
            "FAIL"
        ).otherwise("PASS")
    )
    
    # QUALITY CHECK 4: Month Validation - Ensure Date is valid month abbreviation
    valid_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df = df.withColumn(
        "quality_month_valid",
        when(
            col("Date").isin(valid_months),
            "PASS"
        ).otherwise("FAIL")
    )
    
    # TRANSFORMATION 1: Standardize Day (ensure 2 digits with leading zero)
    df = df.withColumn(
        "Day",
        when(length(col("Day")) == 1, regexp_replace(col("Day"), "^", "0"))
        .otherwise(col("Day"))
    )
    
    # TRANSFORMATION 2: Trim all string fields
    string_columns = ["Date", "Day", "Time", "Component", "Pid", "Content", 
                      "EventId", "EventTemplate"]
    for col_name in string_columns:
        if col_name in df.columns:
            df = df.withColumn(col_name, trim(col(col_name)))
    
    # TRANSFORMATION 3: Create overall quality flag
    df = df.withColumn(
        "overall_quality",
        when(
            (col("quality_completeness") == "PASS") &
            (col("quality_time_format") == "PASS") &
            (col("quality_pid_valid") == "PASS") &
            (col("quality_month_valid") == "PASS"),
            "PASS"
        ).otherwise("FAIL")
    )
    
    # Count quality issues
    total_records = df.count()
    failed_records = df.filter(col("overall_quality") == "FAIL").count()
    passed_records = total_records - failed_records
    
    print(f"[SILVER] Quality Check Results:")
    print(f"  - Total records: {total_records}")
    print(f"  - Passed quality: {passed_records} ({passed_records/total_records*100:.1f}%)")
    print(f"  - Failed quality: {failed_records} ({failed_records/total_records*100:.1f}%)")
    
    return df


def save_to_silver(df, output_path):
    """
    Save transformed data to Silver layer as JSON
    
    Args:
        df: Transformed DataFrame
        output_path: Path to save JSON file
    """
    print(f"[SILVER] Saving to Silver layer: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Select final columns for Silver layer
    silver_df = df.select(
        "LineId",
        "Date",
        "Day",
        "Time",
        "Component",
        "Pid",
        "Content",
        "EventId",
        "EventTemplate",
        "overall_quality",
        "ingestion_timestamp"
    )
    
    # Save as JSON (single line per record)
    silver_df.write \
        .mode("overwrite") \
        .json(output_path)
    
    print(f"[SILVER] Successfully saved {silver_df.count()} records to Silver layer")


def main():
    """Main execution for Silver layer"""
    
    print("=" * 70)
    print("SILVER LAYER - PARSE, TRANSFORM & QUALITY CHECKS")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Define paths
        bronze_input = "data/bronze/raw_logs.parquet"
        silver_output = "data/silver/structured_logs.json"
        
        # Check if input exists
        if not os.path.exists(bronze_input):
            print(f"[ERROR] Bronze data not found: {bronze_input}")
            print("[ERROR] Please run bronze/raw_load.py first")
            return
        
        # Load Bronze data
        bronze_df = load_bronze_data(spark, bronze_input)
        
        # Parse log entries
        parsed_df = parse_openssh_logs(bronze_df)
        
        # Generate event templates
        enriched_df = generate_event_templates(parsed_df)
        
        # Apply quality checks and transformations
        validated_df = apply_quality_checks(enriched_df)
        
        # Show sample
        print("\n[SILVER] Sample transformed data (first 3 records):")
        validated_df.select(
            "LineId", "Date", "Day", "Time", "Component", "Pid", 
            "Content", "EventId", "overall_quality"
        ).show(3, truncate=False)
        
        # Show schema
        print("[SILVER] Schema:")
        validated_df.printSchema()
        
        # Save to Silver layer
        save_to_silver(validated_df, silver_output)
        
        print()
        print("=" * 70)
        print("SILVER LAYER - COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Output: {silver_output}")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n[ERROR] Silver layer processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

