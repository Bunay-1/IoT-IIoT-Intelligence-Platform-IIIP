"""
AR/VR Configuration Module.

Provides configuration management with validation using Pydantic
and support for YAML/JSON configuration files.
"""

import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ARVRConfig(BaseModel):
    """Configuration schema for AR/VR features."""

    # Session management
    max_guidance_sessions: int = Field(default=10, gt=0, description="Maximum concurrent AR guidance sessions")
    simulation_timeout: int = Field(default=3600, ge=60, description="Simulation timeout in seconds (min 60s)")
    dashboard_refresh_rate: int = Field(default=5, ge=1, description="Dashboard refresh rate in seconds")

    # Device support
    supported_devices: list = Field(default_factory=lambda: ["hololens", "oculus", "mobile_ar"], description="Supported AR/VR devices")
    default_device: str = Field(default="hololens", description="Default device for sessions")

    # Performance settings
    enable_caching: bool = Field(default=True, description="Enable caching for overlays and environments")
    cache_ttl: int = Field(default=300, ge=60, description="Cache TTL in seconds")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    structured_logging: bool = Field(default=True, description="Enable structured JSON logging")

    # Security
    enable_auth: bool = Field(default=False, description="Enable authentication for sessions")
    session_encryption: bool = Field(default=True, description="Enable session data encryption")

    # AI/ML integration
    enable_ai_guidance: bool = Field(default=False, description="Enable AI-powered guidance")
    ai_model_path: Optional[str] = Field(default=None, description="Path to AI model for guidance")

    @validator('default_device')
    def validate_default_device(cls, v, values):
        if 'supported_devices' in values and v not in values['supported_devices']:
            raise ValueError(f"Default device '{v}' not in supported devices list")
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level '{v}'. Must be one of {valid_levels}")
        return v.upper()


class ConfigManager:
    """Configuration manager for AR/VR features."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize config manager.

        Args:
            config_file: Path to YAML/JSON config file
        """
        self.config_file = config_file
        self._config = None

    def load_config(self, overrides: Optional[Dict[str, Any]] = None) -> ARVRConfig:
        """
        Load configuration from file and apply overrides.

        Args:
            overrides: Dictionary of config overrides

        Returns:
            Validated ARVRConfig instance
        """
        config_dict = {}

        # Load from file if provided
        if self.config_file and Path(self.config_file).exists():
            config_dict = self._load_from_file(self.config_file)

        # Apply overrides
        if overrides:
            config_dict.update(overrides)

        # Create and validate config
        self._config = ARVRConfig(**config_dict)
        return self._config

    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        path = Path(file_path)

        if path.suffix.lower() in ['.yaml', '.yml']:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        elif path.suffix.lower() == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

    def save_config(self, file_path: str, config: Optional[ARVRConfig] = None) -> None:
        """
        Save configuration to file.

        Args:
            file_path: Path to save config
            config: Config to save (uses current if None)
        """
        if config is None:
            config = self._config
        if config is None:
            raise ValueError("No configuration to save")

        path = Path(file_path)
        config_dict = config.dict()

        if path.suffix.lower() in ['.yaml', '.yml']:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        elif path.suffix.lower() == '.json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

    @property
    def config(self) -> Optional[ARVRConfig]:
        """Get current configuration."""
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        if self._config is None:
            return default
        return getattr(self._config, key, default)