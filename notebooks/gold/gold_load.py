# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer - Feature Engineering
# MAGIC 
# MAGIC **Author:** Aditya Padhi
# MAGIC 
# MAGIC This notebook performs feature engineering on Silver layer data and creates the final Gold layer dataset.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

# Import required libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime

# Initialize Spark session
spark = SparkSession.builder \
    .appName("Gold Layer - Feature Engineering") \
    .getOrCreate()

print("Spark session initialized successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Silver Layer Data

# COMMAND ----------

# Define data paths
silver_input_path = "abfss://silver@delogprocessingdatalake.dfs.core.windows.net/structured_logs.json"
gold_output_path = "abfss://gold@delogprocessingdatalake.dfs.core.windows.net/openssh_logs_final.csv"

print(f"Silver input path: {silver_input_path}")
print(f"Gold output path: {gold_output_path}")

# COMMAND ----------

# Load Silver layer data
print("Loading Silver layer data...")
silver_df = spark.read.json(silver_input_path)

print(f"Silver records: {silver_df.count()}")
print("Silver data sample:")
silver_df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Engineering

# COMMAND ----------

# Create datetime column by combining Date, Day, and Time
print("Creating datetime column...")
gold_df = silver_df.select(
    col("timestamp"),
    col("date").alias("Date"),
    col("day").alias("Day"),
    col("time").alias("Time"),
    col("hostname"),
    col("process"),
    col("pid"),
    col("message")
)

# Add datetime column in dd-mm-yyyy : hh:mm:ss format
gold_df = gold_df.withColumn(
    "datetime", 
    concat(
        split(col("Date"), "-")[2], lit("-"),
        split(col("Date"), "-")[1], lit("-"),
        split(col("Date"), "-")[0], lit(" : "),
        col("Time")
    )
)

print("Gold layer data with datetime column:")
gold_df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Remove Original Date/Time Columns

# COMMAND ----------

# Remove the original Date, Day, Time columns as requested
final_gold_df = gold_df.drop("Date", "Day", "Time")

print("Final Gold layer data (original date/time columns removed):")
final_gold_df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Checks

# COMMAND ----------

# Check for null values
print("Checking for null values:")
final_gold_df.select([count(when(col(c).isNull(), c)).alias(c) for c in final_gold_df.columns]).show()

# Check data types
print("Final data schema:")
final_gold_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Store in Gold Layer (CSV Format)

# COMMAND ----------

# Save to Gold layer as CSV
print("Saving to Gold layer (CSV format)...")
final_gold_df.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(gold_output_path)

print(f"✅ Gold layer data saved successfully to: {gold_output_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify the saved data
print("Verifying saved data...")
saved_data = spark.read.csv(gold_output_path, header=True, inferSchema=True)

print(f"Records saved: {saved_data.count()}")
print("Sample saved data:")
saved_data.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

# Create summary
summary = {
    "layer": "Gold",
    "processing_time": datetime.now().isoformat(),
    "silver_records": silver_df.count(),
    "gold_records": final_gold_df.count(),
    "output_format": "CSV",
    "output_path": gold_output_path,
    "datetime_format": "dd-mm-yyyy : hh:mm:ss",
    "removed_columns": ["Date", "Day", "Time"],
    "final_columns": final_gold_df.columns
}

print("=" * 70)
print("GOLD LAYER PROCESSING SUMMARY")
print("=" * 70)
for key, value in summary.items():
    print(f"{key}: {value}")
print("=" * 70)

print("✅ Gold layer processing completed successfully!")
print("📊 Structured data with feature engineering")
print("🎯 Ready for ML model training")
