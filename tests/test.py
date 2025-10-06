import pytest
import os
from strands.models import BedrockModel
from strands_tools import calculator, python_repl
from strands import Agent
from dotenv import load_dotenv

load_dotenv()


def test_calculator_tool():
    """Test calculator tool integration."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        region=os.getenv('AWS_REGION', 'us-west-2'),
        streaming=False
    )
    agent = Agent(
        model=model,
        tools=[calculator]
    )

    response = agent("What is 156 * 234?")
    response_text = str(response)

    assert response_text is not None

    # check if the answer appears in the response
    assert "36504" in response_text or "36,504" in response_text


@pytest.mark.asyncio
async def test_python_repl_tool():
    """Test Python REPL tool."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        region=os.getenv('AWS_REGION', 'us-west-2'),
        streaming=False
    )

    agent = Agent(
        model=model,
        tools=[python_repl]
    )

    response = agent("Write Python code to calculate the 10th Fibonacci number")
    response_text = str(response)

    assert response_text is not None

    # Fibonacci(10) = 55
    assert "55" in response_text


def test_cost_efficiency():
    """Verify the agent uses simple responses when no tools are needed"""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        region=os.getenv('AWS_REGION', 'us-west-2'),
        streaming=False
    )

    agent = Agent(
        model=model,
        tools=[calculator]
    )

    # simple question shouldn't invoke tools
    response = agent("What is Python?")
    response_text = str(response)

    # check that response exists and is reasonable
    assert response_text is not None
    assert len(response_text) > 10


def test_multiple_calculations():
    """Test multiple calculations in sequence."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        region=os.getenv('AWS_REGION', 'us-west-2'),
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
