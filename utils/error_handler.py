"""
Centralized error handling and recovery.
"""
import time
from typing import Callable, Any, Optional
from functools import wraps
from rich.console import Console

console = Console()


class RetryableError(Exception):
    """Errors that can be retried."""
    pass


class BudgetExceededError(Exception):
    """Budget limit exceeded."""
    pass


class ConfigurationError(Exception):
    """Configuration problems."""
    pass


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (RetryableError,)
):
    """
    Decorator to retry functions on failure.

    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts - 1:
                        console.print(
                            f"[yellow]Attempt {attempt + 1} failed. "
                            f"Retrying in {current_delay:.1f}s...[/yellow]"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        console.print(f"[red]All {max_attempts} attempts failed.[/red]")

            raise last_exception

        return wrapper
    return decorator


def graceful_degradation(fallback_value: Any = None):
    """
    Decorator for graceful degradation on errors.
    Returns fallback value instead of raising exception.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                console.print(
                    f"[yellow]Warning: {func.__name__} failed: {e}[/yellow]"
                )
                console.print(f"[dim]Returning fallback value[/dim]")
                return fallback_value

        return wrapper
    return decorator


class ErrorRecovery:
    """Handle and recover from errors."""

    @staticmethod
    def handle_api_error(error: Exception, logger: Optional[Any] = None) -> str:
        """Handle API-related errors."""
        error_msg = str(error)

        # AWS/Bedrock errors
        if 'ThrottlingException' in error_msg:
            suggestion = (
                "API rate limit reached. Try:\n"
                "1. Wait a few seconds\n"
                "2. Use a cheaper model (haiku)\n"
                "3. Reduce request frequency"
            )
        elif 'ModelTimeoutException' in error_msg:
            suggestion = (
                "Model timed out. Try:\n"
                "1. Simplify your request\n"
                "2. Increase timeout in config\n"
                "3. Retry the request"
            )
        elif 'AccessDeniedException' in error_msg:
            suggestion = (
                "Access denied. Check:\n"
                "1. AWS credentials are valid\n"
                "2. Model access is enabled in Bedrock\n"
                "3. IAM permissions are correct"
            )
        elif 'ValidationException' in error_msg:
            suggestion = (
                "Invalid request. Check:\n"
                "1. Input is within limits\n"
                "2. Parameters are valid\n"
                "3. Model ID is correct"
            )
        else:
            suggestion = (
                "Unexpected API error. Try:\n"
                "1. Check AWS console for service status\n"
                "2. Verify credentials\n"
                "3. Check logs for details"
            )

        if logger:
            logger.log_error(error, {'error_type': 'api_error'})

        return suggestion

    @staticmethod
    def handle_budget_error(daily_cost: float, limit: float) -> str:
        """Handle budget exceeded errors."""
        return f"""
Budget Exceeded!
Daily cost: ${daily_cost:.4f}
Daily limit: ${limit:.2f}

Options:
1. Wait until tomorrow (budget resets)
2. Increase DAILY_BUDGET_LIMIT in .env
3. Review costs: python utils/cost_dashboard.py
"""

    @staticmethod
    def handle_session_error(error: Exception) -> str:
        """Handle session-related errors."""
        return f"""
Session Error: {error}

Solutions:
1. Start new session: Use 'clear' command
2. Delete corrupted session files
3. Check sessions/ directory permissions
"""


def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[Exception]]:
    """
    Safely execute a function and return success status, result, and error.

    Returns:
        (success: bool, result: Any, error: Optional[Exception])
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        return False, None, e
