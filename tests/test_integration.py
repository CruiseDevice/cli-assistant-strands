import os
import pytest
from cli_assistant import initialize_agent
from utils.cost_tracker import CostTracker


# Shared cost tracker instance (tests use same tracking as production)
@pytest.fixture
def cost_tracker():
    """Create a cost tracker using the same storage as production.

    Note: Test API calls cost real money and should be tracked alongside
    production usage for accurate cost monitoring.
    """
    tracker = CostTracker(storage_file="cost_tracking.json")
    yield tracker


def test_full_system_initialization(cost_tracker):
    """Test that the entire system initializes correctly."""
    agent = initialize_agent()
    assert agent is not None

    # Verify tools are loaded (calculator, python_repl, file_read)
    assert len(agent.tool_names) == 3


def test_cost_tracking_integration():
    """Test cost tracking works with agent."""
    cost_tracker = CostTracker('test_cost_tracking.json')

    # simulate a request
    cost_info = cost_tracker.track_request(
        model='claude-3.5-haiku',
        input_tokens=100,
        output_tokens=150
    )

    assert cost_info['request_cost'] > 0
    assert cost_info['daily_cost'] > 0

    # cleanup
    import os
    os.remove('test_cost_tracking.json')


@pytest.mark.integration
def test_agent_basic_query():
    """Test agent can response to basic queries"""
    agent = initialize_agent()

    response = agent("What is 5 + 5?")
    response_text = str(response)

    # track tool usage
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else 'tool_name'
            cost_tracker.track_tool_usage(tool_name)


    assert response_text is not None
    assert len(response_text) > 0


@pytest.mark.integration
def test_agent_with_calculator():
    """Test agent using calculator tool."""
    agent = initialize_agent()

    response = agent("Calculate 25 * 40")
    response_text = str(response)

    # track tool usage
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else 'tool_name'
            cost_tracker.track_tool_usage(tool_name)

    # should mention the result 1000
    assert any(str(num) in response_text for num in ['1000', '1,000'])


@pytest.mark.integration
def test_agent_system_info():
    """Test agent using system info tool."""
    agent = initialize_agent()

    response = agent("What's my current CPU usage?")
    response_text = str(response)

    # track tool usage
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else 'tool_name'
            cost_tracker.track_tool_usage(tool_name)

    assert response_text is not None
    assert 'cpu' in response_text.lower() or '%' in response_text


def test_tool_usage_tracking():
    """Test that tool usage is tracked."""
    cost_tracker = CostTracker('test_tool_tracking.json')

    # Track some tool usage
    cost_tracker.track_tool_usage('calculator')
    cost_tracker.track_tool_usage('calculator')
    cost_tracker.track_tool_usage('get_system_info')

    summary = cost_tracker.get_tool_summary()

    assert 'calculator' in summary
    assert 'get_system_info' in summary

    # Cleanup
    os.remove('test_tool_tracking.json')

# @pytest.mark.integration
# def test_note_workflow():
#     """Test complete note-taking workflow."""
#     from tools.custom_tools import save_note, list_notes
#     from pathlib import Path

#     # Clean up
#     notes_dir = Path('notes')
#     if notes_dir.exists():
#         for note in notes_dir.glob('*.txt'):
#             note.unlink()

#     # Save multiple notes
#     save_note("Note 1", "Content 1")
#     save_note("Note 2", "Content 2")
#     save_note("Note 3", "Content 3")

#     # List should show all notes
#     notes_list = list_notes()
#     assert "Note 1" in notes_list
#     assert "Note 2" in notes_list
#     assert "Note 3" in notes_list
