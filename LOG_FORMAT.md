# Application Log Format Documentation

## Overview

The generated log files simulate a real-world web application's access and event logs. Each log entry contains structured information about user interactions, API requests, and system events.

---

## Log Format Specification

### Structure

Each log entry follows this pipe-delimited format:

```
TIMESTAMP | LEVEL | user_id | session_id | event_type | method | endpoint | status | response_time | duration | value | high_value | device | browser | os | ip
```

### Field Descriptions

| Field | Type | Description | Example | Notes |
|-------|------|-------------|---------|-------|
| `TIMESTAMP` | datetime | When the event occurred | `2025-10-16 14:23:45.123` | Format: YYYY-MM-DD HH:MM:SS.mmm |
| `LEVEL` | string | Log level | `INFO`, `WARN`, `ERROR`, `DEBUG` | Standard logging levels |
| `user_id` | string | Unique user identifier | `user_123` | NULL for ~5% of entries (testing validation) |
| `session_id` | string | Session identifier | `sess_4567` | Groups related events |
| `event_type` | string | Type of event | `purchase`, `login`, `click` | See Event Types below |
| `method` | string | HTTP method | `GET`, `POST`, `PUT`, `DELETE` | Standard HTTP verbs |
| `endpoint` | string | API endpoint | `/api/users`, `/checkout` | Application routes |
| `status` | integer | HTTP status code | `200`, `404`, `500` | Standard HTTP status codes |
| `response_time` | string | Server response time | `145ms` | Includes 'ms' suffix |
| `duration` | string | Event duration | `23.45s` | Includes 's' suffix |
| `value` | string | Transaction value | `$125.50` | Includes '$' prefix |
| `high_value` | integer | High-value flag | `0` or `1` | 1 if value > $100 |
| `device` | string | Device type | `mobile`, `desktop`, `tablet` | User's device |
| `browser` | string | Browser name | `Chrome`, `Firefox`, `Safari` | User's browser |
| `os` | string | Operating system | `Windows`, `MacOS`, `iOS` | User's OS |
| `ip` | string | IP address | `192.168.1.100` | Client IP (simulated) |

---

## Event Types

The logs contain 10 different event types:

| Event Type | Description | Frequency |
|------------|-------------|-----------|
| `page_view` | User viewed a page | ~10% |
| `click` | User clicked an element | ~10% |
| `purchase` | User made a purchase | ~10% |
| `logout` | User logged out | ~10% |
| `login` | User logged in | ~10% |
| `search` | User performed a search | ~10% |
| `add_to_cart` | Item added to cart | ~10% |
| `checkout` | User initiated checkout | ~10% |
| `api_call` | API request made | ~10% |
| `download` | File downloaded | ~10% |

---

## Log Levels

| Level | Purpose | Frequency |
|-------|---------|-----------|
| `INFO` | Normal operations | ~22% |
| `DEBUG` | Debugging information | ~23% |
| `WARN` | Warning conditions | ~28% |
| `ERROR` | Error conditions | ~27% |

---

## Sample Log Entries

### Normal Request
```
2025-10-16 14:23:45.123 | INFO | user_456 | sess_789 | page_view | GET | /home | 200 | 45ms | 12.3s | $0.0 | 0 | desktop | Chrome | Windows | 192.168.1.100
```

### Purchase Event (High Value)
```
2025-10-16 15:30:00.456 | INFO | user_789 | sess_123 | purchase | POST | /checkout | 200 | 234ms | 5.6s | $199.99 | 1 | mobile | Safari | iOS | 192.168.1.200
```

### Error Event
```
2025-10-16 16:45:12.789 | ERROR | user_123 | sess_456 | api_call | GET | /api/users | 500 | 15234ms | 30.2s | $0.0 | 0 | tablet | Firefox | Android | 192.168.1.50
```

### NULL User (Invalid)
```
2025-10-16 17:00:00.000 | WARN | NULL | sess_999 | click | GET | /products | 200 | 89ms | 2.1s | $0.0 | 0 | desktop | Edge | Windows | 192.168.1.75
```

---

## Data Characteristics

### Data Quality Issues (Intentional for Testing)

1. **NULL user_ids**: ~5% of entries have NULL user_id
   - Purpose: Test data validation and filtering
   - Should be rejected by ETL pipeline

2. **Varied Status Codes**: Mix of success, client errors, and server errors
   - Purpose: Test error handling and monitoring

3. **Response Time Variations**: 
   - Normal requests: 10-500ms
   - Client errors (4xx): 100-1000ms
   - Server errors (5xx): 5000-30000ms

### Business Logic

- **High-Value Events**: Transactions > $100 are flagged
- **Purchase/Checkout Events**: Have realistic transaction values ($10-$500)
- **Other Events**: Have minimal values ($0-$50)

---

## ETL Processing Guidelines

### Extraction
- Read compressed log files (.gz format)
- Support both compressed and uncompressed formats
- Handle pipe-delimited parsing

### Transformation Required

1. **Parse Fields**:
   - Extract and clean each field
   - Remove suffixes (ms, s, $)
   - Convert data types appropriately

2. **Data Cleaning**:
   - Filter out NULL user_ids
   - Standardize text fields (lowercase)
   - Parse timestamps correctly

3. **Validation**:
   - Ensure required fields are present
   - Validate timestamp format
   - Check data type consistency

4. **Derived Columns**:
   - Extract date from timestamp (for partitioning)
   - Calculate processing metadata
   - Categorize events (transaction, engagement, auth, etc.)

### Load
- Save as Delta Lake or Parquet format
- Partition by processing_date
- Maintain data lineage

---

## Statistics (10,000 entries)

- **Total Entries**: 10,000
- **NULL Users**: ~470 (4.7%)
- **High-Value Events**: ~1,636 (16.4%)
- **Date Range**: 30 days (Oct 1-30, 2025)
- **Compressed Size**: ~311 KB
- **Uncompressed Size**: ~1.5 MB

---

## Usage in ETL Pipeline

### PySpark Example

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Read log file
df = spark.read.text("application.log.gz")

# Parse log entries
parsed_df = df.select(
    F.split(F.col("value"), r" \| ").alias("fields")
).select(
    F.col("fields")[0].alias("timestamp"),
    F.col("fields")[1].alias("level"),
    F.col("fields")[2].alias("user_id"),
    F.col("fields")[3].alias("session_id"),
    F.col("fields")[4].alias("event_type"),
    # ... parse remaining fields
)

# Clean and validate
clean_df = parsed_df \
    .filter(F.col("user_id") != "NULL") \
    .withColumn("timestamp", F.to_timestamp("timestamp")) \
    .withColumn("response_time", F.regexp_replace("response_time", "ms", "").cast("integer"))
```

---

## Files Generated

1. **Bronze Layer** (Raw): `data/bronze/logs/date=2025-10-16/application.log.gz`
   - 10,000 entries
   - Compressed format
   - Used for ETL processing

2. **Test Fixtures**: `tests/fixtures/application.log`
   - 100 entries
   - Uncompressed format
   - Used for unit testing

---

## Next Steps

1. ✅ Log files generated
2. 🔄 **Create ETL pipeline** to parse logs
3. ⏳ Transform and validate data
4. ⏳ Save to Silver layer (Delta Lake)
5. ⏳ Train ML model on processed data

---

**Generated**: October 16, 2025  
**Format Version**: 1.0  
**Total Entries**: 10,000

