"""
Bronze Layer: Raw Load Script
==============================
This script loads raw OpenSSH log files and saves them as-is to Parquet format.
No transformations are applied - this is the raw data layer.

Author: Aditya Padhi

Input: logs/OpenSSH_2k.log (raw text log file)
Output: data/bronze/raw_logs.parquet (raw data in Parquet format)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import monotonically_increasing_id
from datetime import datetime
import os


def create_spark_session():
    """Create Spark session for Bronze layer processing"""
    return SparkSession.builder \
        .appName("Bronze Layer - Raw Load") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()


def load_raw_logs(spark, input_path):
    """
    Load raw log file as-is
    
    Args:
        spark: SparkSession
        input_path: Path to raw log file
        
    Returns:
        DataFrame with raw log lines
    """
    print(f"[BRONZE] Reading raw log file: {input_path}")
    
    # Read as text file (one line = one record)
    raw_df = spark.read.text(input_path)
    
    # Add LineId and metadata
    bronze_df = raw_df \
        .withColumn("LineId", monotonically_increasing_id() + 1) \
        .withColumn("ingestion_timestamp", spark.sql("current_timestamp()")) \
        .withColumn("source_file", spark.sql(f"string('{input_path}')")) \
        .select("LineId", "value", "ingestion_timestamp", "source_file")
    
    # Rename 'value' to 'raw_log'
    bronze_df = bronze_df.withColumnRenamed("value", "raw_log")
    
    record_count = bronze_df.count()
    print(f"[BRONZE] Total records loaded: {record_count}")
    
    return bronze_df


def save_to_bronze(df, output_path):
    """
    Save raw data to Bronze layer as Parquet
    
    Args:
        df: DataFrame with raw logs
        output_path: Path to save Parquet file
    """
    print(f"[BRONZE] Saving to Bronze layer: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save as Parquet (no partitioning, just raw data)
    df.write \
        .mode("overwrite") \
        .parquet(output_path)
    
    print(f"[BRONZE] Successfully saved {df.count()} records to Bronze layer")


def main():
    """Main execution for Bronze layer"""
    
    print("=" * 70)
    print("BRONZE LAYER - RAW LOAD")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Define paths
        input_log_file = "logs/OpenSSH_2k.log"
        bronze_output = "data/bronze/raw_logs.parquet"
        
        # Check if input file exists
        if not os.path.exists(input_log_file):
            print(f"[ERROR] Input file not found: {input_log_file}")
            return
        
        # Load raw logs
        bronze_df = load_raw_logs(spark, input_log_file)
        
        # Show sample
        print("\n[BRONZE] Sample data (first 3 records):")
        bronze_df.show(3, truncate=False)
        
        # Show schema
        print("[BRONZE] Schema:")
        bronze_df.printSchema()
        
        # Save to Bronze layer
        save_to_bronze(bronze_df, bronze_output)
        
        print()
        print("=" * 70)
        print("BRONZE LAYER - COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Output: {bronze_output}")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n[ERROR] Bronze layer processing failed: {str(e)}")
        raise
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

