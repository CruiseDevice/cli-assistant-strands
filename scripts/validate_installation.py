"""
Validate installation and configuration.
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return True, f"{version.major}.{version.minor}.{version.micro}"
    return False, f"{version.major}.{version.minor}.{version.micro}"


def check_dependencies():
    """Check required dependencies."""
    required = [
        'strands_agents',
        'boto3',
        'rich',
        'pyyaml',
        'tabulate'
    ]

    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    return len(missing) == 0, missing


def check_aws_credentials():
    """Check AWS credentials."""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return True, identity['Account']
    except Exception as e:
        return False, str(e)


def check_bedrock_access():
    """Check Bedrock access."""
    try:
        import boto3
        bedrock = boto3.client('bedrock', region_name='us-west-2')
        bedrock.list_foundation_models()
        return True, "Access granted"
    except Exception as e:
        return False, str(e)


def check_directories():
    """Check required directories exist."""
    required_dirs = ['sessions', 'logs', 'config', 'tools', 'utils', 'models']
    missing = [d for d in required_dirs if not Path(d).exists()]
    return len(missing) == 0, missing


def check_config_file():
    """Check configuration file."""
    config_file = Path('config/default_config.yaml')
    if not config_file.exists():
        return False, "Missing config file"

    try:
        from utils.config_manager import ConfigManager
        config = ConfigManager()
        return config.validate(), "Valid"
    except Exception as e:
        return False, str(e)


def main():
    """Run all validation checks."""
    console.print("\n[bold blue]🔍 Validating Installation[/bold blue]\n")

    checks = [
        ("Python Version (>= 3.9)", check_python_version),
        ("Dependencies", check_dependencies),
        ("AWS Credentials", check_aws_credentials),
        ("Bedrock Access", check_bedrock_access),
        ("Directories", check_directories),
        ("Configuration", check_config_file)
    ]

    table = Table(title="Validation Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    all_passed = True

    for check_name, check_func in checks:
        success, details = check_func()

        if success:
            table.add_row(check_name, "✓ PASS", str(details), style="green")
        else:
            table.add_row(check_name, "✗ FAIL", str(details), style="red")
            all_passed = False

    console.print(table)
    console.print()

    if all_passed:
        console.print("[bold green]✅ All checks passed! Ready to use.[/bold green]\n")
        console.print("Run: python cli_assistant.py\n")
        return 0
    else:
        console.print("[bold red]❌ Some checks failed. Please fix the issues above.[/bold red]\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
