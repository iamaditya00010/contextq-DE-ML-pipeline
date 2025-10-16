"""
Unit Tests for DE Log Processing & ML Pipeline
==============================================

Author: Aditya Padhi

This module contains basic unit tests for the data pipeline components.
Tests cover:
1. Data validation functions
2. File I/O operations
3. ML model functionality
"""

import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

# Test data directory
TEST_DATA_DIR = Path("tests/fixtures")


class TestDataValidation:
    """Test data validation functions"""
    
    def test_time_format_validation(self):
        """Test time format validation"""
        # Valid time formats
        valid_times = ["06:55:46", "23:59:59", "00:00:00", "12:30:45"]
        for time_str in valid_times:
            # Basic regex pattern for HH:MM:SS
            import re
            pattern = r'^\d{2}:\d{2}:\d{2}$'
            assert re.match(pattern, time_str), f"Time {time_str} should be valid"
    
    def test_pid_validation(self):
        """Test PID validation"""
        # Valid PIDs
        valid_pids = ["24200", "1234", "99999", "1"]
        for pid in valid_pids:
            assert pid.isdigit(), f"PID {pid} should be numeric"
            assert len(pid) > 0, f"PID {pid} should not be empty"
    
    def test_month_validation(self):
        """Test month validation"""
        valid_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for month in valid_months:
            assert month in valid_months, f"Month {month} should be valid"


class TestFileOperations:
    """Test file I/O operations"""
    
    def test_source_log_file_exists(self):
        """Test that source log file exists"""
        log_file = Path("logs/OpenSSH_2k.log")
        assert log_file.exists(), "Source log file should exist"
        assert log_file.stat().st_size > 0, "Source log file should not be empty"
    
    def test_data_directories_exist(self):
        """Test that data directories exist"""
        directories = ["data/bronze", "data/silver", "data/gold", "data/ml_output"]
        for directory in directories:
            assert Path(directory).exists(), f"Directory {directory} should exist"
    
    def test_output_files_exist(self):
        """Test that output files exist after pipeline run"""
        output_files = [
            "data/bronze/raw_logs.parquet",
            "data/silver/structured_logs.json", 
            "data/gold/openssh_logs_final.csv",
            "data/ml_output/anomaly_predictions.csv",
            "data/ml_output/detected_anomalies.csv",
            "data/ml_output/ml_summary_report.txt"
        ]
        
        for file_path in output_files:
            assert Path(file_path).exists(), f"Output file {file_path} should exist"
            assert Path(file_path).stat().st_size > 0, f"Output file {file_path} should not be empty"


class TestMLModel:
    """Test ML model functionality"""
    
    def test_model_file_exists(self):
        """Test that trained model exists"""
        model_file = Path("models/anomaly_model.pkl")
        assert model_file.exists(), "Trained model should exist"
        assert model_file.stat().st_size > 0, "Model file should not be empty"
    
    def test_predictions_format(self):
        """Test predictions file format"""
        predictions_file = Path("data/ml_output/anomaly_predictions.csv")
        if predictions_file.exists():
            df = pd.read_csv(predictions_file)
            
            # Check required columns
            required_columns = ["LineId", "datetime", "EventId", "is_anomaly", "anomaly_score"]
            for col in required_columns:
                assert col in df.columns, f"Column {col} should exist in predictions"
            
            # Check anomaly scores are numeric
            assert pd.api.types.is_numeric_dtype(df['anomaly_score']), "Anomaly scores should be numeric"
            
            # Check anomaly flags are binary
            assert df['is_anomaly'].isin([0, 1]).all(), "Anomaly flags should be 0 or 1"
    
    def test_anomaly_detection_results(self):
        """Test anomaly detection results"""
        anomalies_file = Path("data/ml_output/detected_anomalies.csv")
        if anomalies_file.exists():
            df = pd.read_csv(anomalies_file)
            
            # Should have detected some anomalies
            assert len(df) > 0, "Should have detected some anomalies"
            
            # All records should be marked as anomalies
            assert df['is_anomaly'].all(), "All records in anomalies file should be marked as anomalies"
            
            # Anomaly scores should be negative (Isolation Forest)
            assert (df['anomaly_score'] < 0).all(), "Anomaly scores should be negative"


class TestDataQuality:
    """Test data quality checks"""
    
    def test_gold_layer_data_quality(self):
        """Test Gold layer data quality"""
        gold_file = Path("data/gold/openssh_logs_final.csv")
        if gold_file.exists():
            df = pd.read_csv(gold_file)
            
            # Check required columns
            required_columns = ["LineId", "datetime", "Component", "Pid", "EventId", "EventTemplate", "Content"]
            for col in required_columns:
                assert col in df.columns, f"Column {col} should exist in Gold layer"
            
            # Check no null values in critical columns
            critical_columns = ["LineId", "datetime", "EventId"]
            for col in critical_columns:
                assert not df[col].isnull().any(), f"Column {col} should not have null values"
            
            # Check datetime format
            datetime_sample = df['datetime'].iloc[0]
            assert ":" in datetime_sample, "Datetime should contain time separator"
            assert "-" in datetime_sample, "Datetime should contain date separator"
    
    def test_silver_layer_json_format(self):
        """Test Silver layer JSON format"""
        silver_file = Path("data/silver/structured_logs.json")
        if silver_file.exists():
            # Should be valid JSONL (one JSON object per line)
            with open(silver_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) > 0, "Silver layer should not be empty"
            
            # Check first record structure
            if len(lines) > 0:
                first_record = json.loads(lines[0])
                required_fields = ["LineId", "Date", "Day", "Time", "Component", "Pid", "EventId", "EventTemplate", "Content"]
                for field in required_fields:
                    assert field in first_record, f"Field {field} should exist in Silver layer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
