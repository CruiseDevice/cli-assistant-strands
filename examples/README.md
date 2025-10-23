# Examples

## Trace Enrichment Demo

Demonstrates how to capture the agent's orchestration decisions in OpenTelemetry traces.

### Quick Start

```bash
# 1. Start Jaeger
docker run -d --name jaeger -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one:latest

# 2. Run demo
python examples/trace_enrichment_demo.py

# 3. View traces
open http://localhost:16686
```

### What You'll See

**In Jaeger UI:**
```
Service: trace-demo-basic
├── agent.orchestration
│   └── Shows: Available tools, messages, system prompt
├── model.tool_decision  
│   └── Shows: Which tool selected, why, with what inputs
└── agent.tool_execution_result
    └── Shows: Execution status, results
```

### Three Demo Scenarios

1. **Basic Tool Selection**
   - Single tool use
   - Shows complete decision context

2. **Multiple Tool Selection**
   - Multiple tools in sequence
   - Shows decision timeline

3. **Conversation Context**
   - Multi-turn conversation
   - Shows context accumulation

### Learn More

See [../docs/AGENT_REASONING_IN_TRACES.md](../docs/AGENT_REASONING_IN_TRACES.md) for complete documentation.
