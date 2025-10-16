"""
Convert raw log files to Bronze layer (Parquet format) - Pandas Version

This script:
1. Reads raw application log files (.log or .log.gz)
2. Parses the pipe-delimited format  
3. Converts to structured DataFrame
4. Saves as Parquet in Bronze layer
5. Logs the process to logs/export.log

Note: This is the pandas version for local development.
      PySpark version will be used on Databricks.
"""

import gzip
import pandas as pd
from pathlib import Path
from datetime import datetime


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


def parse_raw_logs(raw_log_path: str, log_file: Path):
    """
    Parse raw log files and convert to structured DataFrame
    
    Log format:
    TIMESTAMP | LEVEL | user_id | session_id | event_type | method | endpoint | 
    status | response_time | duration | value | high_value | device | browser | os | ip
    """
    
    log_message(log_file, f"Reading raw log file: {raw_log_path}")
    
    # Read raw log file
    if raw_log_path.endswith('.gz'):
        with gzip.open(raw_log_path, 'rt', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        with open(raw_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    log_message(log_file, f"Total raw entries: {len(lines)}")
    
    # Parse each line
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Split by pipe delimiter
        parts = [p.strip() for p in line.split('|')]
        
        if len(parts) >= 16:
            record = {
                'timestamp_raw': parts[0],
                'log_level': parts[1],
                'user_id': parts[2],
                'session_id': parts[3],
                'event_type': parts[4],
                'http_method': parts[5],
                'endpoint': parts[6],
                'status_code_raw': parts[7],
                'response_time_raw': parts[8],
                'duration_raw': parts[9],
                'value_raw': parts[10],
                'high_value': parts[11],
                'device': parts[12],
                'browser': parts[13],
                'os': parts[14],
                'ip_address': parts[15]
            }
            records.append(record)
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    log_message(log_file, f"Parsed entries: {len(df)}")
    
    # Convert data types and clean fields
    df['event_timestamp'] = pd.to_datetime(df['timestamp_raw'], format='%Y-%m-%d %H:%M:%S.%f')
    df['status_code'] = df['status_code_raw'].astype(int)
    df['response_time_ms'] = df['response_time_raw'].str.replace('ms', '').astype(int)
    df['duration_seconds'] = df['duration_raw'].str.replace('s', '').astype(float)
    df['transaction_value'] = df['value_raw'].str.replace('$', '').astype(float)
    df['is_high_value'] = df['high_value'].astype(int)
    df['ingestion_timestamp'] = pd.Timestamp.now()
    df['source_file'] = raw_log_path
    df['partition_date'] = df['event_timestamp'].dt.date
    
    # Select final columns for bronze layer
    bronze_columns = [
        'event_timestamp',
        'log_level',
        'user_id',
        'session_id',
        'event_type',
        'http_method',
        'endpoint',
        'status_code',
        'response_time_ms',
        'duration_seconds',
        'transaction_value',
        'is_high_value',
        'device',
        'browser',
        'os',
        'ip_address',
        'ingestion_timestamp',
        'source_file',
        'partition_date'
    ]
    
    bronze_df = df[bronze_columns]
    
    log_message(log_file, "Schema created with proper data types")
    log_message(log_file, f"Columns: {', '.join(bronze_df.columns)}")
    
    return bronze_df


def save_to_bronze(df, output_path: str, log_file: Path):
    """Save DataFrame to Bronze layer as Parquet"""
    
    log_message(log_file, f"Writing to Bronze layer: {output_path}")
    
    # Create output directory
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as Parquet (partitioned by date)
    for date in df['partition_date'].unique():
        date_df = df[df['partition_date'] == date]
        partition_dir = output_dir / f"partition_date={date}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        
        # Save partition
        partition_file = partition_dir / "data.parquet"
        date_df.drop('partition_date', axis=1).to_parquet(
            partition_file,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        
        log_message(log_file, f"  ✓ Partition {date}: {len(date_df)} records")
    
    log_message(log_file, f"✅ Successfully wrote {len(df)} records to Bronze layer")
    log_message(log_file, f"Format: Parquet (partitioned by date)")


def verify_bronze(output_path: str, log_file: Path):
    """Verify Bronze layer data"""
    
    log_message(log_file, "Verifying Bronze layer...")
    
    # Read all partitions
    output_dir = Path(output_path)
    all_data = []
    
    for partition_dir in output_dir.glob("partition_date=*"):
        for parquet_file in partition_dir.glob("*.parquet"):
            df = pd.read_parquet(parquet_file)
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        log_message(log_file, f"✅ Verification successful: {len(combined_df)} records found")
        return combined_df
    else:
        log_message(log_file, "❌ No data found in Bronze layer")
        return None


def main():
    """Main execution"""
    
    # Setup logging
    log_file = setup_logging("logs/export.log")
    
    log_message(log_file, "=" * 70)
    log_message(log_file, "RAW TO BRONZE CONVERSION - STARTED")
    log_message(log_file, "=" * 70)
    
    try:
        # Define paths
        raw_log_path = "data/bronze/logs/date=2025-10-16/application.log.gz"
        bronze_output_path = "data/bronze/structured"
        
        # Check if raw file exists
        if not Path(raw_log_path).exists():
            log_message(log_file, f"❌ ERROR: Raw log file not found: {raw_log_path}")
            return
        
        # Parse raw logs
        log_message(log_file, "Starting log parsing...")
        bronze_df = parse_raw_logs(raw_log_path, log_file)
        
        # Show sample data
        log_message(log_file, "Sample data:")
        for idx, row in bronze_df.head(3).iterrows():
            log_message(log_file, f"  Row {idx+1}: {row['event_type']} by {row['user_id']} at {row['event_timestamp']}")
        
        # Show schema
        log_message(log_file, "Bronze layer schema:")
        log_message(log_file, f"{bronze_df.dtypes.to_string()}")
        
        # Save to Bronze layer
        save_to_bronze(bronze_df, bronze_output_path, log_file)
        
        # Verify output
        verify_df = verify_bronze(bronze_output_path, log_file)
        
        if verify_df is not None:
            # Show statistics
            log_message(log_file, "")
            log_message(log_file, "Statistics:")
            log_message(log_file, f"  Total records: {len(verify_df)}")
            log_message(log_file, f"  NULL user_ids: {(verify_df['user_id'] == 'NULL').sum()}")
            log_message(log_file, f"  High-value events: {verify_df['is_high_value'].sum()}")
            log_message(log_file, f"  Unique dates: {verify_df['event_timestamp'].dt.date.nunique()}")
            log_message(log_file, f"  Date range: {verify_df['event_timestamp'].min()} to {verify_df['event_timestamp'].max()}")
            
            # Event type distribution
            log_message(log_file, "")
            log_message(log_file, "Event type distribution:")
            for event_type, count in verify_df['event_type'].value_counts().items():
                log_message(log_file, f"  {event_type:15s}: {count:,}")
        
        log_message(log_file, "")
        log_message(log_file, "=" * 70)
        log_message(log_file, "RAW TO BRONZE CONVERSION - COMPLETED SUCCESSFULLY")
        log_message(log_file, "=" * 70)
        log_message(log_file, "")
        log_message(log_file, "Next steps:")
        log_message(log_file, "  1. Bronze layer (Parquet) is ready for ETL processing")
        log_message(log_file, "  2. Run ETL pipeline to create Silver layer (cleaned data)")
        log_message(log_file, "  3. Train ML model on Silver layer data")
        
    except Exception as e:
        log_message(log_file, f"❌ ERROR: {str(e)}")
        import traceback
        log_message(log_file, traceback.format_exc())
        log_message(log_file, "=" * 70)
        log_message(log_file, "RAW TO BRONZE CONVERSION - FAILED")
        log_message(log_file, "=" * 70)
        raise


if __name__ == "__main__":
    main()

