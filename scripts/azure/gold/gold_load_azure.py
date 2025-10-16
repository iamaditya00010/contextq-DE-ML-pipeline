# Azure Databricks Gold Layer Script
# Author: Aditya Padhi
# Description: Combine date/time columns and create final curated dataset

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
from datetime import datetime

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Gold_Layer_Processing") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Set log level
spark.sparkContext.setLogLevel("WARN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_silver_to_gold():
    """Process data from Silver layer to Gold layer"""
    
    try:
        # Read from Silver layer
        silver_df = spark.read.json("/mnt/silver/structured_logs/structured_logs.json")
        
        logger.info(f"Loaded {silver_df.count()} records from Silver layer")
        
        # Create datetime column by combining Date, Day, and Time
        gold_df = silver_df.withColumn(
            "datetime",
            concat(
                col("Day").cast("string"),
                lit("-"),
                col("Date").cast("string"),
                lit("-2024 : "),
                col("Time").cast("string")
            )
        )
        
        # Remove original date/time columns
        gold_df = gold_df.drop("Date", "Day", "Time", "Month", "Year", "Hour", "Minute", "Second")
        
        # Add business logic columns
        gold_df = gold_df.withColumn("event_category", 
            when(col("EventTemplate").contains("Failed"), "Security_Alert")
            .when(col("EventTemplate").contains("Accepted"), "Authentication_Success")
            .when(col("EventTemplate").contains("Disconnected"), "Session_End")
            .otherwise("Other")
        )
        
        # Add risk score based on event type
        gold_df = gold_df.withColumn("risk_score",
            when(col("event_category") == "Security_Alert", 8)
            .when(col("event_category") == "Authentication_Success", 2)
            .when(col("event_category") == "Session_End", 1)
            .otherwise(3)
        )
        
        # Add processing metadata
        gold_df = gold_df.withColumn("processing_date", current_date()) \
                        .withColumn("processing_timestamp", current_timestamp())
        
        # Data quality checks
        total_records = gold_df.count()
        null_datetime_records = gold_df.filter(col("datetime").isNull()).count()
        null_event_category_records = gold_df.filter(col("event_category").isNull()).count()
        
        logger.info(f"Gold layer records: {total_records}")
        logger.info(f"Null datetime records: {null_datetime_records}")
        logger.info(f"Null event category records: {null_event_category_records}")
        
        # Quality validation
        if null_datetime_records > 0:
            logger.warning(f"Found {null_datetime_records} records with null datetime")
        
        if null_event_category_records > total_records * 0.1:
            logger.warning("High null event category rate detected")
        
        # Write to Gold layer in CSV format
        gold_df.write \
            .mode("overwrite") \
            .option("header", "true") \
            .option("compression", "gzip") \
            .csv("/mnt/gold/final_data/openssh_logs_final.csv")
        
        logger.info("Gold layer processing completed successfully")
        
        # Write business report
        business_report = gold_df.groupBy("event_category") \
                               .agg(
                                   count("*").alias("event_count"),
                                   avg("risk_score").alias("avg_risk_score"),
                                   max("risk_score").alias("max_risk_score")
                               )
        
        business_report.write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv("/mnt/gold/business_reports/event_category_summary.csv")
        
        # Write quality report
        quality_report = spark.createDataFrame([
            ("total_records", total_records),
            ("null_datetime_records", null_datetime_records),
            ("null_event_category_records", null_event_category_records),
            ("processing_timestamp", current_timestamp())
        ], ["metric", "value", "timestamp"])
        
        quality_report.write \
            .mode("overwrite") \
            .parquet("/mnt/gold/quality_reports/gold_quality.parquet")
        
        return gold_df
        
    except Exception as e:
        logger.error(f"Error in Gold layer processing: {str(e)}")
        raise e

def main():
    """Main execution function"""
    
    logger.info("Starting Gold layer processing...")
    
    try:
        # Process Silver to Gold
        gold_df = process_silver_to_gold()
        
        # Display sample data
        logger.info("Sample Gold layer data:")
        gold_df.show(5, truncate=False)
        
        # Display schema
        logger.info("Gold layer schema:")
        gold_df.printSchema()
        
        # Display event category summary
        logger.info("Event category summary:")
        gold_df.groupBy("event_category").count().show()
        
        logger.info("Gold layer processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Gold layer processing failed: {str(e)}")
        raise e
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
