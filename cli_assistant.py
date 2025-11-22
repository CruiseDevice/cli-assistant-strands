import sys
from re import S
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from tabulate import tabulate
from dotenv import load_dotenv

from utils.cost_tracker import CostTracker
from utils.session_manager import SessionManager
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator, python_repl, file_read
from tools.custom_tools import get_system_info, save_note, list_notes,\
    search_web, estimate_cost
from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent

from models.model_config import MODELS, compare_model_costs


# load environment variables
load_dotenv()

# initialize console for pretty output
console = Console()

# global cost tracker
cost_tracker = CostTracker()


class ToolTrackingHook(HookProvider):
    """Hook to track tool usage automatically."""
    def __init__(self, tracker):
        self.tracker = tracker

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register hook for tool calls."""
        registry.add_callback(BeforeToolCallEvent, self.track_tool_call)

    def track_tool_call(self, event: BeforeToolCallEvent) -> None:
        """Track each tool call."""
        tool_use = event.tool_use
        tool_name = tool_use.get('name', 'unknown')
        self.tracker.track_tool_usage(tool_name)
        console.print(f"[dim]Using tool: {tool_name}[/dim]")


def check_aws_credentials():
    """Verify AWS credentials are configured"""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        console.print(f"[green]AWS Credentials valud[/green]")
        console.print(f"    Account: {identity['Account']}")
        console.print(f"    User: {identity['Arn'].split('/')[-1]}")
        return True
    except Exception as e:
        console.print(f"[red]✗ AWS credentials error: {e}[/red]")
        console.print("\n[yellow]Fix:[/yellow]")
        console.print("  1. Run: aws configure")
        console.print("  2. Enter your AWS access key and secret")
        console.print("  3. Set region to: us-west-2")
        return False


class SmartCLIAssistant:
    """
    Enhanced CLI Assistant with multi-model support and session management
    """
    def __init__(self, model_name: str = "haiku", session_id: Optional[str] = None):
        self.model_name = model_name
        self.model_config = MODELS[model_name]
        self.cost_tracker = cost_tracker
        self.session_manager = SessionManager()
        self.agent = None
        self.streaming_enabled = False  # Disabled for now, can be enabled later

        # Load or create session
        if session_id:
            session = self.session_manager.load_session(session_id)
            if session:
                console.print(f"[green]✓ Loaded session: {session_id[:16]}...[/green]")
                console.print(f"  Messages: {session.message_count}")
                console.print(f"  Cost so far: ${session.total_cost:.4f}\n")
            else:
                console.print(f"[yellow]Session not found. Creating new session.[/yellow]\n")
                self.session_manager.create_session(model_name)
        else:
            self.session_manager.create_session(model_name)
            console.print(f"[green]✓ New session created[/green]\n")

    def initialize_agent(self):
        """Initialize agent with current model."""
        model = BedrockModel(
            model_id=self.model_config.model_id,
            streaming=False
        )

        system_prompt = f"""You are a helpful CLI assistant using {self.model_config.name}.

Available tools:
- calculator: Mathematical operations
- python_repl: Execute Python code
- file_read: Read local files
- get_system_info: System metrics (CPU, memory, disk)
- save_note: Save notes locally
- list_notes: List all saved notes
- search_web: Search the web (use sparingly)
- estimate_cost: Estimate costs before operations

COST OPTIMIZATION (Current model: {self.model_config.tier.value}):
- Keep responses concise and focused
- Use tools efficiently
- Avoid unnecessary elaboration
- Be helpful but brief

Current model cost: ${self.model_config.cost_per_1m_input:.2f} input / ${self.model_config.cost_per_1m_output:.2f} output per 1M tokens
"""

        self.agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=[
                calculator, python_repl, file_read,
                get_system_info, save_note, list_notes,
                search_web, estimate_cost
            ],
            hooks=[ToolTrackingHook(self.cost_tracker)]
        )

        console.print(f"[green]✓ Agent initialized with {self.model_config.name}[/green]")
        console.print(f"[dim]  Tier: {self.model_config.tier.value} | "
                     f"Cost: ${self.model_config.cost_per_1m_input:.2f} input / "
                     f"${self.model_config.cost_per_1m_output:.2f} output per 1M tokens[/dim]\n")

    def process_message(self, user_input: str):
        """Process a user message and return response."""
        # Add user message to session
        self.session_manager.add_message('user', user_input)

        console.print("[bold green]Assistant:[/bold green] ", end="")

        try:
            response = self.agent(user_input)
            response_text = str(response)

            # Track costs
            estimated_input_tokens = int(len(user_input.split()) * 1.3)
            estimated_output_tokens = int(len(response_text.split()) * 1.3)

            cost_info = self.cost_tracker.track_request(
                model=self.model_name,
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens
            )

            # Add assistant message to session
            self.session_manager.add_message(
                'assistant',
                response_text,
                tokens=estimated_output_tokens,
                cost=cost_info.get('request_cost')
            )

            # Show cost if significant
            if cost_info['request_cost'] > 0.01:
                console.print(f"\n[dim]💰 Cost: ${cost_info['request_cost']:.4f}[/dim]")

            # Warn if approaching limits
            budget = self.cost_tracker.check_budget()
            if not budget['daily_ok'] or cost_info['daily_cost'] > budget['daily_limit'] * 0.8:
                console.print(
                    f"[yellow]⚠ Daily: ${cost_info['daily_cost']:.4f} / "
                    f"${budget['daily_limit']:.2f}[/yellow]"
                )

            console.print()

        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]\n")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def switch_model(self, model_name: str):
        """Switch to a different model."""
        if model_name not in MODELS:
            console.print(f"[red]Invalid model: {model_name}[/red]")
            console.print(f"[dim]Available models: {list(MODELS.keys())}[/dim]")
            return False

        old_model = self.model_config.name
        self.model_name = model_name
        self.model_config = MODELS[model_name]
        self.initialize_agent()

        console.print(f"[green]✓ Switched to {self.model_config.name}[/green]")
        return True

    def handle_command(self, user_input: str) -> bool:
        """
        Handle special commands.
        Returns True if input was a command, False otherwise
        """
        cmd = user_input.lower().strip()

        # exit commands
        if cmd in ['quit', 'exit', 'q']:
            console.print("\n[yellow]Final cost summary:[/yellow]")
            console.print(self.cost_tracker.get_summary())
            console.print("\n[yellow]Tool usage:[/yellow]")
            console.print(self.cost_tracker.get_tool_summary())
            console.print("\n[green]Goodbye![/green]")
            sys.exit(0)

        # cost command
        if cmd == 'cost':
            console.print("\n" + self.cost_tracker.get_summary())
            console.print("\n" + self.cost_tracker.get_tool_summary())
            return True

        if cmd == 'tools':
            console.print("\n" + cost_tracker.get_tool_summary() + "\n")
            return True

        # TODO: Budget command
        if cmd == 'budeget':
            budget = self.cost_tracker.check_budget()
            table_data = [
                ["Daily", f"${budget['daily_used']:.4f}",
                 f"${budget['daily_limit']:.2f}",
                 "✓" if budget['daily_ok'] else "✗"],
                ["Monthly", f"${budget['monthly_used']:.4f}",
                 f"${budget['monthly_limit']:.2f}",
                 "✓" if budget['monthly_ok'] else "✗"]
            ]
            console.print("\n" + tabulate(
                table_data,
                headers=["Period", "Used", "Limit", "Status"],
                tablefmt="grid"
            ))
            console.print()
            return True

        # TODO: Model Switching
        if cmd.startswith('model '):
            model_name = cmd.split(' ', 1)[1].strip()
            self.switch_model(model_name)
            return True

        # TODO: Model Comparison
        if cmd == 'models':
            console.print("\n[bold]Available Models:[/bold]")
            for key, model in MODELS.items():
                current = "← CURRENT" if key == self.model_name else ""
                console.print(f"\n[cyan]{key}[/cyan] - {model.name} {current}")
                console.print(f"  {model.description}")
                console.print(f"  Cost: ${model.cost_per_1m_input:.2f} in / "
                            f"${model.cost_per_1m_output:.2f} out per 1M tokens")

            # Show cost comparison
            console.print("\n[bold]Cost Comparison (100 input / 200 output tokens):[/bold]")
            console.print(compare_model_costs(100, 200))
            console.print()
            return True

        # help command
        if cmd == 'help':
            self.show_help()
            return True

        # Session commands
        if cmd == 'sessions':
            sessions = self.session_manager.list_sessions()
            if not sessions:
                console.print("[yellow]No saved sessions[/yellow]")
                return True

            table_data = [
                [s['session_id'][:16] + '...', s['model'],
                 s['message_count'], f"${s['total_cost']:.4f}",
                 s['updated_at']]
                for s in sessions[:10]  # Show last 10
            ]

            console.print("\n" + tabulate(
                table_data,
                headers=["Session ID", "Model", "Messages", "Cost", "Last Updated"],
                tablefmt="grid"
            ))
            console.print()
            return True

        if cmd.startswith('load '):
            session_id = cmd.split(' ', 1)[1].strip()
            session = self.session_manager.load_session(session_id)
            if session:
                console.print(f"[green]✓ Loaded session[/green]")
                console.print(self.session_manager.get_session_summary())
            else:
                console.print(f"[red]Session not found: {session_id}[/red]")
            return True

        if cmd == 'session':
            console.print(self.session_manager.get_session_summary())
            return True

        if cmd.startswith('export '):
            parts = cmd.split()
            session_id = parts[1] if len(parts) > 1 else self.session_manager.current_session.session_id
            format_type = parts[2] if len(parts) > 2 else 'markdown'

            exported = self.session_manager.export_session(session_id, format_type)

            # Save to file
            filename = f"export_{session_id[:8]}.{format_type if format_type == 'json' else 'md'}"
            with open(filename, 'w') as f:
                f.write(exported)

            console.print(f"[green]✓ Exported to {filename}[/green]")
            return True

        if cmd.startswith('search '):
            query = cmd.split(' ', 1)[1].strip()
            results = self.session_manager.search_sessions(query)

            if not results:
                console.print("[yellow]No matches found[/yellow]")
                return True

            console.print(f"\n[bold]Found {len(results)} session(s):[/bold]\n")
            for result in results:
                console.print(f"[cyan]{result['session_id'][:16]}...[/cyan]")
                for match in result['matches']:
                    console.print(f"  → {match}")
                console.print()
            return True

        if cmd == 'clear':
            self.session_manager.create_session(self.model_name)
            console.print("[green]✓ New session started[/green]")
            return True

        return False

    def show_help(self):
        """Display help information."""
        help_text = """
**Commands:**
- `quit` or `exit` - Exit the assistant
- `cost` - Show cost summary
- `model <name>` - Switch model (haiku/sonnet/opus)
- `models` - Compare all models
- `budget` - Show budget status
- `tools` - List tool usage
- `help` - Show this help

**Session Commands:**
- `sessions` - List all saved sessions
- `session` - Show current session info
- `load <id>` - Load a previous session
- `export <id> [format]` - Export session (markdown/json)
- `search <query>` - Search sessions by content
- `clear` - Start a new session

**Model Tiers:**
- **haiku** - Cheap, fast (testing & simple tasks)
- **sonnet** - Balanced (most work)
- **opus** - Premium (complex reasoning)

**Tips:**
- Start with 'haiku' for testing
- Use 'sonnet' for regular work
- Reserve 'opus' for complex analysis
- Check costs regularly with `cost`
"""
        console.print(Panel(Markdown(help_text), title="Help", border_style="blue"))



    def run(self):
        """Main CLI Loop."""

        # welcome banner
        console.print(Panel.fit(
            "[bold blue]Smart CLI Assistant[/bold blue]\n"
            "[dim]Powered by AWS Strands & Claude[/dim]",
            border_style="blue"
        ))

        # check AWS credentials
        if not check_aws_credentials():
            sys.exit(1)


        # check bedrock model access
        console.print("\n[yellow]Checking Bedrock model access...[/yellow]")
        try:
            import boto3
            bedrock = boto3.client('bedrock', region_name='us-west-2')
            # this will fail if model access not granted
            console.print("[green]Bedrock access configured[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Bedrock access error: {e}[/red]")
            console.print("\n[yellow]Fix:[/yellow]")
            console.print("  1. Go to AWS Bedrock Console")
            console.print("  2. Navigate to 'Model access'")
            console.print("  3. Request access for Claude models")
            sys.exit(1)

        # check budget before starting
        budget_status = cost_tracker.check_budget()
        if not budget_status['daily_ok']:
            console.print(f"[red]⚠ Daily budget exceeded![/red]")
            console.print(f"  Used: ${budget_status['daily_used']:.4f}")
            console.print(f"  Limit: ${budget_status['daily_limit']:.2f}")
            console.print("\n[yellow]Increase DAILY_BUDGET_LIMIT in .env to continue[/yellow]")
            sys.exit(1)

        if not budget_status['monthly_ok']:
            console.print(f"[red]⚠ Monthly budget exceeded![/red]")
            console.print(f"  Used: ${budget_status['monthly_used']:.4f}")
            console.print(f"  Limit: ${budget_status['monthly_limit']:.2f}")
            sys.exit(1)

        # Show current costs
        console.print("[dim]" + cost_tracker.get_summary() + "[/dim]\n")

        console.print("[yellow]Initializing agent...[/yellow]")
        agent = self.initialize_agent()
        console.print("[green]Agent ready[/green]")

        # Help message
        console.print("[dim]Commands: 'quit' or 'exit' to end, 'cost' for cost summary, 'tools' for tool usage[/dim]\n")

        # main loop
        while True:
            try:
                # get user input
                user_input = console.input("[bold blue]You:[/bold blue] ")
                if not user_input.strip():
                    continue


                # handle commands
                if self.handle_command(user_input):
                    continue

                # process regular message
                self.process_message(user_input)

            except KeyboardInterrupt:
                console.print("\n\n[yellow]Interrupted. Type 'quit' to exit properly.[/yellow]\n")
                continue
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")


def initialize_agent(model_name: str = "haiku", session_id: Optional[str] = None):
    """
    Initialize and return an agent instance.

    This is a convenience function for testing and programmatic use.

    Args:
        model_name: Model to use ('haiku', 'sonnet', or 'opus')
        session_id: Optional session ID to load

    Returns:
        Agent instance ready to use
    """
    assistant = SmartCLIAssistant(model_name=model_name, session_id=session_id)
    assistant.initialize_agent()
    return assistant.agent


def main():

    # entry poiny with command-line parsing"
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart CLI Assistant with AWS Strands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
  python cli_assistant.py                    # Start with Haiku (cheapest)
  python cli_assistant.py --model sonnet     # Start with Sonnet (balanced)
  python cli_assistant.py --model opus       # Start with Opus (premium)

Model Tiers:
  haiku  - Cheap, fast (testing & simple tasks)
  sonnet - Balanced (most production work)
  opus   - Premium (complex reasoning)
        """
    )

    parser.add_argument(
        '--model',
        choices=['haiku', 'sonnet', 'opus'],
        default='haiku',
        help='Model to use (default; haiku)'
    )

    parser.add_argument(
        '--session',
        type=str,
        help='Load existing session ID'
    )

    args = parser.parse_args()

    # create and run assistant
    assistant = SmartCLIAssistant(model_name=args.model, session_id=args.session)
    assistant.run()


if __name__ == "__main__":
    main()
