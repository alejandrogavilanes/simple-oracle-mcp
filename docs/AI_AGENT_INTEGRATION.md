# AI Agent Integration Guide

## Overview

The Simple Oracle MCP Server is specifically designed for safe integration with AI agents, providing secure, read-only access to Oracle databases. This guide covers best practices for integrating with various AI platforms and ensuring optimal performance.

## Supported AI Platforms

### Kiro IDE
Primary integration platform with native MCP support.

```json
{
  "mcpServers": {
    "oracle-analytics": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORACLE_HOST=analytics-db.company.com",
        "-e", "ORACLE_SERVICE_NAME=ANALYTICS",
        "-e", "ORACLE_USERNAME=ai_readonly",
        "-e", "ORACLE_PASSWORD=secure_password",
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

### VSCode with MCP Extensions
Compatible with VSCode MCP extensions for database analysis.

```json
// .vscode/settings.json
{
  "mcp.servers": {
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
      ]
    }
  }
}
```

### Cursor IDE
Cursor supports MCP through its AI integration settings.

```json
// cursor-mcp-config.json
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
        "-e", "ORACLE_PASSWORD=secure_password",
        "-e", "MAX_ROWS=500",
        "-e", "LOG_LEVEL=INFO",
        "simple-oracle-mcp",
        "uv", "run", "python", "main.py"
      ],
      "disabled": false,
      "autoApprove": ["describe_table"]
    }
  }
}
```

### Claude Desktop
Claude Desktop MCP configuration for Oracle database access.

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// %APPDATA%/Claude/claude_desktop_config.json (Windows)
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

### Custom AI Applications
RESTful API integration for custom AI applications.

## AI Agent Use Cases

### 1. Database Schema Analysis
AI agents can safely explore database structures:

```python
# Example AI agent workflow
1. describe_table("CUSTOMERS") -> Get table structure
2. describe_table("ORDERS") -> Get related table structure  
3. query_oracle("SELECT COUNT(*) FROM CUSTOMERS") -> Get record counts
4. Generate insights about data relationships
```

### 2. Data Quality Assessment
```sql
-- AI agents can run queries like:
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(*) - COUNT(email) as missing_emails
FROM CUSTOMERS;
```

### 3. Business Intelligence
```sql
-- Safe analytical queries:
SELECT 
    EXTRACT(YEAR FROM order_date) as year,
    COUNT(*) as order_count,
    AVG(order_total) as avg_order_value
FROM ORDERS 
WHERE order_date >= DATE '2023-01-01'
GROUP BY EXTRACT(YEAR FROM order_date);
```

### 4. Report Generation
AI agents can generate comprehensive reports by combining multiple queries and analyzing results.

## Integration Patterns

### Pattern 1: Schema Discovery
```python
# AI Agent Workflow
def discover_database_schema():
    tables = []
    
    # Get all accessible tables
    result = query_oracle("""
        SELECT table_name 
        FROM user_tables 
        ORDER BY table_name
    """)
    
    # Describe each table
    for table in result:
        schema = describe_table(table['table_name'])
        tables.append(schema)
    
    return analyze_relationships(tables)
```

### Pattern 2: Data Profiling
```python
def profile_table(table_name):
    # Get basic statistics
    stats = query_oracle(f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT *) as unique_rows
        FROM {table_name}
    """)
    
    # Get column information
    columns = describe_table(table_name)
    
    return generate_profile_report(stats, columns)
```

### Pattern 3: Relationship Analysis
```python
def analyze_foreign_keys():
    fk_info = query_oracle("""
        SELECT 
            a.table_name,
            a.column_name,
            a.constraint_name,
            c_pk.table_name r_table_name,
            b.column_name r_column_name
        FROM user_cons_columns a
        JOIN user_constraints c ON a.owner = c.owner 
            AND a.constraint_name = c.constraint_name
        JOIN user_constraints c_pk ON c.r_owner = c_pk.owner 
            AND c.r_constraint_name = c_pk.constraint_name
        JOIN user_cons_columns b ON C_PK.owner = b.owner 
            AND  C_PK.constraint_name = b.constraint_name 
            AND b.position = a.position      
        WHERE c.constraint_type = 'R'
    """)
    
    return build_relationship_graph(fk_info)
```

## Security Considerations for AI Agents

### 1. Query Validation
All AI-generated queries are automatically validated:
- Only SELECT statements allowed
- No DDL operations (CREATE, DROP, ALTER)
- No DML operations (INSERT, UPDATE, DELETE)
- No system function calls

### 2. Result Set Limitations
- Maximum row limits prevent data dumps
- Query timeouts prevent resource exhaustion
- Rate limiting prevents abuse

### 3. Audit Trail
Every AI agent interaction is logged:
```json
{
  "timestamp": "2024-01-01T10:30:00Z",
  "agent_id": "kiro-session-123",
  "operation": "query_oracle",
  "query": "SELECT COUNT(*) FROM CUSTOMERS",
  "result_rows": 1,
  "execution_time_ms": 45,
  "status": "success"
}
```

## Performance Optimization

### 1. Query Optimization Guidelines
```sql
-- Good: Specific columns and WHERE clauses
SELECT customer_id, name, email 
FROM customers 
WHERE created_date >= DATE '2024-01-01';

-- Avoid: SELECT * without WHERE clauses
-- SELECT * FROM large_table;
```

### 2. Connection Management
- Automatic connection pooling
- Connection timeout handling
- Resource cleanup after queries

### 3. Caching Strategies
```python
# AI agents can implement caching for:
- Table schemas (cache for 1 hour)
- Reference data (cache for 30 minutes)  
- Aggregate statistics (cache for 15 minutes)
```

## Error Handling

### Common Error Scenarios

#### 1. Invalid Query Syntax
```json
{
  "error": "SECURITY_VIOLATION",
  "message": "Query contains prohibited operations: INSERT",
  "query": "INSERT INTO users VALUES (...)",
  "timestamp": "2024-01-01T10:30:00Z"
}
```

#### 2. Connection Issues
```json
{
  "error": "CONNECTION_FAILED",
  "message": "Unable to connect to Oracle database",
  "details": "ORA-12541: TNS:no listener",
  "timestamp": "2024-01-01T10:30:00Z"
}
```

#### 3. Query Timeout
```json
{
  "error": "QUERY_TIMEOUT",
  "message": "Query exceeded maximum execution time",
  "timeout_seconds": 300,
  "timestamp": "2024-01-01T10:30:00Z"
}
```

### AI Agent Error Recovery
```python
def robust_query_execution(query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return query_oracle(query)
        except ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        except SecurityError as e:
            # Don't retry security violations
            log_security_violation(e)
            raise
        except QueryTimeout:
            # Simplify query and retry
            query = simplify_query(query)
            continue
```

## Best Practices

### 1. Query Design
- Use specific column names instead of SELECT *
- Include appropriate WHERE clauses
- Limit result sets with ROWNUM or FETCH FIRST
- Use indexes effectively

### 2. AI Agent Behavior
- Implement exponential backoff for retries
- Cache frequently accessed schema information
- Validate queries before execution
- Handle errors gracefully

### 3. Resource Management
- Close connections properly
- Implement query timeouts
- Monitor resource usage
- Use connection pooling

### 4. Security
- Never store credentials in AI agent code
- Use environment variables for configuration
- Implement proper logging
- Monitor for unusual patterns

## Monitoring AI Agent Activity

### 1. Query Pattern Analysis
```bash
# Analyze most common queries
grep "QUERY_EXECUTED" logs/audit-trail.log | \
  awk -F'"query":"' '{print $2}' | \
  awk -F'"' '{print $1}' | \
  sort | uniq -c | sort -nr | head -10
```

### 2. Performance Monitoring
```bash
# Monitor query execution times
grep "execution_time_ms" logs/audit-trail.log | \
  awk -F'"execution_time_ms":' '{print $2}' | \
  awk -F',' '{print $1}' | \
  sort -n | tail -20
```

### 3. Error Rate Tracking
```bash
# Track error rates by AI agent
grep "ERROR" logs/oracle-mcp-server.log | \
  awk '{print $1, $2}' | \
  sort | uniq -c
```

## Advanced Integration

### 1. Custom Tool Development
Extend the MCP server with custom tools for specific AI agent needs:

```python
@mcp.tool()
async def analyze_table_relationships(
    ctx: Context,
    table_name: str
) -> str:
    """Analyze relationships for a specific table."""
    # Custom logic for relationship analysis
    pass
```

### 2. Multi-Database Support
Configure multiple Oracle instances for different AI agent contexts:

```json
{
  "mcpServers": {
    "oracle-prod": { /* production config */ },
    "oracle-analytics": { /* analytics config */ },
    "oracle-reporting": { /* reporting config */ }
  }
}
```

### 3. Integration with AI Frameworks
```python
# Example integration with LangChain
from langchain.tools import Tool

oracle_query_tool = Tool(
    name="oracle_query",
    description="Execute read-only queries on Oracle database",
    func=lambda query: query_oracle(query)
)

oracle_schema_tool = Tool(
    name="describe_table", 
    description="Get table schema information",
    func=lambda table: describe_table(table)
)
```

## Troubleshooting

### Common Integration Issues

1. **MCP Connection Failures**
   - Verify Docker image is built correctly
   - Check environment variable configuration
   - Validate Oracle database connectivity

2. **Query Validation Errors**
   - Review security logs for blocked queries
   - Ensure queries are read-only SELECT statements
   - Check for prohibited keywords

3. **Performance Issues**
   - Monitor query execution times
   - Optimize query patterns
   - Adjust connection pool settings

4. **Authentication Problems**
   - Verify Oracle credentials
   - Check user permissions
   - Review connection string format

### Diagnostic Commands
```bash
# Test MCP server connectivity
docker run --rm simple-oracle-mcp python -c "
import oracledb
print('Oracle client version:', oracledb.version)
"

# Validate configuration
docker run --rm --env-file .env simple-oracle-mcp python -c "
from config.loader import load_config
config = load_config()
print('Configuration loaded successfully')
"
```

## Support and Resources

### Documentation
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Oracle Database Documentation](https://docs.oracle.com/database/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)

### Community
- GitHub Issues for bug reports
- Security issues: Contact maintainers directly
- Feature requests: Submit GitHub issues with detailed use cases

### Professional Support
For enterprise deployments requiring:
- Custom AI agent integrations
- Advanced security configurations
- Performance optimization
- 24/7 support

Contact the development team for professional services.