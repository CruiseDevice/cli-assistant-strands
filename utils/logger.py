"""
Structured logging system for production monitoring.
Tracks costs, performance, and errors.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler


class CostAwareLogger:
    """Logger with cost and performance tracking."""

    def __init__(
        self,
        name: str = "cli_assistant",
        log_dir: str = "logs",
        level: str = "INFO",
        max_bytes: int = 10_000_000,  # 10MB
        backup_count: int = 5
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Console handler (warnings and errors only)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # File handler (all logs)
        file_handler = RotatingFileHandler(
            self.log_dir / 'cli_assistant.log',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # JSON handler for structured logs
        json_handler = RotatingFileHandler(
            self.log_dir / 'cli_assistant_structured.json',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(self.JsonFormatter())

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(json_handler)

    class JsonFormatter(logging.Formatter):
        """Format logs as JSON."""

        def format(self, record):
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }

            # Add extra fields if present
            if hasattr(record, 'cost'):
                log_data['cost'] = record.cost
            if hasattr(record, 'tokens'):
                log_data['tokens'] = record.tokens
            if hasattr(record, 'model'):
                log_data['model'] = record.model
            if hasattr(record, 'duration'):
                log_data['duration'] = record.duration
            if hasattr(record, 'session_id'):
                log_data['session_id'] = record.session_id

            return json.dumps(log_data)

    def log_interaction(
        self,
        user_input: str,
        response: str,
        model: str,
        cost: float,
        tokens: int,
        duration: float,
        session_id: Optional[str] = None,
        tools_used: Optional[list] = None
    ):
        """Log a complete user interaction."""
        extra = {
            'cost': cost,
            'tokens': tokens,
            'model': model,
            'duration': duration,
            'session_id': session_id
        }

        self.logger.info(
            f"Interaction: {len(user_input)} chars in, "
            f"{len(response)} chars out, "
            f"${cost:.6f}, {duration:.2f}s",
            extra=extra
        )

        if tools_used:
            self.logger.info(f"Tools used: {', '.join(tools_used)}", extra=extra)

    def log_cost_alert(self, alert_type: str, current: float, limit: float):
        """Log cost threshold alerts."""
        self.logger.warning(
            f"Cost alert: {alert_type} - ${current:.4f} / ${limit:.2f}",
            extra={'cost': current, 'alert_type': alert_type}
        )

    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """Log errors with context."""
        self.logger.error(
            f"Error: {type(error).__name__}: {str(error)}",
            extra=context or {},
            exc_info=True
        )

    def log_performance(self, operation: str, duration: float, success: bool = True):
        """Log performance metrics."""
        status = "success" if success else "failure"
        self.logger.info(
            f"Performance: {operation} - {duration:.2f}s - {status}",
            extra={'duration': duration, 'operation': operation, 'success': success}
        )

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get statistics from structured logs."""
        stats = {
            'total_interactions': 0,
            'total_cost': 0.0,
            'total_tokens': 0,
            'avg_duration': 0.0,
            'errors': 0,
            'tools_usage': {}
        }

        json_log_file = self.log_dir / 'cli_assistant_structured.json'

        if not json_log_file.exists():
            return stats

        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        durations = []

        with open(json_log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)

                    # Check timestamp
                    log_time = datetime.fromisoformat(
                        log_entry['timestamp'].replace('Z', '+00:00')
                    ).timestamp()

                    if log_time < cutoff_time:
                        continue

                    # Count interactions
                    if 'Interaction:' in log_entry.get('message', ''):
                        stats['total_interactions'] += 1
                        if 'cost' in log_entry:
                            stats['total_cost'] += log_entry['cost']
                        if 'tokens' in log_entry:
                            stats['total_tokens'] += log_entry['tokens']
                        if 'duration' in log_entry:
                            durations.append(log_entry['duration'])

                    # Count errors
                    if log_entry.get('level') == 'ERROR':
                        stats['errors'] += 1

                    # Track tools
                    if 'Tools used:' in log_entry.get('message', ''):
                        tools = log_entry['message'].split('Tools used: ')[1].split(', ')
                        for tool in tools:
                            stats['tools_usage'][tool] = stats['tools_usage'].get(tool, 0) + 1

                except (json.JSONDecodeError, KeyError):
                    continue

        if durations:
            stats['avg_duration'] = sum(durations) / len(durations)

        return stats
