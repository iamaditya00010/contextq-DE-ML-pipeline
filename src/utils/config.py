"""Configuration management utilities"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration loader"""
    
    def __init__(self, env: str = "local"):
        self.env = env
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        # Try to find config directory
        current_dir = Path(__file__).parent.parent.parent
        config_dir = current_dir / "config"
        config_file = config_dir / f"{self.env}.yaml"
        
        if not config_file.exists():
            # Return default config if file not found
            return self._get_default_config()
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'environment': 'local',
            'paths': {
                'bronze': './data/bronze',
                'silver': './data/silver',
                'gold': './data/gold',
                'models': './data/models'
            },
            'spark': {
                'app_name': 'Data Pipeline - Local',
                'master': 'local[*]',
                'executor_memory': '2g',
                'driver_memory': '2g'
            },
            'etl': {
                'batch_size': 1000,
                'partition_column': 'processing_date'
            },
            'ml': {
                'train_split': 0.8,
                'test_split': 0.2,
                'random_seed': 42
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports nested keys with dot notation)"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        result = self.get(key)
        if result is None:
            raise KeyError(f"Configuration key not found: {key}")
        return result


def load_config(env: Optional[str] = None) -> Config:
    """Load configuration based on environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "local")
    
    return Config(env)

