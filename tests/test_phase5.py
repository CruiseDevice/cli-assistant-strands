"""
Tests for Phase 5: Session management.
"""
import pytest
import shutil
from pathlib import Path
from utils.session_manager import SessionManager, Message, Session


@pytest.fixture
def session_manager():
    """Create temporary session manager."""
    sm = SessionManager('test_sessions')
    yield sm
    # Cleanup
    if Path('test_sessions').exists():
        shutil.rmtree('test_sessions')


def test_create_session(session_manager):
    """Test session creation."""
    session = session_manager.create_session('haiku')

    assert session is not None
    assert session.session_id
    assert session.model == 'haiku'
    assert session.message_count == 0
    assert session.total_cost == 0.0


def test_add_message(session_manager):
    """Test adding messages to session."""
    session = session_manager.create_session('haiku')

    session_manager.add_message('user', 'Hello', tokens=10, cost=0.001)
    session_manager.add_message('assistant', 'Hi there!', tokens=15, cost=0.002)

    assert session.message_count == 2
    assert session.total_tokens == 25
    assert abs(session.total_cost - 0.003) < 0.0001


def test_load_session(session_manager):
    """Test loading existing session."""
    session1 = session_manager.create_session('haiku')
    session_id = session1.session_id

    session_manager.add_message('user', 'Test message')

    # Load session
    session2 = session_manager.load_session(session_id)

    assert session2 is not None
    assert session2.session_id == session_id
    assert session2.message_count == 1


def test_context_limits(session_manager):
    """Test context limiting for cost optimization."""
    session = session_manager.create_session('haiku')

    # Add many messages
    for i in range(30):
        session_manager.add_message('user', f'Message {i}' * 100, tokens=130)
        session_manager.add_message('assistant', f'Response {i}' * 100, tokens=130)

    # Get context
    context = session_manager.get_context_for_model()

    # Should be limited
    assert len(context) <= session_manager.max_messages_in_context

    # Calculate total tokens
    total_tokens = sum(len(msg['content'].split()) * 1.3 for msg in context)
    assert total_tokens <= session_manager.max_context_tokens


def test_list_sessions(session_manager):
    """Test listing all sessions."""
    session_manager.create_session('haiku')
    session_manager.create_session('sonnet')

    sessions = session_manager.list_sessions()

    assert len(sessions) == 2
    assert all('session_id' in s for s in sessions)


def test_export_markdown(session_manager):
    """Test markdown export."""
    session = session_manager.create_session('haiku')
    session_manager.add_message('user', 'Hello')
    session_manager.add_message('assistant', 'Hi there!')

    markdown = session_manager.export_session(session.session_id, 'markdown')

    assert '# Conversation Session' in markdown
    assert 'Hello' in markdown
    assert 'Hi there!' in markdown


def test_search_sessions(session_manager):
    """Test searching sessions."""
    session1 = session_manager.create_session('haiku')
    session_manager.add_message('user', 'Python programming question')

    session2 = session_manager.create_session('sonnet')
    session_manager.add_message('user', 'JavaScript debugging help')

    # Search for Python
    results = session_manager.search_sessions('Python')

    assert len(results) == 1
    assert 'Python' in results[0]['matches'][0]


def test_delete_session(session_manager):
    """Test session deletion."""
    session = session_manager.create_session('haiku')
    session_id = session.session_id

    # Delete
    result = session_manager.delete_session(session_id)

    assert result == True
    assert session_manager.load_session(session_id) is None


def test_message_dataclass():
    """Test Message dataclass."""
    msg = Message(
        role='user',
        content='Hello',
        timestamp='2025-01-15T10:30:00',
        tokens=10,
        cost=0.001,
        tools_used=['calculator']
    )

    assert msg.role == 'user'
    assert msg.content == 'Hello'
    assert msg.tokens == 10
    assert msg.cost == 0.001
    assert msg.tools_used == ['calculator']


def test_session_to_dict(session_manager):
    """Test Session to_dict conversion."""
    session = session_manager.create_session('haiku')
    session_manager.add_message('user', 'Hello')

    data = session.to_dict()

    assert isinstance(data, dict)
    assert data['session_id'] == session.session_id
    assert data['model'] == 'haiku'
    assert len(data['messages']) == 1


def test_session_from_dict(session_manager):
    """Test Session from_dict conversion."""
    session = session_manager.create_session('haiku')
    session_manager.add_message('user', 'Hello')

    data = session.to_dict()
    restored_session = Session.from_dict(data)

    assert restored_session.session_id == session.session_id
    assert restored_session.model == session.model
    assert len(restored_session.messages) == len(session.messages)


def test_export_json(session_manager):
    """Test JSON export."""
    session = session_manager.create_session('haiku')
    session_manager.add_message('user', 'Hello')

    json_str = session_manager.export_session(session.session_id, 'json')

    assert 'session_id' in json_str
    assert 'Hello' in json_str


def test_no_active_session():
    """Test error when no active session."""
    sm = SessionManager('test_sessions_temp')

    with pytest.raises(ValueError, match="No active session"):
        sm.add_message('user', 'Hello')

    # Cleanup
    if Path('test_sessions_temp').exists():
        shutil.rmtree('test_sessions_temp')


def test_session_persistence(session_manager):
    """Test that sessions persist across manager instances."""
    session = session_manager.create_session('haiku')
    session_id = session.session_id
    session_manager.add_message('user', 'Persistent message')

    # Create new manager instance
    new_manager = SessionManager('test_sessions')
    loaded_session = new_manager.load_session(session_id)

    assert loaded_session is not None
    assert loaded_session.session_id == session_id
    assert loaded_session.message_count == 1
