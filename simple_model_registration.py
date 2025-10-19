# Simple Model Registration for Databricks UI
# Copy and paste this code into a new Databricks notebook
# Author: Aditya Padhi

# Step 1: Install required packages
%pip install scikit-learn mlflow

# Step 2: Import libraries
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from mlflow.models import infer_signature

# Step 3: Create sample data
print("Creating sample data...")
np.random.seed(42)
n_samples = 1000
n_features = 5

# Generate normal data
normal_data = np.random.normal(0, 1, (n_samples, n_features))
# Generate some anomalies
anomaly_data = np.random.normal(5, 1, (50, n_features))
# Combine data
X = np.vstack([normal_data, anomaly_data])

# Shuffle the data
indices = np.random.permutation(len(X))
X = X[indices]

print(f"Data shape: {X.shape}")

# Step 4: Preprocess data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Step 5: Train Isolation Forest model
print("Training Isolation Forest model...")
model = IsolationForest(contamination=0.05, random_state=42)
predictions = model.fit_predict(X_scaled)

# Convert predictions (-1 = anomaly, 1 = normal)
predictions_binary = (predictions == 1).astype(int)
num_anomalies = np.sum(predictions == -1)
num_normal = np.sum(predictions == 1)

print(f"Model predictions - Anomalies: {num_anomalies}, Normal: {num_normal}")

# Step 6: Register model with MLflow
print("Registering model with MLflow...")

# Start MLflow run
with mlflow.start_run(run_name="Simple_Anomaly_Detection_Model") as run:
    
    # Log parameters
    mlflow.log_param("contamination", 0.05)
    mlflow.log_param("random_state", 42)
    mlflow.log_param("n_estimators", 100)
    
    # Log metrics
    mlflow.log_metric("num_anomalies", num_anomalies)
    mlflow.log_metric("num_normal", num_normal)
    mlflow.log_metric("anomaly_rate", num_anomalies / len(predictions))
    
    # Log model signature
    signature = infer_signature(
        X_scaled[:10],  # Input example
        pd.DataFrame(predictions_binary[:10], columns=['prediction'])  # Output example
    )
    
    # Log and register the model
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="anomaly_detection_model",
        signature=signature,
        input_example=X_scaled[:5],
        registered_model_name="OpenSSH_Anomaly_Detector"  # This registers the model
    )
    
    # Get run information
    run_id = run.info.run_id
    experiment_id = run.info.experiment_id
    
    print(f"Model registration completed!")
    print(f"MLflow Run ID: {run_id}")
    print(f"MLflow Experiment ID: {experiment_id}")
    print(f"Model registered as: 'OpenSSH_Anomaly_Detector'")

print("🎉 Model successfully registered! Check the Models tab in Databricks.")
