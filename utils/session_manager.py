"""
Session management for conversation history.
Cost-optimized context management.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import hashlib
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt


@dataclass
class Message:
    """Represents a single message in conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    tokens: Optional[int] = None
    cost: Optional[float] = None
    tools_used: Optional[List[str]] = None


@dataclass
class Session:
    """Represents a conversation session."""
    session_id: str
    created_at: str
    updated_at: str
    model: str
    total_cost: float
    total_tokens: int
    message_count: int
    messages: List[Message]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['messages'] = [asdict(msg) for msg in self.messages]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Create Session from dictionary."""
        messages = [Message(**msg) for msg in data.get('messages', [])]
        data['messages'] = messages
        return cls(**data)


class SessionManager:
    """Manage conversation sessions with cost tracking."""

    def __init__(self, storage_dir: str = 'sessions'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.current_session: Optional[Session] = None

        # Context management settings
        self.max_context_tokens = 4000  # Conservative limit
        self.max_messages_in_context = 20  # Limit message count

    def create_session(self, model: str) -> Session:
        """Create a new session."""
        session_id = self._generate_session_id()
        now = datetime.now().isoformat()

        session = Session(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            model=model,
            total_cost=0.0,
            total_tokens=0,
            message_count=0,
            messages=[]
        )

        self.current_session = session
        self._save_session(session)

        return session

    def load_session(self, session_id: str) -> Optional[Session]:
        """Load an existing session."""
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        with open(session_file, 'r') as f:
            data = json.load(f)

        session = Session.from_dict(data)
        self.current_session = session

        return session

    def add_message(
        self,
        role: str,
        content: str,
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
        tools_used: Optional[List[str]] = None
    ):
        """Add a message to current session."""
        if not self.current_session:
            raise ValueError("No active session")

        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            tokens=tokens,
            cost=cost,
            tools_used=tools_used
        )

        self.current_session.messages.append(message)
        self.current_session.message_count += 1
        self.current_session.updated_at = message.timestamp

        if tokens:
            self.current_session.total_tokens += tokens
        if cost:
            self.current_session.total_cost += cost

        self._save_session(self.current_session)

    def get_context_for_model(self) -> List[Dict[str, str]]:
        """
        Get optimized context for model.

        Implements cost-saving context management:
        1. Limit total tokens
        2. Limit message count
        3. Keep recent messages
        4. Summarize if needed
        """
        if not self.current_session or not self.current_session.messages:
            return []

        messages = self.current_session.messages

        # Strategy: Keep most recent messages within limits
        context = []
        total_tokens = 0

        # Iterate from most recent
        for message in reversed(messages):
            msg_tokens = message.tokens or len(message.content.split()) * 1.3

            # Check limits
            if len(context) >= self.max_messages_in_context:
                break
            if total_tokens + msg_tokens > self.max_context_tokens:
                break

            context.insert(0, {
                'role': message.role,
                'content': message.content
            })
            total_tokens += msg_tokens

        return context

    def list_sessions(self) -> List[Dict]:
        """List all available sessions."""
        sessions = []

        for session_file in self.storage_dir.glob('*.json'):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)

                sessions.append({
                    'session_id': data['session_id'],
                    'created_at': data['created_at'],
                    'updated_at': data['updated_at'],
                    'model': data['model'],
                    'message_count': data['message_count'],
                    'total_cost': data['total_cost']
                })
            except Exception:
                continue

        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        session_file.unlink()

        if self.current_session and self.current_session.session_id == session_id:
            self.current_session = None

        return True

    def export_session(self, session_id: str, format: str = 'markdown') -> str:
        """Export session in specified format."""
        session = self.load_session(session_id)

        if not session:
            return "Session not found"

        if format == 'markdown':
            return self._export_markdown(session)
        elif format == 'json':
            return json.dumps(session.to_dict(), indent=2)
        else:
            return "Unsupported format"

    def _export_markdown(self, session: Session) -> str:
        """Export session as markdown."""
        lines = [
            f"# Conversation Session",
            f"",
            f"**Session ID:** {session.session_id}",
            f"**Model:** {session.model}",
            f"**Created:** {session.created_at}",
            f"**Messages:** {session.message_count}",
            f"**Total Cost:** ${session.total_cost:.4f}",
            f"",
            f"---",
            f""
        ]

        for msg in session.messages:
            role_emoji = "👤" if msg.role == "user" else "🤖"
            lines.append(f"## {role_emoji} {msg.role.title()}")
            lines.append(f"*{msg.timestamp}*")
            lines.append("")
            lines.append(msg.content)

            if msg.tools_used:
                lines.append(f"\n*Tools used: {', '.join(msg.tools_used)}*")

            if msg.cost:
                lines.append(f"*Cost: ${msg.cost:.6f}*")

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def search_sessions(self, query: str) -> List[Dict]:
        """Search sessions by content."""
        results = []
        query_lower = query.lower()

        for session_file in self.storage_dir.glob('*.json'):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)

                # Search in messages
                matches = []
                for msg in data.get('messages', []):
                    if query_lower in msg.get('content', '').lower():
                        matches.append(msg['content'][:100] + '...')

                if matches:
                    results.append({
                        'session_id': data['session_id'],
                        'created_at': data['created_at'],
                        'matches': matches[:3]  # Show first 3 matches
                    })
            except Exception:
                continue

        return results

    def get_session_preview(self, session_id: str, max_messages: int = 3) -> str:
        """Get a preview of session messages."""
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            return "Session not found"

        with open(session_file, 'r') as f:
            data = json.load(f)

        messages = data.get('messages', [])
        preview_messages = messages[:max_messages]

        preview = []
        for msg in preview_messages:
            role = msg['role']
            content = msg['content'][:80] + ('...' if len(msg['content']) > 80 else '')
            preview.append(f"  {role}: {content}")

        if len(messages) > max_messages:
            preview.append(f"  ... and {len(messages) - max_messages} more messages")

        return '\n'.join(preview)

    def interactive_resume(self) -> Optional[str]:
        """
        Display interactive session selection similar to Claude's /resume command.
        Returns selected session_id or None if cancelled.
        """
        console = Console()
        sessions = self.list_sessions()

        if not sessions:
            console.print("[yellow]No saved sessions found[/yellow]")
            return None

        # Display sessions table
        table = Table(title="📝 Previous Chat Sessions", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Session ID", style="cyan", width=20)
        table.add_column("Model", style="green", width=12)
        table.add_column("Messages", justify="right", style="yellow")
        table.add_column("Cost", justify="right", style="magenta")
        table.add_column("Last Updated", style="blue")
        table.add_column("Preview", style="dim", width=50)

        # Show last 15 sessions
        display_sessions = sessions[:15]

        for idx, session in enumerate(display_sessions, 1):
            session_id = session['session_id']
            short_id = session_id[:16] + '...'

            # Get preview of first messages
            preview = self.get_session_preview(session_id, max_messages=2)
            preview_single_line = preview.replace('\n', ' | ')[:50]

            # Format datetime
            try:
                dt = datetime.fromisoformat(session['updated_at'])
                time_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                time_str = session['updated_at'][:16]

            table.add_row(
                str(idx),
                short_id,
                session['model'],
                str(session['message_count']),
                f"${session['total_cost']:.4f}",
                time_str,
                preview_single_line
            )

        console.print("\n")
        console.print(table)
        console.print("\n")

        if len(sessions) > 15:
            console.print(f"[dim]Showing 15 of {len(sessions)} sessions[/dim]\n")

        # Prompt for selection
        console.print("[cyan]Select a session to resume:[/cyan]")
        console.print("[dim]Enter session number (1-{}) or 'q' to cancel[/dim]".format(len(display_sessions)))

        try:
            choice = Prompt.ask("Choice", default="q")

            if choice.lower() == 'q':
                console.print("[yellow]Cancelled[/yellow]")
                return None

            # Try to parse as number
            try:
                session_idx = int(choice) - 1
                if 0 <= session_idx < len(display_sessions):
                    selected_session = display_sessions[session_idx]
                    console.print(f"\n[green]✓ Selected session: {selected_session['session_id'][:16]}...[/green]")
                    return selected_session['session_id']
                else:
                    console.print("[red]Invalid selection[/red]")
                    return None
            except ValueError:
                console.print("[red]Invalid input[/red]")
                return None

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return None

    def get_session_summary(self) -> str:
        """Get summary of current session."""
        if not self.current_session:
            return "No active session"

        from tabulate import tabulate

        data = [
            ["Session ID", self.current_session.session_id],
            ["Model", self.current_session.model],
            ["Messages", self.current_session.message_count],
            ["Total Cost", f"${self.current_session.total_cost:.4f}"],
            ["Total Tokens", f"{self.current_session.total_tokens:,}"],
            ["Created", self.current_session.created_at],
            ["Updated", self.current_session.updated_at]
        ]

        return tabulate(data, tablefmt="grid")

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{timestamp}{os.urandom(8).hex()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]

    def _save_session(self, session: Session):
        """Save session to disk."""
        session_file = self.storage_dir / f"{session.session_id}.json"

        with open(session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
