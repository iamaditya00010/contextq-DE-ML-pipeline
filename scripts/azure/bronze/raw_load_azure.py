# Azure Databricks Bronze Layer Script
# Author: Aditya Padhi
# Description: Load raw log data from ADLS Gen2 to Bronze layer in Parquet format

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Bronze_Layer_Processing") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Set log level
spark.sparkContext.setLogLevel("WARN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_raw_logs():
    """Load raw log data from ADLS Gen2"""
    
    try:
        # Read raw log file from ADLS Gen2
        raw_logs_df = spark.read.text("/mnt/bronze/raw_logs/OpenSSH_2k.log")
        
        # Add metadata columns
        bronze_df = raw_logs_df.withColumn("line_id", monotonically_increasing_id()) \
                              .withColumn("raw_content", col("value")) \
                              .withColumn("processing_timestamp", current_timestamp()) \
                              .withColumn("source_file", lit("OpenSSH_2k.log")) \
                              .drop("value")
        
        # Data quality checks
        total_records = bronze_df.count()
        null_records = bronze_df.filter(col("raw_content").isNull()).count()
        
        logger.info(f"Total records loaded: {total_records}")
        logger.info(f"Null records: {null_records}")
        
        # Quality validation
        if null_records > total_records * 0.1:  # More than 10% nulls
            raise Exception("Data quality issue: Too many null records")
        
        # Write to Bronze layer in Parquet format
        bronze_df.write \
            .mode("overwrite") \
            .option("compression", "snappy") \
            .parquet("/mnt/bronze/processed/raw_logs.parquet")
        
        logger.info("Bronze layer processing completed successfully")
        
        # Write quality report
        quality_report = spark.createDataFrame([
            ("total_records", total_records),
            ("null_records", null_records),
            ("quality_score", (total_records - null_records) / total_records * 100),
            ("processing_timestamp", current_timestamp())
        ], ["metric", "value", "quality_score", "timestamp"])
        
        quality_report.write \
            .mode("overwrite") \
            .parquet("/mnt/bronze/quality_reports/bronze_quality.parquet")
        
        return bronze_df
        
    except Exception as e:
        logger.error(f"Error in Bronze layer processing: {str(e)}")
        raise e

def main():
    """Main execution function"""
    
    logger.info("Starting Bronze layer processing...")
    
    try:
        # Load raw logs
        bronze_df = load_raw_logs()
        
        # Display sample data
        logger.info("Sample Bronze layer data:")
        bronze_df.show(5, truncate=False)
        
        logger.info("Bronze layer processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Bronze layer processing failed: {str(e)}")
        raise e
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
