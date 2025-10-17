# Observability Implementation Guide

**Author: Aditya Padhi**

This document explains the complete observability implementation for the DE Log Processing & ML Pipeline, covering the journey from raw logs to Prometheus metrics to Grafana dashboards.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Implementation Details](#implementation-details)
5. [Metrics Collection](#metrics-collection)
6. [Prometheus Configuration](#prometheus-configuration)
7. [Grafana Dashboard](#grafana-dashboard)
8. [Monitoring Setup](#monitoring-setup)
9. [Troubleshooting](#troubleshooting)

## Overview

The observability stack provides comprehensive monitoring for the data pipeline, including:

- **Pipeline Execution Metrics**: Success/failure rates, execution times
- **Data Processing Metrics**: Record counts, processing rates by layer
- **ML Model Metrics**: Prediction counts, anomaly detection rates
- **System Health**: Active pipelines, error rates
- **Real-time Visualization**: Live dashboards with manual refresh

## Architecture

```
Raw Logs → Metrics Exporter → Prometheus → Grafana Dashboard
```

The complete flow works as follows:

1. **Raw Logs**: OpenSSH log files are processed through Bronze, Silver, Gold layers
2. **Metrics Exporter**: Python application collects execution metrics and exposes them
3. **Prometheus**: Scrapes metrics from the exporter and stores time-series data
4. **Grafana**: Queries Prometheus and visualizes metrics in real-time dashboards

## Components

### 1. Metrics Exporter (`pipeline-metrics-exporter`)

**Purpose**: Collects and exposes pipeline metrics in Prometheus format

**Location**: `scripts/metrics_exporter.py`

**Key Features**:
- Exposes metrics on port 8080
- Generates static pipeline metrics (one-time execution)
- Uses Prometheus Python client library
- Runs as Kubernetes pod with ConfigMap

**Metrics Exposed**:
- `pipeline_executions_total`: Counter of pipeline executions by layer
- `pipeline_duration_seconds`: Histogram of execution times
- `data_records_processed_total`: Counter of processed records by layer
- `ml_model_predictions_total`: Counter of ML predictions by type
- `pipeline_errors_total`: Counter of pipeline errors
- `active_pipelines`: Gauge of currently active pipelines

### 2. Prometheus Server

**Purpose**: Time-series database for metrics collection and querying

**Configuration**: `kubernetes/prometheus-pod.yaml`

**Key Features**:
- Scrapes metrics from multiple targets
- Stores time-series data
- Provides query API
- Service discovery for Kubernetes pods

**Scrape Targets**:
- `prometheus` (self-monitoring)
- `pipeline-metrics-exporter` (our pipeline metrics)
- `databricks-metrics` (external Databricks)
- `mlflow-metrics` (external MLflow)

### 3. Grafana Dashboard

**Purpose**: Visualization and alerting platform

**Configuration**: `kubernetes/grafana-fixed.yaml`

**Key Features**:
- Pre-configured dashboard
- Manual refresh (no auto-refresh)
- Multiple panel types (stat, timeseries, piechart, gauge)
- Dark theme for better visibility

## Implementation Details

### Metrics Exporter Implementation

The metrics exporter is implemented as a Python application using the `prometheus_client` library:

```python
from prometheus_client import start_http_server, Counter, Histogram, Gauge, Info

# Define metrics
pipeline_executions_total = Counter('pipeline_executions_total', 
                                   'Total pipeline executions', 
                                   ['pipeline_name', 'status'])

pipeline_duration_seconds = Histogram('pipeline_duration_seconds', 
                                     'Pipeline execution duration', 
                                     ['pipeline_name'])

data_records_processed = Counter('data_records_processed_total', 
                                'Total records processed', 
                                ['layer', 'status'])

ml_model_predictions = Counter('ml_model_predictions_total', 
                              'Total ML model predictions', 
                              ['model_name', 'prediction_type'])

active_pipelines = Gauge('active_pipelines', 'Number of active pipelines')
```

### Kubernetes Deployment

The metrics exporter is deployed as a Kubernetes pod with:

- **Image**: `python:3.9-slim`
- **Port**: 8080
- **Resources**: 128Mi memory, 100m CPU (requests)
- **ConfigMap**: Contains the Python script
- **Service**: ClusterIP service for internal access

### Prometheus Configuration

Prometheus is configured to scrape the metrics exporter using a static target:

```yaml
scrape_configs:
  - job_name: 'pipeline-metrics-exporter'
    static_configs:
      - targets: ['pipeline-metrics-service:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Metrics Collection

### Pipeline Execution Metrics

**Metric**: `pipeline_executions_total`

**Labels**:
- `pipeline_name`: bronze_layer, silver_layer, gold_layer, ml_layer
- `status`: success, failed

**Example Values**:
```
pipeline_executions_total{pipeline_name="bronze_layer",status="success"} 4
pipeline_executions_total{pipeline_name="silver_layer",status="success"} 4
pipeline_executions_total{pipeline_name="gold_layer",status="success"} 4
pipeline_executions_total{pipeline_name="ml_layer",status="success"} 4
```

### Data Processing Metrics

**Metric**: `data_records_processed_total`

**Labels**:
- `layer`: bronze, silver, gold
- `status`: success, failed

**Example Values**:
```
data_records_processed_total{layer="bronze",status="success"} 2000
data_records_processed_total{layer="silver",status="success"} 2000
data_records_processed_total{layer="gold",status="success"} 2000
```

### ML Model Metrics

**Metric**: `ml_model_predictions_total`

**Labels**:
- `model_name`: anomaly_detection
- `prediction_type`: anomaly, normal

**Example Values**:
```
ml_model_predictions_total{model_name="anomaly_detection",prediction_type="anomaly"} 170
ml_model_predictions_total{model_name="anomaly_detection",prediction_type="normal"} 1830
```

### Pipeline Duration Metrics

**Metric**: `pipeline_duration_seconds`

**Type**: Histogram

**Labels**:
- `pipeline_name`: bronze_layer, silver_layer, gold_layer, ml_layer

**Buckets**: 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, +Inf

## Prometheus Configuration

### Service Discovery

Prometheus uses multiple discovery methods:

1. **Static Targets**: For known services like our metrics exporter
2. **Kubernetes Service Discovery**: For dynamic pod discovery
3. **Self-Monitoring**: Prometheus monitors itself

### Scrape Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  # Pipeline metrics
  - job_name: 'pipeline-metrics-exporter'
    static_configs:
      - targets: ['pipeline-metrics-service:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
  
  # External services (optional)
  - job_name: 'databricks-metrics'
    static_configs:
      - targets: ['databricks-cluster:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Data Retention

- **Retention Time**: 200 hours (8.3 days)
- **Storage Path**: `/prometheus`
- **Storage Type**: EmptyDir (ephemeral)

## Grafana Dashboard

### Dashboard Configuration

**Title**: "DE Log Processing Pipeline Dashboard"

**Panels**:

1. **Pipeline Executions** (Stat Panel)
   - Query: `sum(pipeline_executions_total)`
   - Color: Green
   - Shows total pipeline executions across all layers

2. **Data Records Processed** (Stat Panel)
   - Query: `sum(data_records_processed_total)`
   - Color: Blue
   - Shows total records processed across all layers

3. **ML Model Predictions** (Stat Panel)
   - Query: `sum(ml_model_predictions_total)`
   - Color: Purple
   - Shows total ML model predictions

4. **Pipeline Duration by Layer** (Time Series)
   - Query: `pipeline_duration_seconds_sum`
   - Legend: `{{pipeline_name}}`
   - Shows execution time trends by layer

5. **Data Processing by Layer** (Time Series)
   - Query: `data_records_processed_total`
   - Legend: `{{layer}} - {{status}}`
   - Shows processing volume trends by layer

6. **ML Predictions by Type** (Pie Chart)
   - Query: `ml_model_predictions_total`
   - Legend: `{{prediction_type}}`
   - Shows distribution of anomaly vs normal predictions

7. **Active Pipelines** (Gauge)
   - Query: `active_pipelines`
   - Thresholds: Red (0), Yellow (1), Green (2+)
   - Shows current number of active pipelines

### Dashboard Settings

- **Time Range**: Last 1 hour
- **Refresh Interval**: Manual (0)
- **Theme**: Dark
- **Timezone**: Browser

## Monitoring Setup

### Prerequisites

1. **Kubernetes Cluster**: AKS cluster running
2. **kubectl**: Configured to access the cluster
3. **Git**: For code deployment

### Deployment Steps

1. **Deploy Metrics Exporter**:
   ```bash
   kubectl apply -f kubernetes/pipeline-metrics-exporter.yaml
   ```

2. **Deploy Prometheus**:
   ```bash
   kubectl apply -f kubernetes/prometheus-pod.yaml
   ```

3. **Deploy Grafana**:
   ```bash
   kubectl apply -f kubernetes/grafana-fixed.yaml
   ```

4. **Verify Deployment**:
   ```bash
   kubectl get pods -l app=prometheus
   kubectl get pods -l app=grafana
   kubectl get pods -l app=pipeline-metrics-exporter
   ```

### Access URLs

- **Prometheus**: http://52.249.210.79:9090
- **Grafana**: http://4.156.146.36:3000
  - Username: admin
  - Password: admin123

### Port Forwarding (Local Access)

```bash
# Prometheus
kubectl port-forward service/prometheus-service 9090:9090

# Grafana
kubectl port-forward service/grafana-service 3000:3000

# Metrics Exporter
kubectl port-forward service/pipeline-metrics-service 8080:8080
```

## Troubleshooting

### Common Issues

1. **No Data in Dashboard**
   - Check if Prometheus is scraping metrics exporter
   - Verify metrics exporter is running and exposing metrics
   - Check Prometheus targets: http://prometheus:9090/targets

2. **Multiple Prometheus Pods**
   - Clean up old ReplicaSets: `kubectl delete replicaset <old-rs-name>`
   - Scale deployment: `kubectl scale deployment prometheus --replicas=1`

3. **Metrics Exporter Not Discovered**
   - Use static target instead of Kubernetes service discovery
   - Reload Prometheus config: `curl -X POST http://prometheus:9090/-/reload`

4. **Dashboard Not Loading**
   - Check Grafana logs: `kubectl logs deployment/grafana`
   - Verify dashboard JSON format
   - Restart Grafana: `kubectl rollout restart deployment/grafana`

5. **Metrics Continuously Updating**
   - Metrics exporter runs simulation only once
   - Dashboard refresh is set to manual (0)
   - Values remain static until manually refreshed

### Verification Commands

```bash
# Check pod status
kubectl get pods -l app=prometheus
kubectl get pods -l app=grafana
kubectl get pods -l app=pipeline-metrics-exporter

# Check services
kubectl get services prometheus-service grafana-service pipeline-metrics-service

# Check metrics
curl -s http://localhost:8080/metrics | grep pipeline_executions_total

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[]'

# Check Prometheus queries
curl -s "http://localhost:9090/api/v1/query?query=pipeline_executions_total"
```

### Log Analysis

```bash
# Metrics exporter logs
kubectl logs deployment/pipeline-metrics-exporter --tail=20

# Prometheus logs
kubectl logs deployment/prometheus --tail=20

# Grafana logs
kubectl logs deployment/grafana --tail=20
```

## Performance Considerations

### Resource Usage

- **Metrics Exporter**: 128Mi memory, 100m CPU
- **Prometheus**: 512Mi memory, 250m CPU
- **Grafana**: 256Mi memory, 100m CPU

### Scaling Considerations

- **Metrics Exporter**: Single instance sufficient for MVP
- **Prometheus**: Can be scaled with remote storage for production
- **Grafana**: Can be scaled horizontally with shared database

### Data Volume

- **Metrics Retention**: 200 hours
- **Scrape Interval**: 15 seconds
- **Estimated Storage**: ~100MB per day for current metrics

## Future Enhancements

1. **Alerting**: Add Prometheus alerting rules
2. **Log Aggregation**: Integrate with ELK stack
3. **Distributed Tracing**: Add OpenTelemetry support
4. **Custom Metrics**: Add business-specific metrics
5. **Multi-Environment**: Support for dev/staging/prod environments

## Conclusion

The observability implementation provides comprehensive monitoring for the data pipeline, enabling:

- **Real-time Monitoring**: Live dashboards with manual refresh
- **Performance Tracking**: Execution times and throughput metrics
- **Error Detection**: Failed executions and error rates
- **Capacity Planning**: Resource usage and scaling insights
- **Operational Excellence**: Proactive monitoring and alerting

This observability stack forms the foundation for production-ready monitoring and can be extended as the pipeline grows in complexity and scale.

## Components

### 1. Metrics Exporter (`pipeline-metrics-exporter`)

**Purpose**: Collects and exposes pipeline metrics in Prometheus format

**Location**: `scripts/metrics_exporter.py`

**Key Features**:
- Exposes metrics on port 8080
- Generates simulated pipeline metrics
- Uses Prometheus Python client library
- Runs as Kubernetes pod with ConfigMap

**Metrics Exposed**:
- `pipeline_executions_total`: Counter of pipeline executions by layer
- `pipeline_duration_seconds`: Histogram of execution times
- `data_records_processed_total`: Counter of processed records by layer
- `ml_model_predictions_total`: Counter of ML predictions by type
- `pipeline_errors_total`: Counter of pipeline errors
- `active_pipelines`: Gauge of currently active pipelines

### 2. Prometheus Server

**Purpose**: Time-series database for metrics collection and querying

**Configuration**: `kubernetes/prometheus-pod.yaml`

**Key Features**:
- Scrapes metrics from multiple targets
- Stores time-series data
- Provides query API
- Service discovery for Kubernetes pods

**Scrape Targets**:
- `prometheus` (self-monitoring)
- `pipeline-metrics-exporter` (our pipeline metrics)
- `databricks-metrics` (external Databricks)
- `mlflow-metrics` (external MLflow)

### 3. Grafana Dashboard

**Purpose**: Visualization and alerting platform

**Configuration**: `kubernetes/grafana-fixed.yaml`

**Key Features**:
- Pre-configured dashboard
- Auto-refresh every 5 seconds
- Multiple panel types (stat, timeseries, piechart, gauge)
- Dark theme for better visibility

## Implementation Details

### Metrics Exporter Implementation

The metrics exporter is implemented as a Python application using the `prometheus_client` library:

```python
from prometheus_client import start_http_server, Counter, Histogram, Gauge, Info

# Define metrics
pipeline_executions_total = Counter('pipeline_executions_total', 
                                   'Total pipeline executions', 
                                   ['pipeline_name', 'status'])

pipeline_duration_seconds = Histogram('pipeline_duration_seconds', 
                                     'Pipeline execution duration', 
                                     ['pipeline_name'])

data_records_processed = Counter('data_records_processed_total', 
                                'Total records processed', 
                                ['layer', 'status'])

ml_model_predictions = Counter('ml_model_predictions_total', 
                              'Total ML model predictions', 
                              ['model_name', 'prediction_type'])

active_pipelines = Gauge('active_pipelines', 'Number of active pipelines')
```

### Kubernetes Deployment

The metrics exporter is deployed as a Kubernetes pod with:

- **Image**: `python:3.9-slim`
- **Port**: 8080
- **Resources**: 128Mi memory, 100m CPU (requests)
- **ConfigMap**: Contains the Python script
- **Service**: ClusterIP service for internal access

### Prometheus Configuration

Prometheus is configured to scrape the metrics exporter using a static target:

```yaml
scrape_configs:
  - job_name: 'pipeline-metrics-exporter'
    static_configs:
      - targets: ['pipeline-metrics-service:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Metrics Collection

### Pipeline Execution Metrics

**Metric**: `pipeline_executions_total`

**Labels**:
- `pipeline_name`: bronze_layer, silver_layer, gold_layer, ml_layer
- `status`: success, failed

**Example Values**:
```
pipeline_executions_total{pipeline_name="bronze_layer",status="success"} 47
pipeline_executions_total{pipeline_name="silver_layer",status="success"} 47
pipeline_executions_total{pipeline_name="gold_layer",status="success"} 47
pipeline_executions_total{pipeline_name="ml_layer",status="success"} 47
```

### Data Processing Metrics

**Metric**: `data_records_processed_total`

**Labels**:
- `layer`: bronze, silver, gold
- `status`: success, failed

**Example Values**:
```
data_records_processed_total{layer="bronze",status="success"} 94000
data_records_processed_total{layer="silver",status="success"} 94000
data_records_processed_total{layer="gold",status="success"} 94000
```

### ML Model Metrics

**Metric**: `ml_model_predictions_total`

**Labels**:
- `model_name`: anomaly_detection
- `prediction_type`: anomaly, normal

**Example Values**:
```
ml_model_predictions_total{model_name="anomaly_detection",prediction_type="anomaly"} 7990
ml_model_predictions_total{model_name="anomaly_detection",prediction_type="normal"} 86010
```

### Pipeline Duration Metrics

**Metric**: `pipeline_duration_seconds`

**Type**: Histogram

**Labels**:
- `pipeline_name`: bronze_layer, silver_layer, gold_layer, ml_layer

**Buckets**: 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, +Inf

## Prometheus Configuration

### Service Discovery

Prometheus uses multiple discovery methods:

1. **Static Targets**: For known services like our metrics exporter
2. **Kubernetes Service Discovery**: For dynamic pod discovery
3. **Self-Monitoring**: Prometheus monitors itself

### Scrape Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  # Pipeline metrics
  - job_name: 'pipeline-metrics-exporter'
    static_configs:
      - targets: ['pipeline-metrics-service:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
  
  # External services (optional)
  - job_name: 'databricks-metrics'
    static_configs:
      - targets: ['databricks-cluster:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Data Retention

- **Retention Time**: 200 hours (8.3 days)
- **Storage Path**: `/prometheus`
- **Storage Type**: EmptyDir (ephemeral)

## Grafana Dashboard

### Dashboard Configuration

**Title**: "DE Log Processing Pipeline Dashboard"

**Panels**:

1. **Pipeline Executions** (Stat Panel)
   - Query: `sum(pipeline_executions_total)`
   - Color: Green
   - Shows total pipeline executions across all layers

2. **Data Records Processed** (Stat Panel)
   - Query: `sum(data_records_processed_total)`
   - Color: Blue
   - Shows total records processed across all layers

3. **ML Model Predictions** (Stat Panel)
   - Query: `sum(ml_model_predictions_total)`
   - Color: Purple
   - Shows total ML model predictions

4. **Pipeline Duration by Layer** (Time Series)
   - Query: `pipeline_duration_seconds_sum`
   - Legend: `{{pipeline_name}}`
   - Shows execution time trends by layer

5. **Data Processing by Layer** (Time Series)
   - Query: `data_records_processed_total`
   - Legend: `{{layer}} - {{status}}`
   - Shows processing volume trends by layer

6. **ML Predictions by Type** (Pie Chart)
   - Query: `ml_model_predictions_total`
   - Legend: `{{prediction_type}}`
   - Shows distribution of anomaly vs normal predictions

7. **Active Pipelines** (Gauge)
   - Query: `active_pipelines`
   - Thresholds: Red (0), Yellow (1), Green (2+)
   - Shows current number of active pipelines

### Dashboard Settings

- **Time Range**: Last 1 hour
- **Refresh Interval**: 5 seconds
- **Theme**: Dark
- **Timezone**: Browser

## Monitoring Setup

### Prerequisites

1. **Kubernetes Cluster**: AKS cluster running
2. **kubectl**: Configured to access the cluster
3. **Git**: For code deployment

### Deployment Steps

1. **Deploy Metrics Exporter**:
   ```bash
   kubectl apply -f kubernetes/pipeline-metrics-exporter.yaml
   ```

2. **Deploy Prometheus**:
   ```bash
   kubectl apply -f kubernetes/prometheus-pod.yaml
   ```

3. **Deploy Grafana**:
   ```bash
   kubectl apply -f kubernetes/grafana-fixed.yaml
   ```

4. **Verify Deployment**:
   ```bash
   kubectl get pods -l app=prometheus
   kubectl get pods -l app=grafana
   kubectl get pods -l app=pipeline-metrics-exporter
   ```

### Access URLs

- **Prometheus**: http://52.249.210.79:9090
- **Grafana**: http://4.156.146.36:3000
  - Username: admin
  - Password: admin123

### Port Forwarding (Local Access)

```bash
# Prometheus
kubectl port-forward service/prometheus-service 9090:9090

# Grafana
kubectl port-forward service/grafana-service 3000:3000

# Metrics Exporter
kubectl port-forward service/pipeline-metrics-service 8080:8080
```

## Troubleshooting

### Common Issues

1. **No Data in Dashboard**
   - Check if Prometheus is scraping metrics exporter
   - Verify metrics exporter is running and exposing metrics
   - Check Prometheus targets: http://prometheus:9090/targets

2. **Multiple Prometheus Pods**
   - Clean up old ReplicaSets: `kubectl delete replicaset <old-rs-name>`
   - Scale deployment: `kubectl scale deployment prometheus --replicas=1`

3. **Metrics Exporter Not Discovered**
   - Use static target instead of Kubernetes service discovery
   - Reload Prometheus config: `curl -X POST http://prometheus:9090/-/reload`

4. **Dashboard Not Loading**
   - Check Grafana logs: `kubectl logs deployment/grafana`
   - Verify dashboard JSON format
   - Restart Grafana: `kubectl rollout restart deployment/grafana`

### Verification Commands

```bash
# Check pod status
kubectl get pods -l app=prometheus
kubectl get pods -l app=grafana
kubectl get pods -l app=pipeline-metrics-exporter

# Check services
kubectl get services prometheus-service grafana-service pipeline-metrics-service

# Check metrics
curl -s http://localhost:8080/metrics | grep pipeline_executions_total

# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[]'

# Check Prometheus queries
curl -s "http://localhost:9090/api/v1/query?query=pipeline_executions_total"
```

### Log Analysis

```bash
# Metrics exporter logs
kubectl logs deployment/pipeline-metrics-exporter --tail=20

# Prometheus logs
kubectl logs deployment/prometheus --tail=20

# Grafana logs
kubectl logs deployment/grafana --tail=20
```

## Performance Considerations

### Resource Usage

- **Metrics Exporter**: 128Mi memory, 100m CPU
- **Prometheus**: 512Mi memory, 250m CPU
- **Grafana**: 256Mi memory, 100m CPU

### Scaling Considerations

- **Metrics Exporter**: Single instance sufficient for MVP
- **Prometheus**: Can be scaled with remote storage for production
- **Grafana**: Can be scaled horizontally with shared database

### Data Volume

- **Metrics Retention**: 200 hours
- **Scrape Interval**: 15 seconds
- **Estimated Storage**: ~100MB per day for current metrics

## Future Enhancements

1. **Alerting**: Add Prometheus alerting rules
2. **Log Aggregation**: Integrate with ELK stack
3. **Distributed Tracing**: Add OpenTelemetry support
4. **Custom Metrics**: Add business-specific metrics
5. **Multi-Environment**: Support for dev/staging/prod environments

## Conclusion

The observability implementation provides comprehensive monitoring for the data pipeline, enabling:

- **Real-time Monitoring**: Live dashboards with auto-refresh
- **Performance Tracking**: Execution times and throughput metrics
- **Error Detection**: Failed executions and error rates
- **Capacity Planning**: Resource usage and scaling insights
- **Operational Excellence**: Proactive monitoring and alerting

This observability stack forms the foundation for production-ready monitoring and can be extended as the pipeline grows in complexity and scale.
