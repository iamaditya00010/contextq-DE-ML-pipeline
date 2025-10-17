"""
Pipeline Metrics Exporter
=========================
This script collects metrics from the data pipeline and exposes them to Prometheus.

Author: Aditya Padhi

Metrics collected:
- Pipeline execution status
- Data processing counts
- Error rates
- Processing times
- ML model performance
"""

import time
import json
import os
from datetime import datetime
from prometheus_client import start_http_server, Counter, Histogram, Gauge, Info
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
pipeline_executions_total = Counter('pipeline_executions_total', 'Total pipeline executions', ['pipeline_name', 'status'])
pipeline_duration_seconds = Histogram('pipeline_duration_seconds', 'Pipeline execution duration', ['pipeline_name'])
data_records_processed = Counter('data_records_processed_total', 'Total records processed', ['layer', 'status'])
ml_model_predictions = Counter('ml_model_predictions_total', 'Total ML model predictions', ['model_name', 'prediction_type'])
pipeline_errors_total = Counter('pipeline_errors_total', 'Total pipeline errors', ['pipeline_name', 'error_type'])
active_pipelines = Gauge('active_pipelines', 'Number of active pipelines')
pipeline_info = Info('pipeline_info', 'Pipeline information')

class PipelineMetricsExporter:
    """Exports pipeline metrics to Prometheus"""
    
    def __init__(self, port=8080):
        self.port = port
        self.start_time = time.time()
        
    def start_server(self):
        """Start the Prometheus metrics server"""
        try:
            start_http_server(self.port)
            logger.info(f"Metrics server started on port {self.port}")
            
            # Set pipeline info
            pipeline_info.info({
                'version': '1.0.0',
                'author': 'Aditya Padhi',
                'description': 'DE Log Processing & ML Pipeline with Anomaly Detection'
            })
            
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise
    
    def record_pipeline_execution(self, pipeline_name, status, duration=None):
        """Record pipeline execution metrics"""
        pipeline_executions_total.labels(pipeline_name=pipeline_name, status=status).inc()
        
        if duration is not None:
            pipeline_duration_seconds.labels(pipeline_name=pipeline_name).observe(duration)
        
        logger.info(f"Recorded pipeline execution: {pipeline_name} - {status} - {duration}s")
    
    def record_data_processing(self, layer, status, count):
        """Record data processing metrics"""
        data_records_processed.labels(layer=layer, status=status).inc(count)
        logger.info(f"Recorded data processing: {layer} - {status} - {count} records")
    
    def record_ml_prediction(self, model_name, prediction_type, count=1):
        """Record ML model prediction metrics"""
        ml_model_predictions.labels(model_name=model_name, prediction_type=prediction_type).inc(count)
        logger.info(f"Recorded ML prediction: {model_name} - {prediction_type} - {count}")
    
    def record_error(self, pipeline_name, error_type):
        """Record pipeline error metrics"""
        pipeline_errors_total.labels(pipeline_name=pipeline_name, error_type=error_type).inc()
        logger.warning(f"Recorded pipeline error: {pipeline_name} - {error_type}")
    
    def update_active_pipelines(self, count):
        """Update active pipelines gauge"""
        active_pipelines.set(count)
        logger.info(f"Updated active pipelines: {count}")
    
    def read_pipeline_logs(self, log_file_path):
        """Read and parse pipeline logs to extract metrics"""
        try:
            if not os.path.exists(log_file_path):
                logger.warning(f"Log file not found: {log_file_path}")
                return
            
            with open(log_file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse log lines for metrics
            bronze_count = 0
            silver_count = 0
            gold_count = 0
            ml_predictions = 0
            errors = 0
            
            for line in lines:
                if '[BRONZE]' in line and 'records loaded' in line:
                    try:
                        bronze_count = int(line.split('records loaded: ')[1].strip())
                    except:
                        pass
                elif '[SILVER]' in line and 'records processed' in line:
                    try:
                        silver_count = int(line.split('records processed: ')[1].strip())
                    except:
                        pass
                elif '[GOLD]' in line and 'records processed' in line:
                    try:
                        gold_count = int(line.split('records processed: ')[1].strip())
                    except:
                        pass
                elif 'anomalies detected' in line:
                    try:
                        ml_predictions = int(line.split('Anomalies detected: ')[1].strip())
                    except:
                        pass
                elif '[ERROR]' in line:
                    errors += 1
            
            # Record metrics
            if bronze_count > 0:
                self.record_data_processing('bronze', 'success', bronze_count)
            if silver_count > 0:
                self.record_data_processing('silver', 'success', silver_count)
            if gold_count > 0:
                self.record_data_processing('gold', 'success', gold_count)
            if ml_predictions > 0:
                self.record_ml_prediction('anomaly_detection', 'anomaly', ml_predictions)
            if errors > 0:
                self.record_error('pipeline', 'processing_error')
            
            logger.info(f"Parsed log metrics: Bronze={bronze_count}, Silver={silver_count}, Gold={gold_count}, ML={ml_predictions}, Errors={errors}")
            
        except Exception as e:
            logger.error(f"Error reading pipeline logs: {e}")
    
    def simulate_pipeline_metrics(self):
        """Simulate pipeline metrics for testing - RUN ONCE ONLY"""
        logger.info("Simulating pipeline metrics (one-time execution)...")
        
        # Simulate Bronze layer
        self.record_pipeline_execution('bronze_layer', 'success', 2.5)
        self.record_data_processing('bronze', 'success', 2000)
        
        # Simulate Silver layer
        self.record_pipeline_execution('silver_layer', 'success', 5.2)
        self.record_data_processing('silver', 'success', 2000)
        
        # Simulate Gold layer
        self.record_pipeline_execution('gold_layer', 'success', 1.8)
        self.record_data_processing('gold', 'success', 2000)
        
        # Simulate ML layer
        self.record_pipeline_execution('ml_layer', 'success', 8.3)
        self.record_ml_prediction('anomaly_detection', 'anomaly', 170)
        self.record_ml_prediction('anomaly_detection', 'normal', 1830)
        
        # Set active pipelines
        self.update_active_pipelines(1)
        
        logger.info("Pipeline metrics simulation completed (one-time)")

def main():
    """Main function to run the metrics exporter"""
    logger.info("Starting Pipeline Metrics Exporter")
    
    # Create metrics exporter
    exporter = PipelineMetricsExporter(port=8080)
    
        try:
            # Start Prometheus server
            exporter.start_server()
            
            # Simulate metrics ONCE ONLY (not continuously)
            exporter.simulate_pipeline_metrics()
            
            # Keep the server running but don't update metrics continuously
            logger.info("Metrics exporter is running. Metrics are static. Press Ctrl+C to stop.")
            while True:
                time.sleep(300)  # Sleep for 5 minutes instead of 60 seconds
                logger.info("Metrics exporter still running (metrics are static)")
                
        except KeyboardInterrupt:
            logger.info("Metrics exporter stopped by user")
        except Exception as e:
            logger.error(f"Metrics exporter error: {e}")
            raise

if __name__ == "__main__":
    main()
