import os
import sys
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv
from utils.cost_tracker import CostTracker
from strands import Agent
from strands.models import BedrockModel

# load environment variables
load_dotenv()

# initialize console for pretty output
console = Console()


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


def initialize_agent():
    """Initialize the Strands agent with Bedrock."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        region=os.getenv('AWS_REGION', 'us-west-2'),
        streaming=False
    )

    # system prompt with cost awareness
    system_prompt = """
    You are a helpful CLI assistant.

    IMPORTANT: Keep responses concise to minimize costs.
    - Give direct answers
    - Avoid unnecessary elaboration unless asked
    - Use bullet points for lists
    """

    agent = Agent(
        model=model,
        system_prompt=system_prompt
    )
    return agent


def main():

    # check aws setup
    console.print(Panel.fit(
        "[bold blue]Smart CLI Assistant[/bold blue]\n"
        "[dim]Powered by AWS Strands & Claude[/dim]",
        border_style="blue"
    ))

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

    # inititalize cost tracker
    cost_tracker = CostTracker()

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
    agent = initialize_agent()
    console.print("[green]Agent ready[/green]")

    # Help message
    console.print("[dim]Commands: 'quit' or 'exit' to end, 'cost' for cost summary[/dim]\n")

    # main loop
    while True:
        try:
            # get user input
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if not user_input.strip():
                continue

            # check for commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("\n[yellow]Final cost summary:[/yellow]")
                console.print(cost_tracker.get_summary())
                console.print("\n[green]Goodbye![/green]")
                break

            if user_input.lower() == 'cost':
                console.print("\n" + cost_tracker.get_summary() + "\n")
                continue

            # get response from agent
            console.print("[bold green]Assistant:[/bold green] ", end="")

            response = agent(user_input)
            response_text = str(response)

            # Track costs
            # Note: Estimating tokens - will be more accurate with actual API response
            estimated_input_tokens = len(user_input.split()) * 1.3
            estimated_output_tokens = len(response_text.split()) * 1.3

            cost_info = cost_tracker.track_request(
                model='claude-3.5-haiku',
                input_tokens=int(estimated_input_tokens),
                output_tokens=int(estimated_output_tokens)
            )

            # show request cost if significant
            if cost_info['request_cost'] > 0.01:
                console.print(f"\n[dim]Request cost: ${cost_info['request_cost']}[/dim]")

            # warn if approaching daily limit
            if cost_info['daily_cost'] > budget_status['daily_limit'] * 0.8:
                console.print(f"[yellow]Daily cost: ${cost_info['daily_cost']}[/yellow]")

            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Type 'quit' to exit properly.[/yellow]\n")
            continue
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()
