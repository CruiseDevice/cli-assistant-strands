# Deployment Guide

Complete guide for deploying the Smart CLI Assistant to various environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development](#local-development)
3. [AWS EC2 Deployment](#aws-ec2-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Production Best Practices](#production-best-practices)
6. [Monitoring & Maintenance](#monitoring--maintenance)

## Pre-Deployment Checklist

Before deploying to any environment, ensure:

### Code Quality
```bash
# Run all tests
./scripts/run_tests.sh

# Run deployment checks
./scripts/deploy_check.sh

# Validate configuration
python scripts/validate_installation.py
```

### Security
- [ ] No secrets in code
- [ ] `.env` file not committed
- [ ] AWS credentials configured properly
- [ ] Pre-commit hooks installed
- [ ] Security scan passed (Bandit)

### Configuration
- [ ] Budget limits set appropriately
- [ ] Log levels configured
- [ ] Session retention policy set
- [ ] Tool permissions reviewed

### Documentation
- [ ] README.md updated
- [ ] API documentation current
- [ ] User guide complete
- [ ] Deployment notes added

## Local Development

### Quick Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd cli-assistant-strands

# 2. Run setup script
./scripts/setup.sh

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Validate
python scripts/validate_installation.py

# 5. Run
python cli_assistant.py
```

### Development Environment

```bash
# Create development environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pre-commit black flake8 mypy pytest-cov

# Setup git hooks
pre-commit install

# Run in development mode
export LOG_LEVEL=DEBUG
python cli_assistant.py --model haiku
```

## AWS EC2 Deployment

### Launch EC2 Instance

1. **Create EC2 Instance:**
   ```bash
   # Use AWS Console or CLI
   aws ec2 run-instances \
     --image-id ami-xxxxxxxx \
     --instance-type t3.small \
     --key-name your-key \
     --security-group-ids sg-xxxxxxxx
   ```

2. **Connect to Instance:**
   ```bash
   ssh -i your-key.pem ec2-user@<instance-ip>
   ```

### Setup on EC2

```bash
# Update system
sudo yum update -y

# Install Python 3.9+
sudo yum install python39 -y

# Install Git
sudo yum install git -y

# Clone repository
git clone <repository-url>
cd cli-assistant-strands

# Run setup
./scripts/setup.sh

# Configure AWS credentials (use IAM role instead)
# Or: aws configure

# Setup as service (optional)
sudo cp deployment/cli-assistant.service /etc/systemd/system/
sudo systemctl enable cli-assistant
sudo systemctl start cli-assistant
```

### IAM Role Configuration

Create IAM role with policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-haiku-*",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-*",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-opus-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

Attach role to EC2 instance.

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p sessions logs notes

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default command
CMD ["python", "cli_assistant.py"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  cli-assistant:
    build: .
    volumes:
      - ./sessions:/app/sessions
      - ./logs:/app/logs
      - ./notes:/app/notes
      - ~/.aws:/home/appuser/.aws:ro
    environment:
      - AWS_REGION=us-west-2
      - DAILY_BUDGET_LIMIT=5.00
      - MONTHLY_BUDGET_LIMIT=50.00
      - DEFAULT_MODEL=haiku
      - LOG_LEVEL=INFO
    stdin_open: true
    tty: true
```

### Build and Run

```bash
# Build image
docker build -t cli-assistant .

# Run container
docker run -it \
  -v ~/.aws:/home/appuser/.aws:ro \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/logs:/app/logs \
  -e AWS_REGION=us-west-2 \
  cli-assistant

# Or use docker-compose
docker-compose up
```

## Production Best Practices

### Environment Configuration

**Production `.env`:**
```bash
# AWS
AWS_REGION=us-west-2
AWS_PROFILE=production

# Models
DEFAULT_MODEL=sonnet

# Budget (production limits)
DAILY_BUDGET_LIMIT=50.00
MONTHLY_BUDGET_LIMIT=500.00

# Logging
LOG_LEVEL=INFO

# Security
ENABLE_AUDIT_LOG=true
```

### Security Hardening

1. **Use IAM Roles (not access keys):**
   ```bash
   # Attach IAM role to EC2/ECS
   # No AWS credentials in .env
   ```

2. **File Permissions:**
   ```bash
   chmod 600 .env
   chmod 700 sessions/
   chmod 700 logs/
   ```

3. **Network Security:**
   - Restrict inbound traffic
   - Use VPC endpoints for AWS services
   - Enable encryption in transit

4. **Secrets Management:**
   ```bash
   # Use AWS Secrets Manager
   aws secretsmanager create-secret \
     --name cli-assistant-config \
     --secret-string file://secrets.json
   ```

### Logging Configuration

**Production logging:**

```yaml
# config/production_config.yaml
logging:
  level: "INFO"
  log_dir: "/var/log/cli-assistant"
  max_file_size: 104857600  # 100MB
  backup_count: 10
  console_logging: false
  track_performance: true
```

**Log Rotation (logrotate):**

```bash
# /etc/logrotate.d/cli-assistant
/var/log/cli-assistant/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
}
```

### Monitoring

**CloudWatch Integration:**

```python
# Add to cli_assistant.py
import boto3

cloudwatch = boto3.client('cloudwatch')

def send_metric(name, value):
    cloudwatch.put_metric_data(
        Namespace='CLIAssistant',
        MetricData=[{
            'MetricName': name,
            'Value': value,
            'Unit': 'None'
        }]
    )
```

**CloudWatch Alarms:**

```bash
# Create cost alarm
aws cloudwatch put-metric-alarm \
  --alarm-name cli-assistant-daily-cost \
  --alarm-description "Alert when daily cost exceeds $40" \
  --metric-name DailyCost \
  --namespace CLIAssistant \
  --statistic Sum \
  --period 86400 \
  --threshold 40 \
  --comparison-operator GreaterThanThreshold
```

### Backup Strategy

**Automated Backups:**

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/cli-assistant"
DATE=$(date +%Y%m%d)

# Backup sessions
tar -czf "$BACKUP_DIR/sessions-$DATE.tar.gz" sessions/

# Backup cost data
cp cost_tracking.json "$BACKUP_DIR/cost_tracking-$DATE.json"

# Backup logs
tar -czf "$BACKUP_DIR/logs-$DATE.tar.gz" logs/

# Keep last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.json" -mtime +30 -delete
```

**Cron Job:**
```bash
# Backup daily at 2 AM
0 2 * * * /app/scripts/backup.sh
```

## Monitoring & Maintenance

### Health Checks

**Create health check script:**

```python
# scripts/health_check.py
import sys
from utils.config_manager import ConfigManager
from utils.cost_tracker import CostTracker

def check_health():
    checks = {
        'config': False,
        'cost_tracker': False,
        'budget': False
    }

    try:
        # Check config
        config = ConfigManager()
        checks['config'] = config.validate()

        # Check cost tracker
        tracker = CostTracker()
        checks['cost_tracker'] = True

        # Check budget
        daily_cost = tracker.get_daily_cost()
        daily_limit = config.get('cost.daily_limit')
        checks['budget'] = daily_cost < daily_limit

    except Exception as e:
        print(f"Health check failed: {e}")
        return False

    return all(checks.values())

if __name__ == "__main__":
    sys.exit(0 if check_health() else 1)
```

**Monitor with cron:**
```bash
# Check every 5 minutes
*/5 * * * * python /app/scripts/health_check.py || /app/scripts/alert.sh
```

### Performance Monitoring

**Track metrics:**

```python
from utils.logger import CostAwareLogger

logger = CostAwareLogger()

# Daily report
stats = logger.get_stats(hours=24)
print(f"Interactions: {stats['total_interactions']}")
print(f"Avg duration: {stats['avg_duration']:.2f}s")
print(f"Error rate: {stats['errors'] / stats['total_interactions'] * 100:.1f}%")
```

### Cost Monitoring

**Daily cost report:**

```bash
#!/bin/bash
# scripts/daily_cost_report.sh

python -c "
from utils.cost_tracker import CostTracker
tracker = CostTracker()
summary = tracker.get_summary()
print(f'Daily Cost: \${summary[\"daily_cost\"]:.2f}')
print(f'Monthly Cost: \${summary[\"monthly_cost\"]:.2f}')
"
```

### Maintenance Tasks

**Weekly:**
- Review logs for errors
- Check disk space
- Verify backups
- Update dependencies (if needed)

**Monthly:**
- Review cost trends
- Archive old sessions
- Update documentation
- Security audit

**Quarterly:**
- Performance review
- Capacity planning
- Cost optimization review
- Disaster recovery test

### Scaling

**Horizontal Scaling:**

For multiple instances:

1. Use shared storage (EFS/S3) for sessions
2. Centralized cost tracking (DynamoDB)
3. Load balancer for distribution
4. Shared configuration (Parameter Store)

**Example with S3:**

```python
# utils/s3_session_storage.py
import boto3

class S3SessionManager:
    def __init__(self, bucket_name):
        self.s3 = boto3.client('s3')
        self.bucket = bucket_name

    def save_session(self, session_id, data):
        self.s3.put_object(
            Bucket=self.bucket,
            Key=f'sessions/{session_id}.json',
            Body=json.dumps(data)
        )
```

## Troubleshooting

### Common Deployment Issues

**Issue: Permission denied**
```bash
# Fix file permissions
chmod +x scripts/*.sh
chmod 600 .env
```

**Issue: AWS credentials not found**
```bash
# Use IAM role (recommended)
# Or configure credentials
aws configure
```

**Issue: Port already in use**
```bash
# Find process
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Rollback Procedure

```bash
# 1. Stop service
sudo systemctl stop cli-assistant

# 2. Restore from backup
tar -xzf /backups/sessions-latest.tar.gz

# 3. Restore previous version
git checkout <previous-version>

# 4. Restart service
sudo systemctl start cli-assistant
```

## Production Checklist

Before going live:

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Configuration validated
- [ ] Budget limits set
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Backups configured
- [ ] Health checks enabled
- [ ] Documentation updated
- [ ] Runbook created
- [ ] On-call rotation defined
- [ ] Rollback tested

## Support

For deployment issues:

1. Check logs: `cat logs/cli_assistant.log`
2. Run diagnostics: `./scripts/deploy_check.sh`
3. Review documentation
4. Contact support team

## Next Steps

After successful deployment:

1. Monitor performance for 24 hours
2. Review cost trends
3. Fine-tune configuration
4. Document any custom changes
5. Train team on operations

---

**Version:** 1.0.0
**Last Updated:** 2025-01-15
