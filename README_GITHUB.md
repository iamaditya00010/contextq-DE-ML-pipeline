# 🔐 DE Log Processing & ML Pipeline with Anomaly Detection

A production-ready **3-layer data pipeline** (Bronze → Silver → Gold) for processing OpenSSH authentication logs with **ML-powered anomaly detection**.

**Author:** Aditya Padhi

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PySpark](https://img.shields.io/badge/PySpark-3.4.1-orange.svg)](https://spark.apache.org/)
[![scikit--learn](https://img.shields.io/badge/scikit--learn-Latest-green.svg)](https://scikit-learn.org/)

---

## 🏗️ Architecture

```
Raw OpenSSH Logs (2,000 events)
         ↓
   ┌──────────┐
   │  BRONZE  │  Raw → Parquet
   └──────────┘
         ↓
   ┌──────────┐
   │  SILVER  │  Parse, Transform, Quality → JSON
   └──────────┘
         ↓
   ┌──────────┐
   │   GOLD   │  Combine datetime → CSV
   └──────────┘
         ↓
   ┌──────────┐
   │    ML    │  Anomaly Detection (Isolation Forest)
   └──────────┘
```

---

## ✨ Features

- **3-Layer Data Pipeline** (Medallion Architecture)
- **PySpark Implementation** (Databricks-ready)
- **Data Quality Checks** (4 comprehensive validations)
- **ML Anomaly Detection** (Isolation Forest)
- **Dual Implementation** (PySpark + Pandas for local testing)
- **Complete Documentation**

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.10+
pip install -r requirements.txt
```

### Run Pipeline

```bash
# Run complete ETL pipeline (Bronze → Silver → Gold)
python scripts/run_pipeline_pandas.py

# Run ML anomaly detection
python scripts/ml_anomaly_detection.py
```

---

## 📊 Data Flow

### Bronze Layer
- **Input**: Raw OpenSSH log files
- **Process**: Load as-is
- **Output**: `data/bronze/raw_logs.parquet`
- **Script**: `scripts/bronze/raw_load.py`

### Silver Layer
- **Input**: Bronze Parquet
- **Process**: 
  - Parse log format
  - Extract fields (Date, Time, Component, Pid, Content)
  - Generate EventId & EventTemplate
  - Apply quality checks
- **Output**: `data/silver/structured_logs.json`
- **Script**: `scripts/silver/silver_load.py`

### Gold Layer
- **Input**: Silver JSON
- **Process**:
  - Combine Date + Day + Time → datetime
  - Remove original date/time columns
  - Filter quality-passed records
- **Output**: `data/gold/openssh_logs_final.csv`
- **Script**: `scripts/gold/gold_load.py`

### ML Layer
- **Input**: Gold CSV
- **Process**: Anomaly detection using Isolation Forest
- **Output**: 
  - Trained model: `models/anomaly_model.pkl`
  - Predictions: `data/ml_output/anomaly_predictions.csv`
  - Anomalies: `data/ml_output/detected_anomalies.csv`
- **Script**: `scripts/ml_anomaly_detection.py`

---

## 🤖 ML Model Details

### Anomaly Detection

**Model**: Isolation Forest (Unsupervised Learning)

**Purpose**: Detect suspicious SSH login attempts

**Features**:
- Event type patterns
- Time of day
- Failed login indicators
- Invalid user attempts
- Break-in attempt flags
- Event rarity scores

**Results** (on 2,000 records):
- Detected 170 anomalies (8.5%)
- Peak anomaly hours: 07:00-08:00
- Top anomaly types: Failed passwords, Invalid users

---

## 📁 Project Structure

```
data-pipeline-openssh/
├── scripts/
│   ├── bronze/
│   │   └── raw_load.py              # PySpark: Bronze layer
│   ├── silver/
│   │   └── silver_load.py           # PySpark: Silver layer
│   ├── gold/
│   │   └── gold_load.py             # PySpark: Gold layer
│   ├── ml_anomaly_detection.py      # ML: Anomaly detection
│   └── run_pipeline_pandas.py       # Master runner (Pandas)
│
├── logs/
│   └── OpenSSH_2k.log               # Source data (2,000 lines)
│
├── docs/
│   ├── PIPELINE_README.md           # Detailed documentation
│   ├── PIPELINE_COMPLETE.md         # Implementation summary
│   └── LOG_FORMAT.md                # Log format spec
│
├── requirements.txt                  # Python dependencies
└── README.md                        # This file
```

---

## 📋 Data Quality Checks

The Silver layer implements 4 quality checks:

1. **Completeness**: Required fields not null/empty
2. **Time Format**: Valid HH:MM:SS format
3. **PID Validation**: Numeric and not empty
4. **Month Validation**: Valid month abbreviation

**Result**: 100% of records passed quality checks ✅

---

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Data Processing** | PySpark 3.4.1, Pandas |
| **ML Model** | scikit-learn (Isolation Forest) |
| **Storage Formats** | Parquet, JSON, CSV |
| **Deployment** | Azure Databricks, Azure Data Factory |
| **CI/CD** | GitHub Actions (planned) |

---

## 📊 Sample Output

### Gold Layer CSV

```csv
LineId,datetime,Component,Pid,EventId,EventTemplate,Content
1,10-Dec-2024 : 06:55:46,LabSZ,24200,E27,reverse mapping...,reverse mapping...
2,10-Dec-2024 : 06:55:46,LabSZ,24200,E13,Invalid user <*>...,Invalid user webmaster...
```

### ML Predictions

```csv
LineId,datetime,EventId,is_anomaly,anomaly_score
6,10-Dec-2024 : 06:55:48,E10,1,-0.106232
1,10-Dec-2024 : 06:55:46,E27,1,-0.097716
```

---

##  Use Cases

1. **Security Monitoring**: Detect brute force attacks
2. **Threat Intelligence**: Identify suspicious IPs
3. **Compliance**: Audit SSH access patterns
4. **ML Training**: Security event classification

---

## 📚 Documentation

- **PIPELINE_README.md** - Complete pipeline documentation
- **PIPELINE_COMPLETE.md** - Implementation summary
- **LOG_FORMAT.md** - Log format specification

---

## 🚀 Deployment

### Local Development
```bash
python scripts/run_pipeline_pandas.py
```

### Azure Databricks
1. Upload scripts to `/Workspace/production/`
2. Configure Azure Data Factory pipeline
3. Schedule daily runs

---

## 📈 Performance

- **Pipeline Speed**: <1 second (2,000 records)
- **ML Training**: <1 second
- **Scalability**: Tested up to 10,000 records
- **Quality**: 100% pass rate

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file

---

## 👨‍💻 Author

Data Engineering Team

---

## 🎉 Acknowledgments

- Built for Data & AI Engineering Assignment
- Uses Apache Spark, scikit-learn
- Follows Azure best practices

---

**⭐ If you find this useful, please star the repository!**

