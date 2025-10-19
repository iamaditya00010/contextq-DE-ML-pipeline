"""
Convert raw log files to Bronze layer (Parquet format)

This script:
1. Reads raw application log files (.log or .log.gz)
2. Parses the pipe-delimited format
3. Converts to structured DataFrame
4. Saves as Parquet in Bronze layer
5. Logs the process to logs/export.log
"""

import gzip
from pathlib import Path
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType


def setup_logging(log_file: str = "logs/export.log"):
    """Setup logging to file"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def log_message(log_file: Path, message: str):
    """Write message to log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def create_spark_session():
    """Create Spark session for local processing"""
    return SparkSession.builder \
        .appName("Raw to Bronze Converter") \
        .master("local[*]") \
        .config("spark.sql.session.timeZone", "UTC") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()


def parse_raw_logs(spark, raw_log_path: str, log_file: Path):
    """
    Parse raw log files and convert to structured DataFrame
    
    Log format:
    TIMESTAMP | LEVEL | user_id | session_id | event_type | method | endpoint | 
    status | response_time | duration | value | high_value | device | browser | os | ip
    """
    
    log_message(log_file, f"Reading raw log file: {raw_log_path}")
    
    # Read raw log file as text
    raw_df = spark.read.text(raw_log_path)
    
    log_message(log_file, f"Total raw entries: {raw_df.count()}")
    
    # Split by pipe delimiter and extract fields
    parsed_df = raw_df.select(
        F.split(F.col("value"), r" \| ").alias("fields")
    ).select(
        F.trim(F.col("fields")[0]).alias("timestamp_raw"),
        F.trim(F.col("fields")[1]).alias("log_level"),
        F.trim(F.col("fields")[2]).alias("user_id"),
        F.trim(F.col("fields")[3]).alias("session_id"),
        F.trim(F.col("fields")[4]).alias("event_type"),
        F.trim(F.col("fields")[5]).alias("http_method"),
        F.trim(F.col("fields")[6]).alias("endpoint"),
        F.trim(F.col("fields")[7]).alias("status_code_raw"),
        F.trim(F.col("fields")[8]).alias("response_time_raw"),
        F.trim(F.col("fields")[9]).alias("duration_raw"),
        F.trim(F.col("fields")[10]).alias("value_raw"),
        F.trim(F.col("fields")[11]).alias("high_value"),
        F.trim(F.col("fields")[12]).alias("device"),
        F.trim(F.col("fields")[13]).alias("browser"),
        F.trim(F.col("fields")[14]).alias("os"),
        F.trim(F.col("fields")[15]).alias("ip_address")
    )
    
    # Convert data types and clean fields
    bronze_df = parsed_df \
        .withColumn("event_timestamp", F.to_timestamp("timestamp_raw", "yyyy-MM-dd HH:mm:ss.SSS")) \
        .withColumn("status_code", F.col("status_code_raw").cast(IntegerType())) \
        .withColumn("response_time_ms", 
                   F.regexp_replace("response_time_raw", "ms", "").cast(IntegerType())) \
        .withColumn("duration_seconds", 
                   F.regexp_replace("duration_raw", "s", "").cast("double")) \
        .withColumn("transaction_value", 
                   F.regexp_replace("value_raw", r"[\$]", "").cast("double")) \
        .withColumn("is_high_value", F.col("high_value").cast(IntegerType())) \
        .withColumn("ingestion_timestamp", F.current_timestamp()) \
        .withColumn("source_file", F.lit(raw_log_path))
    
    # Select final columns for bronze layer
    bronze_final = bronze_df.select(
        "event_timestamp",
        "log_level",
        "user_id",
        "session_id",
        "event_type",
        "http_method",
        "endpoint",
        "status_code",
        "response_time_ms",
        "duration_seconds",
        "transaction_value",
        "is_high_value",
        "device",
        "browser",
        "os",
        "ip_address",
        "ingestion_timestamp",
        "source_file"
    )
    
    log_message(log_file, f"Parsed entries: {bronze_final.count()}")
    log_message(log_file, "Schema created with proper data types")
    
    return bronze_final


def save_to_bronze(df, output_path: str, log_file: Path):
    """Save DataFrame to Bronze layer as Parquet"""
    
    log_message(log_file, f"Writing to Bronze layer: {output_path}")
    
    # Save as Parquet (partitioned by date for efficient querying)
    df.withColumn("partition_date", F.to_date("event_timestamp")) \
        .write \
        .mode("overwrite") \
        .partitionBy("partition_date") \
        .parquet(output_path)
    
    log_message(log_file, f"Successfully wrote {df.count()} records to Bronze layer")
    log_message(log_file, f"Format: Parquet (partitioned by date)")


def main():
    """Main execution"""
    
    # Setup logging
    log_file = setup_logging("logs/export.log")
    
    log_message(log_file, "=" * 70)
    log_message(log_file, "RAW TO BRONZE CONVERSION - STARTED")
    log_message(log_file, "=" * 70)
    
    try:
        # Create Spark session
        log_message(log_file, "Creating Spark session...")
        spark = create_spark_session()
        log_message(log_file, "Spark session created")
        
        # Define paths
        raw_log_path = "data/bronze/logs/date=2025-10-16/application.log.gz"
        bronze_output_path = "data/bronze/structured"
        
        # Check if raw file exists
        if not Path(raw_log_path).exists():
            log_message(log_file, f"❌ ERROR: Raw log file not found: {raw_log_path}")
            return
        
        # Parse raw logs
        log_message(log_file, "Starting log parsing...")
        bronze_df = parse_raw_logs(spark, raw_log_path, log_file)
        
        # Show sample data
        log_message(log_file, "Sample data:")
        sample_data = bronze_df.limit(3).toPandas()
        for idx, row in sample_data.iterrows():
            log_message(log_file, f"  Row {idx+1}: {row['event_type']} by {row['user_id']} at {row['event_timestamp']}")
        
        # Show schema
        log_message(log_file, "Bronze layer schema:")
        for field in bronze_df.schema.fields:
            log_message(log_file, f"  - {field.name}: {field.dataType}")
        
        # Save to Bronze layer
        save_to_bronze(bronze_df, bronze_output_path, log_file)
        
        # Verify output
        log_message(log_file, "Verifying Bronze layer...")
        verify_df = spark.read.parquet(bronze_output_path)
        log_message(log_file, f"Verification successful: {verify_df.count()} records found")
        
        # Show statistics
        log_message(log_file, "")
        log_message(log_file, "Statistics:")
        log_message(log_file, f"  Total records: {verify_df.count()}")
        log_message(log_file, f"  NULL user_ids: {verify_df.filter(F.col('user_id') == 'NULL').count()}")
        log_message(log_file, f"  High-value events: {verify_df.filter(F.col('is_high_value') == 1).count()}")
        log_message(log_file, f"  Date partitions: {verify_df.select('partition_date').distinct().count()}")
        
        log_message(log_file, "")
        log_message(log_file, "=" * 70)
        log_message(log_file, "RAW TO BRONZE CONVERSION - COMPLETED SUCCESSFULLY")
        log_message(log_file, "=" * 70)
        
    except Exception as e:
        log_message(log_file, f"❌ ERROR: {str(e)}")
        log_message(log_file, "=" * 70)
        log_message(log_file, "RAW TO BRONZE CONVERSION - FAILED")
        log_message(log_file, "=" * 70)
        raise
    
    finally:
        spark.stop()
        log_message(log_file, "Spark session stopped")


if __name__ == "__main__":
    main()

