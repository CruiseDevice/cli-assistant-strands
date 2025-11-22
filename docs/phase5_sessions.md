# Phase 5: Session Management Guide

## Overview

Session management allows you to:
- Save conversation history
- Resume previous conversations
- Search past discussions
- Export conversations
- Manage context efficiently (cost optimization)

## Basic Usage

### Starting a New Session
```bash
python cli_assistant.py
# Automatically creates new session
```

### Loading an Existing Session
```bash
python cli_assistant.py --session <session-id>
```

### Session Commands

**List all sessions:**
```
You: sessions
```

**View current session info:**
```
You: session
```

**Load a different session:**
```
You: load <session-id>
```

**Start fresh session:**
```
You: clear
```

**Export session:**
```
You: export <session-id> markdown
You: export <session-id> json
```

**Search sessions:**
```
You: search python
You: search AWS configuration
```

## Cost Optimization Features

### Context Management

Sessions automatically limit context to reduce costs:

**Token Limit:** 4,000 tokens
- Keeps only recent messages
- Prevents excessive context costs
- Maintains conversation quality

**Message Limit:** 20 messages
- Focuses on recent conversation
- Avoids context bloat
- Reduces input tokens

### How It Works

```
Session: 50 messages (10,000 tokens total)
↓
Context Manager applies limits
↓
Sends to model: 15 messages (3,500 tokens)
↓
Cost savings: ~65% reduction in input tokens!
```

### Customizing Limits

Edit `utils/session_manager.py`:
```python
self.max_context_tokens = 4000  # Increase for more context
self.max_messages_in_context = 20  # Increase for longer memory
```

⚠️ **Warning:** Higher limits = higher costs

## Best Practices

### 1. Session Strategy

**Short Tasks (< 10 messages):**
```bash
# Start fresh each time
python cli_assistant.py
```

**Ongoing Projects:**
```bash
# Use same session
python cli_assistant.py --session abc123def456
```

**Multiple Projects:**
```bash
# Create separate sessions per project
Project A: session_id_1
Project B: session_id_2
```

### 2. Cost Management

**Check session costs regularly:**
```
You: session
# Shows total cost for current session
```

**Export before deleting:**
```
You: export <session-id> markdown
# Save for records
```

**Clear old context when switching topics:**
```
You: clear
# Start fresh to avoid irrelevant context
```

### 3. Search and Organization

**Descriptive first messages:**
```
You: Working on AWS Lambda deployment for project X
```

**Tag important sessions:**
```
You: save_note "Project X Session" "session-id: abc123"
```

**Regular cleanup:**
```python
# Delete old sessions
from utils.session_manager import SessionManager
sm = SessionManager()
sessions = sm.list_sessions()

# Delete sessions older than 30 days
for session in sessions:
    # ... check date and delete ...
```

## Examples

### Example 1: Resume Work
```bash
# Yesterday
python cli_assistant.py
You: I'm working on a Python web scraper
Assistant: Great! What do you need help with?
You: quit

# Today - resume
python cli_assistant.py --session <id-from-yesterday>
You: sessions
# Find yesterday's session
You: load abc123
You: Let's continue with the scraper. How do I handle rate limiting?
Assistant: [Remembers previous context about your scraper]
```

### Example 2: Research Project
```bash
python cli_assistant.py --model sonnet

You: I'm researching AWS cost optimization strategies
Assistant: I can help with that...

# Multiple interactions...

You: save_note "AWS Research" "Session ID: abc123. Covered: S3, Lambda, RDS optimization"
You: export abc123 markdown
# Saves full conversation

You: quit
```

### Example 3: Search Past Help
```bash
python cli_assistant.py

You: search Lambda cold start
# Finds all sessions discussing Lambda cold starts

You: load def456
# Load session with relevant discussion

You: What did we discuss about cold starts?
Assistant: [Provides summary from loaded session]
```

## Session File Format

Sessions are stored as JSON in `sessions/` directory:

```json
{
  "session_id": "abc123...",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T11:45:00",
  "model": "haiku",
  "total_cost": 0.0234,
  "total_tokens": 1500,
  "message_count": 12,
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-01-15T10:30:00",
      "tokens": 10,
      "cost": 0.0001
    }
  ]
}
```

## Troubleshooting

### Session Not Found
```
Error: Session not found
Solution: Check session ID with 'sessions' command
```

### Context Too Large
```
Warning: Context exceeds token limit
Solution: Start new session with 'clear'
```

### Slow Loading
```
Issue: Large session takes time to load
Solution: Export and archive old sessions
```

## Advanced: Programmatic Access

```python
from utils.session_manager import SessionManager

# Create manager
sm = SessionManager()

# Create session
session = sm.create_session('haiku')

# Add messages
sm.add_message('user', 'Hello')
sm.add_message('assistant', 'Hi!')

# Get optimized context
context = sm.get_context_for_model()

# Export
markdown = sm.export_session(session.session_id, 'markdown')
```

## Architecture

### Components

1. **Message** - Individual conversation message
   - role (user/assistant)
   - content
   - timestamp
   - tokens (optional)
   - cost (optional)
   - tools_used (optional)

2. **Session** - Complete conversation session
   - session_id
   - created_at / updated_at
   - model
   - total_cost / total_tokens
   - message_count
   - messages list

3. **SessionManager** - Session lifecycle management
   - create_session()
   - load_session()
   - add_message()
   - get_context_for_model()
   - list_sessions()
   - search_sessions()
   - export_session()
   - delete_session()

### Context Optimization Algorithm

```python
def get_context_for_model():
    """
    Cost-optimized context selection.

    Algorithm:
    1. Start from most recent message
    2. Work backwards
    3. Keep adding messages until:
       - Message count limit reached (20)
       - Token limit reached (4000)
    4. Return selected messages
    """
```

This ensures:
- Most recent context is preserved
- Older messages are dropped first
- Cost is minimized
- Quality is maintained

## Performance

### Storage
- Sessions stored as JSON files
- One file per session
- Lightweight and portable
- Easy backup/restore

### Memory
- Only current session in memory
- Messages loaded on demand
- Minimal memory footprint

### Cost Savings
- 60-70% reduction in input tokens for long conversations
- Automatic context trimming
- No manual intervention required

## Migration Guide

### From No Sessions to Sessions

If you're upgrading from a version without sessions:

1. **No action needed** - Sessions are created automatically
2. **Existing conversations** - Not preserved (no migration)
3. **Cost tracking** - Continues to work as before

### Backing Up Sessions

```bash
# Backup all sessions
tar -czf sessions_backup.tar.gz sessions/

# Restore sessions
tar -xzf sessions_backup.tar.gz
```

## FAQ

**Q: How long are sessions kept?**
A: Forever, unless you delete them manually.

**Q: Can I share sessions?**
A: Yes, copy the JSON file from `sessions/` directory.

**Q: What happens if I hit the message limit?**
A: Oldest messages are excluded from context, but still stored in session.

**Q: Can I increase the limits?**
A: Yes, edit `utils/session_manager.py` (see Customizing Limits section).

**Q: Are sessions encrypted?**
A: No, they're stored as plain JSON. Don't share sessions containing sensitive data.

## Future Enhancements

Potential improvements for future phases:
- Session tagging and categorization
- Automatic session summarization
- Session merging
- Cloud storage integration
- Encrypted sessions
- Session analytics dashboard
