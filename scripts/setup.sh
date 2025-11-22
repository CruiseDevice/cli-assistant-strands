#!/bin/bash
# Setup script for CLI Assistant

set -e

echo "🚀 Setting up Smart CLI Assistant..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ required. You have $python_version"
    exit 1
fi

echo "✓ Python version OK: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p sessions logs config notes

# Copy .env.example to .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your settings"
fi

# Initialize git hooks
echo "Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install

# Verify AWS credentials
echo "Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✓ AWS credentials configured"
else
    echo "⚠️  AWS credentials not found"
    echo "   Run: aws configure"
fi

# Check Bedrock access
echo "Checking AWS Bedrock access..."
if aws bedrock list-foundation-models --region us-west-2 > /dev/null 2>&1; then
    echo "✓ Bedrock access OK"
else
    echo "⚠️  Bedrock access issue"
    echo "   Check model access in AWS Console"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your settings"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python cli_assistant.py"
echo ""
