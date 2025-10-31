from datetime import date
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from utils.cost_tracker import CostTracker


def main():
    console = Console()
    tracker = CostTracker()

    # show budget status
    budget = tracker.check_budget()

    # title
    console.print("\n")
    console.print(Panel.fit(
        "[bold blue]AWS Strands - Cost Dashboard[/bold blue]",
        border_style="blue"
    ))
    console.print()

    # show main table
    table = Table(title="Cost Summary")
    table.add_column("Period", style="cyan", no_wrap=True)
    table.add_column("Cost", style="green", justify="right")
    table.add_column("Requests", style="yellow", justify="right")
    table.add_column("Budget", style="magenta", justify="rigth")
    table.add_column("Status", justify="center")

    today = str(date.today())
    month = today[:7]

    daily = tracker.data['daily'].get(today, {})
    monthly = tracker.data['monthly'].get(month, {})

    daily_status = "OK" if budget['daily_ok'] else "EXCEEDED"
    daily_status_style = "green" if budget['daily_ok'] else "red"

    monthly_status = "OK" if budget['monthly_ok'] else "EXCEEDED"
    monthly_status_style = "green" if budget["monthly_ok"] else "red"

    table.add_row(
        "Today",
        f"${daily.get('cost', 0):.4f}",
        str(daily.get('requests', 0)),
        f"${budget['daily_limit']:.2f}",
        f"[{daily_status_style}]{daily_status}[/{daily_status_style}]"
    )

    table.add_row(
        "This Month",
        f"${monthly.get('cost', 0):.4f}",
        str(monthly.get('requests', 0)),
        f"${budget['monthly_limit']:.2f}",
        f"[{monthly_status_style}]{monthly_status}[/{monthly_status_style}]"
    )

    console.print(table)
    console.print()

    # token usage details
    token_table = Table(title="Token Usage")
    token_table.add_column("Period", style="cyan")
    token_table.add_column("Input Tokens", style="blue", justify="right")
    token_table.add_column("Output Tokens", style="green", justify="right")
    token_table.add_column("Total Tokens", style="yellow", justify="right")

    daily_input = daily.get('input_tokens', 0)
    daily_output = daily.get('output_tokens', 0)
    monthly_input = monthly.get('input_tokens', 0)
    monthly_output = monthly.get('output_tokens', 0)

    token_table.add_row(
        "Today",
        f"{daily_input:,}",
        f"{daily_output:,}",
        f"{daily_input + daily_output:,}"
    )

    token_table.add_row(
        "This Month",
        f"{monthly_input:,}",
        f"{monthly_output:,}",
        f"{monthly_input + monthly_output:,}"
    )

    console.print(token_table)
    console.print()

    # tool usage
    tool_summary = tracker.get_tool_summary()
    console.print(Panel(tool_summary, title="Tool Usage Today", border_style="green"))
    console.print()

    # budget alerts
    if not budget['daily_ok']:
        console.print(Panel(
            f"[bold red]⚠️  Daily Budget Exceeded![/bold red]\n\n"
            f"Used: ${budget['daily_used']:.4f}\n"
            f"Limit: ${budget['daily_limit']:.2f}\n\n"
            f"[yellow]Increase DAILY_BUDGET_LIMIT in .env to continue[/yellow]",
            border_style="red"
        ))
    elif budget['daily_used'] > budget['daily_limit'] * 0.8:
        console.print(Panel(
            f"[bold yellow]⚠️  Approaching Daily Limit[/bold yellow]\n\n"
            f"Used: ${budget['daily_used']:.4f}\n"
            f"Limit: ${budget['daily_limit']:.2f}\n"
            f"Remaining: ${budget['daily_limit'] - budget['daily_used']:.4f}",
            border_style="yellow"
        ))

    if not budget['monthly_ok']:
        console.print(Panel(
            f"[bold red]⚠️  Monthly Budget Exceeded![/bold red]\n\n"
            f"Used: ${budget['monthly_used']:.4f}\n"
            f"Limit: ${budget['monthly_limit']:.2f}",
            border_style="red"
        ))

    # recommendations
    console.print(Panel(
        "[bold]Cost Optimization Tips:[/bold]\n\n"
        "• Use 'estimate_cost' tool before expensive operations\n"
        "• Switch to Haiku model for testing\n"
        "• Limit web_search tool usage\n"
        "• Keep responses concise\n"
        "• Review tool usage regularly",
        title="💡 Recommendations",
        border_style="blue"
    ))
    console.print()


if __name__ == "__main__":
    main()
