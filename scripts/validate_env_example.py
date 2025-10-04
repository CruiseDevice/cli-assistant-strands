def validate_env_example():
    """Validate .env.example file structure"""
    import re
    from pathlib import Path

    print("Validating .env.example")

    env_example = Path('.env.example')

    if not env_example.exists():
        print(".env.example not found!")
        return False

    required_vars = [
        'AWS_REGION',
        'AWS_PROFILE',
        'DEFAULT_MODEL',
        'DAILY_BUDGET_LIMIT',
        'MONTHLY_BUDGET_LIMIT',
        'LOG_LEVEL',
    ]

    found_vars = set()
    issues = []

    with open(env_example, 'r') as f:
        for line_num, line in enumerate(f, 1):
            # skip comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                continue

            # check for actual values
            if '=' in line:
                var_name, var_value = line.split('=', 1)
                var_name = var_name.strip()
                var_value = var_value.strip()

                found_vars.add(var_name)

                # check for suspicious real values
                suspicious_patterns = [
                    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
                    (r'sk-[a-zA-Z0-9]{48}', 'API Key'),
                    (r'\d{12}', 'AWS Account ID'),
                ]

                for pattern, desc in suspicious_patterns:
                    if re.search(pattern, var_value):
                        issues.append(f"Line {line_num}: Possible real {desc} in {var_name}")

    # check for required variables
    missing_vars = set(required_vars) - found_vars

    if missing_vars:
        issues.append(f"Missing required variables: {', '.join(missing_vards)}")

    if issues:
        print(f"\n Issues found in .env.example:\n")
        for issue in issues:
            print(f" - {issue}")
        return False

    print(f"✅ .env.example is valid!")
    print(f"   Found {len(found_vars)} environment variables")
    return True


if __name__ == '__main__':
    import sys
    sys.exit(0 if validate_env_example() else 1)
