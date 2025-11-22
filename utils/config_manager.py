"""
Configuration management system.
Loads from YAML files and environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Manage application configuration."""

    def __init__(self, config_file: str = "config/default_config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

        # Override with environment variables
        load_dotenv()
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)

    def _apply_env_overrides(self):
        """Override config with environment variables."""
        # Cost settings
        if os.getenv('DAILY_BUDGET_LIMIT'):
            self.config['cost']['daily_limit'] = float(os.getenv('DAILY_BUDGET_LIMIT'))

        if os.getenv('MONTHLY_BUDGET_LIMIT'):
            self.config['cost']['monthly_limit'] = float(os.getenv('MONTHLY_BUDGET_LIMIT'))

        # AWS settings
        if os.getenv('AWS_REGION'):
            self.config['aws']['region'] = os.getenv('AWS_REGION')

        # Logging
        if os.getenv('LOG_LEVEL'):
            self.config['logging']['level'] = os.getenv('LOG_LEVEL')

        # Default model
        if os.getenv('DEFAULT_MODEL'):
            self.config['models']['default'] = os.getenv('DEFAULT_MODEL')

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Example: config.get('cost.daily_limit')
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self, output_file: Optional[str] = None):
        """Save current configuration to file."""
        output_path = Path(output_file) if output_file else self.config_file

        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)

    def validate(self) -> bool:
        """Validate configuration values."""
        errors = []

        # Check required fields
        required_fields = [
            'app.name',
            'models.default',
            'aws.region',
            'cost.daily_limit',
            'cost.monthly_limit'
        ]

        for field in required_fields:
            if self.get(field) is None:
                errors.append(f"Missing required field: {field}")

        # Validate ranges
        if self.get('cost.daily_limit', 0) < 0:
            errors.append("cost.daily_limit must be positive")

        if self.get('cost.monthly_limit', 0) < self.get('cost.daily_limit', 0):
            errors.append("cost.monthly_limit must be >= daily_limit")

        if self.get('sessions.max_context_tokens', 0) < 100:
            errors.append("sessions.max_context_tokens too low")

        if errors:
            for error in errors:
                print(f"Config error: {error}")
            return False

        return True
