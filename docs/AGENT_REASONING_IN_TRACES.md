# Capturing Agent Reasoning in Traces

## Summary

You asked: **"How can I capture the agent's reasoning behind choosing a tool in traces?"**

The answer involves understanding what "agent reasoning" actually means in the Strands/AWS Bedrock architecture.

## The Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Framework (Strands)                 │
│  - Orchestrates the loop                                     │
│  - Manages tools                                             │
│  - Sends context to model                                    │
│  - Executes tool calls                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Sends to Model:
                    ✓ Available tools specs
                    ✓ Conversation history
                    ✓ System prompt
                    ✓ User query
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  LLM (Claude, etc.)                          │
│  - Analyzes the context                                      │
│  - DECIDES which tool to use                                 │
│  - Determines tool parameters                                │
│  - Returns tool use decision                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent Framework                           │
│  - Receives model's decision                                 │
│  - Executes the chosen tool                                  │
│  - Sends result back to model                                │
└─────────────────────────────────────────────────────────────┘
```

## Key Insight

**The agent framework doesn't decide which tool to use - the LLM does.**

Therefore, "agent reasoning" means capturing:
1. **What context the agent provides to the model** (orchestration)
2. **How the model uses that context to decide** (tool selection)
3. **The complete decision-making flow** (traces)

## What We Can Capture in Traces

### Standard Strands Traces (Already Included)
```
✓ User input
✓ Model invocation
✓ Tool execution
✓ Token usage
✓ Timings
```

### Enhanced Traces (Our Solution)
```
✓ Available tool specifications sent to model
✓ Complete conversation context/messages
✓ System prompt
✓ Model's tool selection decision
✓ Tool input parameters (the "reasoning")
✓ Tool execution results
✓ Full orchestration flow
```

## The Solution

We created a **trace enrichment system** that adds custom OpenTelemetry spans capturing:

### 1. Agent Orchestration Context
**What:** Everything the agent sends to the model
**Where:** `agent.orchestration` span
**Contains:**
- All available tool specs (name, description, input schema)
- All messages in conversation history
- System prompt
- Invocation state/context

### 2. Model's Decision
**What:** The model's tool selection and reasoning
**Where:** `model.tool_decision` span
**Contains:**
- Which tool was selected
- Tool input parameters
- Which tool spec was matched
- Decision explanation

### 3. Tool Execution
**What:** What happened when the tool ran
**Where:** `agent.tool_execution_result` span
**Contains:**
- Execution status
- Result content
- Error details (if any)

## Files Created

### 1. `utils/trace_enrichment.py`
The core enrichment system:
- `TraceEnrichmentHook`: Hooks into agent lifecycle
- `setup_enriched_tracing()`: Easy setup function
- Adds custom spans and attributes to OpenTelemetry traces

### 2. `examples/trace_enrichment_demo.py`
Three demo scenarios:
- Basic tool selection
- Multiple tool usage
- Conversation context tracking

### 3. `docs/TRACE_ENRICHMENT.md`
Complete guide with:
- Quick start instructions
- Trace structure visualization
- Use cases and troubleshooting
- Integration examples

## How to Use

### Step 1: Start Observability Backend

```bash
# Jaeger (local development)
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

### Step 2: Enable in Your Code

```python
from utils.trace_enrichment import setup_enriched_tracing

agent = Agent(...)

setup_enriched_tracing(
    agent,
    service_name="my-agent",
    additional_attributes={"environment": "prod"}
)

result = agent("What is 15% of 230?")
```

### Step 3: View Traces

Open http://localhost:16686 and see:

```
Trace Timeline:
├── agent.orchestration (NEW!)
│   ├── Available tools: [calculator, file_read, ...]
│   ├── Messages: [user query, previous context, ...]
│   └── System prompt: "You are a helpful assistant..."
│
├── model.tool_decision (NEW!)
│   ├── Selected: "calculator"
│   ├── Inputs: {"expression": "230 * 0.15"}
│   └── Reasoning: Model chose calculator based on math query
│
├── Tool execution
│   └── Result: "34.5"
│
└── agent.tool_execution_result (NEW!)
    └── Status: success, Result: "34.5"
```

## What This Solves

### Before
❌ "Why did my agent choose the wrong tool?"
- Could only see THAT a tool was used
- Couldn't see what other tools were available
- Couldn't see what context the model had

### After
✅ "I can see exactly why the tool was chosen:"
- See all available tools and their descriptions
- See the complete conversation context
- See the system prompt guiding decisions
- See the tool input parameters (the reasoning)
- Correlate tool selection with available context

## Real-World Benefits

### 1. Debugging
- Quickly identify why wrong tool was selected
- See if tool descriptions are clear enough
- Verify correct tools are available

### 2. Optimization
- A/B test different system prompts
- Optimize tool descriptions for better selection
- Identify redundant tools

### 3. Monitoring
- Alert on unexpected tool usage
- Track tool selection accuracy over time
- Monitor conversation context growth

### 4. Compliance
- Audit trail of agent decisions
- Understand what data was used in decisions
- Verify tool usage policies

## Example Trace Output

### Jaeger UI View
```
Service: smart-cli-assistant
Trace ID: abc123...

Spans:
[====================================] strands-agent (2.5s)
  [===                              ] agent.orchestration (50ms)
    Attributes:
      agent.tools.count: 3
      agent.tools.available: ["calculator", "file_read", "current_time"]
      agent.system_prompt: "You are a helpful..."
    Events:
      → agent.tool.spec.0 (calculator)
      → agent.message.0 (user query)

  [==========                       ] model.tool_decision (100ms)
    Attributes:
      model.tool.selected: "calculator"
      model.tool.inputs: {"expression": "230 * 0.15"}
    Events:
      → model.decided_tool

  [==========================       ] agent.tool_execution_result (10ms)
    Attributes:
      tool.status: "success"
      tool.result.summary: "34.5"
```

### AWS X-Ray View
Similar structure with:
- Segment: strands-agent
- Subsegments: orchestration, decision, execution
- Annotations: tool names, counts, status
- Metadata: full tool specs, messages, results

## Key Takeaways

1. **The "agent" doesn't reason - the LLM does**
   - Agent = orchestration framework
   - LLM = decision maker

2. **We capture the orchestration decisions**
   - What tools to make available
   - What context to provide
   - How to structure the interaction

3. **We capture the model's decisions**
   - Which tool it chose
   - What parameters it decided on
   - Based on what context

4. **Everything is in OpenTelemetry traces**
   - Standard observability format
   - Works with any OTLP-compatible backend
   - Queryable, filterable, alertable

5. **This IS the "agent's reasoning"**
   - It's the complete decision-making context
   - It's the orchestration logic
   - It's the model's tool selection rationale

## Next Steps

1. **Try the demo:**
   ```bash
   python examples/trace_enrichment_demo.py
   ```

2. **View traces:**
   - Open http://localhost:16686
   - Select service: "trace-demo-basic"
   - Explore the spans

3. **Integrate with your app:**
   - Update `cli_assistant.py` to use `setup_enriched_tracing()`
   - Deploy to production
   - Set up dashboards in your observability platform

4. **Create alerts:**
   - Tool selection failures
   - Unexpected tool usage
   - Context window issues

## Questions?

**Q: Can I get the LLM's internal reasoning?**
A: Only if the model supports it (like Claude's Extended Thinking). That's different from agent orchestration.

**Q: Will this increase costs?**
A: Minimal - only adds spans/attributes to existing traces. No extra LLM calls.

**Q: Does it work with AWS Bedrock Agents?**
A: Yes! Same architecture - agent orchestrates, model decides.

**Q: Can I customize what's captured?**
A: Yes! Extend the `TraceEnrichmentHook` class to add your own attributes.

**Q: What about PII in traces?**
A: Add span processors to redact sensitive data (examples in docs).
