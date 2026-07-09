"""
Configuration settings for MAE - AIoT Intelligence Platform
"""

import os
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    name: str = "mae_platform"
    user: str = "postgres"
    password: str = "password"
    pool_size: int = 20
    max_overflow: int = 30


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/application.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    enable_console: bool = True


@dataclass
class APIConfig:
    """API configuration."""
    title: str = "MAE - AIoT Intelligence Platform API"
    description: str = "Advanced IoT and AI platform for industrial automation"
    version: str = "1.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enable_metrics: bool = True
    enable_tracing: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    performance_monitoring: bool = True


@dataclass
class IoTConfig:
    """IoT configuration."""
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    device_timeout: int = 300
    data_retention_days: int = 30


@dataclass
class AIConfig:
    """AI/ML configuration."""
    model_cache_size: int = 100
    prediction_timeout: int = 30
    training_batch_size: int = 32
    max_concurrent_predictions: int = 10
    model_update_interval: int = 3600


class Settings:
    """Main settings class."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.security = SecurityConfig()
        self.logging = LoggingConfig()
        self.api = APIConfig()
        self.monitoring = MonitoringConfig()
        self.iot = IoTConfig()
        self.ai = AIConfig()
        
        # Load environment overrides
        self._load_from_env()
    
    @property
    def secret_key(self) -> str:
        """Get secret key."""
        return self.security.secret_key
    
    @property
    def algorithm(self) -> str:
        """Get algorithm."""
        return self.security.algorithm
    
    @property
    def access_token_expire_minutes(self) -> int:
        """Get access token expire minutes."""
        return self.security.access_token_expire_minutes
    
    @property
    def refresh_token_expire_days(self) -> int:
        """Get refresh token expire days."""
        return self.security.refresh_token_expire_days
    
    @property
    def bcrypt_rounds(self) -> int:
        """Get bcrypt rounds."""
        return self.security.bcrypt_rounds
    
    @property
    def app_name(self) -> str:
        """Get app name."""
        return self.api.title
    
    @property
    def app_version(self) -> str:
        """Get app version."""
        return self.api.version
    
    @property
    def debug(self) -> bool:
        """Get debug mode."""
        return self.api.debug
    
    def _load_from_env(self):
        """Load settings from environment variables."""
        # Database
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", self.database.port))
        self.database.name = os.getenv("DB_NAME", self.database.name)
        self.database.user = os.getenv("DB_USER", self.database.user)
        self.database.password = os.getenv("DB_PASSWORD", self.database.password)
        
        # Redis
        self.redis.host = os.getenv("REDIS_HOST", self.redis.host)
        self.redis.port = int(os.getenv("REDIS_PORT", self.redis.port))
        self.redis.password = os.getenv("REDIS_PASSWORD", self.redis.password)
        
        # Security
        self.security.secret_key = os.getenv("SECRET_KEY", self.security.secret_key)
        
        # API
        self.api.host = os.getenv("API_HOST", self.api.host)
        self.api.port = int(os.getenv("API_PORT", self.api.port))
        self.api.debug = os.getenv("API_DEBUG", "false").lower() == "true"
        
        # Logging
        self.logging.level = os.getenv("LOG_LEVEL", self.logging.level)
        self.logging.file_path = os.getenv("LOG_FILE", self.logging.file_path)
        
        # IoT
        self.iot.mqtt_broker = os.getenv("MQTT_BROKER", self.iot.mqtt_broker)
        self.iot.mqtt_port = int(os.getenv("MQTT_PORT", self.iot.mqtt_port))
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        return (
            f"postgresql://{self.database.user}:{self.database.password}"
            f"@{self.database.host}:{self.database.port}/{self.database.name}"
        )
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.redis.password}@" if self.redis.password else ""
        return f"redis://{auth}{self.redis.host}:{self.redis.port}/{self.redis.db}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "database": self.database.__dict__,
            "redis": self.redis.__dict__,
            "security": self.security.__dict__,
            "logging": self.logging.__dict__,
            "api": self.api.__dict__,
            "monitoring": self.monitoring.__dict__,
            "iot": self.iot.__dict__,
            "ai": self.ai.__dict__,
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings


def reload_settings():
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings
