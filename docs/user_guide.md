# User Guide - Smart CLI Assistant

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Cost Management](#cost-management)
5. [Session Management](#session-management)
6. [Tools](#tools)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before using the Smart CLI Assistant, ensure you have:

- Python 3.9 or higher
- AWS Account with Bedrock access
- AWS CLI configured
- Access to Claude models in AWS Bedrock

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cli-assistant-strands
   ```

2. **Run the setup script**:
   ```bash
   ./scripts/setup.sh
   ```

3. **Configure your environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Validate the installation**:
   ```bash
   python scripts/validate_installation.py
   ```

### First Run

Start the assistant with:

```bash
python cli_assistant.py
```

You'll see a welcome message and cost information. The assistant is now ready to use!

## Basic Usage

### Asking Questions

Simply type your question or command:

```
You: What is 25% of 180?
Assistant: 25% of 180 is 45.

💰 Cost: $0.0001
```

### Using Commands

Special commands start without any prefix:

- `cost` - View cost summary
- `budget` - Check budget status
- `tools` - List tool usage
- `model <name>` - Switch models
- `models` - Compare all models
- `help` - Show help
- `quit` - Exit

Example:

```
You: cost

╭──────────── Cost Summary ────────────╮
│ Today:     $0.0234                   │
│ This Month: $0.1567                  │
│ This Session: $0.0034                │
╰──────────────────────────────────────╯
```

### Model Selection

Choose the right model for your task:

```bash
# Start with Haiku (cheapest)
python cli_assistant.py --model haiku

# Switch to Sonnet during session
You: model sonnet
```

**Model Comparison**:

| Model  | Cost (Input/Output per 1M tokens) | Best For |
|--------|-----------------------------------|----------|
| Haiku  | $0.80 / $4.00 | Testing, simple Q&A |
| Sonnet | $3.00 / $15.00 | Most production work |
| Opus   | $15.00 / $75.00 | Complex reasoning |

## Advanced Features

### Session Management

Sessions preserve conversation history across runs.

**Creating Sessions**:
Sessions are created automatically when you start the assistant.

**Loading Sessions**:
```bash
# List all sessions
You: sessions

# Load a specific session
python cli_assistant.py --session <session-id>
```

**Exporting Sessions**:
```bash
You: export <session-id>
```

**Searching Sessions**:
```bash
You: search machine learning
```

### Streaming Responses

Streaming provides real-time responses:

```bash
# Enable streaming (default)
python cli_assistant.py

# Disable streaming
python cli_assistant.py --no-stream

# Toggle during session
You: stream off
You: stream on
```

### Context Management

The assistant limits context to save costs:

- **Token limit**: 4000 tokens (configurable)
- **Message limit**: 20 messages (configurable)

Older messages are automatically removed to stay within limits.

## Cost Management

### Budget Limits

Set daily and monthly budget limits:

```bash
# In .env file
DAILY_BUDGET_LIMIT=1.00
MONTHLY_BUDGET_LIMIT=10.00
```

### Cost Tracking

Track costs in real-time:

```bash
# During session
You: cost

# Detailed dashboard
python utils/cost_dashboard.py
```

### Budget Alerts

The assistant warns when approaching limits:

- 50% of limit: Yellow warning
- 80% of limit: Orange warning
- 95% of limit: Red warning
- 100% of limit: Requests blocked

### Cost Optimization Tips

1. **Use Haiku for development**: Save costs during testing
2. **Enable context limits**: Reduce input token costs by ~65%
3. **Batch questions**: Ask multiple related questions in one session
4. **Avoid web search**: It uses additional tokens
5. **Monitor usage**: Check `cost` command regularly

## Tools

### Available Tools

The assistant has 8 built-in tools:

1. **calculator**: Mathematical operations
   ```
   You: Calculate 15% of 230
   ```

2. **python_repl**: Execute Python code
   ```
   You: Run Python code to generate first 10 Fibonacci numbers
   ```

3. **file_read**: Read local files
   ```
   You: Read the contents of config.yaml
   ```

4. **get_system_info**: System metrics
   ```
   You: What's my current CPU usage?
   ```

5. **save_note**: Save notes
   ```
   You: Save a note about this calculation
   ```

6. **list_notes**: List saved notes
   ```
   You: Show all my notes
   ```

7. **search_web**: Web search (use sparingly)
   ```
   You: Search for latest Python 3.12 features
   ```

8. **estimate_cost**: Cost estimation
   ```
   You: Estimate the cost of processing a 5000 word document
   ```

### Tool Usage Statistics

View tool usage:

```bash
You: tools

╭──────────── Tool Usage ────────────╮
│ calculator:        5 times         │
│ python_repl:       3 times         │
│ file_read:         2 times         │
│ save_note:         1 time          │
╰────────────────────────────────────╯
```

## Configuration

### Environment Variables

Configure via `.env` file:

```bash
# AWS Settings
AWS_REGION=us-west-2
AWS_PROFILE=default

# Model Settings
DEFAULT_MODEL=haiku

# Budget Settings
DAILY_BUDGET_LIMIT=1.00
MONTHLY_BUDGET_LIMIT=10.00

# Logging
LOG_LEVEL=INFO
```

### YAML Configuration

Advanced settings in `config/default_config.yaml`:

```yaml
# Session settings
sessions:
  max_context_tokens: 4000
  max_messages_in_context: 20
  retention_days: 30

# Tool settings
tools:
  web_search:
    enabled: true
    max_results: 3
    timeout: 5

# Security
security:
  input_validation: true
  max_input_length: 10000
  rate_limit: 60
```

### Configuration Precedence

1. Environment variables (highest priority)
2. `.env` file
3. `config/default_config.yaml` (lowest priority)

## Troubleshooting

### Common Issues

#### AWS Credentials Not Found

**Error**: `Unable to locate credentials`

**Solution**:
```bash
aws configure
# Enter your access key, secret key, and region
```

#### Bedrock Access Denied

**Error**: `AccessDeniedException`

**Solution**:
1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access for Claude models
4. Wait for approval (usually instant)

#### Budget Exceeded

**Error**: `Budget limit exceeded`

**Solution**:
1. Check current costs: `You: cost`
2. Increase limit in `.env`:
   ```bash
   DAILY_BUDGET_LIMIT=5.00
   ```
3. Or wait until tomorrow (daily budgets reset)

#### Session Loading Failed

**Error**: `Session not found`

**Solution**:
```bash
# List available sessions
You: sessions

# Start fresh session
You: clear
```

#### Tool Execution Failed

**Error**: `Tool execution error`

**Solution**:
1. Check tool is enabled in config
2. Verify required permissions (e.g., file access)
3. Check tool-specific requirements
4. Review logs: `cat logs/cli_assistant.log`

### Performance Issues

#### Slow Responses

**Causes**:
- Large context size
- Complex queries
- Network latency

**Solutions**:
- Reduce context: `clear` command
- Use streaming: `stream on`
- Switch to Haiku: `model haiku`

#### High Costs

**Causes**:
- Using Opus for simple tasks
- Large context size
- Frequent web searches

**Solutions**:
- Switch to Haiku for development
- Enable context limits
- Avoid unnecessary web searches
- Monitor with `cost` command

### Getting Help

1. **Built-in help**: `You: help`
2. **Check logs**: `cat logs/cli_assistant.log`
3. **Validate config**: `python scripts/validate_installation.py`
4. **Run diagnostics**: `./scripts/deploy_check.sh`
5. **Review documentation**: See `docs/` directory

## Best Practices

### Daily Usage

1. Start with Haiku for testing
2. Check budget: `You: budget`
3. Monitor costs: `You: cost`
4. Save important notes: `You: save note`
5. Export sessions regularly: `You: export <id>`

### Production Usage

1. Use Sonnet as default
2. Set appropriate budget limits
3. Enable all context limits
4. Monitor logs regularly
5. Set up cost alerts
6. Review tool usage statistics

### Security

1. Never commit `.env` files
2. Use IAM roles in production
3. Enable rate limiting
4. Review security logs
5. Keep dependencies updated

## Tips and Tricks

### Save Time

- Use short commands: `c` for `cost`, `m` for `model`
- Batch related questions
- Reuse sessions for related work

### Save Money

- Start with Haiku
- Enable context limits
- Avoid web search when possible
- Use local files instead of describing content

### Improve Accuracy

- Provide clear, specific questions
- Use appropriate model for complexity
- Give context when needed
- Use tools explicitly when needed

## What's Next?

After mastering the basics:

1. Explore advanced configuration
2. Create custom tools
3. Integrate with other systems
4. Set up monitoring
5. Deploy to production

See [docs/deployment.md](deployment.md) for production deployment guide.
