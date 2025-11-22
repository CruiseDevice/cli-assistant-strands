# API Reference

## Core Modules

### cli_assistant.py

Main application entry point.

#### SmartCLIAssistant

Main application class that orchestrates the CLI assistant.

**Initialization:**
```python
from cli_assistant import SmartCLIAssistant

assistant = SmartCLIAssistant(
    model_name="haiku",      # Model to use (haiku, sonnet, opus)
    session_id=None,         # Optional session ID to resume
    enable_streaming=True    # Enable response streaming
)
```

**Methods:**

- `run()`: Start the interactive CLI loop
- `process_command(command: str)`: Process a user command
- `switch_model(model_name: str)`: Switch to a different model

## Utils

### utils.cost_tracker

Cost tracking and budget management.

#### CostTracker

Track and manage costs across sessions.

**Initialization:**
```python
from utils.cost_tracker import CostTracker

tracker = CostTracker(storage_file="cost_tracking.json")
```

**Methods:**

- `track_request(model: str, input_tokens: int, output_tokens: int) -> float`
  - Track a request and return cost
  - Returns: Total cost in USD

- `get_daily_cost() -> float`
  - Get today's total cost
  - Returns: Cost in USD

- `get_monthly_cost() -> float`
  - Get current month's total cost
  - Returns: Cost in USD

- `check_budget(daily_limit: float, monthly_limit: float) -> tuple[bool, str]`
  - Check if within budget limits
  - Returns: (is_within_budget, message)

- `get_summary() -> dict`
  - Get comprehensive cost summary
  - Returns: Dict with daily, monthly, and per-model costs

**Example:**
```python
tracker = CostTracker()

# Track a request
cost = tracker.track_request("haiku", 100, 200)
print(f"Cost: ${cost:.6f}")

# Check budget
within_budget, msg = tracker.check_budget(1.00, 10.00)
if not within_budget:
    print(msg)

# Get summary
summary = tracker.get_summary()
print(f"Daily: ${summary['daily_cost']:.4f}")
```

### utils.session_manager

Session persistence and management.

#### SessionManager

Manage conversation sessions.

**Initialization:**
```python
from utils.session_manager import SessionManager

manager = SessionManager(storage_dir="sessions")
```

**Methods:**

- `create_session(model: str) -> Session`
  - Create a new session
  - Returns: Session object

- `load_session(session_id: str) -> Session`
  - Load an existing session
  - Returns: Session object or None

- `list_sessions() -> list[Session]`
  - List all sessions
  - Returns: List of Session objects

- `add_message(role: str, content: str, tokens: int = 0, cost: float = 0.0)`
  - Add a message to current session
  - role: "user" or "assistant"

- `export_session(session_id: str, output_file: str)`
  - Export session to file
  - Supports JSON and Markdown formats

- `search_sessions(query: str) -> list[Session]`
  - Search sessions by content
  - Returns: Matching sessions

**Example:**
```python
manager = SessionManager()

# Create session
session = manager.create_session("haiku")

# Add messages
manager.add_message("user", "Hello", tokens=5, cost=0.0001)
manager.add_message("assistant", "Hi there!", tokens=8, cost=0.0002)

# Export session
manager.export_session(session.session_id, "session.md")
```

### utils.logger

Production logging system.

#### CostAwareLogger

Logger with cost and performance tracking.

**Initialization:**
```python
from utils.logger import CostAwareLogger

logger = CostAwareLogger(
    name="cli_assistant",
    log_dir="logs",
    level="INFO",
    max_bytes=10_000_000,  # 10MB
    backup_count=5
)
```

**Methods:**

- `log_interaction(user_input, response, model, cost, tokens, duration, session_id, tools_used)`
  - Log a complete user interaction

- `log_cost_alert(alert_type: str, current: float, limit: float)`
  - Log budget alerts

- `log_error(error: Exception, context: dict)`
  - Log errors with context

- `log_performance(operation: str, duration: float, success: bool)`
  - Log performance metrics

- `get_stats(hours: int = 24) -> dict`
  - Get statistics from logs
  - Returns: Dict with interaction counts, costs, tool usage

**Example:**
```python
logger = CostAwareLogger()

# Log interaction
logger.log_interaction(
    user_input="Hello",
    response="Hi!",
    model="haiku",
    cost=0.0001,
    tokens=50,
    duration=1.2,
    session_id="abc123",
    tools_used=["calculator"]
)

# Get stats
stats = logger.get_stats(hours=24)
print(f"Interactions: {stats['total_interactions']}")
print(f"Total cost: ${stats['total_cost']:.4f}")
```

### utils.config_manager

Configuration management.

#### ConfigManager

Manage application configuration.

**Initialization:**
```python
from utils.config_manager import ConfigManager

config = ConfigManager("config/default_config.yaml")
```

**Methods:**

- `get(key_path: str, default: Any = None) -> Any`
  - Get config value using dot notation
  - Example: `config.get('cost.daily_limit')`

- `set(key_path: str, value: Any)`
  - Set config value using dot notation

- `save(output_file: str = None)`
  - Save configuration to file

- `validate() -> bool`
  - Validate configuration
  - Returns: True if valid

**Example:**
```python
config = ConfigManager()

# Get values
daily_limit = config.get('cost.daily_limit')
log_level = config.get('logging.level', 'INFO')

# Set values
config.set('cost.daily_limit', 5.00)

# Validate
if config.validate():
    config.save()
```

### utils.error_handler

Error handling and recovery.

#### Decorators

**retry_on_failure:**
```python
from utils.error_handler import retry_on_failure, RetryableError

@retry_on_failure(
    max_attempts=3,
    delay=1.0,
    backoff=2.0,
    exceptions=(RetryableError,)
)
def api_call():
    # Will retry up to 3 times
    pass
```

**graceful_degradation:**
```python
from utils.error_handler import graceful_degradation

@graceful_degradation(fallback_value=None)
def risky_operation():
    # Returns None on error instead of raising
    pass
```

#### ErrorRecovery

Static methods for error handling.

**Methods:**

- `handle_api_error(error: Exception, logger=None) -> str`
  - Handle API errors and return suggestions

- `handle_budget_error(daily_cost: float, limit: float) -> str`
  - Handle budget exceeded errors

- `handle_session_error(error: Exception) -> str`
  - Handle session errors

**Example:**
```python
from utils.error_handler import ErrorRecovery

try:
    # API call
    pass
except Exception as e:
    suggestion = ErrorRecovery.handle_api_error(e)
    print(suggestion)
```

#### safe_execute

Safely execute functions.

```python
from utils.error_handler import safe_execute

success, result, error = safe_execute(risky_function, arg1, arg2)

if success:
    print(f"Result: {result}")
else:
    print(f"Error: {error}")
```

## Models

### models.model_config

Model configurations and pricing.

#### MODELS Dictionary

```python
from models.model_config import MODELS

# Access model info
haiku = MODELS["haiku"]
print(haiku.input_cost)   # Cost per 1M input tokens
print(haiku.output_cost)  # Cost per 1M output tokens
print(haiku.tier)         # ModelTier.CHEAP
```

#### ModelConfig

```python
@dataclass
class ModelConfig:
    model_id: str           # AWS Bedrock model ID
    name: str              # Display name
    tier: ModelTier        # CHEAP, BALANCED, PREMIUM
    input_cost: float      # Cost per 1M input tokens
    output_cost: float     # Cost per 1M output tokens
    context_window: int    # Maximum context size
    description: str       # Model description
```

#### Helper Functions

- `get_model(name: str) -> ModelConfig`
  - Get model configuration by name

- `calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float`
  - Calculate cost for token usage

- `compare_models() -> dict`
  - Compare all models

## Tools

### tools.custom_tools

Custom tool implementations.

#### Available Tools

- `calculator`: Mathematical operations
- `python_repl`: Execute Python code
- `file_read`: Read files
- `get_system_info`: System metrics
- `save_note`: Save notes
- `list_notes`: List notes
- `search_web`: Web search
- `estimate_cost`: Cost estimation

## Testing

### Running Tests

```python
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_production.py -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests only
pytest -m integration
```

### Test Utilities

```python
from tests.conftest import *

# Fixtures available:
# - mock_bedrock
# - temp_session_dir
# - cost_tracker
# - config_manager
```

## Command Line Interface

### Main Command

```bash
python cli_assistant.py [OPTIONS]
```

**Options:**

- `--model MODEL`: Model to use (haiku, sonnet, opus)
- `--session SESSION_ID`: Resume session
- `--no-stream`: Disable streaming
- `--help`: Show help

### Scripts

**Setup:**
```bash
./scripts/setup.sh
```

**Run Tests:**
```bash
./scripts/run_tests.sh
```

**Deployment Check:**
```bash
./scripts/deploy_check.sh
```

**Validate Installation:**
```bash
python scripts/validate_installation.py
```

## Environment Variables

- `AWS_REGION`: AWS region (default: us-west-2)
- `AWS_PROFILE`: AWS profile name
- `DEFAULT_MODEL`: Default model (haiku/sonnet/opus)
- `DAILY_BUDGET_LIMIT`: Daily budget limit in USD
- `MONTHLY_BUDGET_LIMIT`: Monthly budget limit in USD
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)

## Configuration File Schema

```yaml
app:
  name: string
  version: string
  environment: string

models:
  default: string
  streaming_enabled: boolean

aws:
  region: string
  bedrock:
    retry_attempts: integer
    retry_delay: float
    timeout: integer

cost:
  daily_limit: float
  monthly_limit: float
  alert_thresholds: list[float]
  stop_on_budget_exceeded: boolean

sessions:
  storage_dir: string
  max_context_tokens: integer
  max_messages_in_context: integer
  auto_save: boolean
  retention_days: integer

logging:
  level: string
  log_dir: string
  max_file_size: integer
  backup_count: integer
  console_logging: boolean
  track_performance: boolean

tools:
  web_search:
    enabled: boolean
    max_results: integer
    timeout: integer
  python_repl:
    enabled: boolean
    timeout: integer
  system_info:
    enabled: boolean
    interval: integer

security:
  input_validation: boolean
  max_input_length: integer
  file_operations:
    allowed_extensions: list[string]
    max_file_size: integer
  rate_limit: integer

ui:
  color_output: boolean
  show_cost_warnings: boolean
  show_tool_usage: boolean
  show_loading: boolean
  history_size: integer
```

## Error Handling

### Custom Exceptions

```python
from utils.error_handler import (
    RetryableError,      # Errors that can be retried
    BudgetExceededError, # Budget limit exceeded
    ConfigurationError   # Configuration issues
)
```

### Error Codes

- `BUDGET_EXCEEDED`: Budget limit reached
- `SESSION_NOT_FOUND`: Session ID invalid
- `MODEL_ACCESS_DENIED`: Bedrock access issue
- `INVALID_CONFIG`: Configuration validation failed

## Performance

### Benchmarks

Typical response times (Haiku):
- Simple query: 0.5-1.5s
- With tool use: 1.5-3.0s
- With web search: 3.0-5.0s

### Optimization

- Enable context limiting
- Use streaming for better UX
- Choose appropriate model
- Batch related questions

## Version History

- **1.0.0**: Production release with Phase 6 features
  - Logging system
  - Configuration management
  - Error handling
  - Comprehensive testing
  - Deployment tools
