# Deployment Guide

## Overview

This guide covers deploying the Simple Oracle MCP Server in various environments, from development to production, with emphasis on security and reliability for AI agent integration.

## Deployment Options

### 1. Docker Deployment for local developement and testing for Developers (Recommended)

#### Single Container
- 1. First you need docker running and you need to build using the code base
```bash
# Build the image
docker build -t simple-oracle-mcp .
```

-  2. Now the container is built it will be possible to launch the local MCP Server using your IDE like VSCode, Kiro, etc...

by passing the docker run command on the MCP config. See [config templates](../docs/config-templates/) for IDE-specific examples. 



NOTE: The docker run command is as follows if you want to run the server locally and pass through parameters for testing

```bash
# Run with environment variables
docker run --rm -i \
  -e ORACLE_HOST=your-oracle-host \
  -e ORACLE_PORT=1521 \
  -e ORACLE_SERVICE_NAME=your-service \
  -e ORACLE_USERNAME=readonly_user \
  -e ORACLE_PASSWORD=secure_password \
  -e MAX_ROWS=1000 \
  simple-oracle-mcp \
  uv run python main.py
```

#### Docker Compose

If you want to run the server in a docker compose environment, you can use the docker compose file, with more granualr logging for local troubleshooting.

**Step 1: Start the services**
```bash
# Build and start all services in detached mode
docker compose up -d
```

**Step 2: View logs (optional)**
```bash
# Follow logs from all services
docker compose logs -f
```

**Step 3: Stop the services**
```bash
# Stop and remove containers
docker compose down
```

**Step 4: Stop and clean up (optional)**
```bash
# Stop containers and remove volumes
docker compose down -v
```

## Environment-Specific Configurations

### Development Environment

This example of config that could be used on IDE to execute the server.

Please Note as long as you have run the 

```json
{
  "mcpServers": {
    "oracle-dev": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=dev-oracle.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=DEV_SERVICE",
        "-e", "ORACLE_USERNAME=dev_readonly",
        "-e", "ORACLE_PASSWORD=dev_password",
        "-e", "MAX_ROWS=500",
        "-e", "LOG_LEVEL=DEBUG",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": ["describe_table", "query_oracle"]
    }
  }
}
```

### Staging Environment
```json
{
  "mcpServers": {
    "oracle-staging": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=staging-oracle.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=STAGING_SERVICE",
        "-e", "ORACLE_USERNAME=staging_readonly",
        "-e", "ORACLE_PASSWORD=staging_password",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": ["describe_table"]
    }
  }
}
```

### Production Environment
```json
{
  "mcpServers": {
    "oracle-prod": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=prod-oracle.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=PROD_SERVICE",
        "-e", "ORACLE_USERNAME=prod_readonly",
        "-e", "ORACLE_PASSWORD=secure_prod_password",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "-e", "LOG_LEVEL=INFO",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Security Hardening

### Container Security
```dockerfile
# Use non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app
USER app

# Minimal permissions
RUN chmod 755 /app
RUN chmod 644 /app/*.py
```

### Network Security
```bash
# Create isolated network
docker network create oracle-mcp-network

# Run with network isolation
docker run --network oracle-mcp-network \
  --name oracle-mcp \
  simple-oracle-mcp
```

### Secrets Management
```bash
# Using Docker secrets
echo "secure_password" | docker secret create oracle_password -

# Using environment file
docker run --env-file .env.production simple-oracle-mcp
```

## Monitoring and Logging

### Log Configuration
```yaml
# docker-compose.yml
services:
  oracle-mcp:
    volumes:
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
      - AUDIT_LOG_ENABLED=true
```

### Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import oracledb; print('OK')" || exit 1
```

### Prometheus Metrics
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'oracle-mcp'
    static_configs:
      - targets: ['oracle-mcp:8080']
```

## Performance Tuning

### Connection Pooling
```python
# Optimal connection pool settings
CONNECTION_POOL_SIZE = 5
CONNECTION_POOL_MAX = 10
CONNECTION_TIMEOUT = 30
```

### Resource Limits
```yaml
# Kubernetes resource limits
resources:
  limits:
    memory: "1Gi"
    cpu: "1000m"
  requests:
    memory: "512Mi"
    cpu: "500m"
```

## Backup and Recovery

### Configuration Backup
```bash
# Backup MCP configurations
cp .kiro/settings/mcp.json backups/mcp-config-$(date +%Y%m%d).json

# Backup environment files
cp .env.production backups/env-production-$(date +%Y%m%d).backup
```

### Log Rotation
```bash
# Setup log rotation
cat > /etc/logrotate.d/oracle-mcp << EOF
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 app app
}
EOF
```

## Troubleshooting

### Common Issues

#### Connection Failures
```bash
# Check network connectivity
docker run --rm simple-oracle-mcp \
  sh -c "nc -zv oracle-host 1521"

# Verify credentials
docker run --rm -e ORACLE_HOST=host -e ORACLE_USERNAME=user \
  simple-oracle-mcp python -c "import oracledb; print('Testing...')"
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats oracle-mcp

# Check query performance
tail -f logs/oracle-mcp-server.log | grep "Query execution time"
```

#### Security Validation Errors
```bash
# Check security logs
tail -f logs/security-events.log

# Validate query syntax
docker exec oracle-mcp python -c "
from config.security import validate_query
print(validate_query('SELECT * FROM users'))
"
```

### Log Analysis
```bash
# Audit trail analysis
grep "QUERY_EXECUTED" logs/audit-trail.log | tail -20

# Security events
grep "SECURITY_VIOLATION" logs/security-events.log

# Performance metrics
grep "PERFORMANCE" logs/oracle-mcp-server.log | tail -10
```

## Maintenance

### Regular Tasks
1. **Weekly**: Review security logs
2. **Monthly**: Update dependencies
3. **Quarterly**: Rotate credentials
4. **Annually**: Security audit

### Update Procedure
```bash
# 1. Build new image
docker build -t simple-oracle-mcp:v2.0.0 .

# 2. Test in staging
docker run --env-file .env.staging simple-oracle-mcp:v2.0.0

# 3. Deploy to production
docker tag simple-oracle-mcp:v2.0.0 simple-oracle-mcp:latest
docker-compose up -d
```

## Support

### Diagnostic Information
```bash
# Collect diagnostic info
docker exec oracle-mcp python -c "
import sys, oracledb
print(f'Python: {sys.version}')
print(f'Oracle Client: {oracledb.version}')
"

# Export logs
docker cp oracle-mcp:/app/logs ./diagnostic-logs-$(date +%Y%m%d)
```

### Performance Monitoring
```bash
# Monitor query performance
docker exec oracle-mcp tail -f /app/logs/audit-trail.log | \
  grep "execution_time" | \
  awk '{print $NF}' | \
  sort -n
```