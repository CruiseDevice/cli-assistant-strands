import json
from pathlib import Path
from datetime import datetime, date
import os
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()


class CostTracker:
    """Track token usage and estimated costs."""

    # Pricing per 1M tokens (updated October 2025)
    PRICING = {
        'claude-4-sonnet': {
            'input': 3.00,
            'output': 15.00
        },
        'claude-3.5-haiku': {
            'input': 0.80,
            'output': 4.00
        }
    }

    def __init__(self, storage_file: str = "cost_tracking.json"):
        self.storage_file = Path(storage_file)
        self.data = self._load_data()

    def _load_data(self):
        """Load existing tracking data."""
        if self.storage_file.exists():
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return {'sessions': {}, 'daily': {}, 'monthly': {}, 'tool_usage': {}}

    def check_budget(self):
        """Check if we're within budget limits"""
        daily_limit = float(os.getenv('DAILY_BUDGET_LIMIT', 1.00))
        monthly_limit = float(os.getenv('MONTHLY_BUDGET_LIMIT', 10.00))

        today = str(date.today())
        month = today[:7]

        daily_cost = self.data['daily'].get(today, {}).get('cost', 0)
        monthly_cost = self.data['monthly'].get(month, {}).get('cost', 0)

        return {
            'daily_ok': daily_cost < daily_limit,
            'monthly_ok': monthly_cost < monthly_limit,
            'daily_used': daily_cost,
            'daily_limit': daily_limit,
            'monthly_used': monthly_cost,
            'monthly_limit': monthly_limit
        }

    def get_tool_summary(self):
        """Get tool usage summary."""
        today = str(date.today())
        tool_data = self.data.get('tool_usage', {}).get(today, {})

        if not tool_data:
            return "No tools used today."

        table = [[tool, count] for tool, count in tool_data.items()]
        return tabulate(table, headers=['Tool', 'Uses'], tablefmt='grid')

    def get_summary(self):
        """Get a formatted summary of costs."""
        today = str(date.today())
        month = today[:7]

        daily = self.data['daily'].get(today, {})
        monthly = self.data['monthly'].get(month, {})

        table = [
            ['Today', f"${daily.get('cost', 0):.4f}",
             f"{daily.get('input_tokens', 0):,}",
             f"{daily.get('output_tokens', 0):,}",
             daily.get('requests', 0)],
            ['This Month', f"${monthly.get('cost', 0):.4f}",
             f"{monthly.get('input_tokens', 0):,}",
             f"{monthly.get('output_tokens', 0):,}",
             monthly.get('requests', 0)]
        ]

        return tabulate(
            table,
            headers=['Period', 'Cost', 'Input Tokens', 'Output Tokens', 'Requests'],
            tablefmt='grid'
        )

    def _save_data(self):
        """Save tracking data."""
        with open(self.storage_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def track_request(self, model, input_tokens, output_tokens, session_id=None):
        """Track a single API request and return cost info."""

        # calculate cost
        pricing = self.PRICING.get(model, self.PRICING['claude-4-sonnet'])
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost

        # update tracking
        today = str(date.today())
        month = today[:7]   # YYYY-MM

        # daily tracking
        if today not in self.data['daily']:
            self.data['daily'][today] = {
                'cost': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'requests': 0
            }

        self.data['daily'][today]['cost'] += total_cost
        self.data['daily'][today]['input_tokens'] += input_tokens
        self.data['daily'][today]['output_tokens'] += output_tokens
        self.data['daily'][today]['requests'] += 1

        # monthly tracking
        if month not in self.data['monthly']:
            self.data['monthly'][month] = {
                'cost': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'requests': 0
            }

        self.data['monthly'][month]['cost'] += total_cost
        self.data['monthly'][month]['input_tokens'] += input_tokens
        self.data['monthly'][month]['output_tokens'] += output_tokens
        self.data['monthly'][month]['requests'] += 1

        # session tracking
        if session_id:
            if session_id not in self.data['sessions']:
                self.data['sessions'][session_id] = {
                    'cost': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'requests': 0,
                    'started': datetime.now().isoformat()
                }

            self.data['sessions'][session_id]['cost'] += total_cost
            self.data['sessions'][session_id]['input_tokens'] += input_tokens
            self.data['sessions'][session_id]['output_tokens'] += output_tokens
            self.data['sessions'][session_id]['requests'] += 1

        self._save_data()

        return {
            'request_cost': total_cost,
            'daily_cost': self.data['daily'][today]['cost'],
            'monthly_cost': self.data['monthly'][month]['cost']
        }

    def track_tool_usage(self, tool_name, session_id=None):
        """Track tool invocations."""
        today = str(date.today())

        if 'tool_usage' not in self.data:
            self.data['tool_usage'] = {}

        if today not in self.data['tool_usage']:
            self.data['tool_usage'][today] = {}

        if tool_name not in self.data['tool_usage'][today]:
            self.data['tool_usage'][today][tool_name] = 0

        self.data['tool_usage'][today][tool_name] += 1
        self.save_data()
