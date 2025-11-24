# Resume Feature - Interactive Session Selection

## Overview

The resume feature allows you to interactively select and continue previous chat sessions, similar to Claude's `/resume` command. This makes it easy to pick up where you left off without needing to remember session IDs.

## Usage

### Interactive Resume Command

Simply type `resume` in the CLI:

```bash
You: resume
```

This will display a rich table showing your previous chat sessions with:
- Session number (for selection)
- Short session ID
- Model used
- Number of messages
- Total cost
- Last updated time
- Preview of conversation

### Selecting a Session

After the table is displayed, you can:

1. **Select a session**: Type the session number (e.g., `1`, `2`, `3`)
2. **Cancel**: Type `q` or press `Ctrl+C`

Example:

```
📝 Previous Chat Sessions
┌───┬────────────────────┬────────┬──────────┬─────────┬─────────────────┬──────────────┐
│ # │ Session ID         │ Model  │ Messages │ Cost    │ Last Updated    │ Preview      │
├───┼────────────────────┼────────┼──────────┼─────────┼─────────────────┼──────────────┤
│ 1 │ abc123def456...    │ haiku  │ 15       │ $0.0234 │ 2025-11-23 14:30│ user: How... │
│ 2 │ xyz789ghi012...    │ sonnet │ 8        │ $0.0145 │ 2025-11-22 10:15│ user: Wha... │
│ 3 │ mno345pqr678...    │ haiku  │ 22       │ $0.0567 │ 2025-11-21 16:45│ user: Can... │
└───┴────────────────────┴────────┴──────────┴─────────┴─────────────────┴──────────────┘

Select a session to resume:
Enter session number (1-3) or 'q' to cancel
Choice [q]: 1

✓ Selected session: abc123def456...
Session ID      abc123def456...
Model           haiku
Messages        15
Total Cost      $0.0234
...

You can now continue the conversation...
```

## Features

### Session Preview
Each session shows a preview of the first few messages, helping you identify the right conversation quickly.

### Smart Ordering
Sessions are displayed in reverse chronological order (most recent first), making it easy to find your latest conversations.

### Limit Display
By default, only the 15 most recent sessions are shown to keep the interface clean. All sessions are still available through the `sessions` command.

## Comparison with Other Session Commands

| Command | Purpose |
|---------|---------|
| `resume` | **Interactive selection** - Browse and select from a visual list |
| `sessions` | List all sessions in table format |
| `load <id>` | Load specific session by ID |
| `search <query>` | Search sessions by content |
| `session` | Show current session info |

## Tips

1. **Quick Resume**: Use `resume` when you're not sure which session to continue
2. **Direct Load**: Use `load <id>` when you know the exact session ID
3. **Search First**: Use `search` to find sessions by topic, then use `resume` to select
4. **Preview Helps**: The preview column shows the conversation start to help identify sessions

## Example Workflow

```bash
# Start the assistant
python cli_assistant.py

# Work on something...
You: How do I deploy to AWS Lambda?
Assistant: ...

# Later, start a new session
python cli_assistant.py

# Resume previous session interactively
You: resume
# Select the session from the list
Choice: 1

# Continue the conversation
You: Now how do I add environment variables?
Assistant: [Remembers previous Lambda context]
```

## Implementation Details

The resume feature is implemented in:
- [`utils/session_manager.py`](../utils/session_manager.py:309) - `interactive_resume()` method
- [`cli_assistant.py`](../cli_assistant.py:274) - `resume` command handler

Key methods:
- `get_session_preview(session_id, max_messages=3)` - Generate message preview
- `interactive_resume()` - Display table and handle selection
- Rich table display with color-coded information
- Graceful error handling for invalid selections
