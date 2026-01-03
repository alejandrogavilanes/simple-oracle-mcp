# IDE Configuration Guide

## Overview

This guide provides configuration examples for integrating the Simple Oracle MCP Server with various IDEs and AI development environments. Each configuration is optimized for secure, read-only database access.

## Kiro IDE

### Basic Configuration
```json
// .kiro/settings/mcp.json
{
  "mcpServers": {
    "oracle-main": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-kiro",
        "-e", "ORACLE_HOST=your-oracle-host.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=YOUR_SERVICE",
        "-e", "ORACLE_USERNAME=kiro_readonly",
        "-e", "ORACLE_PASSWORD=secure_kiro_password",
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

### Multi-Environment Configuration
```json
// .kiro/settings/mcp.json
{
  "mcpServers": {
    "oracle-dev": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-dev",
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
    },
    "oracle-prod": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-prod",
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

## VSCode

### Using MCP Extension
```json
// .vscode/settings.json
{
  "mcp.servers": {
    "oracle-database": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-vscode",
        "-e", "ORACLE_HOST=your-oracle-host.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=YOUR_SERVICE",
        "-e", "ORACLE_USERNAME=vscode_readonly",
        "-e", "ORACLE_PASSWORD=secure_vscode_password",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  },
  "mcp.autoStart": true,
  "mcp.logLevel": "info"
}
```

### Workspace-Specific Configuration
```json
// .vscode/settings.json (workspace-specific)
{
  "mcp.servers": {
    "project-oracle": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-project",
        "-e", "ORACLE_HOST=project-db.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=PROJECT_DB",
        "-e", "ORACLE_USERNAME=project_readonly",
        "-e", "ORACLE_PASSWORD=project_password",
        "-e", "MAX_ROWS=500",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

## Cursor IDE

### Main Configuration
```json
// ~/.cursor/mcp_config.json
{
  "mcpServers": {
    "oracle-analytics": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-cursor",
        "-e", "ORACLE_HOST=analytics-db.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=ANALYTICS",
        "-e", "ORACLE_USERNAME=cursor_readonly",
        "-e", "ORACLE_PASSWORD=secure_cursor_password",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "-e", "LOG_LEVEL=INFO",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": ["describe_table"],
      "description": "Oracle database access for AI-powered analytics"
    }
  }
}
```

### Project-Specific Configuration
```json
// .cursor/project_mcp.json
{
  "mcpServers": {
    "customer-db": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-customers",
        "-e", "ORACLE_HOST=customer-db.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=CUSTOMERS",
        "-e", "ORACLE_USERNAME=cursor_customer_readonly",
        "-e", "ORACLE_PASSWORD=customer_db_password",
        "-e", "MAX_ROWS=2000",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": ["describe_table"]
    }
  }
}
```

## Claude Desktop

### macOS Configuration
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "oracle-database": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-claude",
        "-e", "ORACLE_HOST=your-oracle-host.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=YOUR_SERVICE",
        "-e", "ORACLE_USERNAME=claude_readonly",
        "-e", "ORACLE_PASSWORD=secure_claude_password",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

### Windows Configuration
```json
// %APPDATA%/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "oracle-database": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-claude-win",
        "-e", "ORACLE_HOST=your-oracle-host.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=YOUR_SERVICE",
        "-e", "ORACLE_USERNAME=claude_readonly",
        "-e", "ORACLE_PASSWORD=secure_claude_password",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

### Linux Configuration
```json
// ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "oracle-database": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-claude-linux",
        "-e", "ORACLE_HOST=your-oracle-host.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=YOUR_SERVICE",
        "-e", "ORACLE_USERNAME=claude_readonly",
        "-e", "ORACLE_PASSWORD=secure_claude_password",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

## Continue.dev

### Configuration for Continue Extension
```json
// ~/.continue/config.json
{
  "models": [
    {
      "title": "GPT-4 with Oracle",
      "provider": "openai",
      "model": "gpt-4",
      "apiKey": "your-api-key"
    }
  ],
  "mcpServers": {
    "oracle-db": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-continue",
        "-e", "ORACLE_HOST=your-oracle-host.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=YOUR_SERVICE",
        "-e", "ORACLE_USERNAME=continue_readonly",
        "-e", "ORACLE_PASSWORD=continue_password",
        "-e", "MAX_ROWS=1000",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

## Environment-Specific Configurations

### Development Environment
```json
{
  "mcpServers": {
    "oracle-dev": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-dev",
        "-e", "ORACLE_HOST=dev-oracle.internal",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=DEVDB",
        "-e", "ORACLE_USERNAME=dev_user",
        "-e", "ORACLE_PASSWORD=dev_password",
        "-e", "MAX_ROWS=500",
        "-e", "LOG_LEVEL=DEBUG",
        "-e", "CONNECTION_TIMEOUT=15",
        "-e", "QUERY_TIMEOUT=120",
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
        "run", "--rm", "-i", "--name", "oracle-mcp-staging",
        "-e", "ORACLE_HOST=staging-oracle.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=STAGINGDB",
        "-e", "ORACLE_USERNAME=staging_readonly",
        "-e", "ORACLE_PASSWORD=staging_secure_password",
        "-e", "MAX_ROWS=1000",
        "-e", "LOG_LEVEL=INFO",
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
        "run", "--rm", "-i", "--name", "oracle-mcp-prod",
        "-e", "ORACLE_HOST=prod-oracle.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=PRODDB",
        "-e", "ORACLE_USERNAME=prod_readonly",
        "-e", "ORACLE_PASSWORD=highly_secure_prod_password",
        "-e", "MAX_ROWS=1000",
        "-e", "LOG_LEVEL=WARN",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Security Best Practices

### 1. Credential Management
```bash
# Use environment files instead of hardcoded passwords
# Create .env files for each environment

# .env.dev
ORACLE_HOST=dev-oracle.internal
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=DEVDB
ORACLE_USERNAME=dev_user
ORACLE_PASSWORD=dev_password
MAX_ROWS=500

# .env.prod
ORACLE_HOST=prod-oracle.company.com
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=PRODDB
ORACLE_USERNAME=prod_readonly
ORACLE_PASSWORD=highly_secure_prod_password
MAX_ROWS=1000
```

### 2. Using Environment Files
```json
{
  "mcpServers": {
    "oracle-secure": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-secure",
        "--env-file", ".env.prod",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 3. Docker Secrets (Production)
```json
{
  "mcpServers": {
    "oracle-secrets": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-secrets",
        "-e", "ORACLE_HOST=prod-oracle.company.com",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=PRODDB",
        "-e", "ORACLE_USERNAME_FILE=/run/secrets/oracle_username",
        "-e", "ORACLE_PASSWORD_FILE=/run/secrets/oracle_password",
        "-e", "MAX_ROWS=1000",
        "--secret", "oracle_username",
        "--secret", "oracle_password",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Configuration Validation

### Test Configuration
```bash
# Test Docker image
docker run --rm simple-oracle-mcp python -c "print('Image OK')"

# Test with environment variables
docker run --rm \
  -e ORACLE_HOST=test-host \
  -e ORACLE_USERNAME=test-user \
  -e ORACLE_PASSWORD=test-pass \
  -e ORACLE_SERVICE_NAME=TEST \
  simple-oracle-mcp \
  python -c "from config.loader import load_config; print('Config OK')"
```

### Validate MCP Connection
```bash
# For Kiro
# Check if MCP server starts correctly in Kiro's MCP panel

# For VSCode
# Use Command Palette: "MCP: Restart Servers"

# For Claude Desktop
# Check Claude Desktop logs for connection status
```

## Troubleshooting

### Common Issues

#### 1. Docker Image Not Found
```bash
# Build the image first
docker build -t simple-oracle-mcp .

# Verify image exists
docker images simple-oracle-mcp
```

#### 2. Connection Refused
```bash
# Test Oracle connectivity
docker run --rm \
  -e ORACLE_HOST=your-host \
  -e ORACLE_PORT=1521 \
  simple-oracle-mcp \
  python -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('your-host', 1521))
print('Connection OK' if result == 0 else 'Connection Failed')
"
```

#### 3. Authentication Errors
```bash
# Test credentials
docker run --rm \
  -e ORACLE_HOST=your-host \
  -e ORACLE_USERNAME=your-user \
  -e ORACLE_PASSWORD=your-password \
  -e ORACLE_SERVICE_NAME=your-service \
  simple-oracle-mcp \
  python -c "
import oracledb
try:
    conn = oracledb.connect(user='your-user', password='your-password', 
                           dsn='your-host:1521/your-service')
    print('Authentication OK')
    conn.close()
except Exception as e:
    print(f'Authentication Failed: {e}')
"
```

### IDE-Specific Troubleshooting

#### Kiro
- Check MCP server status in Kiro's MCP panel
- Review logs in `.kiro/logs/mcp-servers.log`
- Restart MCP servers from the panel

#### VSCode
- Use Command Palette: "MCP: Show Logs"
- Check VSCode's Output panel for MCP extension logs
- Restart the MCP extension

#### Cursor
- Check Cursor's AI panel for connection status
- Review Cursor's logs for MCP-related errors
- Restart Cursor if connection issues persist

#### Claude Desktop
- Check Claude Desktop's system logs
- Verify configuration file location and syntax
- Restart Claude Desktop application

## Performance Optimization

### Connection Pooling
```json
{
  "mcpServers": {
    "oracle-optimized": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-optimized",
        "-e", "ORACLE_HOST=your-host",
        "-e", "ORACLE_USERNAME=your-user",
        "-e", "ORACLE_PASSWORD=your-password",
        "-e", "ORACLE_SERVICE_NAME=your-service",
        "-e", "MAX_ROWS=1000",
        "-e", "CONNECTION_POOL_SIZE=5",
        "-e", "CONNECTION_POOL_MAX=10",
        "-e", "CONNECTION_TIMEOUT=30",
        "-e", "QUERY_TIMEOUT=300",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

### Resource Limits
```json
{
  "mcpServers": {
    "oracle-limited": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--name", "oracle-mcp-limited",
        "--memory", "512m",
        "--cpus", "0.5",
        "-e", "ORACLE_HOST=your-host",
        "-e", "ORACLE_USERNAME=your-user",
        "-e", "ORACLE_PASSWORD=your-password",
        "-e", "ORACLE_SERVICE_NAME=your-service",
        "-e", "MAX_ROWS=1000",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```