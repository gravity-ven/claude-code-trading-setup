"""
Configuration management for Spartan Trading Agent.

Loads configuration from YAML files with environment variable substitution.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# Load environment variables
load_dotenv()


def resolve_env_vars(value: Any) -> Any:
    """
    Recursively resolve environment variables in configuration values.

    Supports ${VAR_NAME} syntax.
    """
    if isinstance(value, str):
        # Match ${VAR_NAME} patterns
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, value)

        for var_name in matches:
            env_value = os.getenv(var_name, '')
            value = value.replace(f'${{{var_name}}}', env_value)

        return value

    elif isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [resolve_env_vars(item) for item in value]

    return value


class ClaudeConfig(BaseModel):
    """Claude AI configuration."""
    model: str = "claude-sonnet-4-5-20250929"
    api_key: str
    max_tokens: int = 4096
    temperature: float = 0.7
    extended_thinking: bool = True
    max_context_tokens: int = 180000


class RiskConfig(BaseModel):
    """Risk management configuration."""
    max_position_size: float = 0.05
    min_position_size: float = 0.01
    max_portfolio_risk: float = 0.02
    max_positions: int = 10
    max_drawdown: float = 0.15
    daily_loss_limit: float = 0.05
    stop_loss_percent: float = 0.03
    trailing_stop: bool = True
    trailing_stop_percent: float = 0.02
    take_profit_percent: float = 0.06
    max_leverage: float = 1.0
    max_sector_allocation: float = 0.30
    max_single_stock: float = 0.10


class MonitoringConfig(BaseModel):
    """Monitoring and alerting configuration."""
    enabled: bool = True
    log_level: str = "INFO"
    log_file: str = "logs/spartan.log"


class SafetyConfig(BaseModel):
    """Safety features configuration."""
    require_confirmation: bool = True
    kill_switch_enabled: bool = True
    dry_run: bool = False
    max_claude_calls_per_minute: int = 50


class Config(BaseModel):
    """Main configuration model."""
    mode: str = "paper_trading"
    claude: ClaudeConfig
    risk: RiskConfig
    monitoring: MonitoringConfig
    safety: SafetyConfig
    data_sources: Dict[str, Any] = Field(default_factory=dict)
    execution: Dict[str, Any] = Field(default_factory=dict)
    strategies: Dict[str, Any] = Field(default_factory=dict)
    universe: Dict[str, Any] = Field(default_factory=dict)
    backtest: Dict[str, Any] = Field(default_factory=dict)
    database: Dict[str, Any] = Field(default_factory=dict)
    api: Dict[str, Any] = Field(default_factory=dict)
    performance: Dict[str, Any] = Field(default_factory=dict)


def load_config(config_path: str = "config/config.yaml") -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration YAML file

    Returns:
        Config object with all settings

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML
    with open(config_file, 'r') as f:
        raw_config = yaml.safe_load(f)

    # Resolve environment variables
    resolved_config = resolve_env_vars(raw_config)

    # Create and validate config
    try:
        config = Config(**resolved_config)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")

    return config


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config object
    """
    return load_config()


# Singleton instance
_config: Config | None = None


def init_config(config_path: str = "config/config.yaml") -> Config:
    """
    Initialize the global configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        Config object
    """
    global _config
    _config = load_config(config_path)
    return _config


def config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config object

    Raises:
        RuntimeError: If config hasn't been initialized
    """
    if _config is None:
        raise RuntimeError("Configuration not initialized. Call init_config() first.")
    return _config
