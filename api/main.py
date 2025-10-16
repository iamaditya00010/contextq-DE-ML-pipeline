# FastAPI service for DE Log Processing Pipeline
# Author: Aditya Padhi

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DE Log Processing Pipeline API",
    description="API service for managing the DE Log Processing Pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration
DATABRICKS_URL = os.getenv("DATABRICKS_URL", "https://de-log-processing-databricks.azuredatabricks.net")
MLFLOW_URL = os.getenv("MLFLOW_URL", "http://mlflow-service:5000")
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME", "delogprocessingdatalake")
STORAGE_CONTAINER_NAME = os.getenv("STORAGE_CONTAINER_NAME", "bronze")

# Pydantic models
class PipelineStatus(BaseModel):
    status: str
    timestamp: datetime
    message: str

class PipelineRun(BaseModel):
    run_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None

class ModelInfo(BaseModel):
    model_name: str
    version: str
    status: str
    metrics: Dict[str, float]
    created_at: datetime

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "DE Log Processing Pipeline API",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DE Log Processing Pipeline API",
        "version": "1.0.0",
        "author": "Aditya Padhi",
        "docs": "/docs",
        "health": "/health"
    }

# Pipeline management endpoints
@app.get("/pipeline/status")
async def get_pipeline_status():
    """Get current pipeline status"""
    try:
        # This would typically check the actual pipeline status
        # For now, return a mock status
        return PipelineStatus(
            status="running",
            timestamp=datetime.now(),
            message="Pipeline is currently running"
        )
    except Exception as e:
        logger.error(f"Error getting pipeline status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline status")

@app.post("/pipeline/trigger")
async def trigger_pipeline():
    """Trigger pipeline execution"""
    try:
        # This would typically trigger the actual pipeline
        # For now, return a mock response
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return PipelineRun(
            run_id=run_id,
            status="started",
            start_time=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error triggering pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger pipeline")

@app.get("/pipeline/runs")
async def get_pipeline_runs():
    """Get list of pipeline runs"""
    try:
        # This would typically fetch from a database or API
        # For now, return mock data
        runs = [
            PipelineRun(
                run_id="run_20241016_120000",
                status="completed",
                start_time=datetime(2024, 10, 16, 12, 0, 0),
                end_time=datetime(2024, 10, 16, 12, 5, 0),
                duration=300
            ),
            PipelineRun(
                run_id="run_20241016_110000",
                status="failed",
                start_time=datetime(2024, 10, 16, 11, 0, 0),
                end_time=datetime(2024, 10, 16, 11, 2, 0),
                duration=120
            )
        ]
        
        return {"runs": runs}
    except Exception as e:
        logger.error(f"Error getting pipeline runs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline runs")

# Model management endpoints
@app.get("/models")
async def get_models():
    """Get list of available models"""
    try:
        # This would typically fetch from MLflow
        # For now, return mock data
        models = [
            ModelInfo(
                model_name="ssh-anomaly-detection-model",
                version="1.0.0",
                status="production",
                metrics={
                    "auc": 0.85,
                    "precision": 0.82,
                    "recall": 0.78,
                    "f1_score": 0.80
                },
                created_at=datetime(2024, 10, 16, 10, 0, 0)
            )
        ]
        
        return {"models": models}
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get models")

@app.get("/models/{model_name}")
async def get_model_info(model_name: str):
    """Get specific model information"""
    try:
        # This would typically fetch from MLflow
        # For now, return mock data
        if model_name == "ssh-anomaly-detection-model":
            return ModelInfo(
                model_name=model_name,
                version="1.0.0",
                status="production",
                metrics={
                    "auc": 0.85,
                    "precision": 0.82,
                    "recall": 0.78,
                    "f1_score": 0.80
                },
                created_at=datetime(2024, 10, 16, 10, 0, 0)
            )
        else:
            raise HTTPException(status_code=404, detail="Model not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get model info")

# Data quality endpoints
@app.get("/data-quality/bronze")
async def get_bronze_quality():
    """Get Bronze layer data quality metrics"""
    try:
        # This would typically fetch from storage
        # For now, return mock data
        return {
            "layer": "bronze",
            "total_records": 2000,
            "null_records": 0,
            "quality_score": 100.0,
            "last_updated": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting bronze quality: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get bronze quality")

@app.get("/data-quality/silver")
async def get_silver_quality():
    """Get Silver layer data quality metrics"""
    try:
        # This would typically fetch from storage
        # For now, return mock data
        return {
            "layer": "silver",
            "total_records": 2000,
            "null_date_records": 0,
            "null_time_records": 0,
            "null_component_records": 0,
            "quality_issues": 0,
            "last_updated": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting silver quality: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get silver quality")

@app.get("/data-quality/gold")
async def get_gold_quality():
    """Get Gold layer data quality metrics"""
    try:
        # This would typically fetch from storage
        # For now, return mock data
        return {
            "layer": "gold",
            "total_records": 2000,
            "null_datetime_records": 0,
            "null_event_category_records": 0,
            "event_categories": {
                "Security_Alert": 150,
                "Authentication_Success": 1800,
                "Session_End": 50
            },
            "last_updated": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting gold quality: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get gold quality")

# Configuration endpoints
@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "databricks_url": DATABRICKS_URL,
        "mlflow_url": MLFLOW_URL,
        "storage_account_name": STORAGE_ACCOUNT_NAME,
        "storage_container_name": STORAGE_CONTAINER_NAME,
        "environment": "production"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Not found", "message": "The requested resource was not found"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "message": "An internal error occurred"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
