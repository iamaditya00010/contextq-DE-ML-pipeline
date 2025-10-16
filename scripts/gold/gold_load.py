"""
Gold Layer: Final Aggregation and Business Logic
=================================================
This script reads Silver layer data, combines date/time fields into a single datetime column,
and saves the final curated data to Gold layer as CSV.

Author: Aditya Padhi

Transformations:
- Combine Date, Day, Time into single datetime column (format: dd-mm-yyyy : hh:mm:ss)
- Remove original Date, Day, Time columns
- Filter only quality-passed records
- Save as CSV for business consumption

Input: data/silver/structured_logs.json
Output: data/gold/openssh_logs_final.csv
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, concat, lit, lpad, when, regexp_replace, concat_ws
)
from datetime import datetime
import os


def create_spark_session():
    """Create Spark session for Gold layer processing"""
    return SparkSession.builder \
        .appName("Gold Layer - Final Curated Data") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()


def load_silver_data(spark, silver_path):
    """
    Load data from Silver layer
    
    Args:
        spark: SparkSession
        silver_path: Path to Silver JSON files
        
    Returns:
        DataFrame with Silver data
    """
    print(f"[GOLD] Loading Silver data from: {silver_path}")
    
    df = spark.read.json(silver_path)
    record_count = df.count()
    
    print(f"[GOLD] Silver records loaded: {record_count}")
    
    return df


def filter_quality_data(df):
    """
    Filter to keep only quality-passed records
    
    Args:
        df: DataFrame from Silver layer
        
    Returns:
        Filtered DataFrame with only PASS quality records
    """
    print("[GOLD] Filtering quality data...")
    
    total_before = df.count()
    
    # Keep only records that passed quality checks
    quality_df = df.filter(col("overall_quality") == "PASS")
    
    total_after = quality_df.count()
    filtered_out = total_before - total_after
    
    print(f"[GOLD] Quality filtering results:")
    print(f"  - Input records: {total_before}")
    print(f"  - Quality passed: {total_after} ({total_after/total_before*100:.1f}%)")
    print(f"  - Filtered out: {filtered_out} ({filtered_out/total_before*100:.1f}%)")
    
    return quality_df


def combine_datetime_fields(df):
    """
    Combine Date, Day, Time into single datetime column
    
    Format: dd-mm-yyyy : hh:mm:ss
    Example: 10-Dec-2024 : 06:55:46
    
    Note: We assume year 2024 since it's not in the original log
    
    Args:
        df: DataFrame with Date, Day, Time columns
        
    Returns:
        DataFrame with datetime column (Date, Day, Time removed)
    """
    print("[GOLD] Combining date and time fields...")
    
    # Map month abbreviations to month numbers
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    
    # Create month number column
    df_with_month = df
    for month_abbr, month_num in month_map.items():
        df_with_month = df_with_month.withColumn(
            "month_num",
            when(col("Date") == month_abbr, month_num)
            .otherwise(col("month_num") if "month_num" in df_with_month.columns else lit("00"))
        )
    
    # Ensure Day is 2 digits (add leading zero if needed)
    df_with_month = df_with_month.withColumn(
        "day_formatted",
        lpad(col("Day"), 2, "0")
    )
    
    # Assume year 2024 (since not in original log)
    df_with_month = df_with_month.withColumn("year", lit("2024"))
    
    # Combine into datetime format: dd-mm-yyyy : hh:mm:ss
    # Using Day (original value for display), month_num, year
    df_with_datetime = df_with_month.withColumn(
        "datetime",
        concat(
            col("day_formatted"), lit("-"),
            col("Date"), lit("-"),  # Keep month abbreviation
            col("year"), lit(" : "),
            col("Time")
        )
    )
    
    # Drop temporary columns
    df_final = df_with_datetime.drop("month_num", "day_formatted", "year")
    
    print("[GOLD] Datetime field created successfully")
    
    return df_final


def prepare_gold_dataset(df):
    """
    Prepare final Gold layer dataset
    
    - Remove Date, Day, Time columns (replaced by datetime)
    - Remove quality check columns
    - Keep only business-relevant columns
    - Reorder columns for readability
    
    Args:
        df: DataFrame with datetime column
        
    Returns:
        Final curated DataFrame for Gold layer
    """
    print("[GOLD] Preparing final dataset...")
    
    # Select and reorder columns for Gold layer
    gold_df = df.select(
        "LineId",
        "datetime",           # Combined datetime
        "Component",
        "Pid",
        "EventId",
        "EventTemplate",
        "Content"
    )
    
    # Sort by LineId for consistent output
    gold_df = gold_df.orderBy("LineId")
    
    print(f"[GOLD] Final dataset prepared with {gold_df.count()} records")
    
    return gold_df


def save_to_gold(df, output_path):
    """
    Save curated data to Gold layer as CSV
    
    Args:
        df: Final curated DataFrame
        output_path: Path to save CSV file
    """
    print(f"[GOLD] Saving to Gold layer: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save as single CSV file with header
    df.coalesce(1) \
        .write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(output_path)
    
    print(f"[GOLD] ✅ Successfully saved {df.count()} records to Gold layer")
    
    # Rename the output file to remove part-00000 prefix
    import glob
    csv_files = glob.glob(f"{output_path}/part-*.csv")
    if csv_files:
        final_output = os.path.join(os.path.dirname(output_path), "openssh_logs_final.csv")
        os.rename(csv_files[0], final_output)
        print(f"[GOLD] Final CSV: {final_output}")


def generate_summary_statistics(df):
    """
    Generate and display summary statistics for Gold layer
    
    Args:
        df: Final Gold DataFrame
    """
    print("\n[GOLD] Summary Statistics:")
    print("=" * 70)
    
    total_records = df.count()
    print(f"Total records: {total_records}")
    
    # Event distribution
    print("\nEvent distribution:")
    df.groupBy("EventId") \
        .count() \
        .orderBy("count", ascending=False) \
        .show(10)
    
    # Component distribution
    print("Component distribution:")
    df.groupBy("Component") \
        .count() \
        .show(truncate=False)
    
    print("=" * 70)


def main():
    """Main execution for Gold layer"""
    
    print("=" * 70)
    print("GOLD LAYER - FINAL CURATED DATA")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Define paths
        silver_input = "data/silver/structured_logs.json"
        gold_output = "data/gold"
        
        # Check if input exists
        if not os.path.exists(silver_input):
            print(f"[ERROR] Silver data not found: {silver_input}")
            print("[ERROR] Please run silver/silver_load.py first")
            return
        
        # Load Silver data
        silver_df = load_silver_data(spark, silver_input)
        
        # Filter quality data
        quality_df = filter_quality_data(silver_df)
        
        # Combine datetime fields
        datetime_df = combine_datetime_fields(quality_df)
        
        # Prepare final Gold dataset
        gold_df = prepare_gold_dataset(datetime_df)
        
        # Show sample
        print("\n[GOLD] Sample final data (first 5 records):")
        gold_df.show(5, truncate=False)
        
        # Show schema
        print("[GOLD] Final Schema:")
        gold_df.printSchema()
        
        # Generate summary statistics
        generate_summary_statistics(gold_df)
        
        # Save to Gold layer
        save_to_gold(gold_df, gold_output)
        
        print()
        print("=" * 70)
        print("GOLD LAYER - COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Output directory: {gold_output}")
        print(f"Final CSV: {gold_output}/openssh_logs_final.csv")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n[ERROR] Gold layer processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

