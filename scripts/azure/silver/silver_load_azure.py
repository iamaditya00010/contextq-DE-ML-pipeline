# Azure Databricks Silver Layer Script
# Author: Aditya Padhi
# Description: Transform and standardize data from Bronze layer to Silver layer

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import json
from datetime import datetime

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Silver_Layer_Processing") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Set log level
spark.sparkContext.setLogLevel("WARN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_log_line(log_line):
    """Parse individual log line and extract structured data"""
    
    try:
        # Split log line into components
        parts = log_line.split()
        
        if len(parts) < 6:
            return None
        
        # Extract date and time
        date_part = parts[0]
        time_part = parts[1]
        
        # Extract component and PID
        component_pid = parts[2]
        if '[' in component_pid and ']' in component_pid:
            component = component_pid.split('[')[0]
            pid = component_pid.split('[')[1].split(']')[0]
        else:
            component = component_pid
            pid = None
        
        # Extract event ID
        event_id = parts[3] if len(parts) > 3 else None
        
        # Extract event template
        event_template = parts[4] if len(parts) > 4 else None
        
        # Extract content (remaining parts)
        content = ' '.join(parts[5:]) if len(parts) > 5 else None
        
        return {
            "Date": date_part,
            "Time": time_part,
            "Component": component,
            "Pid": pid,
            "EventId": event_id,
            "EventTemplate": event_template,
            "Content": content
        }
        
    except Exception as e:
        logger.warning(f"Failed to parse log line: {log_line[:100]}... Error: {str(e)}")
        return None

def process_bronze_to_silver():
    """Process data from Bronze layer to Silver layer"""
    
    try:
        # Read from Bronze layer
        bronze_df = spark.read.parquet("/mnt/bronze/processed/raw_logs.parquet")
        
        logger.info(f"Loaded {bronze_df.count()} records from Bronze layer")
        
        # Parse log lines
        parse_udf = udf(parse_log_line, MapType(StringType(), StringType()))
        
        # Apply parsing
        parsed_df = bronze_df.withColumn("parsed_data", parse_udf(col("raw_content")))
        
        # Filter out failed parsing
        valid_df = parsed_df.filter(col("parsed_data").isNotNull())
        
        # Extract structured fields
        silver_df = valid_df.select(
            col("line_id").alias("LineId"),
            col("parsed_data")["Date"].alias("Date"),
            col("parsed_data")["Time"].alias("Time"),
            col("parsed_data")["Component"].alias("Component"),
            col("parsed_data")["Pid"].alias("Pid"),
            col("parsed_data")["EventId"].alias("EventId"),
            col("parsed_data")["EventTemplate"].alias("EventTemplate"),
            col("parsed_data")["Content"].alias("Content"),
            col("processing_timestamp").alias("ProcessingTimestamp"),
            col("source_file").alias("SourceFile")
        )
        
        # Data quality checks
        total_records = silver_df.count()
        null_date_records = silver_df.filter(col("Date").isNull()).count()
        null_time_records = silver_df.filter(col("Time").isNull()).count()
        null_component_records = silver_df.filter(col("Component").isNull()).count()
        
        logger.info(f"Silver layer records: {total_records}")
        logger.info(f"Null date records: {null_date_records}")
        logger.info(f"Null time records: {null_time_records}")
        logger.info(f"Null component records: {null_component_records}")
        
        # Quality validation
        quality_issues = []
        
        if null_date_records > total_records * 0.05:  # More than 5% null dates
            quality_issues.append("High null date rate")
        
        if null_time_records > total_records * 0.05:  # More than 5% null times
            quality_issues.append("High null time rate")
        
        if null_component_records > total_records * 0.1:  # More than 10% null components
            quality_issues.append("High null component rate")
        
        if quality_issues:
            logger.warning(f"Data quality issues detected: {', '.join(quality_issues)}")
        
        # Add derived columns
        silver_df = silver_df.withColumn("Day", dayofmonth(col("Date"))) \
                           .withColumn("Month", month(col("Date"))) \
                           .withColumn("Year", year(col("Date"))) \
                           .withColumn("Hour", hour(col("Time"))) \
                           .withColumn("Minute", minute(col("Time"))) \
                           .withColumn("Second", second(col("Time")))
        
        # Write to Silver layer in JSON format
        silver_df.write \
            .mode("overwrite") \
            .option("compression", "gzip") \
            .json("/mnt/silver/structured_logs/structured_logs.json")
        
        logger.info("Silver layer processing completed successfully")
        
        # Write quality report
        quality_report = spark.createDataFrame([
            ("total_records", total_records),
            ("null_date_records", null_date_records),
            ("null_time_records", null_time_records),
            ("null_component_records", null_component_records),
            ("quality_issues", len(quality_issues)),
            ("processing_timestamp", current_timestamp())
        ], ["metric", "value", "quality_issues", "timestamp"])
        
        quality_report.write \
            .mode("overwrite") \
            .parquet("/mnt/silver/quality_reports/silver_quality.parquet")
        
        return silver_df
        
    except Exception as e:
        logger.error(f"Error in Silver layer processing: {str(e)}")
        raise e

def main():
    """Main execution function"""
    
    logger.info("Starting Silver layer processing...")
    
    try:
        # Process Bronze to Silver
        silver_df = process_bronze_to_silver()
        
        # Display sample data
        logger.info("Sample Silver layer data:")
        silver_df.show(5, truncate=False)
        
        # Display schema
        logger.info("Silver layer schema:")
        silver_df.printSchema()
        
        logger.info("Silver layer processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Silver layer processing failed: {str(e)}")
        raise e
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
