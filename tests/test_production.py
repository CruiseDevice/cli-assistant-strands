"""
Production-level integration tests.
"""
import pytest
import os
from pathlib import Path
from utils.logger import CostAwareLogger
from utils.config_manager import ConfigManager
from utils.error_handler import retry_on_failure, RetryableError, ErrorRecovery


def test_logger_initialization():
    """Test logger creates necessary files."""
    import logging
    logger = CostAwareLogger(name="test_logger_init", log_dir="test_logs")

    assert Path("test_logs").exists()
    assert Path("test_logs/cli_assistant.log").exists()

    # Cleanup
    import shutil
    shutil.rmtree("test_logs")
    # Remove logger from cache to avoid conflicts
    logging.getLogger("test_logger_init").handlers.clear()


def test_logger_interaction_tracking():
    """Test interaction logging."""
    import logging
    logger = CostAwareLogger(name="test_logger_interaction", log_dir="test_logs")

    logger.log_interaction(
        user_input="Test input",
        response="Test response",
        model="haiku",
        cost=0.001,
        tokens=100,
        duration=1.5,
        session_id="test_session"
    )

    # Flush handlers to ensure log is written
    for handler in logger.logger.handlers:
        handler.flush()

    # Check log file exists and has content
    log_file = Path("test_logs/cli_assistant.log")
    assert log_file.exists()
    assert log_file.stat().st_size > 0

    # Cleanup
    import shutil
    shutil.rmtree("test_logs")
    # Remove logger from cache to avoid conflicts
    logging.getLogger("test_logger_interaction").handlers.clear()


def test_config_manager_loads_defaults():
    """Test configuration loading."""
    config = ConfigManager("config/default_config.yaml")

    assert config.get('app.name') == "Smart CLI Assistant"
    assert config.get('models.default') == "haiku"
    assert config.get('cost.daily_limit') > 0


def test_config_manager_env_override():
    """Test environment variable overrides."""
    os.environ['DAILY_BUDGET_LIMIT'] = '5.00'

    config = ConfigManager("config/default_config.yaml")

    assert config.get('cost.daily_limit') == 5.00

    # Cleanup
    del os.environ['DAILY_BUDGET_LIMIT']


def test_config_validation():
    """Test configuration validation."""
    config = ConfigManager("config/default_config.yaml")

    assert config.validate() == True

    # Test invalid config
    config.set('cost.daily_limit', -1)
    assert config.validate() == False


def test_retry_decorator():
    """Test retry mechanism."""
    attempt_count = 0

    @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(RetryableError,))
    def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise RetryableError("Temporary failure")
        return "Success"

    result = failing_function()

    assert result == "Success"
    assert attempt_count == 3


def test_error_recovery_api_suggestions():
    """Test API error recovery suggestions."""
    recovery = ErrorRecovery()

    # Test throttling error
    error = Exception("ThrottlingException: Rate limit exceeded")
    suggestion = recovery.handle_api_error(error)

    assert "rate limit" in suggestion.lower()
    assert "wait" in suggestion.lower()


def test_full_system_config_integration():
    """Test that all components can be initialized from config."""
    from utils.cost_tracker import CostTracker
    from utils.session_manager import SessionManager

    config = ConfigManager("config/default_config.yaml")
    logger = CostAwareLogger(log_dir=config.get('logging.log_dir'))
    cost_tracker = CostTracker()
    session_manager = SessionManager(storage_dir=config.get('sessions.storage_dir'))

    assert logger is not None
    assert cost_tracker is not None
    assert session_manager is not None

    # Cleanup
    import shutil
    if Path("test_logs").exists():
        shutil.rmtree("test_logs")


@pytest.mark.parametrize("model,expected_tier", [
    ("haiku", "economy"),
    ("sonnet", "balanced"),
    ("opus", "premium")
])
def test_model_configurations(model, expected_tier):
    """Test model configurations from config."""
    from models.model_config import MODELS

    assert model in MODELS
    assert MODELS[model].tier.value == expected_tier
