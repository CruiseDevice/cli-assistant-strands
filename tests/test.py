import pytest
import os
from strands.models import BedrockModel
from strands_tools import calculator, python_repl, file_read
from strands import Agent
from dotenv import load_dotenv
from utils.cost_tracker import CostTracker


load_dotenv()


# Shared cost tracker instance (tests use same tracking as production)
@pytest.fixture
def cost_tracker():
    """Create a cost tracker using the same storage as production.

    Note: Test API calls cost real money and should be tracked alongside
    production usage for accurate cost monitoring.
    """
    tracker = CostTracker(storage_file="cost_tracking.json")
    yield tracker


def test_calculator_tool(cost_tracker):
    """Test calculator tool integration."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        streaming=False
    )
    agent = Agent(
        model=model,
        tools=[calculator]
    )

    user_input = "What is 156 * 234?"
    response = agent(user_input)
    response_text = str(response)

    assert response_text is not None

    # check if the answer appears in the response
    assert "36504" in response_text or "36,504" in response_text

    # Track costs
    estimated_input_tokens = len(user_input.split()) * 1.3
    estimated_output_tokens = len(response_text.split()) * 1.3

    cost_info = cost_tracker.track_request(
        model='claude-3.5-haiku',
        input_tokens=int(estimated_input_tokens),
        output_tokens=int(estimated_output_tokens)
    )

    # Track tool usage
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else 'calculator'
            cost_tracker.track_tool_usage(tool_name)

    # Verify cost tracking worked
    assert cost_info['request_cost'] > 0


@pytest.mark.asyncio
async def test_python_repl_tool(cost_tracker):
    """Test Python REPL tool."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        streaming=False
    )

    agent = Agent(
        model=model,
        tools=[python_repl]
    )

    user_input = "Write Python code to calculate the 10th Fibonacci number"
    response = agent(user_input)
    response_text = str(response)

    assert response_text is not None

    # Fibonacci(10) = 55
    assert "55" in response_text

    # Track costs
    estimated_input_tokens = len(user_input.split()) * 1.3
    estimated_output_tokens = len(response_text.split()) * 1.3

    cost_info = cost_tracker.track_request(
        model='claude-3.5-haiku',
        input_tokens=int(estimated_input_tokens),
        output_tokens=int(estimated_output_tokens)
    )

    # Track tool usage
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else 'python_repl'
            cost_tracker.track_tool_usage(tool_name)

    # Verify cost tracking worked
    assert cost_info['request_cost'] > 0


def test_cost_efficiency(cost_tracker):
    """Verify the agent uses simple responses when no tools are needed"""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        streaming=False
    )

    agent = Agent(
        model=model,
        tools=[calculator]
    )

    # simple question shouldn't invoke tools
    user_input = "What is Python?"
    response = agent(user_input)
    response_text = str(response)

    # check that response exists and is reasonable
    assert response_text is not None
    assert len(response_text) > 10

    # Track costs
    estimated_input_tokens = len(user_input.split()) * 1.3
    estimated_output_tokens = len(response_text.split()) * 1.3

    cost_info = cost_tracker.track_request(
        model='claude-3.5-haiku',
        input_tokens=int(estimated_input_tokens),
        output_tokens=int(estimated_output_tokens)
    )

    # Verify cost tracking worked
    assert cost_info['request_cost'] > 0

    # Verify no tools were used (cost efficiency)
    if hasattr(response, 'tool_calls'):
        assert not response.tool_calls or len(response.tool_calls) == 0


def test_multiple_calculations(cost_tracker):
    """Test multiple calculations in sequence."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        streaming=False
    )

    agent = Agent(
        model=model,
        tools=[calculator]
    )

    # Test a series of calculations
    test_cases = [
        ("What is 25 + 75?", "100"),
        ("Calculate 12 * 12", "144"),
        ("What's 1000 / 25?", "40"),
    ]

    for question, expected in test_cases:
        response = agent(question)
        response_text = str(response)
        assert expected in response_text, f"Expected {expected} in response to '{question}'"

        # Track costs for each request
        estimated_input_tokens = len(question.split()) * 1.3
        estimated_output_tokens = len(response_text.split()) * 1.3

        cost_tracker.track_request(
            model='claude-3.5-haiku',
            input_tokens=int(estimated_input_tokens),
            output_tokens=int(estimated_output_tokens)
        )

        # Track tool usage
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else 'calculator'
                cost_tracker.track_tool_usage(tool_name)


def test_file_read_tool(cost_tracker):
    """Test file_read tool integration."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        streaming=False
    )

    agent = Agent(
        model=model,
        tools=[file_read]
    )

    # Create a temporary test file
    test_file_path = "test_read_file.txt"
    test_content = "This is a test file for file_read tool."

    with open(test_file_path, "w") as f:
        f.write(test_content)

    try:
        user_input = f"Read the contents of {test_file_path}"
        response = agent(user_input)
        response_text = str(response)

        assert response_text is not None
        assert "test file for file_read tool" in response_text

        # Track costs
        estimated_input_tokens = len(user_input.split()) * 1.3
        estimated_output_tokens = len(response_text.split()) * 1.3

        cost_info = cost_tracker.track_request(
            model='claude-3.5-haiku',
            input_tokens=int(estimated_input_tokens),
            output_tokens=int(estimated_output_tokens)
        )

        # Track tool usage
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else 'file_read'
                cost_tracker.track_tool_usage(tool_name)

        # Verify cost tracking worked
        assert cost_info['request_cost'] > 0
    finally:
        # Clean up the test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
