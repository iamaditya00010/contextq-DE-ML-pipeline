# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer - Raw Data Processing
# MAGIC 
# MAGIC **Author:** Aditya Padhi
# MAGIC 
# MAGIC This notebook processes raw log data and stores it in the Bronze layer as Parquet format.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

# Import required libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import os
from datetime import datetime

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Bronze Layer - Raw Data Processing") \
    .getOrCreate()

print("Spark session initialized successfully")
print(f"Spark version: {spark.version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Raw Data

# COMMAND ----------

# Define data paths
raw_data_path = "abfss://bronze@delogprocessingdatalake.dfs.core.windows.net/raw_logs/OpenSSH_2k.log"
bronze_output_path = "abfss://bronze@delogprocessingdatalake.dfs.core.windows.net/raw_logs.parquet"

print(f"Raw data path: {raw_data_path}")
print(f"Bronze output path: {bronze_output_path}")

# COMMAND ----------

# Load raw log data
print("Loading raw log data...")
raw_data_df = spark.read.text(raw_data_path)

# Display basic information
print(f"Total records: {raw_data_df.count()}")
print("Sample data:")
raw_data_df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Checks

# COMMAND ----------

# Check for null values
null_count = raw_data_df.filter(col("value").isNull()).count()
print(f"Null records: {null_count}")

# Check for empty lines
empty_count = raw_data_df.filter(col("value") == "").count()
print(f"Empty records: {empty_count}")

# Check data types
print("Data schema:")
raw_data_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Store in Bronze Layer (Parquet Format)

# COMMAND ----------

# Add metadata columns
bronze_df = raw_data_df.withColumn("processing_timestamp", current_timestamp()) \
                       .withColumn("source_file", lit("OpenSSH_2k.log")) \
                       .withColumn("layer", lit("bronze"))

print("Bronze layer data with metadata:")
bronze_df.show(5, truncate=False)

# COMMAND ----------

# Save to Bronze layer as Parquet
print("Saving to Bronze layer (Parquet format)...")
bronze_df.write \
    .mode("overwrite") \
    .parquet(bronze_output_path)

print(f"Bronze layer data saved successfully to: {bronze_output_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify the saved data
print("Verifying saved data...")
saved_data = spark.read.parquet(bronze_output_path)

print(f"Records saved: {saved_data.count()}")
print("Sample saved data:")
saved_data.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

# Create summary
summary = {
    "layer": "Bronze",
    "processing_time": datetime.now().isoformat(),
    "source_file": "OpenSSH_2k.log",
    "total_records": raw_data_df.count(),
    "output_format": "Parquet",
    "output_path": bronze_output_path,
    "null_records": null_count,
    "empty_records": empty_count
}

print("=" * 70)
print("BRONZE LAYER PROCESSING SUMMARY")
print("=" * 70)
for key, value in summary.items():
    print(f"{key}: {value}")
print("=" * 70)

print("Bronze layer processing completed successfully!")
print("Raw data converted to Parquet format")
print("Ready for Silver layer processing")
