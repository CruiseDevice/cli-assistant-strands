#!/bin/bash
# Pre-deployment checklist

set -e

echo "📋 Running deployment checklist..."

# Check all tests pass
echo "1. Running tests..."
./scripts/run_tests.sh > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ All tests pass"
else
    echo "   ✗ Tests failing"
    exit 1
fi

# Check configuration
echo "2. Validating configuration..."
python -c "from utils.config_manager import ConfigManager; c = ConfigManager(); assert c.validate()"
echo "   ✓ Configuration valid"

# Check no secrets in code
echo "3. Checking for secrets..."
if grep -r "sk-" . --exclude-dir=venv --exclude-dir=.git --exclude="*.pyc" > /dev/null 2>&1; then
    echo "   ✗ Possible secrets found!"
    exit 1
fi
echo "   ✓ No secrets detected"

# Check .gitignore
echo "4. Checking .gitignore..."
if [ -f ".gitignore" ]; then
    echo "   ✓ .gitignore exists"
else
    echo "   ✗ .gitignore missing"
    exit 1
fi

# Check documentation
echo "5. Checking documentation..."
if [ -f "README.md" ]; then
    echo "   ✓ README.md exists"
else
    echo "   ✗ README.md missing"
    exit 1
fi

# Check cost tracking
echo "6. Verifying cost tracking..."
python -c "from utils.cost_tracker import CostTracker; ct = CostTracker('test_cost.json'); ct.track_request('haiku', 100, 100); import os; os.remove('test_cost.json')"
echo "   ✓ Cost tracking functional"

echo ""
echo "✅ Deployment checklist passed!"
echo "Ready for production deployment."
