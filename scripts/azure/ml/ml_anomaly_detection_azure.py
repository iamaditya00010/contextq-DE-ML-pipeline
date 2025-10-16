# Azure Databricks ML Anomaly Detection Script
# Author: Aditya Padhi
# Description: Train ML model using Spark MLlib and register with MLflow

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, OneHotEncoder
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import mlflow
import mlflow.spark
import logging
from datetime import datetime

# Initialize Spark session
spark = SparkSession.builder \
    .appName("ML_Anomaly_Detection") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

# Set log level
spark.sparkContext.setLogLevel("WARN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure MLflow
mlflow.set_tracking_uri("http://mlflow-service:5000")
mlflow.set_experiment("ssh-anomaly-detection")

def prepare_features(df):
    """Prepare feature vectors for ML model"""
    
    try:
        # Read Gold layer data
        gold_df = spark.read.csv("/mnt/gold/final_data/openssh_logs_final.csv", header=True, inferSchema=True)
        
        logger.info(f"Loaded {gold_df.count()} records for ML training")
        
        # Feature engineering
        # Create time-based features
        feature_df = gold_df.withColumn("hour_of_day", 
            when(col("datetime").contains("00:"), 0)
            .when(col("datetime").contains("01:"), 1)
            .when(col("datetime").contains("02:"), 2)
            .when(col("datetime").contains("03:"), 3)
            .when(col("datetime").contains("04:"), 4)
            .when(col("datetime").contains("05:"), 5)
            .when(col("datetime").contains("06:"), 6)
            .when(col("datetime").contains("07:"), 7)
            .when(col("datetime").contains("08:"), 8)
            .when(col("datetime").contains("09:"), 9)
            .when(col("datetime").contains("10:"), 10)
            .when(col("datetime").contains("11:"), 11)
            .when(col("datetime").contains("12:"), 12)
            .when(col("datetime").contains("13:"), 13)
            .when(col("datetime").contains("14:"), 14)
            .when(col("datetime").contains("15:"), 15)
            .when(col("datetime").contains("16:"), 16)
            .when(col("datetime").contains("17:"), 17)
            .when(col("datetime").contains("18:"), 18)
            .when(col("datetime").contains("19:"), 19)
            .when(col("datetime").contains("20:"), 20)
            .when(col("datetime").contains("21:"), 21)
            .when(col("datetime").contains("22:"), 22)
            .when(col("datetime").contains("23:"), 23)
            .otherwise(12)
        )
        
        # Create event pattern features
        feature_df = feature_df.withColumn("has_failed_login", 
            when(col("Content").contains("Failed"), 1).otherwise(0))
        
        feature_df = feature_df.withColumn("has_invalid_user", 
            when(col("Content").contains("Invalid user"), 1).otherwise(0))
        
        feature_df = feature_df.withColumn("has_connection_refused", 
            when(col("Content").contains("Connection refused"), 1).otherwise(0))
        
        # Create target variable (anomaly detection)
        feature_df = feature_df.withColumn("is_anomaly",
            when(col("risk_score") >= 7, 1).otherwise(0)
        )
        
        # Select features for ML
        ml_df = feature_df.select(
            "hour_of_day",
            "has_failed_login",
            "has_invalid_user", 
            "has_connection_refused",
            "risk_score",
            "is_anomaly"
        ).filter(col("is_anomaly").isNotNull())
        
        logger.info(f"Prepared {ml_df.count()} records for ML training")
        
        return ml_df
        
    except Exception as e:
        logger.error(f"Error in feature preparation: {str(e)}")
        raise e

def train_ml_model(df):
    """Train ML model using Spark MLlib"""
    
    try:
        # Split data
        train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
        
        logger.info(f"Training set: {train_df.count()} records")
        logger.info(f"Test set: {test_df.count()} records")
        
        # Feature vector assembly
        feature_cols = ["hour_of_day", "has_failed_login", "has_invalid_user", "has_connection_refused", "risk_score"]
        
        vector_assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features"
        )
        
        # Logistic Regression model
        lr = LogisticRegression(
            featuresCol="features",
            labelCol="is_anomaly",
            maxIter=100,
            regParam=0.01
        )
        
        # Create pipeline
        pipeline = Pipeline(stages=[vector_assembler, lr])
        
        # Train model
        logger.info("Training ML model...")
        model = pipeline.fit(train_df)
        
        # Make predictions
        predictions = model.transform(test_df)
        
        # Evaluate model
        evaluator = BinaryClassificationEvaluator(
            labelCol="is_anomaly",
            rawPredictionCol="rawPrediction",
            metricName="areaUnderROC"
        )
        
        auc = evaluator.evaluate(predictions)
        logger.info(f"Model AUC: {auc}")
        
        # Calculate additional metrics
        total_predictions = predictions.count()
        true_positives = predictions.filter((col("prediction") == 1) & (col("is_anomaly") == 1)).count()
        false_positives = predictions.filter((col("prediction") == 1) & (col("is_anomaly") == 0)).count()
        true_negatives = predictions.filter((col("prediction") == 0) & (col("is_anomaly") == 0)).count()
        false_negatives = predictions.filter((col("prediction") == 0) & (col("is_anomaly") == 1)).count()
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        logger.info(f"Precision: {precision}")
        logger.info(f"Recall: {recall}")
        logger.info(f"F1-Score: {f1_score}")
        
        return model, {
            "auc": auc,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "total_predictions": total_predictions,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives
        }
        
    except Exception as e:
        logger.error(f"Error in model training: {str(e)}")
        raise e

def log_model_to_mlflow(model, metrics):
    """Log model and metrics to MLflow"""
    
    try:
        with mlflow.start_run():
            # Log parameters
            mlflow.log_param("algorithm", "LogisticRegression")
            mlflow.log_param("max_iter", 100)
            mlflow.log_param("reg_param", 0.01)
            mlflow.log_param("features", "hour_of_day,has_failed_login,has_invalid_user,has_connection_refused,risk_score")
            
            # Log metrics
            mlflow.log_metric("auc", metrics["auc"])
            mlflow.log_metric("precision", metrics["precision"])
            mlflow.log_metric("recall", metrics["recall"])
            mlflow.log_metric("f1_score", metrics["f1_score"])
            mlflow.log_metric("total_predictions", metrics["total_predictions"])
            
            # Log model
            mlflow.spark.log_model(
                model, 
                "model",
                registered_model_name="ssh-anomaly-detection-model"
            )
            
            logger.info("Model logged to MLflow successfully")
            
    except Exception as e:
        logger.error(f"Error logging to MLflow: {str(e)}")
        raise e

def save_model_artifacts(model, metrics):
    """Save model artifacts to ADLS Gen2"""
    
    try:
        # Save model
        model.write().overwrite().save("/mnt/models/anomaly_detection_model")
        
        # Save metrics summary
        metrics_df = spark.createDataFrame([
            ("auc", metrics["auc"]),
            ("precision", metrics["precision"]),
            ("recall", metrics["recall"]),
            ("f1_score", metrics["f1_score"]),
            ("total_predictions", metrics["total_predictions"]),
            ("training_timestamp", current_timestamp())
        ], ["metric", "value", "timestamp"])
        
        metrics_df.write \
            .mode("overwrite") \
            .parquet("/mnt/models/ml_metrics/ml_metrics.parquet")
        
        # Create summary report
        summary_report = f"""
ML ANOMALY DETECTION SUMMARY REPORT
=====================================

Model: SSH Anomaly Detection (Logistic Regression)
Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PERFORMANCE METRICS:
- AUC Score: {metrics['auc']:.4f}
- Precision: {metrics['precision']:.4f}
- Recall: {metrics['recall']:.4f}
- F1-Score: {metrics['f1_score']:.4f}

PREDICTION SUMMARY:
- Total Predictions: {metrics['total_predictions']}
- True Positives: {metrics['true_positives']}
- False Positives: {metrics['false_positives']}
- True Negatives: {metrics['true_negatives']}
- False Negatives: {metrics['false_negatives']}

MODEL ARTIFACTS:
- Model Path: /mnt/models/anomaly_detection_model
- Metrics Path: /mnt/models/ml_metrics/ml_metrics.parquet
- MLflow Registry: ssh-anomaly-detection-model

FEATURES USED:
- hour_of_day: Hour of the day (0-23)
- has_failed_login: Binary indicator for failed login attempts
- has_invalid_user: Binary indicator for invalid user attempts
- has_connection_refused: Binary indicator for connection refusals
- risk_score: Risk score from Gold layer (1-10)

Author: Aditya Padhi
        """
        
        # Save summary report
        summary_df = spark.createDataFrame([(summary_report,)], ["summary"])
        summary_df.write \
            .mode("overwrite") \
            .text("/mnt/models/ml_summary_report.txt")
        
        logger.info("Model artifacts saved successfully")
        
    except Exception as e:
        logger.error(f"Error saving model artifacts: {str(e)}")
        raise e

def main():
    """Main execution function"""
    
    logger.info("Starting ML anomaly detection training...")
    
    try:
        # Prepare features
        ml_df = prepare_features(spark)
        
        # Train model
        model, metrics = train_ml_model(ml_df)
        
        # Log to MLflow
        log_model_to_mlflow(model, metrics)
        
        # Save artifacts
        save_model_artifacts(model, metrics)
        
        logger.info("ML anomaly detection training completed successfully!")
        
    except Exception as e:
        logger.error(f"ML training failed: {str(e)}")
        raise e
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
