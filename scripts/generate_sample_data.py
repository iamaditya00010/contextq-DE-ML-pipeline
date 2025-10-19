"""Generate realistic application log files for testing"""
import random
import gzip
from pathlib import Path
from datetime import datetime, timedelta


def generate_log_entries(num_entries: int = 10000) -> list:
    """Generate realistic application log entries
    
    This simulates a web application's access and event logs with:
    - Timestamps
    - Log levels
    - User IDs
    - Event types
    - Session information
    - Response times
    - Transaction values
    - Device/browser info
    
    Args:
        num_entries: Number of log entries to generate
        
    Returns:
        List of log entry strings
    """
    
    random.seed(42)
    
    print(f"Generating {num_entries} realistic log entries...")
    
    log_entries = []
    
    # Configuration for realistic data
    log_levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    event_types = ['page_view', 'click', 'purchase', 'logout', 'login', 'search', 
                   'add_to_cart', 'checkout', 'api_call', 'download']
    devices = ['mobile', 'desktop', 'tablet']
    browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Mobile Safari']
    os_list = ['Windows', 'MacOS', 'Linux', 'iOS', 'Android']
    endpoints = ['/home', '/products', '/api/users', '/api/orders', '/checkout', 
                 '/search', '/profile', '/cart', '/api/items', '/downloads']
    http_methods = ['GET', 'POST', 'PUT', 'DELETE']
    status_codes = [200, 201, 400, 401, 403, 404, 500, 502, 503]
    
    start_date = datetime(2025, 10, 1)
    
    for i in range(num_entries):
        # Generate timestamp
        timestamp = start_date + timedelta(minutes=random.randint(0, 43200))
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Generate user info (5% null users for validation testing)
        if random.random() > 0.05:
            user_id = f"user_{random.randint(1, 1000)}"
        else:
            user_id = "NULL"
        
        session_id = f"sess_{random.randint(1, 5000)}"
        
        # Generate event details
        event_type = random.choice(event_types)
        log_level = random.choice(log_levels)
        
        # Weight error rates realistically
        if random.random() < 0.1:  # 10% warnings/errors
            log_level = random.choice(['WARN', 'ERROR'])
        
        # Generate request details
        method = random.choice(http_methods)
        endpoint = random.choice(endpoints)
        status_code = random.choice(status_codes)
        
        # Realistic response times (milliseconds)
        if status_code >= 500:
            response_time = random.randint(5000, 30000)  # Slow for errors
        elif status_code >= 400:
            response_time = random.randint(100, 1000)
        else:
            response_time = random.randint(10, 500)
        
        # Generate transaction value (for purchase events)
        if event_type in ['purchase', 'checkout']:
            value = round(random.uniform(10, 500), 2)
            high_value = 1 if value > 100 else 0
        else:
            value = round(random.uniform(0, 50), 2)
            high_value = 0
        
        # Device and browser info
        device = random.choice(devices)
        browser = random.choice(browsers)
        os = random.choice(os_list)
        ip_address = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        # Generate duration (seconds)
        duration = round(random.expovariate(1/30), 2)
        
        # Create log entry in a structured format
        # Format: TIMESTAMP | LEVEL | user_id | session_id | event_type | method | endpoint | 
        #         status | response_time | duration | value | high_value | device | browser | os | ip
        
        log_entry = (
            f"{timestamp_str} | {log_level} | {user_id} | {session_id} | {event_type} | "
            f"{method} | {endpoint} | {status_code} | {response_time}ms | {duration}s | "
            f"${value} | {high_value} | {device} | {browser} | {os} | {ip_address}"
        )
        
        log_entries.append(log_entry)
    
    return log_entries


def save_log_file(log_entries: list, output_dir: str, compressed: bool = True):
    """Save log entries to file
    
    Args:
        log_entries: List of log entry strings
        output_dir: Output directory path
        compressed: Whether to compress the output (gzip)
    """
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if compressed:
        output_file = output_path / "application.log.gz"
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            for entry in log_entries:
                f.write(entry + '\n')
        print(f"✓ Saved {len(log_entries)} log entries to {output_file}")
    else:
        output_file = output_path / "application.log"
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in log_entries:
                f.write(entry + '\n')
        print(f"✓ Saved {len(log_entries)} log entries to {output_file}")
    
    return output_file


def analyze_log_data(log_entries: list):
    """Print statistics about the generated log data"""
    
    print()
    print("=" * 60)
    print("Log Data Statistics:")
    print("=" * 60)
    print(f"  Total log entries: {len(log_entries):,}")
    
    # Count by event type
    event_counts = {}
    level_counts = {}
    status_counts = {}
    null_users = 0
    high_value_count = 0
    
    for entry in log_entries:
        parts = entry.split(' | ')
        if len(parts) >= 12:
            level = parts[1]
            user_id = parts[2]
            event_type = parts[4]
            status = parts[7]
            high_value = parts[11]
            
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            level_counts[level] = level_counts.get(level, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if user_id == "NULL":
                null_users += 1
            if high_value == "1":
                high_value_count += 1
    
    print(f"  NULL user_ids: {null_users:,} ({null_users/len(log_entries)*100:.1f}%)")
    print(f"  High-value events: {high_value_count:,} ({high_value_count/len(log_entries)*100:.1f}%)")
    
    print()
    print("Event type distribution:")
    for event, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {event:20s}: {count:,} ({count/len(log_entries)*100:.1f}%)")
    
    print()
    print("Log level distribution:")
    for level, count in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {level:20s}: {count:,} ({count/len(log_entries)*100:.1f}%)")
    
    print()
    print("Status code distribution:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {status:20s}: {count:,} ({count/len(log_entries)*100:.1f}%)")
    
    # Show sample log entries
    print()
    print("Sample log entries:")
    print("-" * 60)
    for entry in log_entries[:3]:
        print(entry)
    print("...")
    for entry in log_entries[-2:]:
        print(entry)


def main():
    """Main function"""
    
    print("=" * 60)
    print("Application Log File Generation")
    print("=" * 60)
    print()
    
    # Create output directories
    bronze_dir = Path("data/bronze/logs/date=2025-10-16")
    test_dir = Path("tests/fixtures")
    
    # Generate log entries
    log_entries = generate_log_entries(num_entries=10000)
    
    # Save to bronze layer (compressed)
    print()
    save_log_file(log_entries, bronze_dir, compressed=True)
    
    # Save smaller sample for tests (uncompressed)
    sample_logs = log_entries[:100]
    save_log_file(sample_logs, test_dir, compressed=False)
    
    # Analyze and print statistics
    analyze_log_data(log_entries)
    
    print()
    print("=" * 60)
    print("Log file generation complete!")
    print("=" * 60)
    print()
    print("Files created:")
    print(f"  - {bronze_dir}/application.log.gz (10,000 entries)")
    print(f"  - {test_dir}/application.log (100 entries for testing)")
    print()
    print("Next step: Run ETL pipeline to parse and process these logs!")
    print("=" * 60)


if __name__ == "__main__":
    main()

