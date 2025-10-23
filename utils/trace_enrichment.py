"""
Enhanced tracing for Strands Agent orchestration decisions.

This module enriches OpenTelemetry traces with detailed information about:
- What tools are available to the model
- What messages/context are sent to the model
- The system prompt
- The model's tool selection decisions
- Tool execution results

View these enriched traces in your observability platform (Grafana, AWS X-Ray, Honeycomb, etc.)
"""

import json
from typing import Any, Dict, List
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeInvocationEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent
)


class TraceEnrichmentHook(HookProvider):
    """
    Hook that enriches OpenTelemetry traces with agent orchestration details.

    This captures the "agent's reasoning" in terms of:
    - What information the agent provides to the model
    - What tools are made available
    - How the model decides to use that information
    - The complete decision-making context
    """

    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.current_span = None

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register hooks for different stages of agent execution."""
        registry.add_callback(BeforeInvocationEvent, self.enrich_invocation_trace)
        registry.add_callback(BeforeToolCallEvent, self.enrich_tool_selection_trace)
        registry.add_callback(AfterToolCallEvent, self.enrich_tool_result_trace)

    def enrich_invocation_trace(self, event: BeforeInvocationEvent) -> None:
        """
        Add detailed context about what the agent sends to the model.
        This creates a custom span with all the orchestration details.
        """
        with self.tracer.start_as_current_span("agent.orchestration") as span:
            agent = event.agent

            # 1. Capture available tools
            tool_names = getattr(agent, 'tool_names', []) or []
            tool_specs = []

            # Get tool specifications from the tool registry
            if hasattr(agent, 'tool_registry'):
                try:
                    tool_specs = agent.tool_registry.get_all_tool_specs() or []
                except:
                    pass  # Fallback if method fails

            span.set_attribute("agent.tools.count", len(tool_names))
            span.set_attribute("agent.tools.available", json.dumps(tool_names))

            # Add detailed tool specs as span events
            for i, tool_spec in enumerate(tool_specs):
                if isinstance(tool_spec, dict):
                    tool_name = tool_spec.get('name', 'unknown')
                    tool_desc = tool_spec.get('description', 'No description')
                    span.add_event(
                        name=f"agent.tool.spec.{i}",
                        attributes={
                            "tool.name": tool_name,
                            "tool.description": str(tool_desc)[:500],
                            "tool.has_schema": 'inputSchema' in tool_spec
                        }
                    )

            # 2. Capture messages sent to model
            messages = getattr(agent, 'messages', []) or []
            span.set_attribute("agent.messages.count", len(messages))

            for i, msg in enumerate(messages[-5:]):  # Last 5 messages to avoid overload
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', [])
                else:
                    role = getattr(msg, 'role', 'unknown')
                    content = getattr(msg, 'content', [])

                # Add each message as a span event
                message_summary = self._summarize_message(content)
                span.add_event(
                    name=f"agent.message.{i}",
                    attributes={
                        "message.role": str(role),
                        "message.summary": message_summary[:1000],
                    }
                )

            # 3. Capture system prompt
            system_prompt = getattr(agent, 'system_prompt', None)
            if system_prompt:
                span.set_attribute("agent.system_prompt", str(system_prompt)[:1000])
                span.add_event(
                    name="agent.system_prompt",
                    attributes={"prompt": str(system_prompt)[:2000]}
                )

            # 4. Capture agent state
            state = getattr(agent, 'state', {}) or {}
            if isinstance(state, dict):
                for key, value in state.items():
                    if not key.startswith('_'):  # Skip internal keys
                        try:
                            span.set_attribute(f"agent.context.{key}", str(value)[:500])
                        except:
                            pass  # Skip non-serializable values

            # 5. Add metadata about the orchestration
            span.set_attribute("agent.orchestration.phase", "before_model_invocation")
            span.set_attribute("agent.model.decision_pending", True)

    def enrich_tool_selection_trace(self, event: BeforeToolCallEvent) -> None:
        """
        Capture the model's tool selection decision.
        This shows how the model decided to use the information provided.
        """
        with self.tracer.start_as_current_span("model.tool_decision") as span:
            tool_use = event.tool_use

            # Capture the decision details
            span.set_attribute("model.decision.type", "tool_use")
            span.set_attribute("model.tool.selected", tool_use.get('name', 'unknown'))
            span.set_attribute("model.tool.use_id", tool_use.get('toolUseId', 'unknown'))

            # Capture tool inputs (the model's reasoning about parameters)
            tool_inputs = tool_use.get('input', {})
            span.set_attribute("model.tool.inputs", json.dumps(tool_inputs)[:1000])

            # Add detailed event for the tool decision
            span.add_event(
                name="model.decided_tool",
                attributes={
                    "tool.name": tool_use.get('name'),
                    "tool.use_id": tool_use.get('toolUseId'),
                    "tool.inputs.full": json.dumps(tool_inputs),
                    "decision.explanation": f"Model selected {tool_use.get('name')} with {len(tool_inputs)} parameters"
                }
            )

            # Capture which tool spec was matched
            if hasattr(event.selected_tool, '__name__'):
                span.set_attribute("agent.tool.matched_function", event.selected_tool.__name__)

            if hasattr(event.selected_tool, '__doc__'):
                span.set_attribute("agent.tool.matched_description",
                                 str(event.selected_tool.__doc__)[:500])

            span.set_status(Status(StatusCode.OK))

    def enrich_tool_result_trace(self, event: AfterToolCallEvent) -> None:
        """
        Capture tool execution results that will be sent back to the model.
        """
        with self.tracer.start_as_current_span("agent.tool_execution_result") as span:
            # AfterToolCallEvent has 'result' attribute, not 'tool_result'
            tool_result = event.result

            # Handle both dict and object formats
            if hasattr(tool_result, '__dict__'):
                tool_use_id = getattr(tool_result, 'toolUseId', 'unknown')
                status = getattr(tool_result, 'status', 'unknown')
                content = getattr(tool_result, 'content', [])
            else:
                tool_use_id = tool_result.get('toolUseId', 'unknown') if isinstance(tool_result, dict) else 'unknown'
                status = tool_result.get('status', 'unknown') if isinstance(tool_result, dict) else 'unknown'
                content = tool_result.get('content', []) if isinstance(tool_result, dict) else []

            span.set_attribute("tool.use_id", str(tool_use_id))
            span.set_attribute("tool.status", str(status))

            # Capture result content
            span.set_attribute("tool.result.content_blocks", len(content) if isinstance(content, list) else 1)

            # Add result details as span event
            result_summary = self._summarize_tool_result(content)
            span.add_event(
                name="tool.execution_completed",
                attributes={
                    "tool.use_id": str(tool_use_id),
                    "tool.status": str(status),
                    "tool.result.summary": result_summary[:1000],
                    "tool.result.full": json.dumps(content)[:2000] if len(json.dumps(content)) < 2000 else "truncated"
                }
            )

            # Set span status based on tool execution
            if str(status) == 'success':
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR))
                if str(status) == 'error':
                    error_content = next((c.get('text') for c in content if isinstance(c, dict) and 'text' in c), 'Unknown error')
                    span.record_exception(Exception(error_content))

    def _summarize_message(self, content: Any) -> str:
        """Create a human-readable summary of message content."""
        if isinstance(content, str):
            return content[:200]

        if isinstance(content, list):
            summary_parts = []
            for block in content:
                if isinstance(block, dict):
                    if 'text' in block:
                        summary_parts.append(f"[text]: {block['text'][:100]}")
                    elif 'toolUse' in block:
                        tool_use = block['toolUse']
                        summary_parts.append(f"[toolUse]: {tool_use.get('name')}")
                    elif 'toolResult' in block:
                        tool_result = block['toolResult']
                        summary_parts.append(f"[toolResult]: {tool_result.get('toolUseId')} - {tool_result.get('status')}")
            return " | ".join(summary_parts)

        return str(content)[:200]

    def _summarize_tool_result(self, content: Any) -> str:
        """Create a human-readable summary of tool result content."""
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and 'text' in block:
                    return block['text'][:200]
        return str(content)[:200]


def setup_enriched_tracing(
    agent,
    otlp_endpoint: str = "http://localhost:4318",
    service_name: str = "strands-agent",
    additional_attributes: Dict[str, Any] = None
) -> None:
    """
    Set up enriched tracing for a Strands agent.

    Args:
        agent: The Strands Agent instance
        otlp_endpoint: OpenTelemetry collector endpoint
        service_name: Service name for traces
        additional_attributes: Extra attributes to add to all spans

    Example:
        >>> from strands import Agent
        >>> agent = Agent(tools=[...])
        >>> setup_enriched_tracing(agent, service_name="my-cli-assistant")
        >>> result = agent("What is 15% of 230?")
        # View enriched traces in your observability platform
    """
    from strands.telemetry import StrandsTelemetry
    import os

    # Configure OpenTelemetry
    os.environ["OTEL_SERVICE_NAME"] = service_name
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint

    # Set up telemetry
    telemetry = StrandsTelemetry()
    telemetry.setup_otlp_exporter(endpoint=otlp_endpoint)
    telemetry.setup_console_exporter()  # Also print to console for debugging

    # Add custom attributes to agent spans
    trace_attrs = {
        "service.name": service_name,
        "agent.enhanced_tracing": True,
        "agent.tracing.version": "1.0.0"
    }

    if additional_attributes:
        trace_attrs.update(additional_attributes)

    agent.trace_attributes = trace_attrs

    # Register trace enrichment hook
    enrichment_hook = TraceEnrichmentHook()
    agent.hooks.add_hook(enrichment_hook)

    print(f"✓ Enhanced tracing enabled for {service_name}")
    print(f"✓ Traces will be sent to: {otlp_endpoint}")
    print(f"✓ View traces in your observability platform")


# Example usage
if __name__ == "__main__":
    from strands import Agent
    from strands.models import BedrockModel
    from strands_tools import calculator, file_read, current_time

    # Create agent with cross-region inference profile
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0"
    )

    agent = Agent(
        model=model,
        system_prompt="You are a helpful assistant with access to tools.",
        tools=[calculator, file_read, current_time]
    )

    # Set up enriched tracing
    setup_enriched_tracing(
        agent,
        service_name="smart-cli-assistant",
        additional_attributes={
            "environment": "development",
            "user.id": "demo-user"
        }
    )

    # Use the agent - all orchestration details will be in traces
    result = agent("What is 15% of 230 and what time is it now?")
    print(f"\nResult: {result}")

    print("\n✓ Check your observability platform to see enriched traces with:")
    print("  - Available tools sent to model")
    print("  - Messages and conversation context")
    print("  - System prompt")
    print("  - Model's tool selection decisions")
    print("  - Tool execution results")
