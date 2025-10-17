"""
ML Model: SSH Log Anomaly Detection with MLflow
===============================================
This script trains an anomaly detection model to identify suspicious SSH login attempts.
Integrated with MLflow for model tracking and serving.

Author: Aditya Padhi

Model: Isolation Forest (unsupervised learning)
Input: Gold layer CSV (data/gold/openssh_logs_final.csv)
Output: 
  - Trained model registered in MLflow
  - Predictions with anomaly scores (data/ml_output/anomaly_predictions.csv)
  - Model artifacts and metrics tracked in MLflow

Features used:
  - Event type patterns
  - Time of day
  - Event sequence patterns
  - Failed login indicators
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os
from datetime import datetime
import warnings
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
warnings.filterwarnings('ignore')


def load_gold_data(file_path):
    """Load data from Gold layer"""
    print(f"[ML] Loading data from: {file_path}")
    df = pd.read_csv(file_path)
    print(f"[ML] Loaded {len(df):,} records")
    return df


def feature_engineering(df):
    """
    Create features for anomaly detection
    
    Features:
    1. Event type encoded
    2. Hour of day (from datetime)
    3. Is failed login event
    4. Is invalid user event
    5. Is break-in attempt
    6. Event frequency (how common this event type is)
    """
    print("[ML] Engineering features...")
    
    # Parse datetime to extract time features
    df['datetime_parsed'] = pd.to_datetime(df['datetime'], format='%d-%b-%Y : %H:%M:%S')
    df['hour'] = df['datetime_parsed'].dt.hour
    df['day_of_week'] = df['datetime_parsed'].dt.dayofweek
    
    # Encode EventId
    le_event = LabelEncoder()
    df['event_encoded'] = le_event.fit_transform(df['EventId'])
    
    # Create binary flags for security events
    df['is_failed_login'] = df['EventId'].isin(['E10', 'E9']).astype(int)
    df['is_invalid_user'] = df['EventId'].isin(['E13', 'E12']).astype(int)
    df['is_break_in_attempt'] = df['EventId'].isin(['E27']).astype(int)
    df['is_auth_failure'] = df['EventId'].isin(['E19', 'E21']).astype(int)
    
    # Event frequency (rare events might be anomalies)
    event_counts = df['EventId'].value_counts()
    df['event_frequency'] = df['EventId'].map(event_counts)
    df['event_rarity'] = 1 / df['event_frequency']  # Inverse frequency
    
    # Component encoding
    le_component = LabelEncoder()
    df['component_encoded'] = le_component.fit_transform(df['Component'])
    
    # Select features for model
    feature_columns = [
        'event_encoded',
        'hour',
        'day_of_week',
        'is_failed_login',
        'is_invalid_user',
        'is_break_in_attempt',
        'is_auth_failure',
        'event_rarity',
        'component_encoded'
    ]
    
    X = df[feature_columns]
    
    print(f"[ML] Created {len(feature_columns)} features")
    print(f"[ML] Feature matrix shape: {X.shape}")
    
    return X, df, le_event, le_component


def train_anomaly_model(X, contamination=0.1):
    """
    Train Isolation Forest for anomaly detection
    
    Args:
        X: Feature matrix
        contamination: Expected proportion of anomalies (default 10%)
    
    Returns:
        Trained model
    """
    print(f"\n[ML] Training Isolation Forest model...")
    print(f"[ML] Contamination (expected anomalies): {contamination*100}%")
    
    # Initialize model
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        max_samples='auto',
        verbose=0
    )
    
    # Train model
    model.fit(X)
    
    print(f"[ML] Model trained successfully!")
    
    return model


def detect_anomalies(model, X, df):
    """
    Use trained model to detect anomalies
    
    Returns:
        DataFrame with predictions and anomaly scores
    """
    print("\n[ML] Detecting anomalies...")
    
    # Predict (-1 = anomaly, 1 = normal)
    predictions = model.predict(X)
    
    # Get anomaly scores (lower = more anomalous)
    anomaly_scores = model.decision_function(X)
    
    # Add to dataframe
    df['prediction'] = predictions
    df['anomaly_score'] = anomaly_scores
    df['is_anomaly'] = (predictions == -1).astype(int)
    
    # Statistics
    total_records = len(df)
    anomalies = (df['is_anomaly'] == 1).sum()
    normal = (df['is_anomaly'] == 0).sum()
    
    print(f"[ML] Detection complete:")
    print(f"  - Total records: {total_records:,}")
    print(f"  - Anomalies detected: {anomalies:,} ({anomalies/total_records*100:.1f}%)")
    print(f"  - Normal events: {normal:,} ({normal/total_records*100:.1f}%)")
    
    return df


def save_model(model, encoders, model_dir='models'):
    """Save trained model and encoders"""
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'anomaly_model.pkl')
    encoders_path = os.path.join(model_dir, 'label_encoders.pkl')
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save encoders
    with open(encoders_path, 'wb') as f:
        pickle.dump(encoders, f)
    
    print(f"\n[ML] Model saved to: {model_path}")
    print(f"[ML] Encoders saved to: {encoders_path}")


def save_predictions(df, output_dir='data/ml_output'):
    """Save predictions with anomaly scores"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Select relevant columns for output
    output_df = df[[
        'LineId', 'datetime', 'EventId', 'EventTemplate', 
        'is_anomaly', 'anomaly_score', 
        'is_failed_login', 'is_invalid_user', 'is_break_in_attempt'
    ]].copy()
    
    # Sort by anomaly score (most anomalous first)
    output_df = output_df.sort_values('anomaly_score')
    
    output_file = os.path.join(output_dir, 'anomaly_predictions.csv')
    output_df.to_csv(output_file, index=False)
    
    print(f"[ML] Predictions saved to: {output_file}")
    
    # Save only anomalies for easy review
    anomalies_only = output_df[output_df['is_anomaly'] == 1]
    anomalies_file = os.path.join(output_dir, 'detected_anomalies.csv')
    anomalies_only.to_csv(anomalies_file, index=False)
    
    print(f"[ML] Anomalies only saved to: {anomalies_file}")
    
    return output_file, anomalies_file


def generate_summary_report(df, output_dir='data/ml_output'):
    """Generate summary statistics and insights"""
    print("\n" + "=" * 70)
    print("ML MODEL SUMMARY REPORT")
    print("=" * 70)
    
    # Overall statistics
    anomalies_df = df[df['is_anomaly'] == 1]
    
    print(f"\n1. ANOMALY DISTRIBUTION")
    print(f"   Total anomalies: {len(anomalies_df):,}")
    
    print(f"\n2. ANOMALIES BY EVENT TYPE")
    anomaly_events = anomalies_df['EventId'].value_counts()
    for event, count in anomaly_events.head(5).items():
        percentage = count / len(anomalies_df) * 100
        print(f"   {event}: {count:,} ({percentage:.1f}%)")
    
    print(f"\n3. ANOMALIES BY TIME")
    anomaly_hours = anomalies_df['hour'].value_counts().sort_index()
    print(f"   Peak anomaly hours:")
    for hour, count in anomaly_hours.head(3).items():
        print(f"   Hour {hour:02d}:00 - {count:,} anomalies")
    
    print(f"\n4. TOP 5 MOST ANOMALOUS EVENTS")
    top_anomalies = anomalies_df.nsmallest(5, 'anomaly_score')[
        ['LineId', 'datetime', 'EventId', 'EventTemplate', 'anomaly_score']
    ]
    print(top_anomalies.to_string(index=False))
    
    print("\n" + "=" * 70)
    
    # Save report
    report_file = os.path.join(output_dir, 'ml_summary_report.txt')
    with open(report_file, 'w') as f:
        f.write("ML ANOMALY DETECTION SUMMARY REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total Records: {len(df):,}\n")
        f.write(f"Anomalies Detected: {len(anomalies_df):,}\n")
        f.write(f"Anomaly Rate: {len(anomalies_df)/len(df)*100:.2f}%\n\n")
        f.write("Top Anomalous Event Types:\n")
        for event, count in anomaly_events.head(5).items():
            f.write(f"  {event}: {count:,}\n")
    
    print(f"\nReport saved to: {report_file}")


def main():
    """Main execution with MLflow integration"""
    
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  SSH LOG ANOMALY DETECTION".center(68) + "█")
    print("█" + "  Isolation Forest Model + MLflow".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70 + "\n")
    
    start_time = datetime.now()
    
    # Set MLflow experiment
    mlflow.set_experiment("ssh-anomaly-detection")
    
    with mlflow.start_run(run_name=f"anomaly_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        try:
            # 1. Load data
            input_file = 'data/gold/openssh_logs_final.csv'
            if not os.path.exists(input_file):
                print(f"Error: {input_file} not found")
                print("Please run the pipeline first: python scripts/run_pipeline_pandas.py")
                return
            
            df = load_gold_data(input_file)
            
            # Log data info
            mlflow.log_param("total_records", len(df))
            mlflow.log_param("input_file", input_file)
            
            # 2. Feature engineering
            X, df_features, le_event, le_component = feature_engineering(df)
            
            # Log feature info
            mlflow.log_param("num_features", X.shape[1])
            mlflow.log_param("feature_names", list(X.columns))
            
            # 3. Train model
            contamination = 0.1
            mlflow.log_param("contamination", contamination)
            model = train_anomaly_model(X, contamination=contamination)
            
            # 4. Detect anomalies
            df_predictions = detect_anomalies(model, X, df_features)
            
            # Calculate metrics
            anomaly_count = len(df_predictions[df_predictions['is_anomaly'] == 1])
            anomaly_rate = anomaly_count / len(df_predictions) * 100
            
            # Log metrics
            mlflow.log_metric("anomaly_count", anomaly_count)
            mlflow.log_metric("anomaly_rate", anomaly_rate)
            mlflow.log_metric("total_predictions", len(df_predictions))
            
            # 5. Save model and artifacts
            encoders = {'event': le_event, 'component': le_component}
            model_path = save_model(model, encoders)
            
            # 6. Save predictions
            output_file, anomalies_file = save_predictions(df_predictions)
            
            # Log model artifacts
            mlflow.log_artifact(model_path)
            mlflow.log_artifact(output_file)
            mlflow.log_artifact(anomalies_file)
            
            # 7. Generate summary
            generate_summary_report(df_predictions)
            mlflow.log_artifact("data/ml_output/ml_summary_report.txt")
            
            # 8. Register model in MLflow
            signature = infer_signature(X, df_predictions[['is_anomaly', 'anomaly_score']])
            
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="anomaly_model",
                signature=signature,
                registered_model_name="ssh_anomaly_detector",
                metadata={
                    "model_type": "IsolationForest",
                    "features": list(X.columns),
                    "contamination": contamination,
                    "anomaly_rate": anomaly_rate
                }
            )
            
            # Summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "=" * 70)
            print("ML PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 70)
            print(f"Duration: {duration}")
            print(f"\nOutputs:")
            print(f"  Model: {model_path}")
            print(f"  Predictions: {output_file}")
            print(f"  Anomalies only: {anomalies_file}")
            print(f"  Summary report: data/ml_output/ml_summary_report.txt")
            print(f"\n🎯 Model registered in MLflow as 'ssh_anomaly_detector'")
            print(f"📊 Anomaly rate: {anomaly_rate:.2f}%")
            print(f"🔍 Total anomalies detected: {anomaly_count:,}")
            print("\n🎉 Anomaly detection complete!")
            print("=" * 70 + "\n")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            mlflow.log_param("error", str(e))
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

