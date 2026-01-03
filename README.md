# Simple Oracle MCP Server

A **secure, read-only** Oracle database MCP (Model Context Protocol) server designed specifically for AI agents and developer IDEs like Kiro and VSCode. This server provides safe database access by strictly limiting operations to read-only queries, preventing unwanted high-risk changes or errors on mission-critical Oracle databases.

## 🔒 Security-First Design

This MCP server is built with security as the primary concern:

- **Read-Only Operations**: Only SELECT queries and table descriptions are allowed
- **SQL Injection Prevention**: Comprehensive query validation and sanitization
- **Rate Limiting**: Built-in protection against excessive database load
- **Query Complexity Validation**: Prevents resource-intensive operations
- **Automatic Row Limiting**: Configurable limits to prevent large data dumps
- **Audit Logging**: Complete audit trail of all database operations

## 🎯 Purpose

Designed for AI agents that need to:
- Analyze database schemas and structures
- Query data for insights and reporting
- Understand relationships between tables
- Generate reports without risk of data modification
- Provide database assistance in development environments

**Perfect for mission-critical environments** where data integrity is paramount and any write operations could have severe consequences.

## ✨ Features

- **Simple Setup**: Docker-based deployment with minimal configuration
- **Multiple Environment Support**: Dev, staging, and production configurations
- **Enterprise-Grade Security**: Comprehensive validation and logging
- **FastMCP Integration**: Built on the FastMCP framework for optimal performance
- **Flexible Configuration**: Environment variable-based configuration
- **Connection Pooling**: Efficient database connection management
- **Comprehensive Logging**: Structured logging with audit trails

## 🚀 Quick Start

### Prerequisites

- Docker
- Oracle database access credentials
- Kiro IDE or compatible MCP client

### 1. Build the Docker Image

```bash
docker build -t simple-oracle-mcp .
```

### 2. Configure Your Environment

The Simple Oracle MCP Server supports multiple AI development environments. Choose your preferred IDE and follow the configuration guide:

#### Kiro IDE (Recommended)
```json
// .kiro/settings/mcp.json
{
  "mcpServers": {
    "oracle-db": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=your-oracle-host",
        "-e", "ORACLE_PORT=1521",
        "-e", "ORACLE_SERVICE_NAME=your-service",
        "-e", "ORACLE_USERNAME=readonly_user",
        "-e", "ORACLE_PASSWORD=your-password",
        "-e", "MAX_ROWS=1000",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": ["describe_table"]
    }
  }
}
```

#### VSCode with MCP Extension
```json
// .vscode/settings.json
{
  "mcp.servers": {
    "oracle-database": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=your-oracle-host",
        "-e", "ORACLE_SERVICE_NAME=your-service",
        "-e", "ORACLE_USERNAME=readonly_user",
        "-e", "ORACLE_PASSWORD=your-password",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

#### Cursor IDE
```json
// cursor-mcp-config.json
{
  "mcpServers": {
    "oracle-analytics": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=your-oracle-host",
        "-e", "ORACLE_SERVICE_NAME=your-service",
        "-e", "ORACLE_USERNAME=readonly_user",
        "-e", "ORACLE_PASSWORD=your-password",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "autoApprove": ["describe_table"]
    }
  }
}
```

#### Claude Desktop
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// %APPDATA%/Claude/claude_desktop_config.json (Windows)
// ~/.config/Claude/claude_desktop_config.json (Linux)
{
  "mcpServers": {
    "oracle-database": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=your-oracle-host",
        "-e", "ORACLE_SERVICE_NAME=your-service",
        "-e", "ORACLE_USERNAME=readonly_user",
        "-e", "ORACLE_PASSWORD=your-password",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ]
    }
  }
}
```

**📁 Template Configurations**: Ready-to-use configuration templates are available in the `docs/config-templates/` directory for all supported IDEs.

### 3. Start Using with AI Agents

Once configured, AI agents can safely:
- Query database schemas
- Analyze table structures
- Run SELECT queries
- Generate insights and reports

## 🛠️ Available Tools

### `query_oracle`
Execute read-only SQL SELECT queries with built-in security validation.

**Parameters:**
- `query`: SQL SELECT statement
- `limit`: Maximum rows to return (default: 100)

### `describe_table`
Get detailed table structure and column information.

**Parameters:**
- `table_name`: Name of the table to describe

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ORACLE_HOST` | Oracle database hostname | - | Yes |
| `ORACLE_PORT` | Oracle database port | 1521 | No |
| `ORACLE_SERVICE_NAME` | Oracle service name | - | Yes |
| `ORACLE_USERNAME` | Database username | - | Yes |
| `ORACLE_PASSWORD` | Database password | - | Yes |
| `CONNECTION_TIMEOUT` | Connection timeout (seconds) | 30 | No |
| `QUERY_TIMEOUT` | Query timeout (seconds) | 300 | No |
| `MAX_ROWS` | Maximum rows per query | 1000 | No |
| `LOG_LEVEL` | Logging level | INFO | No |

### Security Configuration

The server includes multiple security layers:

- **Query Validation**: Only SELECT statements are allowed
- **SQL Injection Protection**: Pattern-based validation and sanitization
- **Rate Limiting**: Configurable per-client request limits
- **Resource Protection**: Automatic query complexity analysis
- **Audit Logging**: Complete operation logging for compliance

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Agent      │───▶│  Simple Oracle   │───▶│  Oracle         │
│   (Kiro/VSCode) │    │  MCP Server      │    │  Database       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Security Layer  │
                       │  • Query Validation│
                       │  • Rate Limiting  │
                       │  • Audit Logging  │
                       └──────────────────┘
```

## 🔍 Monitoring and Logging

The server provides comprehensive logging:

- **Audit Trail**: All queries and operations logged
- **Security Events**: Failed validation attempts and security violations
- **Performance Metrics**: Query execution times and resource usage
- **Error Tracking**: Detailed error logging for troubleshooting

Logs are available in the `logs/` directory:
- `audit-trail.log`: Complete audit trail
- `security-events.log`: Security-related events
- `oracle-mcp-server.log`: General server operations

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/test_integration_*.py

# Property-based tests (security validation)
pytest tests/test_property_*.py
```

## 🤝 Contributing

This project prioritizes security and simplicity. When contributing:

1. Maintain read-only operation constraints
2. Add comprehensive tests for any new features
3. Follow security best practices
4. Update documentation for any changes

## 📄 License

Proprietary - See LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check the logs in the `logs/` directory
2. Review the security validation messages
3. Ensure your Oracle credentials have appropriate read-only permissions
4. Verify network connectivity to your Oracle database

## ⚠️ Important Security Notes

- **Always use read-only database users** in production
- **Never expose write permissions** to AI agents
- **Monitor audit logs** regularly for unusual activity
- **Use strong passwords** and secure credential storage
- **Limit network access** to authorized systems only

This server is designed to be a safe bridge between AI agents and your critical Oracle databases, ensuring data integrity while enabling powerful AI-driven insights.
