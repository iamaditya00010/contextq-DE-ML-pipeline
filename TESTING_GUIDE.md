# Quick Testing Guide

**Author:** Aditya Padhi

## Quick Start

### Prerequisites
```bash
# Install testing tools
pip install pytest pytest-cov

# Ensure pipeline has been run
python scripts/run_pipeline_pandas.py
python scripts/ml_anomaly_detection.py
```

### Run All Tests
```bash
python -m pytest tests/test_pipeline.py -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/test_pipeline.py --cov=scripts --cov-report=term-missing -v
```

## Test Summary

| Category | Tests | Description |
|----------|-------|-------------|
| **Data Validation** | 3 | Time format, PID, Month validation |
| **File Operations** | 3 | File existence, directories, outputs |
| **ML Model** | 3 | Model file, predictions, anomalies |
| **Data Quality** | 2 | Gold CSV, Silver JSON validation |
| **Total** | **11** | **100% pass rate** |

## What Gets Tested

✅ **Data Validation**
- Time format (HH:MM:SS)
- PID validation (numeric, non-empty)
- Month validation (Jan-Dec)

✅ **File Operations**
- Source log file exists
- Data directories exist
- Output files exist and not empty

✅ **ML Model**
- Trained model exists
- Predictions have correct format
- Anomaly scores are negative
- Anomaly flags are binary (0/1)

✅ **Data Quality**
- Gold layer CSV structure
- Silver layer JSON format
- Required columns present
- No null values in critical fields

## Expected Results

```
============================== test session starts ==============================
collected 11 items

tests/test_pipeline.py::TestDataValidation::test_time_format_validation PASSED [  9%]
tests/test_pipeline.py::TestDataValidation::test_pid_validation PASSED   [ 18%]
tests/test_pipeline.py::TestDataValidation::test_month_validation PASSED [ 27%]
tests/test_pipeline.py::TestFileOperations::test_source_log_file_exists PASSED [ 36%]
tests/test_pipeline.py::TestFileOperations::test_data_directories_exist PASSED [ 45%]
tests/test_pipeline.py::TestFileOperations::test_output_files_exist PASSED [ 54%]
tests/test_pipeline.py::TestMLModel::test_model_file_exists PASSED       [ 63%]
tests/test_pipeline.py::TestMLModel::test_predictions_format PASSED      [ 72%]
tests/test_pipeline.py::TestMLModel::test_anomaly_detection_results PASSED [ 81%]
tests/test_pipeline.py::TestDataQuality::test_gold_layer_data_quality PASSED [ 90%]
tests/test_pipeline.py::TestDataQuality::test_silver_layer_json_format PASSED [100%]

============================== 11 passed in 0.52s ==============================
```

## Troubleshooting

### Common Issues

**❌ Tests fail with "File not found"**
```bash
# Solution: Run the pipeline first
python scripts/run_pipeline_pandas.py
python scripts/ml_anomaly_detection.py
```

**❌ Coverage shows 0%**
```bash
# This is expected! Tests validate outputs, not code execution
# This is integration testing approach
```

**❌ pytest not found**
```bash
# Solution: Install pytest
pip install pytest pytest-cov
```

## More Information

- **Full Documentation:** [TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md)
- **Test Configuration:** `pytest.ini`
- **Test Files:** `tests/test_pipeline.py`

---

**Last Updated:** October 16, 2025  
**Framework:** pytest 7.4.4  
**Total Tests:** 11 (100% pass rate)
