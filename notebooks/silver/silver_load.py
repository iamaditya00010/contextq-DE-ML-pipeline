# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer - Data Transformation
# MAGIC 
# MAGIC **Author:** Aditya Padhi
# MAGIC 
# MAGIC This notebook transforms raw data from Bronze layer into structured format for Silver layer.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

# Import required libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
from datetime import datetime

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Silver Layer - Data Transformation") \
    .getOrCreate()

print("Spark session initialized successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Bronze Layer Data

# COMMAND ----------

# Define data paths
bronze_input_path = "abfss://bronze@delogprocessingdatalake.dfs.core.windows.net/raw_logs.parquet"
silver_output_path = "abfss://silver@delogprocessingdatalake.dfs.core.windows.net/structured_logs.json"

print(f"Bronze input path: {bronze_input_path}")
print(f"Silver output path: {silver_output_path}")

# COMMAND ----------

# Load Bronze layer data
print("Loading Bronze layer data...")
bronze_df = spark.read.parquet(bronze_input_path)

print(f"Bronze records: {bronze_df.count()}")
print("Bronze data sample:")
bronze_df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parse Log Entries

# COMMAND ----------

# Define log parsing function
def parse_log_line(line):
    """Parse a single log line into structured format"""
    try:
        parts = line.split()
        if len(parts) >= 6:
            return {
                "timestamp": f"{parts[0]} {parts[1]}",
                "hostname": parts[2],
                "process": parts[3],
                "pid": parts[4].rstrip(':'),
                "message": ' '.join(parts[5:])
            }
    except:
        pass
    return None

# Apply parsing to Bronze data
print("Parsing log entries...")
parsed_data = bronze_df.select("value").rdd.map(lambda row: parse_log_line(row.value)).filter(lambda x: x is not None)

# Convert to DataFrame
structured_df = spark.createDataFrame(parsed_data)

print(f"Parsed records: {structured_df.count()}")
print("Structured data sample:")
structured_df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Checks

# COMMAND ----------

# Check for parsing success rate
total_bronze = bronze_df.count()
parsed_count = structured_df.count()
parsing_success_rate = (parsed_count / total_bronze) * 100

print(f"Parsing success rate: {parsing_success_rate:.2f}%")
print(f"Total Bronze records: {total_bronze}")
print(f"Successfully parsed: {parsed_count}")
print(f"Failed to parse: {total_bronze - parsed_count}")

# COMMAND ----------

# Check for null values in structured data
print("Checking for null values in structured data:")
structured_df.select([count(when(col(c).isNull(), c)).alias(c) for c in structured_df.columns]).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Add Derived Fields

# COMMAND ----------

# Add derived fields
enhanced_df = structured_df.withColumn("date", split(col("timestamp"), " ")[0]) \
                           .withColumn("time", split(col("timestamp"), " ")[1]) \
                           .withColumn("day", dayofweek(to_date(col("date"), "MMM dd"))) \
                           .withColumn("processing_timestamp", current_timestamp()) \
                           .withColumn("layer", lit("silver"))

print("Enhanced data with derived fields:")
enhanced_df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Store in Silver Layer (JSON Format)

# COMMAND ----------

# Save to Silver layer as JSON
print("Saving to Silver layer (JSON format)...")
enhanced_df.write \
    .mode("overwrite") \
    .json(silver_output_path)

print(f"✅ Silver layer data saved successfully to: {silver_output_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify the saved data
print("Verifying saved data...")
saved_data = spark.read.json(silver_output_path)

print(f"Records saved: {saved_data.count()}")
print("Sample saved data:")
saved_data.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

# Create summary
summary = {
    "layer": "Silver",
    "processing_time": datetime.now().isoformat(),
    "bronze_records": total_bronze,
    "parsed_records": parsed_count,
    "parsing_success_rate": f"{parsing_success_rate:.2f}%",
    "output_format": "JSON",
    "output_path": silver_output_path,
    "derived_fields": ["date", "time", "day", "processing_timestamp"]
}

print("=" * 70)
print("SILVER LAYER PROCESSING SUMMARY")
print("=" * 70)
for key, value in summary.items():
    print(f"{key}: {value}")
print("=" * 70)

print("✅ Silver layer processing completed successfully!")
print("📊 Raw data transformed to structured JSON format")
print("🎯 Ready for Gold layer processing")
