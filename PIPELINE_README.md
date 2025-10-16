# OpenSSH Log Processing Pipeline

## 📋 Overview

This is a **3-layer data pipeline** (Bronze → Silver → Gold) that processes OpenSSH log files using **PySpark**.

### Pipeline Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Raw Log File (logs/OpenSSH_2k.log)                         │
│  - Unstructured text logs                                   │
│  - 2000 OpenSSH authentication events                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  BRONZE LAYER (scripts/bronze/raw_load.py)                  │
│  - Load raw logs as-is                                      │
│  - Save to Parquet format                                   │
│  - Output: data/bronze/raw_logs.parquet                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  SILVER LAYER (scripts/silver/silver_load.py)               │
│  - Parse log format                                         │
│  - Extract: Date, Day, Time, Component, Pid, Content        │
│  - Generate: EventId, EventTemplate                         │
│  - Apply quality checks                                     │
│  - Save to JSON format                                      │
│  - Output: data/silver/structured_logs.json                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  GOLD LAYER (scripts/gold/gold_load.py)                     │
│  - Combine Date+Day+Time → datetime                         │
│  - Filter quality-passed records                            │
│  - Save to CSV format                                       │
│  - Output: data/gold/openssh_logs_final.csv                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
contextq/
├── logs/
│   └── OpenSSH_2k.log                    # Source log file (2000 lines)
│
├── scripts/
│   ├── bronze/
│   │   └── raw_load.py                   # Bronze layer: Raw load
│   ├── silver/
│   │   └── silver_load.py                # Silver layer: Parse & transform
│   ├── gold/
│   │   └── gold_load.py                  # Gold layer: Final curated
│   └── run_pipeline.py                   # Master pipeline runner
│
├── data/
│   ├── bronze/
│   │   └── raw_logs.parquet              # Raw logs in Parquet
│   ├── silver/
│   │   └── structured_logs.json          # Parsed & validated JSON
│   └── gold/
│       └── openssh_logs_final.csv        # Final curated CSV
│
└── Data_file/
    └── OpenSSH_2k.log_structured.csv     # Reference format
```

---

## 🚀 Quick Start

### 1. Run Complete Pipeline

```bash
# Run all layers (Bronze → Silver → Gold)
python scripts/run_pipeline.py
```

### 2. Run Individual Layers

```bash
# Run only Bronze layer
python scripts/run_pipeline.py --layer bronze

# Run only Silver layer (requires Bronze to be run first)
python scripts/run_pipeline.py --layer silver

# Run only Gold layer (requires Silver to be run first)
python scripts/run_pipeline.py --layer gold
```

### 3. Run Scripts Directly

```bash
# Bronze layer
python scripts/bronze/raw_load.py

# Silver layer
python scripts/silver/silver_load.py

# Gold layer
python scripts/gold/gold_load.py
```

---

## 📊 Data Transformation Details

### Bronze Layer

**Input**: `logs/OpenSSH_2k.log`
```
Dec 10 06:55:46 LabSZ sshd[24200]: Invalid user webmaster from 173.234.31.186
```

**Output**: `data/bronze/raw_logs.parquet`
```
| LineId | raw_log                                                      | ingestion_timestamp     | source_file          |
|--------|--------------------------------------------------------------|-------------------------|----------------------|
| 1      | Dec 10 06:55:46 LabSZ sshd[24200]: Invalid user webmaster...| 2025-10-16 19:30:00    | logs/OpenSSH_2k.log  |
```

---

### Silver Layer

**Transformations**:
1. **Parse log fields**:
   - Date (month): `Dec`
   - Day: `10`
   - Time: `06:55:46`
   - Component: `LabSZ`
   - Pid: `24200`
   - Content: `Invalid user webmaster from 173.234.31.186`

2. **Generate event patterns**:
   - EventId: `E13`
   - EventTemplate: `Invalid user <*> from <*>`

3. **Quality checks**:
   - Completeness check
   - Time format validation
   - PID validation
   - Month validation

**Output**: `data/silver/structured_logs.json`
```json
{
  "LineId": 1,
  "Date": "Dec",
  "Day": "10",
  "Time": "06:55:46",
  "Component": "LabSZ",
  "Pid": "24200",
  "Content": "Invalid user webmaster from 173.234.31.186",
  "EventId": "E13",
  "EventTemplate": "Invalid user <*> from <*>",
  "overall_quality": "PASS"
}
```

---

### Gold Layer

**Transformations**:
1. **Combine datetime**: `Date + Day + Time` → `10-Dec-2024 : 06:55:46`
2. **Remove**: Original `Date`, `Day`, `Time` columns
3. **Filter**: Keep only quality-passed records

**Output**: `data/gold/openssh_logs_final.csv`
```csv
LineId,datetime,Component,Pid,EventId,EventTemplate,Content
1,10-Dec-2024 : 06:55:46,LabSZ,24200,E13,Invalid user <*> from <*>,Invalid user webmaster from 173.234.31.186
```

---

## 🔍 Data Quality Checks (Silver Layer)

The Silver layer applies comprehensive quality checks:

| Check | Description | Action |
|-------|-------------|--------|
| **Completeness** | Ensure required fields are not null/empty | Flag as FAIL |
| **Time Format** | Validate HH:MM:SS format | Flag as FAIL |
| **PID Validation** | Ensure PID is numeric | Flag as FAIL |
| **Month Validation** | Check valid month abbreviation | Flag as FAIL |
| **Overall Quality** | All checks must PASS | Filter in Gold layer |

---

## 📈 Event Categories

The pipeline recognizes these SSH event patterns:

| EventId | Event Type | Example |
|---------|-----------|---------|
| E27 | Reverse mapping check failed | `POSSIBLE BREAK-IN ATTEMPT!` |
| E13 | Invalid user | `Invalid user webmaster` |
| E12 | Invalid user auth request | `input_userauth_request: invalid user` |
| E21 | User unknown | `check pass; user unknown` |
| E19 | Authentication failure | `authentication failure` |
| E10 | Failed password (invalid user) | `Failed password for invalid user` |
| E2 | Connection closed | `Connection closed by` |
| E24 | Disconnect received | `Received disconnect` |
| E9 | Failed password | `Failed password for` |
| E18 | Accepted password | `Accepted password for` |

---

## 💾 Output Formats

| Layer | Format | Why? |
|-------|--------|------|
| **Bronze** | Parquet | Columnar storage, compressed, fast read |
| **Silver** | JSON | Flexible schema, human-readable, queryable |
| **Gold** | CSV | Business-friendly, Excel-compatible, portable |

---

## 🔧 Technical Details

### PySpark Configuration

Each layer uses PySpark with:
- **Master**: `local[*]` (all available cores)
- **Memory**: 2GB driver memory
- **App Name**: Layer-specific names

### Processing Mode

- **Bronze**: Append-only, immutable raw data
- **Silver**: Overwrite mode with quality filtering
- **Gold**: Overwrite mode with curated data

### Error Handling

- Bronze failures stop the pipeline
- Silver failures are logged with quality flags
- Gold only processes quality-passed records

---

## 📝 Example: Running the Pipeline

```bash
$ python scripts/run_pipeline.py

████████████████████████████████████████████████████████████████████████████████
█                                                                              █
█                  OpenSSH Log Processing Pipeline                            █
█                      Bronze → Silver → Gold                                 █
█                                                                              █
████████████████████████████████████████████████████████████████████████████████

Pipeline started at: 2025-10-16 19:30:00
Layers to run: BRONZE, SILVER, GOLD

==============================================================================
  Running BRONZE Layer
==============================================================================
Script: scripts/bronze/raw_load.py
...

✅ BRONZE layer completed successfully

==============================================================================
  Running SILVER Layer
==============================================================================
...

✅ SILVER layer completed successfully

==============================================================================
  Running GOLD Layer
==============================================================================
...

✅ GOLD layer completed successfully

==============================================================================
  PIPELINE SUMMARY
==============================================================================
Start Time:    2025-10-16 19:30:00
End Time:      2025-10-16 19:30:45
Duration:      0:00:45
Status:        ✅ SUCCESS
==============================================================================

🎉 Pipeline completed successfully!

Output locations:
  📁 Bronze: data/bronze/raw_logs.parquet
  📁 Silver: data/silver/structured_logs.json
  📁 Gold:   data/gold/openssh_logs_final.csv
```

---

## 🐛 Troubleshooting

### Issue: Java not found

```bash
# Install Java 11
brew install openjdk@11

# Set JAVA_HOME
export JAVA_HOME=/opt/homebrew/opt/openjdk@11
```

### Issue: PySpark not installed

```bash
pip install pyspark==3.4.1
```

### Issue: Bronze data not found

Make sure to run Bronze layer first:
```bash
python scripts/run_pipeline.py --layer bronze
```

---

## 📚 Documentation

- **LOG_FORMAT.md** - Log format specification
- **DATA_PIPELINE_STATUS.md** - Pipeline status and architecture
- **AZURE_ARCHITECTURE_PLAN.md** - Azure deployment plan

---

## ✅ Success Criteria

- ✅ Bronze: 2000 raw log lines converted to Parquet
- ✅ Silver: All 2000 lines parsed with quality checks
- ✅ Gold: ~1900-2000 quality-passed records in CSV
- ✅ datetime field combines Date+Day+Time correctly
- ✅ Original Date, Day, Time columns removed in Gold

---

## 🎯 Next Steps

1. ✅ Local pipeline complete
2. 🔄 Deploy to Azure Databricks
3. ⏳ Orchestrate with Azure Data Factory
4. ⏳ Add ML model training (anomaly detection)
5. ⏳ Set up CI/CD pipeline

---

**Created**: October 16, 2025  
**Pipeline Version**: 1.0  
**Author**: Data Engineering Team

