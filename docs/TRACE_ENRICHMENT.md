# Enhanced Agent Tracing

This guide explains how to capture the **agent's orchestration decisions** in OpenTelemetry traces, giving you complete visibility into how the agent decides which tools to use.

## What Gets Captured in Traces

When you enable enhanced tracing, your observability platform (Grafana, AWS X-Ray, Honeycomb, Jaeger, etc.) will show:

### 1. **Agent Orchestration Span** (`agent.orchestration`)
Shows what the agent sends to the model:

```
Attributes:
- agent.tools.count: 3
- agent.tools.available: ["calculator", "file_read", "current_time"]
- agent.messages.count: 2
- agent.system_prompt: "You are a helpful assistant..."
- agent.orchestration.phase: "before_model_invocation"

Events:
- agent.tool.spec.0
  - tool.name: "calculator"
  - tool.description: "Perform mathematical calculations"
  - tool.input_schema: { type: "object", properties: {...} }

- agent.message.0
  - message.role: "user"
  - message.content: "What is 15% of 230?"

- agent.message.1
  - message.role: "assistant"
  - message.content: [toolUse, text result]
```

### 2. **Model Decision Span** (`model.tool_decision`)
Shows how the model decided to use the information:

```
Attributes:
- model.decision.type: "tool_use"
- model.tool.selected: "calculator"
- model.tool.use_id: "tooluse_abc123"
- model.tool.inputs: {"expression": "230 * 0.15"}
- agent.tool.matched_function: "calculator"

Events:
- model.decided_tool
  - tool.name: "calculator"
  - tool.inputs.full: {"expression": "230 * 0.15", "mode": "evaluate"}
  - decision.explanation: "Model selected calculator with 2 parameters"
```

### 3. **Tool Execution Result Span** (`agent.tool_execution_result`)
Shows what happened when the tool ran:

```
Attributes:
- tool.use_id: "tooluse_abc123"
- tool.status: "success"
- tool.result.content_blocks: 1

Events:
- tool.execution_completed
  - tool.use_id: "tooluse_abc123"
  - tool.status: "success"
  - tool.result.summary: "34.5"
  - tool.result.full: [{"text": "34.5"}]
```

## Quick Start

### 1. Start an Observability Backend

**Option A: Jaeger (Local Development)**
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# View UI at: http://localhost:16686
```

**Option B: AWS X-Ray**
```bash
# Configure AWS X-Ray daemon
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:2000"
```

**Option C: Grafana Cloud / Honeycomb / Other**
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://your-endpoint"
export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=your-key"
```

### 2. Enable Enhanced Tracing in Your Code

```python
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator, file_read, current_time
from utils.trace_enrichment import setup_enriched_tracing

# Create your agent
agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-3-5-haiku-20241022-v1:0"),
    system_prompt="You are a helpful assistant.",
    tools=[calculator, file_read, current_time]
)

# Enable enhanced tracing
setup_enriched_tracing(
    agent,
    service_name="my-cli-assistant",
    otlp_endpoint="http://localhost:4318",  # Your collector endpoint
    additional_attributes={
        "environment": "production",
        "version": "1.0.0",
        "user.id": "demo-user"
    }
)

# Use the agent normally - all orchestration details are captured
result = agent("What is 15% of 230 and what time is it?")
```

### 3. View Traces in Your Observability Platform

**Jaeger:**
1. Open http://localhost:16686
2. Select service: `my-cli-assistant`
3. Click "Find Traces"
4. Click on a trace to see the spans

**AWS X-Ray:**
1. Open AWS Console → X-Ray → Traces
2. Filter by service: `my-cli-assistant`
3. Click on a trace ID

**Grafana:**
1. Open Grafana → Explore → Tempo
2. Query: `{service.name="my-cli-assistant"}`
3. Click on a trace

## Trace Structure Visualization

```
strands-agent (root span)
├── gen_ai.system: "bedrock"
├── gen_ai.agent.name: "my-cli-assistant"
├── gen_ai.user.message: "What is 15% of 230?"
│
├── Cycle 1
│   │
│   ├── agent.orchestration (CUSTOM SPAN - NEW!)
│   │   ├── Attributes:
│   │   │   ├── agent.tools.count: 3
│   │   │   ├── agent.tools.available: [...]
│   │   │   ├── agent.messages.count: 1
│   │   │   └── agent.system_prompt: "..."
│   │   │
│   │   └── Events:
│   │       ├── agent.tool.spec.0 (calculator spec)
│   │       ├── agent.tool.spec.1 (file_read spec)
│   │       ├── agent.tool.spec.2 (current_time spec)
│   │       └── agent.message.0 (user query)
│   │
│   ├── Model invoke (Bedrock API call)
│   │   ├── gen_ai.request.model: "claude-3-5-haiku"
│   │   ├── gen_ai.usage.input_tokens: 850
│   │   └── gen_ai.choice: [toolUse: calculator]
│   │
│   ├── model.tool_decision (CUSTOM SPAN - NEW!)
│   │   ├── Attributes:
│   │   │   ├── model.decision.type: "tool_use"
│   │   │   ├── model.tool.selected: "calculator"
│   │   │   └── model.tool.inputs: {...}
│   │   │
│   │   └── Events:
│   │       └── model.decided_tool (full decision context)
│   │
│   ├── Tool: calculator (execution)
│   │
│   └── agent.tool_execution_result (CUSTOM SPAN - NEW!)
│       ├── Attributes:
│       │   ├── tool.status: "success"
│       │   └── tool.result.content_blocks: 1
│       │
│       └── Events:
│           └── tool.execution_completed (full result)
│
└── Cycle 2 (final response synthesis)
```

## What This Solves

### Before Enhanced Tracing
Standard traces show:
- ✓ User input
- ✓ Model was called
- ✓ Tool was executed
- ✗ **What tools were available?**
- ✗ **What context did the model have?**
- ✗ **Why did it choose this tool?**
- ✗ **What were the tool parameters?**

### After Enhanced Tracing
You can answer:
- ✅ **What tools were available to the model?**
  - See all tool specs in `agent.orchestration` span

- ✅ **What context did the model use to decide?**
  - See all messages, system prompt, conversation history

- ✅ **Why did the model choose this specific tool?**
  - See tool description and input schema that guided the choice

- ✅ **What parameters did it decide to use?**
  - See full tool inputs in `model.tool_decision` span

- ✅ **How did the agent orchestrate the interaction?**
  - See complete flow: context → decision → execution

## Use Cases

### 1. Debugging Tool Selection
**Problem:** "Why did my agent use the wrong tool?"

**Solution:** Look at the `agent.orchestration` span to see:
- Was the correct tool even available?
- Was the tool description clear enough?
- What context was in the conversation history?

### 2. Optimizing System Prompts
**Problem:** "Is my system prompt helping or hurting tool selection?"

**Solution:** Compare traces with different system prompts:
- See exactly what prompt was used in each trace
- Correlate prompts with tool selection accuracy
- A/B test different prompt strategies

### 3. Understanding Multi-Tool Workflows
**Problem:** "How is my agent chaining multiple tools?"

**Solution:** View the trace timeline:
- See the sequence of tool decisions
- Understand why it chose tool A before tool B
- Identify inefficient tool usage patterns

### 4. Monitoring Production Agent Behavior
**Problem:** "Is my agent selecting tools correctly in production?"

**Solution:** Set up alerts on trace attributes:
```
Alert: tool.status == "error"
Alert: agent.tools.available != expected_tools
Alert: model.tool.selected not in approved_tools
```

### 5. Conversation Context Analysis
**Problem:** "Is the agent maintaining proper context?"

**Solution:** Examine `agent.messages.count` over time:
- Track conversation length
- See what context is being sent to the model
- Identify context window issues early

## Integration with Existing Code

### Update Your CLI Assistant

```python
# cli_assistant.py

from utils.trace_enrichment import setup_enriched_tracing

def initialize_agent():
    """Initialize the agent with enhanced tracing."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0"
    )

    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[calculator, python_repl, file_read, get_system_info]
    )

    # Enable enhanced tracing
    setup_enriched_tracing(
        agent,
        service_name="smart-cli-assistant",
        additional_attributes={
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": "1.0.0"
        }
    )

    return agent
```

### Cost Tracking with Traces

Combine with your existing cost tracking:

```python
# Track costs AND capture in traces
result = agent(user_input)

# Cost tracking
cost_info = cost_tracker.track_request(
    model='claude-3.5-haiku',
    input_tokens=result.metrics.accumulated_usage['inputTokens'],
    output_tokens=result.metrics.accumulated_usage['outputTokens']
)

# Traces automatically include:
# - gen_ai.usage.input_tokens
# - gen_ai.usage.output_tokens
# - tool usage details
# - decision context
```

## Advanced Configuration

### Custom Span Processors

Add your own span processor for custom logic:

```python
from opentelemetry.sdk.trace import SpanProcessor

class CustomSpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context):
        # Add custom attributes when span starts
        if span.name == "model.tool_decision":
            span.set_attribute("custom.timestamp", time.time())

    def on_end(self, span):
        # Process span when it ends
        if span.attributes.get("tool.status") == "error":
            self.alert_on_tool_error(span)

# Add to tracer provider
from strands.telemetry import StrandsTelemetry
telemetry = StrandsTelemetry()
telemetry.tracer_provider.add_span_processor(CustomSpanProcessor())
```

### Sampling Strategy

Control trace volume for high-traffic applications:

```python
import os

# Sample 10% of traces
os.environ["OTEL_TRACES_SAMPLER"] = "traceidratio"
os.environ["OTEL_TRACES_SAMPLER_ARG"] = "0.1"

# Always sample errors
os.environ["OTEL_TRACES_SAMPLER"] = "parentbased_traceidratio"
```

### Filtering Sensitive Data

Redact PII from traces:

```python
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

class PiiRedactingProcessor(SimpleSpanProcessor):
    def on_end(self, span):
        # Redact sensitive attributes
        if "user.email" in span.attributes:
            span.attributes["user.email"] = "REDACTED"
        super().on_end(span)
```

## Troubleshooting

### No traces appearing in Jaeger?

```bash
# Check Jaeger is running
curl http://localhost:16686

# Check OTLP endpoint is reachable
curl http://localhost:4318/v1/traces

# Enable console exporter to see traces locally
# (already enabled in setup_enriched_tracing)
```

### Traces but missing custom spans?

```python
# Verify hooks are registered
print(agent.hooks.registry)

# Enable debug logging
import logging
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
```

### Spans are truncated?

```python
# Increase attribute size limits
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
# Attributes are limited by default, use events for large data
# Events support larger payloads than attributes
```

## Next Steps

1. **Run the demo:** `python examples/trace_enrichment_demo.py`
2. **View traces:** http://localhost:16686
3. **Integrate with your app:** Update `cli_assistant.py`
4. **Set up production backend:** Configure AWS X-Ray or Grafana Cloud
5. **Create dashboards:** Visualize tool selection patterns over time

## Learn More

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [Strands Observability Guide](https://github.com/strands-agents/docs/blob/main/docs/user-guide/observability-evaluation/traces.md)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [AWS X-Ray Integration](https://aws.amazon.com/xray/)
