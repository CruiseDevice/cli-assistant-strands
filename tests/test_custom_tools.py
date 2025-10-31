"""
Test suite for custom tools.
Run with: pytest tests/test_custom_tools.py -v
"""
import pytest
from pathlib import Path
from tools.custom_tools import (
    get_system_info,
    save_note,
    list_notes,
    search_web,
    estimate_cost
)

def test_system_info():
    """Test system info retrieval."""
    info = get_system_info()

    assert 'cpu_percent' in info
    assert 'memory_percent' in info
    assert 'disk_percent' in info
    assert 0 <= info['cpu_percent'] <= 100
    assert 0 <= info['memory_percent'] <= 100

def test_save_and_list_notes():
    """Test note saving and listing."""
    # Clean up notes directory
    notes_dir = Path('notes')
    if notes_dir.exists():
        for note in notes_dir.glob('*.txt'):
            note.unlink()

    # Save a note
    result = save_note("Test Note", "This is a test")
    assert "Note saved" in result

    # List notes
    notes = list_notes()
    assert "Test Note" in notes

def test_web_search():
    """Test web search functionality."""
    results = search_web("Python programming")

    # Should return some results or an error message
    assert len(results) > 0
    assert isinstance(results, str)

def test_cost_estimation():
    """Test cost estimation tool."""
    estimate = estimate_cost(
        "What is the capital of France?",
        output_words=50
    )

    assert "Cost Estimate" in estimate
    assert "$" in estimate
    assert "tokens" in estimate

@pytest.mark.parametrize("title,content", [
    ("Simple Note", "Simple content"),
    ("Note with Numbers 123", "Content 456"),
    ("Note-with-dashes", "Dashed content")
])
def test_note_variations(title, content):
    """Test note saving with various titles."""
    result = save_note(title, content)
    assert "Note saved" in result

    # Verify file exists
    notes_dir = Path('notes')
    assert any(notes_dir.glob('*.txt'))
