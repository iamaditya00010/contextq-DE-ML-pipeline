# MVP Architecture: DE Log Processing & ML Pipeline with Anomaly Detection

##  MVP Overview

This project implements a **Minimum Viable Product (MVP)** for a full-stack data and AI pipeline using:

- **Databricks**: ETL processing + ML training + MLflow model registry
- **AKS**: 3 specialized pods for monitoring, testing, and visualization
- **Azure Storage**: Data lake architecture (Bronze/Silver/Gold layers)

## 🏗️ Architecture Components

### 📊 Databricks (Core Processing)
- **Bronze Layer**: Raw logs → Parquet format
- **Silver Layer**: Parquet → JSON (structured data)
- **Gold Layer**: JSON → CSV (final processed data)
- **ML Training**: Isolation Forest anomaly detection
- **MLflow Registry**: Model versioning and serving

### 🐳 AKS (3 Pods Deployment)

#### 1. 🧪 Pytest Pod
- **Purpose**: Code coverage and testing
- **Function**: Validates pipeline outputs and data quality
- **Output**: Test reports and coverage metrics

#### 2. 📊 Prometheus Pod
- **Purpose**: Pipeline monitoring and metrics collection
- **Function**: Captures logs from ingestion → Bronze → Silver → Gold → ML
- **Output**: Time-series metrics and alerts

#### 3. 📈 Grafana Pod
- **Purpose**: Metrics visualization and dashboarding
- **Function**: Creates 2-3 key metrics dashboard
- **Output**: Real-time pipeline monitoring dashboard

## 🔄 Data Flow

```
Raw Logs → Databricks (Bronze) → Databricks (Silver) → Databricks (Gold) → Databricks (ML+MLflow)
                                                                    ↓
AKS Pods: Pytest ← Prometheus ← Grafana (Monitoring & Testing)
```

## 🚀 Key Features

### Full ETL Pipeline
- **Extract**: Raw SSH logs from Azure Storage
- **Transform**: Data cleansing, validation, and standardization
- **Load**: Structured data into data lake layers

### ML Pipeline
- **Training**: Isolation Forest for anomaly detection
- **Serving**: MLflow model registry and endpoints
- **Monitoring**: Model performance tracking

### Observability
- **Metrics**: Prometheus collects pipeline metrics
- **Visualization**: Grafana dashboard with key KPIs
- **Testing**: Automated pytest validation

### Cloud-Native
- **Scalable**: PySpark on Databricks clusters
- **Containerized**: Kubernetes pods for services
- **Automated**: GitHub Actions CI/CD pipeline

## 📋 MVP Metrics Dashboard

The Grafana dashboard displays 3 key metrics:

1. **Pipeline Processing Time**
   - Bronze layer duration
   - Silver layer duration
   - Gold layer duration
   - ML training time

2. **Data Quality Metrics**
   - Records processed per layer
   - Data validation success rate
   - Anomaly detection accuracy

3. **System Health**
   - Pod status and health
   - Resource utilization
   - Error rates and alerts

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Data Processing** | PySpark 3.4.1, Pandas |
| **ML Model** | scikit-learn (Isolation Forest) |
| **Storage Formats** | Parquet, JSON, CSV |
| **ML Platform** | Databricks MLflow |
| **Orchestration** | Azure Data Factory |
| **Container Platform** | Azure Kubernetes Service (AKS) |
| **Monitoring** | Prometheus + Grafana |
| **Testing** | pytest + pytest-cov |
| **CI/CD** | GitHub Actions |

##  MVP Benefits

### **Simple but Comprehensive**
- Focuses on core functionality
- Easy to understand and maintain
- Demonstrates full-stack capabilities

### **Production-Ready**
- Proper monitoring and alerting
- Automated testing and validation
- Scalable cloud architecture

### **Cost-Effective**
- Uses managed services (Databricks, AKS)
- Minimal infrastructure overhead
- Pay-per-use model

### **Future-Proof**
- Easy to scale and extend
- Modern cloud-native patterns
- Industry-standard tools

## 🚀 Getting Started

### Prerequisites
- Azure subscription
- GitHub repository with secrets configured
- Databricks workspace access

### Quick Start
1. **Configure Secrets**: Add Azure credentials and Databricks token to GitHub secrets
2. **Trigger Pipeline**: Push to main branch or manually trigger workflow
3. **Monitor Progress**: Watch GitHub Actions and Grafana dashboard
4. **View Results**: Check Databricks MLflow for model artifacts

### Access Points
- **Databricks**: MLflow UI for model management
- **Grafana**: Dashboard at `http://grafana-service:3000`
- **Prometheus**: Metrics at `http://prometheus-service:9090`
- **GitHub Actions**: Pipeline execution logs

## 📊 Expected Outcomes

After successful deployment:

1. **Data Pipeline**: Raw logs processed through Bronze → Silver → Gold layers
2. **ML Model**: Anomaly detection model trained and registered in MLflow
3. **Monitoring**: Real-time metrics and alerts via Prometheus/Grafana
4. **Testing**: Automated validation and code coverage reports
5. **Serving**: Model available for predictions via MLflow endpoints

## 🔧 Customization

### Adding New Metrics
- Modify Prometheus configuration in `kubernetes/prometheus-pod.yaml`
- Update Grafana dashboard in `kubernetes/grafana-pod.yaml`

### Extending ML Pipeline
- Add new models to `scripts/ml_anomaly_detection.py`
- Register additional models in MLflow

### Scaling Components
- Increase Databricks cluster size for larger datasets
- Scale AKS pods for higher throughput
- Add more monitoring targets to Prometheus

## 📈 Future Enhancements

- **Real-time Processing**: Stream processing with Apache Kafka
- **Advanced ML**: Deep learning models for complex patterns
- **Multi-cloud**: Extend to AWS/GCP for redundancy
- **API Gateway**: RESTful API for model serving
- **Data Lineage**: Track data flow and transformations

---

**Author: Aditya Padhi**

This MVP demonstrates a complete end-to-end data and AI pipeline suitable for production use cases while maintaining simplicity and cost-effectiveness.
