# Smart CLI Assistant

A powerful command-line assistant powered by AWS Bedrock and Claude models, featuring cost tracking, session management, and observability through OpenTelemetry traces.

## Features

- 🤖 **Multi-Model Support**: Choose from Claude 3.5 Haiku, Sonnet, or Opus based on your needs
- 💰 **Cost Tracking**: Real-time cost monitoring with daily and monthly budget limits
- 🛠️ **Rich Toolset**: Built-in tools for calculations, file operations, system info, notes, and web search
- 📊 **Session Management**: Persistent conversation sessions with cost tracking
- 🔍 **Observability**: Enhanced OpenTelemetry traces for debugging and analysis
- ⚡ **Cost Optimization**: Built-in cost estimation and budget warnings

## Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- AWS CLI configured with credentials
- Access to Claude models in AWS Bedrock (request access in AWS Console)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CruiseDevice/cli-assistant-strands
   cd smart-cli-assistant
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure AWS credentials:**
   ```bash
   aws configure
   ```
   Set your region to `us-east-1` (or your preferred region)

5. **Request Bedrock model access:**
   - Go to AWS Bedrock Console
   - Navigate to "Model access"
   - Request access for Claude models (Haiku, Sonnet, Opus)

6. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```bash
   AWS_REGION=us-east-1
   AWS_PROFILE=default
   DEFAULT_MODEL=haiku
   DAILY_BUDGET_LIMIT=1.00
   MONTHLY_BUDGET_LIMIT=10.00
   LOG_LEVEL=INFO
   ```

## Usage

### Basic Usage

Start the assistant with the default model (Haiku):
```bash
python cli_assistant.py
```

### Start with a Specific Model

```bash
# Use Sonnet (balanced performance)
python cli_assistant.py --model sonnet

# Use Opus (premium reasoning)
python cli_assistant.py --model opus
```

### Resume a Session

```bash
python cli_assistant.py --session <session-id>
```

### Interactive Commands

Once running, you can use these commands:

- `cost` - Show cost summary and token usage
- `tools` - List tool usage statistics
- `budget` - Check budget status (daily/monthly limits)
- `model <name>` - Switch to a different model (haiku/sonnet/opus)
- `models` - Compare all available models and their costs
- `help` - Show help information
- `quit` or `exit` - Exit the assistant

### Example Session

```
You: What's 15% of 230?
Assistant: 15% of 230 is 34.5.

💰 Cost: $0.0001

You: Save a note about this calculation
Assistant: [Saves note using save_note tool]

You: cost
[Shows cost summary table]

You: quit
[Shows final cost summary and tool usage]
```

## Available Models

### Haiku (Economy Tier)
- **Model**: Claude 3.5 Haiku
- **Cost**: $0.80 input / $4.00 output per 1M tokens
- **Use Cases**: Simple Q&A, quick calculations, basic file operations, testing
- **Best For**: Development, testing, simple tasks

### Sonnet (Balanced Tier)
- **Model**: Claude 3.5 Sonnet
- **Cost**: $3.00 input / $15.00 output per 1M tokens
- **Use Cases**: Complex reasoning, code generation, data analysis, production workloads
- **Best For**: Most production work, balanced performance

### Opus (Premium Tier)
- **Model**: Claude 3 Opus
- **Cost**: $15.00 input / $75.00 output per 1M tokens
- **Use Cases**: Advanced reasoning, complex problem solving, research tasks
- **Best For**: Critical applications requiring advanced reasoning

## Available Tools

The assistant comes with a rich set of built-in tools:

- **calculator**: Perform mathematical operations
- **python_repl**: Execute Python code interactively
- **file_read**: Read local files
- **get_system_info**: Get system metrics (CPU, memory, disk usage)
- **save_note**: Save notes to local storage
- **list_notes**: List all saved notes
- **search_web**: Search the web using DuckDuckGo (use sparingly)
- **estimate_cost**: Estimate costs before operations

## Cost Tracking

The assistant automatically tracks costs for all requests:

- **Daily Tracking**: Costs reset daily
- **Monthly Tracking**: Cumulative monthly costs
- **Session Tracking**: Per-session cost tracking
- **Tool Usage**: Statistics on tool invocations
- **Budget Warnings**: Alerts when approaching limits

View costs anytime with the `cost` command or check budget status with `budget`.

Cost data is stored in `cost_tracking.json` and persists across sessions.

## Session Management

Sessions allow you to maintain conversation context across runs:

- Sessions are automatically created when starting the assistant
- Session data includes conversation history and cost tracking
- Resume sessions using `--session <session-id>`
- Session data is stored in the `sessions/` directory

## Trace Enrichment & Observability

The project includes enhanced OpenTelemetry tracing to capture agent orchestration decisions:

### Quick Start with Jaeger

```bash
# Start Jaeger locally
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Run trace enrichment demo
python examples/trace_enrichment_demo.py

# View traces at http://localhost:16686
```

### What's Captured

Traces include:
- Available tools and system prompts
- Model tool selection decisions
- Tool execution results
- Conversation context

See [docs/TRACE_ENRICHMENT.md](docs/TRACE_ENRICHMENT.md) and [docs/AGENT_REASONING_IN_TRACES.md](docs/AGENT_REASONING_IN_TRACES.md) for detailed documentation.

## Project Structure

```
smart-cli-assistant/
├── cli_assistant.py          # Main entry point
├── models/
│   └── model_config.py       # Model configurations and pricing
├── tools/
│   └── custom_tools.py       # Custom tool implementations
├── utils/
│   ├── cost_tracker.py       # Cost tracking functionality
│   ├── session_manager.py    # Session management
│   ├── trace_enrichment.py   # OpenTelemetry trace enrichment
│   └── cost_dashboard.py     # Cost visualization
├── examples/
│   └── trace_enrichment_demo.py  # Trace enrichment examples
├── tests/                    # Test suite
├── docs/                     # Documentation
└── notes/                    # Saved notes directory
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run integration tests only
pytest -m integration

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Quality

The project uses:
- **black**: Code formatting
- **flake8**: Linting
- **bandit**: Security scanning
- **pre-commit**: Git hooks for quality checks

Run pre-commit hooks:
```bash
pre-commit run --all-files
```

### Scripts

- `scripts/check_credentials.py`: Verify AWS credentials
- `scripts/check_cost_limits.py`: Check cost tracking limits
- `scripts/validate_env_example.py`: Validate environment configuration

## Configuration

### Environment Variables

- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: AWS profile name (default: default)
- `DEFAULT_MODEL`: Default model to use (haiku/sonnet/opus)
- `DAILY_BUDGET_LIMIT`: Daily cost limit in USD (default: 1.00)
- `MONTHLY_BUDGET_LIMIT`: Monthly cost limit in USD (default: 10.00)
- `LOG_LEVEL`: Logging level (default: INFO)

### Budget Limits

The assistant will:
- Warn when approaching 80% of daily/monthly limits
- Block execution if limits are exceeded
- Track costs across all sessions

Adjust limits in your `.env` file or environment variables.

## Troubleshooting

### AWS Credentials Issues

If you see credential errors:
```bash
aws configure
# Enter your access key, secret key, and region
```

### Bedrock Access Denied

1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access for Claude models
4. Wait for approval (usually instant for most accounts)

### Budget Exceeded

If you hit budget limits:
- Increase `DAILY_BUDGET_LIMIT` or `MONTHLY_BUDGET_LIMIT` in `.env`
- Or reset cost tracking by deleting `cost_tracking.json` (not recommended for production)

## Security

- Never commit `.env` files or credentials
- AWS credentials should be in `~/.aws/` directory
- Cost tracking data may contain sensitive information
- Review `.gitignore` for excluded files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

[Add your license here]

## Production Features

### Logging System

The assistant includes a comprehensive logging system with structured JSON logs:

- **Multi-level logging**: Console (warnings/errors) + File (all levels) + JSON (structured data)
- **Cost tracking**: Automatic logging of costs, tokens, and performance metrics
- **Log rotation**: 10MB files with 5 backups
- **Analytics**: Built-in stats extraction from logs

```python
from utils.logger import CostAwareLogger

logger = CostAwareLogger()
stats = logger.get_stats(hours=24)  # Get last 24h statistics
```

Logs are stored in the `logs/` directory:
- `cli_assistant.log` - Human-readable logs
- `cli_assistant_structured.json` - Structured JSON logs for analysis

### Configuration Management

Flexible configuration system with YAML files and environment variable overrides:

```yaml
# config/default_config.yaml
cost:
  daily_limit: 1.00
  monthly_limit: 10.00

sessions:
  max_context_tokens: 4000
  max_messages_in_context: 20
```

Environment variables override config file values:
```bash
export DAILY_BUDGET_LIMIT=5.00
export DEFAULT_MODEL=sonnet
```

### Error Handling & Recovery

Production-grade error handling with retry logic and graceful degradation:

- **Retry decorator**: Automatic retry with exponential backoff
- **Error recovery**: Contextual suggestions for common errors
- **Budget protection**: Automatic blocking when limits exceeded

```python
from utils.error_handler import retry_on_failure, ErrorRecovery

@retry_on_failure(max_attempts=3, delay=1.0, backoff=2.0)
def api_call():
    # Function will retry up to 3 times on failure
    pass
```

### Testing

Comprehensive test suite with 90%+ coverage:

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test categories
pytest tests/test_production.py -v
pytest tests/test_end_to_end.py -v -m integration

# Check coverage
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

Test categories:
- **Unit tests**: Component-level testing
- **Integration tests**: Multi-component workflows
- **Production tests**: Configuration, logging, error handling
- **End-to-end tests**: Complete user scenarios

### Deployment

Production deployment scripts:

```bash
# Setup new environment
./scripts/setup.sh

# Validate installation
python scripts/validate_installation.py

# Pre-deployment checks
./scripts/deploy_check.sh
```

The deployment checklist validates:
- ✅ All tests passing
- ✅ Configuration valid
- ✅ No secrets in code
- ✅ Documentation complete
- ✅ Required files present
- ✅ Cost tracking functional

### Code Quality

Pre-commit hooks ensure code quality:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Checks include:
- Secret detection
- Trailing whitespace
- YAML/JSON validation
- Security scanning (Bandit)
- Code formatting (Black)
- Linting (Flake8)

## Monitoring & Analytics

### Cost Dashboard

View detailed cost analytics:

```bash
python utils/cost_dashboard.py
```

Shows:
- Daily/monthly costs
- Cost by model
- Tool usage statistics
- Token consumption
- Cost trends

### Log Analytics

Extract statistics from structured logs:

```python
from utils.logger import CostAwareLogger

logger = CostAwareLogger()
stats = logger.get_stats(hours=24)

print(f"Total interactions: {stats['total_interactions']}")
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Average duration: {stats['avg_duration']:.2f}s")
print(f"Tool usage: {stats['tools_usage']}")
```

## Deployment Guide

### Local Development

```bash
# 1. Clone and setup
git clone <repository-url>
cd cli-assistant-strands
./scripts/setup.sh

# 2. Configure
cp .env.example .env
# Edit .env with your settings

# 3. Validate
python scripts/validate_installation.py

# 4. Run
python cli_assistant.py
```

### Production Deployment

1. **Pre-deployment validation**:
   ```bash
   ./scripts/deploy_check.sh
   ```

2. **Environment setup**:
   - Set production environment variables
   - Configure appropriate budget limits
   - Set up log rotation
   - Configure monitoring

3. **Security**:
   - Use AWS IAM roles (not access keys)
   - Enable CloudWatch logging
   - Set restrictive file permissions
   - Enable audit logging

4. **Monitoring**:
   - Set up CloudWatch alarms for costs
   - Monitor error rates
   - Track performance metrics
   - Review logs regularly

See [docs/deployment.md](docs/deployment.md) for detailed deployment instructions.

## Performance Optimization

### Context Management

The assistant implements smart context limiting to reduce costs:

- **Token limiting**: Max 4000 tokens of context (configurable)
- **Message limiting**: Last 20 messages kept in context
- **Cost savings**: ~65% reduction in input token costs

### Model Selection

Choose the right model for your use case:

```bash
# Development/testing
python cli_assistant.py --model haiku  # Cheapest

# Production workloads
python cli_assistant.py --model sonnet  # Balanced

# Critical reasoning
python cli_assistant.py --model opus  # Premium
```

### Streaming

Streaming responses provide faster perceived performance:

```bash
# Enable streaming (default)
python cli_assistant.py

# Disable streaming
python cli_assistant.py --no-stream
```

## Acknowledgments

- Built with [AWS Strands](https://github.com/aws/strands-agents)
- Powered by [Anthropic Claude](https://www.anthropic.com/) models via AWS Bedrock
- Observability with [OpenTelemetry](https://opentelemetry.io/)
