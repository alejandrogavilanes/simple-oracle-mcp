# Security Documentation

## Overview

The Simple Oracle MCP Server is designed with security as the primary concern, specifically for use with AI agents accessing mission-critical Oracle databases. This document outlines the comprehensive security measures implemented.

## Security Principles

### 1. Read-Only by Design
- **Principle**: Only SELECT queries and table descriptions are permitted
- **Implementation**: SQL query validation rejects any non-SELECT statements
- **Benefit**: Eliminates risk of data modification, deletion, or schema changes

### 2. Defense in Depth
Multiple security layers protect against various attack vectors:

#### Query Validation Layer
- Pattern-based SQL injection detection
- Keyword blacklisting (INSERT, UPDATE, DELETE, DROP, etc.)
- Query structure analysis
- Parameter sanitization

#### Rate Limiting Layer
- Per-client request throttling
- Configurable request limits
- Automatic blocking of excessive requests
- Resource usage monitoring

#### Connection Security Layer
- Secure credential handling
- Connection timeout enforcement
- Encrypted connections (when supported by Oracle)
- Connection pooling with limits

## Security Features

### SQL Injection Prevention
```python
# Example of blocked queries
BLOCKED_QUERIES = [
    "DROP TABLE users",           # Schema modification
    "INSERT INTO logs VALUES",    # Data insertion
    "UPDATE users SET password",  # Data modification
    "DELETE FROM audit_trail",    # Data deletion
    "GRANT SELECT ON users",      # Permission changes
]
```

### Query Complexity Validation
- Maximum query length limits
- Nested query depth restrictions
- JOIN operation limits
- Subquery complexity analysis

### Audit Logging
All operations are logged with:
- Timestamp and user identification
- Complete query text
- Execution results and errors
- Security validation outcomes
- Performance metrics

## Configuration Security

### Environment Variables
Sensitive configuration is handled through environment variables:

```bash
# Required - Database Connection
ORACLE_HOST=your-oracle-host
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=your-service
ORACLE_USERNAME=readonly_user  # Use read-only accounts only
ORACLE_PASSWORD=secure_password

# Optional - Security Limits
MAX_ROWS=1000                  # Limit result set size
CONNECTION_TIMEOUT=30          # Prevent hanging connections
QUERY_TIMEOUT=300             # Prevent long-running queries
```

### Docker Security
- Non-root user execution
- Minimal base image (Python slim)
- No unnecessary packages or tools
- Temporary containers (--rm flag)

## Best Practices

### Database User Configuration
1. **Create dedicated read-only users**:
   ```sql
   CREATE USER mcp_readonly IDENTIFIED BY 'secure_password';
   GRANT CONNECT TO mcp_readonly;
   GRANT SELECT ON schema.table1 TO mcp_readonly;
   GRANT SELECT ON schema.table2 TO mcp_readonly;
   -- Grant only necessary SELECT permissions
   ```

2. **Avoid using administrative accounts**
3. **Use strong, unique passwords**
4. **Regularly rotate credentials**

### Network Security
- Use VPNs or private networks when possible
- Implement firewall rules restricting database access
- Consider using Oracle's native encryption features
- Monitor network traffic for anomalies

### Monitoring and Alerting
- Set up alerts for failed authentication attempts
- Monitor for unusual query patterns
- Track resource usage and performance
- Regular security log reviews

## Threat Model

### Threats Mitigated
1. **SQL Injection**: Comprehensive query validation
2. **Data Exfiltration**: Row limits and query timeouts
3. **Resource Exhaustion**: Rate limiting and complexity validation
4. **Unauthorized Access**: Authentication and authorization checks
5. **Data Modification**: Read-only operation enforcement

### Residual Risks
1. **Credential Compromise**: Mitigated by read-only permissions
2. **Information Disclosure**: Limited by row limits and logging
3. **Denial of Service**: Mitigated by rate limiting and timeouts

## Compliance Considerations

### Audit Requirements
- Complete audit trail of all database access
- User identification and query logging
- Performance and security metrics
- Retention policies for log data

### Data Privacy
- No sensitive data modification capabilities
- Configurable result set limits
- Secure credential storage
- Encrypted connections (when available)

## Incident Response

### Security Event Detection
Monitor logs for:
- Failed authentication attempts
- Blocked query attempts
- Rate limit violations
- Unusual query patterns
- Performance anomalies

### Response Procedures
1. **Immediate**: Block suspicious IP addresses
2. **Short-term**: Rotate credentials if compromise suspected
3. **Long-term**: Review and update security policies

## Security Testing

### Automated Testing
- SQL injection attempt validation
- Rate limiting verification
- Query complexity testing
- Authentication bypass attempts

### Manual Testing
- Penetration testing recommendations
- Security code reviews
- Configuration audits
- Access control verification

## Updates and Maintenance

### Security Updates
- Regular dependency updates
- Security patch management
- Vulnerability scanning
- Configuration reviews

### Monitoring
- Continuous security monitoring
- Log analysis and alerting
- Performance impact assessment
- Security metric tracking

## Contact

For security-related issues or questions:
- Review audit logs first
- Check security event logs
- Verify configuration settings
- Contact system administrators for credential issues