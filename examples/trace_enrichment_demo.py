"""
Demo: Enhanced Tracing for Agent Orchestration

This example demonstrates how to capture the agent's orchestration decisions
in OpenTelemetry traces. View these traces in your observability platform to see:

1. What tools are available to the model
2. What messages/context are sent to the model
3. The system prompt
4. The model's tool selection decision
5. Tool execution results

Setup:
    1. Run Jaeger locally:
       docker run -d --name jaeger \
         -p 16686:16686 \
         -p 4318:4318 \
         jaegertracing/all-in-one:latest

    2. Run this script:
       python examples/trace_enrichment_demo.py

    3. View traces at: http://localhost:16686
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator, current_time
from utils.trace_enrichment import setup_enriched_tracing
from rich.console import Console
from rich.panel import Panel

console = Console()


def demo_basic_tracing():
    """Basic example with enriched tracing."""
    console.print("\n[bold blue]Demo 1: Basic Tool Selection with Enriched Tracing[/bold blue]\n")

    # Create agent with cross-region inference profile
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0"
    )

    agent = Agent(
        model=model,
        system_prompt="""You are a helpful assistant with access to tools.

When selecting tools:
- Use calculator for mathematical operations
- Use current_time for time-related queries
- Explain your reasoning before using tools""",
        tools=[calculator, current_time]
    )

    # Enable enriched tracing
    setup_enriched_tracing(
        agent,
        service_name="trace-demo-basic",
        additional_attributes={
            "demo.type": "basic",
            "demo.scenario": "tool_selection"
        }
    )

    # Run query that requires tool selection
    query = "What is 15% of 230?"
    console.print(f"[yellow]Query:[/yellow] {query}\n")

    result = agent(query)
    console.print(f"[green]Result:[/green] {result}\n")

    # Show what's in the traces
    console.print(Panel(
        """[bold]✓ Trace Data Captured:[/bold]

1. [cyan]Agent Orchestration Span:[/cyan]
   - agent.tools.count: 2
   - agent.tools.available: ["calculator", "current_time"]
   - agent.system_prompt: "You are a helpful assistant..."
   - agent.messages.count: 1

2. [cyan]Tool Spec Events:[/cyan]
   - tool.name: "calculator"
   - tool.description: "Perform mathematical calculations"
   - tool.input_schema: {...}

3. [cyan]Model Decision Span:[/cyan]
   - model.decision.type: "tool_use"
   - model.tool.selected: "calculator"
   - model.tool.inputs: {"expression": "230 * 0.15"}

4. [cyan]Tool Execution Span:[/cyan]
   - tool.status: "success"
   - tool.result.summary: "34.5"

[dim]View complete traces at: http://localhost:16686[/dim]""",
        title="Trace Contents",
        border_style="green"
    ))


def demo_multi_tool_selection():
    """Demo with multiple tool calls."""
    console.print("\n[bold blue]Demo 2: Multiple Tool Selection[/bold blue]\n")

    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0"
    )

    agent = Agent(
        model=model,
        system_prompt="""You are a helpful assistant.

Available tools:
- calculator: For math operations
- current_time: For time queries

Use multiple tools when needed to answer the query completely.""",
        tools=[calculator, current_time]
    )

    setup_enriched_tracing(
        agent,
        service_name="trace-demo-multi-tool",
        additional_attributes={
            "demo.type": "multi_tool",
            "demo.expected_tools": 2
        }
    )

    query = "What is 25 * 48 and what time is it now?"
    console.print(f"[yellow]Query:[/yellow] {query}\n")

    result = agent(query)
    console.print(f"[green]Result:[/green] {result}\n")

    console.print(Panel(
        """[bold]✓ Multiple Tool Decisions Captured:[/bold]

Each tool selection creates its own span showing:
- Why the model chose calculator first
- Then why it chose current_time
- The inputs for each tool
- The sequence of decision-making

[cyan]Trace Timeline:[/cyan]
1. Agent orchestration (what was sent to model)
2. Model decision: calculator (with expression parameter)
3. Tool execution: calculator result
4. Model decision: current_time (with timezone parameter)
5. Tool execution: current_time result
6. Final response synthesis

[dim]View the complete decision timeline at: http://localhost:16686[/dim]""",
        title="Multi-Tool Trace",
        border_style="green"
    ))


def demo_conversation_context():
    """Demo showing conversation context in traces."""
    console.print("\n[bold blue]Demo 3: Conversation Context in Traces[/bold blue]\n")

    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0"
    )

    agent = Agent(
        model=model,
        system_prompt="You are a helpful assistant that remembers conversation context.",
        tools=[calculator]
    )

    setup_enriched_tracing(
        agent,
        service_name="trace-demo-conversation",
        additional_attributes={
            "demo.type": "conversation_context"
        }
    )

    # First query
    query1 = "Calculate 100 * 25"
    console.print(f"[yellow]Query 1:[/yellow] {query1}\n")
    result1 = agent(query1)
    console.print(f"[green]Result 1:[/green] {result1}\n")

    # Follow-up query with context
    query2 = "Now divide that result by 10"
    console.print(f"[yellow]Query 2:[/yellow] {query2}\n")
    result2 = agent(query2)
    console.print(f"[green]Result 2:[/green] {result2}\n")

    console.print(Panel(
        """[bold]✓ Conversation Context Captured:[/bold]

For the second query, the trace shows:

[cyan]Agent Orchestration Span:[/cyan]
- agent.messages.count: 3
  - Message 0 (user): "Calculate 100 * 25"
  - Message 1 (assistant): [toolUse: calculator] + text response
  - Message 2 (user): "Now divide that result by 10"

[cyan]Model Decision Span:[/cyan]
Shows how the model used conversation history to understand
"that result" refers to 2500 from the previous calculation.

This lets you see:
- What context the model had available
- How it used previous tool results
- The full conversation flow in the trace

[dim]View the conversation flow at: http://localhost:16686[/dim]""",
        title="Conversation Context Trace",
        border_style="green"
    ))


def main():
    """Run all demos."""
    console.print(Panel(
        """[bold cyan]Enhanced Agent Tracing Demo[/bold cyan]

This demo shows how agent orchestration decisions are captured in traces.

[yellow]Prerequisites:[/yellow]
1. Jaeger running on http://localhost:4318
2. AWS credentials configured
3. Bedrock access enabled

[yellow]What you'll see in traces:[/yellow]
✓ Available tools sent to model
✓ Messages and conversation context
✓ System prompts
✓ Model's tool selection decisions
✓ Tool execution results
✓ Complete orchestration flow

[dim]After running, view traces at: http://localhost:16686[/dim]""",
        title="Trace Enrichment Demo",
        border_style="blue"
    ))

    try:
        demo_basic_tracing()
        console.print("\n" + "="*80 + "\n")

        demo_multi_tool_selection()
        console.print("\n" + "="*80 + "\n")

        demo_conversation_context()

        console.print(Panel(
            """[bold green]✓ Demos Complete![/bold green]

[yellow]View your traces:[/yellow]
1. Open http://localhost:16686
2. Select service: "trace-demo-basic" (or other demo names)
3. Click "Find Traces"
4. Click on a trace to see:
   - Agent orchestration details
   - Tool specs sent to model
   - Model's decision-making
   - Tool execution results

[cyan]Trace Structure:[/cyan]
strands-agent
  └── agent.orchestration (what was sent to model)
      ├── Events: tool specs, messages, system prompt
      └── model.tool_decision (model's choice)
          ├── Attributes: selected tool, inputs
          └── agent.tool_execution_result
              └── Attributes: status, result

[bold]This is the "agent's reasoning" captured in traces![/bold]""",
            title="Next Steps",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]Make sure:[/yellow]")
        console.print("1. Jaeger is running: docker run -d --name jaeger -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one:latest")
        console.print("2. AWS credentials are configured")
        console.print("3. Bedrock access is enabled")


if __name__ == "__main__":
    main()
