# Manual Model Registration Script for Databricks
# Author: Aditya Padhi

import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from mlflow.models import infer_signature

# Set MLflow tracking URI (if needed)
# mlflow.set_tracking_uri("databricks")

# Create sample data for demonstration
print("Creating sample data for model training...")
np.random.seed(42)
n_samples = 1000
n_features = 5

# Generate normal data
normal_data = np.random.normal(0, 1, (n_samples, n_features))
# Generate some anomalies
anomaly_data = np.random.normal(5, 1, (50, n_features))
# Combine data
X = np.vstack([normal_data, anomaly_data])
y = np.hstack([np.zeros(n_samples), np.ones(50)])  # 0 = normal, 1 = anomaly

# Shuffle the data
indices = np.random.permutation(len(X))
X = X[indices]
y = y[indices]

print(f"Data shape: {X.shape}")
print(f"Anomalies: {np.sum(y)}")

# Preprocess data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train Isolation Forest model
print("Training Isolation Forest model...")
model = IsolationForest(contamination=0.05, random_state=42)
predictions = model.fit_predict(X_scaled)

# Convert predictions (-1 = anomaly, 1 = normal)
predictions_binary = (predictions == 1).astype(int)
num_anomalies = np.sum(predictions == -1)
num_normal = np.sum(predictions == 1)

print(f"Model predictions - Anomalies: {num_anomalies}, Normal: {num_normal}")

# Start MLflow run
print("Starting MLflow run...")
with mlflow.start_run(run_name="Manual_Anomaly_Detection_Model") as run:
    
    # Log parameters
    mlflow.log_param("contamination", 0.05)
    mlflow.log_param("random_state", 42)
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_samples", "auto")
    
    # Log metrics
    mlflow.log_metric("num_anomalies", num_anomalies)
    mlflow.log_metric("num_normal", num_normal)
    mlflow.log_metric("anomaly_rate", num_anomalies / len(predictions))
    
    # Log model signature
    signature = infer_signature(
        X_scaled[:10],  # Input example
        pd.DataFrame(predictions_binary[:10], columns=['prediction'])  # Output example
    )
    
    # Log the model with registration
    print("Logging and registering model...")
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="anomaly_detection_model",
        signature=signature,
        input_example=X_scaled[:5],
        registered_model_name="OpenSSH_Anomaly_Detector"  # This registers the model
    )
    
    # Log scaler as well
    mlflow.sklearn.log_model(
        sk_model=scaler,
        artifact_path="data_scaler",
        registered_model_name="Data_Scaler"
    )
    
    # Get run information
    run_id = run.info.run_id
    experiment_id = run.info.experiment_id
    
    print(f"Model registration completed!")
    print(f"MLflow Run ID: {run_id}")
    print(f"MLflow Experiment ID: {experiment_id}")
    print(f"Model registered as: 'OpenSSH_Anomaly_Detector'")
    print(f"Scaler registered as: 'Data_Scaler'")

print("Script completed successfully!")
