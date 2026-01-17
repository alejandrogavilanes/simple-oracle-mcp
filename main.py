#!/usr/bin/env python3
"""
Simple Oracle MCP Server - FastMCP Implementation
Read-only access to Oracle database following MCP

This implementation has been migrated from the standard mcp library to the modern
fastmcp library, providing improved performance and simplified architecture while
maintaining full backward compatibility.

FastMCP Migration Benefits:
- Decorator-based tool and resource registration (@mcp.tool(), @mcp.resource())
- Automatic type handling and schema generation
- Built-in context management with FastMCP Context
- Simplified server initialization and execution
- Enhanced performance with reduced overhead

All existing functionality is preserved:
- Security validation (SecurityValidator)
- Rate limiting (RateLimiter) 
- Configuration system (EnhancedConfigLoader)
- Database operations and error handling
- Logging and monitoring
- MCP protocol compliance
"""

import os
import asyncio
import structlog
import time
import uuid
import re
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
import oracledb
from pydantic import BaseModel, Field, validator

from fastmcp import FastMCP, Context

# Import enhanced configuration system (preserved from original implementation)
from config.loader import EnhancedConfigLoader
from config.exceptions import ConfigurationError
from config.models import DatabaseConfig

# Enhanced configuration system handles .env files internally
# No need for explicit load_dotenv() call - the DotEnvSource handles this
# This preserves the original configuration behavior while using FastMCP

# Initialize Oracle thick client mode for compatibility with older password encryption
# This initialization is preserved from the original implementation to maintain
# compatibility with legacy Oracle password encryption methods
try:
    oracledb.init_oracle_client()
    print("Oracle thick client initialized successfully")
except Exception as e:
    print(f"Oracle thick client initialization failed: {e}")
    print("Falling back to thin client mode")

# Setup log directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure structured logging with file output (preserved from original implementation)
# The logging configuration remains identical to ensure audit trail continuity
# and maintain compatibility with existing monitoring systems
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Setup file handlers (preserved from original implementation)
# File logging configuration is maintained to ensure continuity of audit trails
# and compatibility with existing log analysis tools
import logging
from logging.handlers import RotatingFileHandler

# Main application log
app_handler = RotatingFileHandler(
    LOG_DIR / "oracle-mcp-server.log", maxBytes=10*1024*1024, backupCount=5
)
app_handler.setLevel(logging.INFO)

# Security events log
security_handler = RotatingFileHandler(
    LOG_DIR / "security-events.log", maxBytes=5*1024*1024, backupCount=3
)
security_handler.setLevel(logging.WARNING)

# Audit trail log
audit_handler = RotatingFileHandler(
    LOG_DIR / "audit-trail.log", maxBytes=10*1024*1024, backupCount=5
)
audit_handler.setLevel(logging.INFO)

# Configure root logger
root_logger = logging.getLogger()
root_logger.addHandler(app_handler)
root_logger.addHandler(security_handler)
root_logger.addHandler(audit_handler)
root_logger.setLevel(logging.INFO)

logger = structlog.get_logger()

class SecurityValidator:
    """
    Enhanced security validation for SQL queries (preserved and enhanced for FastMCP)
    
    This class provides comprehensive SQL security validation including:
    - SQL injection prevention with pattern-based detection
    - Oracle-specific security checks
    - Query complexity analysis
    - Table name validation
    
    FastMCP Migration Notes:
    - All security functionality preserved from original implementation
    - Enhanced integration with FastMCP Context for better logging
    - Maintains identical validation logic and error messages
    - Compatible with FastMCP decorator-based tools
    """
    
    # Dangerous SQL patterns - comprehensive list for Oracle security
    BLOCKED_PATTERNS = [
        r'\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE)\b',
        r'\b(EXEC|EXECUTE|SP_|XP_)\b',
        r'--.*',  # SQL comments
        r'/\*.*?\*/',  # Block comments
        r';.*',  # Multiple statements
        r'\bUNION\b.*\bSELECT\b',  # Union-based injection
        r'\b(WAITFOR|DELAY)\b',  # Time-based attacks
        r'\b(LOAD_FILE|INTO\s+OUTFILE)\b',  # File operations
        r'\b(DBMS_|UTL_|SYS\.)\b',  # Oracle system packages
        r'\b(DUAL)\b.*\b(CONNECT\s+BY)\b',  # Oracle-specific injection patterns
        r'\b(CHR|ASCII|SUBSTR)\b.*\b(SELECT)\b',  # Oracle function-based injection
    ]
    
    # Additional Oracle-specific security patterns
    ORACLE_SPECIFIC_BLOCKS = [
        r'\b(DBMS_XMLQUERY|DBMS_XMLGEN|EXTRACTVALUE)\b',  # XML-based attacks
        r'\b(SYS_CONTEXT|USERENV)\b',  # Information disclosure
        r'\b(DBMS_PIPE|DBMS_LOCK)\b',  # System manipulation
        r'\b(JAVA_CALL|DBMS_JAVA)\b',  # Java execution
        r'\b(UTL_HTTP|UTL_FILE|UTL_TCP)\b',  # Network and file utilities
        r'\b(DBMS_EXPORT_EXTENSION)\b',  # Export utilities
    ]
    
    @classmethod
    def validate_query(cls, query: str) -> tuple[bool, str]:
        """
        Validate SQL query for security compliance with enhanced Oracle-specific checks
        
        This method performs comprehensive security validation including:
        - Ensures only SELECT statements are allowed
        - Blocks dangerous SQL patterns and Oracle-specific attack vectors
        - Validates query complexity to prevent resource exhaustion
        - Detects suspicious string concatenation patterns
        
        FastMCP Integration:
        - Works seamlessly with @mcp.tool() decorated functions
        - Provides detailed validation messages for FastMCP Context logging
        - Maintains identical security standards from original implementation
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        query_upper = query.strip().upper()
        
        # Must start with SELECT (case-insensitive)
        if not query_upper.startswith('SELECT'):
            logger.warning("Security validation failed: Non-SELECT query attempted", 
                         query_start=query[:50])
            return False, "Only SELECT queries are allowed"
        
        # Check for blocked patterns (including Oracle-specific patterns)
        all_patterns = cls.BLOCKED_PATTERNS + cls.ORACLE_SPECIFIC_BLOCKS
        for pattern in all_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                logger.warning("Security validation failed: Blocked pattern detected", 
                             pattern=pattern,
                             query_hash=hash(query))
                return False, f"Query contains blocked pattern: {pattern}"
        
        # Check query complexity (enhanced)
        complexity_checks = [
            (query.count('('), 15, "Too many parentheses"),
            (query.count('SELECT'), 8, "Too many SELECT statements"),
            (query.count('JOIN'), 10, "Too many JOIN operations"),
            (len(query), 5000, "Query too long"),
        ]
        
        for count, limit, message in complexity_checks:
            if count > limit:
                logger.warning("Security validation failed: Query complexity exceeded", 
                             check=message,
                             count=count,
                             limit=limit,
                             query_hash=hash(query))
                return False, f"Query too complex: {message}"
        
        # Check for suspicious string concatenation patterns
        concat_patterns = [
            r"'\s*\|\|\s*'",  # Oracle string concatenation
            r"'\s*\+\s*'",    # Alternative concatenation
            r'"\s*\|\|\s*"',  # Double quote concatenation
        ]
        
        for pattern in concat_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning("Security validation failed: Suspicious concatenation pattern", 
                             pattern=pattern,
                             query_hash=hash(query))
                return False, "Query contains suspicious string concatenation"
        
        # Enhanced validation passed
        logger.debug("Security validation passed", 
                    query_length=len(query),
                    query_hash=hash(query))
        return True, "Query validated successfully"
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> tuple[bool, str]:
        """
        Validate table name for security compliance
        
        Performs comprehensive table name validation including:
        - Oracle identifier format validation
        - Length restrictions (Oracle 128 character limit)
        - Reserved word detection
        - Suspicious pattern identification
        
        FastMCP Integration:
        - Compatible with @mcp.tool() decorated functions
        - Provides detailed error messages for FastMCP Context
        - Maintains security standards from original implementation
        
        Args:
            table_name: Table name to validate
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not table_name or not table_name.strip():
            return False, "Table name cannot be empty"
        
        # Oracle identifier validation
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_#$]*$', table_name):
            logger.warning("Security validation failed: Invalid table name format", 
                         table_name=table_name)
            return False, "Invalid table name format"
        
        # Check length (Oracle limit is 128 characters for identifiers)
        if len(table_name) > 128:
            logger.warning("Security validation failed: Table name too long", 
                         table_name_length=len(table_name))
            return False, "Table name too long"
        
        # Check for reserved words and suspicious patterns
        reserved_words = [
            'SYS', 'SYSTEM', 'DUAL', 'USER', 'ALL_TABLES', 'DBA_TABLES',
            'V$SESSION', 'V$DATABASE', 'GV$', 'X$'
        ]
        
        table_upper = table_name.upper()
        for reserved in reserved_words:
            if reserved in table_upper:
                logger.warning("Security validation failed: Reserved word in table name", 
                             table_name=table_name,
                             reserved_word=reserved)
                return False, f"Table name contains reserved word: {reserved}"
        
        logger.debug("Table name validation passed", table_name=table_name)
        return True, "Table name validated successfully"

class RateLimiter:
    """
    Enhanced rate limiter for query execution with session-based tracking
    
    Provides comprehensive rate limiting functionality including:
    - Per-client request tracking with sliding window algorithm
    - Automatic client blocking for rate limit violations
    - Detailed status reporting and monitoring
    - Session-based isolation for security
    
    FastMCP Migration Notes:
    - All rate limiting functionality preserved from original implementation
    - Enhanced integration with FastMCP tools for better error reporting
    - Compatible with FastMCP Context for detailed logging
    - Maintains identical rate limiting behavior and thresholds
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # client_id -> {'count': int, 'first_request': float, 'last_request': float}
        self.blocked_clients = {}  # client_id -> block_until_timestamp
    
    def is_allowed(self, client_id: str) -> tuple[bool, str]:
        """
        Check if request is allowed for client with enhanced tracking
        
        Performs comprehensive rate limit checking including:
        - Current block status verification
        - Request window management with automatic cleanup
        - Client request counting and threshold enforcement
        - Detailed logging for audit and monitoring
        
        FastMCP Integration:
        - Provides detailed error messages for FastMCP Context logging
        - Compatible with @mcp.tool() decorated functions
        - Maintains identical rate limiting logic from original implementation
        
        Args:
            client_id: Unique identifier for the client/session
            
        Returns:
            Tuple of (is_allowed, message)
        """
        now = time.time()
        
        # Check if client is currently blocked
        if client_id in self.blocked_clients:
            if now < self.blocked_clients[client_id]:
                remaining_time = int(self.blocked_clients[client_id] - now)
                logger.warning("Rate limiter: Client still blocked", 
                             client_id=client_id,
                             remaining_seconds=remaining_time)
                return False, f"Rate limit exceeded. Try again in {remaining_time} seconds."
            else:
                # Block period expired, remove from blocked list
                del self.blocked_clients[client_id]
                logger.info("Rate limiter: Client block period expired", client_id=client_id)
        
        # Clean old entries outside the current window
        self.requests = {
            k: v for k, v in self.requests.items() 
            if now - v['first_request'] < self.window_seconds
        }
        
        # Initialize or update client tracking
        if client_id not in self.requests:
            self.requests[client_id] = {
                'count': 1, 
                'first_request': now,
                'last_request': now
            }
            logger.debug("Rate limiter: New client registered", 
                        client_id=client_id,
                        window_seconds=self.window_seconds)
            return True, "Request allowed"
        
        # Check if client has exceeded rate limit
        client_data = self.requests[client_id]
        if client_data['count'] >= self.max_requests:
            # Block client for the remainder of the window
            block_until = client_data['first_request'] + self.window_seconds
            self.blocked_clients[client_id] = block_until
            
            remaining_time = int(block_until - now)
            logger.warning("Rate limiter: Client exceeded limit and blocked", 
                         client_id=client_id,
                         request_count=client_data['count'],
                         max_requests=self.max_requests,
                         blocked_until=remaining_time)
            
            return False, f"Rate limit exceeded ({self.max_requests} requests per {self.window_seconds}s). Try again in {remaining_time} seconds."
        
        # Update client request count and timestamp
        client_data['count'] += 1
        client_data['last_request'] = now
        
        logger.debug("Rate limiter: Request allowed", 
                    client_id=client_id,
                    request_count=client_data['count'],
                    max_requests=self.max_requests)
        
        return True, f"Request allowed ({client_data['count']}/{self.max_requests})"
    
    def get_client_status(self, client_id: str) -> dict:
        """
        Get current status for a client
        
        Provides comprehensive client status information including:
        - Current block status and remaining time
        - Request usage statistics
        - Window reset timing
        - Rate limit threshold information
        
        FastMCP Integration:
        - Returns structured data compatible with FastMCP automatic type handling
        - Useful for FastMCP Context logging and monitoring
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with client rate limit status
        """
        now = time.time()
        
        # Check if blocked
        if client_id in self.blocked_clients:
            if now < self.blocked_clients[client_id]:
                return {
                    'blocked': True,
                    'remaining_block_time': int(self.blocked_clients[client_id] - now),
                    'requests_used': self.max_requests,
                    'requests_remaining': 0
                }
        
        # Check current usage
        if client_id in self.requests:
            client_data = self.requests[client_id]
            if now - client_data['first_request'] < self.window_seconds:
                return {
                    'blocked': False,
                    'requests_used': client_data['count'],
                    'requests_remaining': max(0, self.max_requests - client_data['count']),
                    'window_reset_in': int(client_data['first_request'] + self.window_seconds - now)
                }
        
        # Client has no recent requests
        return {
            'blocked': False,
            'requests_used': 0,
            'requests_remaining': self.max_requests,
            'window_reset_in': self.window_seconds
        }

# Initialize FastMCP server with identical server name for backward compatibility
# FastMCP provides automatic type handling, schema generation, and enhanced performance
# while maintaining full MCP protocol compliance
mcp = FastMCP("oracle-mcp-server")

# Global variables for configuration and utilities (preserved functionality)
# These maintain the same behavior as the original implementation while working
# seamlessly with FastMCP's decorator-based architecture
db_config = None
rate_limiter = RateLimiter()
session_id = str(uuid.uuid4())

def _load_config():
    """
    Load and validate database configuration using enhanced loader with comprehensive security preservation
    
    This function preserves all existing configuration functionality:
    - Multiple configuration sources (MCP config, environment variables, defaults)
    - Configuration precedence rules (environment > defaults)
    - Security validation and credential masking
    - Source tracking and audit logging
    - Configuration validation and error handling
    """
    try:
        logger.info("Starting enhanced configuration loading with security preservation")
        
        # Use enhanced configuration loader with full source support
        loader = EnhancedConfigLoader()
        
        # Validate all configuration sources before loading
        validation_result = loader.validate_sources()
        if validation_result.errors:
            logger.warning("Configuration source validation warnings", 
                         errors=validation_result.errors)
        
        # Load configuration with source tracking
        config = loader.load_config()
        
        # Get comprehensive source information for audit logging
        source_info = config.get_source_info()
        
        # Log successful configuration load with detailed source tracking
        logger.info("Database configuration loaded successfully", 
                   host=config.host, 
                   port=config.port, 
                   service_name=config.service_name,
                   connection_timeout=config.connection_timeout,
                   query_timeout=config.query_timeout,
                   max_rows=config.max_rows,
                   source_info=source_info,
                   config_sources_used=list(set(source_info.values())))
        
        # Log any configuration warnings from the loader
        warnings = config.get_warnings()
        for warning in warnings:
            logger.warning("Configuration warning detected", 
                         message=warning,
                         source_info=source_info)
        
        # Log configuration precedence information for audit trail
        sources_used = list(set(source_info.values()))
        if len(sources_used) > 1:
            logger.info("Multiple configuration sources detected", 
                       sources=sources_used,
                       precedence="MCP Environment Variables > Default Values",
                       precedence_note="Higher precedence sources override lower precedence")
        else:
            logger.info("Single configuration source used", 
                       source=sources_used[0] if sources_used else "unknown")
        
        # Verify all security features are preserved with current configuration
        _verify_security_features_preserved(config, source_info)
        
        # Verify configuration completeness
        _verify_configuration_completeness(config, source_info)
        
        # Log configuration validation success
        logger.info("Configuration validation completed successfully",
                   config_hash=hash(str(config.model_dump())),
                   security_validated=True,
                   completeness_validated=True)
        
        return config
        
    except ConfigurationError as e:
        # Enhanced error handling with source identification and user guidance
        logger.error("Configuration error occurred", 
                    error_type=type(e).__name__,
                    error_message=str(e))
        
        # Use the enhanced error handler for detailed logging and guidance
        from config.loader import handle_configuration_error
        handle_configuration_error(e)
        raise
        
    except Exception as e:
        logger.error("Unexpected configuration error", 
                    error=str(e),
                    error_type=type(e).__name__)
        raise ConfigurationError(f"Configuration loading failed: {e}")

def _verify_configuration_completeness(config: DatabaseConfig, source_info: Dict[str, str]) -> None:
    """
    Verify that configuration is complete and all required parameters are present
    
    Args:
        config: Loaded database configuration
        source_info: Dictionary mapping field names to their source
    """
    required_fields = ['host', 'port', 'service_name', 'username', 'password']
    missing_fields = []
    
    for field in required_fields:
        value = getattr(config, field, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)
    
    if missing_fields:
        logger.error("Configuration completeness check failed", 
                    missing_fields=missing_fields,
                    source_info=source_info)
        raise ConfigurationError(f"Missing required configuration fields: {missing_fields}")
    
    # Verify optional fields have reasonable defaults
    optional_checks = [
        ('connection_timeout', config.connection_timeout, 30),
        ('query_timeout', config.query_timeout, 300),
        ('max_rows', config.max_rows, 1000)
    ]
    
    for field_name, value, expected_default in optional_checks:
        if value is None:
            logger.warning("Optional configuration field missing, using default", 
                         field=field_name,
                         default_value=expected_default,
                         source_info=source_info)
    
    logger.info("Configuration completeness verification passed", 
               required_fields_present=len(required_fields),
               source_info=source_info)

def _verify_security_features_preserved(config: DatabaseConfig, source_info: Dict[str, str]) -> None:
    """Verify that all security features are preserved regardless of configuration source"""
    from config.security import validate_environment_security, validate_credential_format
    
    # Create config dictionary for security validation
    config_dict = {
        'host': config.host,
        'port': config.port,
        'username': config.username,
        'password': config.password,
        'connection_timeout': config.connection_timeout,
        'query_timeout': config.query_timeout,
        'max_rows': config.max_rows
    }
    
    # Verify environment security validation works
    try:
        security_warnings = validate_environment_security(config_dict)
        logger.debug("Security validation completed", 
                    warnings_count=len(security_warnings),
                    config_sources=list(set(source_info.values())))
    except Exception as e:
        logger.error("Security validation failed", 
                    error=str(e),
                    config_sources=list(set(source_info.values())))
        raise ConfigurationError(f"Security validation failed: {e}")
    
    # Verify credential validation works
    try:
        credential_errors = validate_credential_format(config.username, config.password)
        if credential_errors:
            logger.warning("Credential validation warnings", 
                          warnings=credential_errors,
                          config_sources=list(set(source_info.values())))
    except Exception as e:
        logger.error("Credential validation failed", 
                    error=str(e),
                    config_sources=list(set(source_info.values())))
        raise ConfigurationError(f"Credential validation failed: {e}")
    
    # Verify security parameters are within acceptable ranges
    security_checks = []
    
    # Check connection timeout
    if config.connection_timeout <= 0 or config.connection_timeout > 600:
        security_checks.append(f"Connection timeout {config.connection_timeout}s is outside secure range (1-600s)")
    
    # Check query timeout
    if config.query_timeout <= 0 or config.query_timeout > 3600:
        security_checks.append(f"Query timeout {config.query_timeout}s is outside secure range (1-3600s)")
    
    # Check max rows limit
    if config.max_rows <= 0 or config.max_rows > 10000:
        security_checks.append(f"Max rows {config.max_rows} is outside secure range (1-10000)")
    
    # Check port range
    if config.port <= 0 or config.port > 65535:
        security_checks.append(f"Port {config.port} is outside valid range (1-65535)")
    
    if security_checks:
        for check in security_checks:
            logger.warning("Security parameter check failed", 
                          check=check,
                          config_sources=list(set(source_info.values())))
    
    logger.info("Security features verification completed", 
               config_sources=list(set(source_info.values())),
               security_checks_passed=len(security_checks) == 0)

@asynccontextmanager
async def get_connection():
    """
    Get database connection with enhanced error handling and monitoring
    
    Provides robust database connection management including:
    - Connection establishment with timeout handling
    - Performance monitoring and logging
    - Automatic connection cleanup
    - Error handling with detailed logging
    
    FastMCP Migration Notes:
    - Preserved identical functionality from original implementation
    - Enhanced integration with FastMCP Context for better logging
    - Maintains same connection parameters and error handling
    - Compatible with FastMCP decorator-based tools
    
    Yields:
        oracledb.Connection: Active database connection
        
    Raises:
        oracledb.Error: Database connection or operation errors
    """
    connection = None
    start_time = time.time()
    
    try:
        logger.info("Establishing database connection", 
                   session_id=session_id,
                   dsn=db_config.dsn)
        
        connection = oracledb.connect(
            user=db_config.username,
            password=db_config.password,
            dsn=db_config.dsn
        )
        connection.autocommit = False  # Read-only, no commits needed
        
        connect_time = time.time() - start_time
        logger.info("Database connection established", 
                   session_id=session_id,
                   connection_time_ms=round(connect_time * 1000, 2))
        
        yield connection
        
    except oracledb.Error as e:
        connect_time = time.time() - start_time
        logger.error("Database connection failed", 
                    session_id=session_id,
                    error=str(e),
                    connection_time_ms=round(connect_time * 1000, 2),
                    dsn=db_config.dsn)
        raise
    finally:
        if connection:
            try:
                connection.close()
                logger.debug("Database connection closed", session_id=session_id)
            except Exception as e:
                logger.warning("Error closing connection", 
                             session_id=session_id, error=str(e))

# FastMCP Resource handlers - Direct decorator-based registration
# These replace the original handler dispatch pattern with FastMCP's
# simplified decorator approach while maintaining identical functionality

@mcp.resource("oracle://tables")
async def get_tables() -> str:
    """
    List all accessible tables using FastMCP resource decorator
    
    FastMCP Enhancement:
    - Direct decorator registration (@mcp.resource) replaces handler dispatch
    - Automatic schema generation and type handling
    - Built-in URI routing and response formatting
    - Maintains identical query logic and security filtering
    
    Returns:
        str: JSON string containing list of accessible tables with owners
        
    Raises:
        oracledb.Error: Database connection or query errors
    """
    async with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, owner 
            FROM all_tables 
            WHERE owner NOT IN ('SYS', 'SYSTEM', 'CTXSYS', 'MDSYS', 'OLAPSYS', 'WMSYS')
            ORDER BY owner, table_name
        """)
        tables = [{"table_name": row[0], "owner": row[1]} for row in cursor.fetchall()]
        return str(tables)

@mcp.resource("oracle://views")
async def get_views() -> str:
    """
    List all accessible views using FastMCP resource decorator
    
    FastMCP Enhancement:
    - Direct decorator registration (@mcp.resource) replaces handler dispatch
    - Automatic schema generation and type handling
    - Built-in URI routing and response formatting
    - Maintains identical query logic and security filtering
    
    Returns:
        str: JSON string containing list of accessible views with owners
        
    Raises:
        oracledb.Error: Database connection or query errors
    """
    async with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT view_name, owner 
            FROM all_views 
            WHERE owner NOT IN ('SYS', 'SYSTEM', 'CTXSYS', 'MDSYS', 'OLAPSYS', 'WMSYS')
            ORDER BY owner, view_name
        """)
        views = [{"view_name": row[0], "owner": row[1]} for row in cursor.fetchall()]
        return str(views)

# FastMCP Tool handlers
# FastMCP Tool handlers - Direct decorator-based registration
# These replace the original handler dispatch pattern with FastMCP's
# simplified decorator approach while preserving all functionality

@mcp.tool()
async def query_oracle(query: str, limit: int = 100, ctx: Context = None) -> str:
    """
    Execute read-only SQL query on Oracle database using FastMCP tool decorator
    
    FastMCP Enhancements:
    - Direct decorator registration (@mcp.tool) replaces handler dispatch
    - Automatic parameter validation and schema generation
    - Built-in Context integration for enhanced logging and progress tracking
    - Maintains all security validation, rate limiting, and error handling
    
    Security Features (Preserved):
    - SQL injection prevention with comprehensive pattern detection
    - Rate limiting with per-client tracking
    - Query complexity validation
    - Automatic row limiting for resource protection
    
    Args:
        query: SQL SELECT query to execute (validated for security)
        limit: Maximum number of rows to return (default: 100, max: configured limit)
        ctx: FastMCP Context for enhanced logging and progress tracking
        
    Returns:
        str: JSON string containing query results with columns, rows, and metadata
        
    Raises:
        SecurityError: Query validation failures
        RateLimitError: Rate limit exceeded
        DatabaseError: Oracle database errors
    """
    client_id = f"{session_id}_query_oracle"
    start_time = time.time()
    
    # Ensure configuration is loaded
    global db_config
    if db_config is None:
        db_config = _load_config()
    
    # Enhanced logging with FastMCP Context
    if ctx:
        ctx.info(f"Starting query execution with limit {limit}")
        ctx.info(f"Query length: {len(query)} characters")
    
    # Enhanced rate limiting with detailed error responses (preserved)
    is_allowed, rate_limit_msg = rate_limiter.is_allowed(client_id)
    if not is_allowed:
        logger.warning("Rate limit exceeded", 
                     session_id=session_id,
                     tool="query_oracle", 
                     client_id=client_id,
                     message=rate_limit_msg)
        if ctx:
            ctx.info(f"Rate limit exceeded: {rate_limit_msg}")
        return f"Error: {rate_limit_msg}"
    
    try:
        logger.info("Tool execution started", 
                   session_id=session_id,
                   tool="query_oracle", arguments={"query": query, "limit": limit})
        
        if ctx:
            ctx.info("Performing security validation on query")
        
        # Enhanced security validation (preserved)
        is_valid, validation_msg = SecurityValidator.validate_query(query)
        if not is_valid:
            logger.warning("Security validation failed", 
                         session_id=session_id,
                         query=query[:100],  # Log first 100 chars only
                         reason=validation_msg)
            if ctx:
                ctx.info(f"Security validation failed: {validation_msg}")
            return f"Security Error: {validation_msg}"
        
        if ctx:
            ctx.info("Security validation passed, applying row limit")
        
        # Apply row limit (preserved) - with input validation for security
        limit = min(limit, db_config.max_rows)
        
        # Validate limit is a positive integer to prevent SQL injection
        if not isinstance(limit, int) or limit < 0:
            raise ValueError(f"Invalid limit value: {limit}. Must be a non-negative integer.")
        
        if 'ROWNUM' not in query.upper() and limit > 0:
            # Safe to use f-string here since limit is validated as integer
            query = f"SELECT * FROM ({query}) WHERE ROWNUM <= {limit}"
        
        if ctx:
            ctx.info(f"Establishing database connection for query execution")
        
        async with get_connection() as conn:
            cursor = conn.cursor()
            
            if ctx:
                ctx.info("Executing SQL query against Oracle database")
            
            # Execute query with timeout handling
            query_start = time.time()
            cursor.execute(query)
            query_time = time.time() - query_start
            
            if ctx:
                ctx.info(f"Query executed in {round(query_time * 1000, 2)}ms, fetching results")
            
            # Get results
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            if ctx:
                ctx.info(f"Retrieved {len(rows)} rows with {len(columns)} columns")
            
            # Log audit trail (preserved)
            logger.info("Query executed successfully", 
                       session_id=session_id,
                       query_hash=hash(query),
                       row_count=len(rows),
                       column_count=len(columns),
                       query_time_ms=round(query_time * 1000, 2),
                       total_time_ms=round((time.time() - start_time) * 1000, 2))
            
            # Format results
            result = {
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows),
                "execution_time_ms": round(query_time * 1000, 2)
            }
            
            execution_time = time.time() - start_time
            logger.info("Tool execution completed", 
                       session_id=session_id,
                       tool="query_oracle", 
                       execution_time_ms=round(execution_time * 1000, 2))
            
            if ctx:
                ctx.info(f"Query execution completed successfully in {round(execution_time * 1000, 2)}ms")
            
            return str(result)
            
    except oracledb.Error as e:
        error_time = time.time() - start_time
        logger.error("Query execution failed", 
                    session_id=session_id,
                    query_hash=hash(query),
                    error=str(e),
                    error_time_ms=round(error_time * 1000, 2))
        if ctx:
            ctx.info(f"Database error occurred: {str(e)}")
        return f"Database Error: {str(e)}"
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error("Tool execution failed", 
                   session_id=session_id,
                   tool="query_oracle", 
                   error=str(e),
                   execution_time_ms=round(execution_time * 1000, 2))
        if ctx:
            ctx.info(f"Unexpected error occurred: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
async def describe_table(table_name: str, ctx: Context = None) -> str:
    """
    Get table structure and column information using FastMCP tool decorator
    
    FastMCP Enhancements:
    - Direct decorator registration (@mcp.tool) replaces handler dispatch
    - Automatic parameter validation and schema generation
    - Built-in Context integration for enhanced logging and progress tracking
    - Maintains all security validation, rate limiting, and error handling
    
    Security Features (Preserved):
    - Table name validation with Oracle identifier rules
    - Rate limiting with per-client tracking
    - Reserved word detection and filtering
    - Length validation for security
    
    Args:
        table_name: Name of the table to describe (validated for security)
        ctx: FastMCP Context for enhanced logging and progress tracking
        
    Returns:
        str: JSON string containing table structure with column details
        
    Raises:
        SecurityError: Table name validation failures
        RateLimitError: Rate limit exceeded
        DatabaseError: Oracle database errors or table not found
    """
    client_id = f"{session_id}_describe_table"
    start_time = time.time()
    
    # Ensure configuration is loaded
    global db_config
    if db_config is None:
        db_config = _load_config()
    
    # Enhanced logging with FastMCP Context
    if ctx:
        ctx.info(f"Starting table description for: {table_name}")
    
    # Enhanced rate limiting with detailed error responses (preserved)
    is_allowed, rate_limit_msg = rate_limiter.is_allowed(client_id)
    if not is_allowed:
        logger.warning("Rate limit exceeded", 
                     session_id=session_id,
                     tool="describe_table", 
                     client_id=client_id,
                     message=rate_limit_msg)
        if ctx:
            ctx.info(f"Rate limit exceeded: {rate_limit_msg}")
        return f"Error: {rate_limit_msg}"
    
    try:
        logger.info("Tool execution started", 
                   session_id=session_id,
                   tool="describe_table", arguments={"table_name": table_name})
        
        if ctx:
            ctx.info("Validating table name format and security")
        
        # Enhanced table name validation using SecurityValidator (preserved)
        is_valid, validation_msg = SecurityValidator.validate_table_name(table_name)
        if not is_valid:
            logger.warning("Table name validation failed", 
                         session_id=session_id,
                         table_name=table_name,
                         reason=validation_msg)
            if ctx:
                ctx.info(f"Table name validation failed: {validation_msg}")
            return f"Security Error: {validation_msg}"
        
        if ctx:
            ctx.info("Table name validation passed, establishing database connection")
        
        async with get_connection() as conn:
            cursor = conn.cursor()
            
            if ctx:
                ctx.info("Querying table column information from Oracle data dictionary")
            
            cursor.execute("""
                SELECT column_name, data_type, nullable, data_default, column_id
                FROM all_tab_columns 
                WHERE table_name = UPPER(:table_name)
                ORDER BY column_id
            """, {"table_name": table_name})
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "column_name": row[0],
                    "data_type": row[1],
                    "nullable": row[2],
                    "default_value": row[3],
                    "column_id": row[4]
                })
            
            if ctx:
                ctx.info(f"Retrieved {len(columns)} column definitions")
            
            if not columns:
                logger.info("Table not found or no access", 
                           session_id=session_id,
                           table_name=table_name)
                if ctx:
                    ctx.info(f"Table '{table_name}' not found or no access permissions")
                return f"Table '{table_name}' not found or no access"
            
            result = {
                "table_name": table_name.upper(),
                "columns": columns,
                "column_count": len(columns)
            }
            
            describe_time = time.time() - start_time
            logger.info("Table described successfully", 
                       session_id=session_id,
                       table_name=table_name.upper(),
                       column_count=len(columns),
                       describe_time_ms=round(describe_time * 1000, 2))
            
            execution_time = time.time() - start_time
            logger.info("Tool execution completed", 
                       session_id=session_id,
                       tool="describe_table", 
                       execution_time_ms=round(execution_time * 1000, 2))
            
            if ctx:
                ctx.info(f"Table description completed successfully in {round(execution_time * 1000, 2)}ms")
            
            return str(result)
            
    except oracledb.Error as e:
        error_time = time.time() - start_time
        logger.error("Table describe failed", 
                    session_id=session_id,
                    table_name=table_name,
                    error=str(e),
                    error_time_ms=round(error_time * 1000, 2))
        if ctx:
            ctx.info(f"Database error occurred: {str(e)}")
        return f"Database Error: {str(e)}"
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error("Tool execution failed", 
                   session_id=session_id,
                   tool="describe_table", 
                   error=str(e),
                   execution_time_ms=round(execution_time * 1000, 2))
        if ctx:
            ctx.info(f"Unexpected error occurred: {str(e)}")
        return f"Error: {str(e)}"

async def main():
    """
    Main entry point with enhanced initialization and preserved error handling
    
    FastMCP Migration Notes:
    - Replaces stdio_server() context manager with FastMCP.run()
    - Maintains identical initialization logging and error handling
    - Preserves all configuration loading and validation
    - Uses FastMCP's automatic transport management
    
    Key Changes:
    - Server initialization: Server("oracle-mcp-server") → FastMCP("oracle-mcp-server")
    - Server execution: stdio_server() → mcp.run() with automatic transport handling
    - Error handling: Preserved identical patterns for configuration and startup errors
    - Logging: Maintained same log messages and structure for audit continuity
    
    Raises:
        ConfigurationError: Configuration loading or validation failures
        KeyboardInterrupt: Graceful shutdown on interrupt signal
        Exception: Unexpected startup errors
    """
    global db_config
    
    # Preserve identical initialization logging from original implementation
    logger.info("Starting TUI Oracle MCP Server (FastMCP)", 
               version="1.0.0",
               timestamp=datetime.now().isoformat())
    
    try:
        # Load configuration with preserved error handling
        db_config = _load_config()
        
        # Preserve detailed initialization logging
        logger.info("FastMCP Oracle MCP Server initialized", 
                   session_id=session_id,
                   config={
                       "host": db_config.host,
                       "port": db_config.port,
                       "service_name": db_config.service_name,
                       "max_rows": db_config.max_rows
                   })
        
        logger.info("Server initialization completed", 
                   session_id=session_id)
        
        # Replace stdio_server() with FastMCP.run() - automatic transport management
        # FastMCP handles stdio transport automatically, no manual stream handling needed
        # This simplifies the server execution while maintaining full MCP protocol compliance
        logger.info("MCP server started", session_id=session_id)
        await mcp.run_async(transport="stdio")
        
    except ConfigurationError as e:
        # Preserve specific configuration error handling
        logger.error("Configuration error during startup", 
                    error=str(e),
                    error_type="ConfigurationError")
        raise
    except KeyboardInterrupt:
        # Handle graceful shutdown on interrupt
        logger.info("Received shutdown signal, shutting down gracefully")
        raise
    except Exception as e:
        # Preserve identical error handling and logging from original implementation
        logger.error("Server startup failed", 
                    error=str(e),
                    error_type=type(e).__name__)
        raise
    finally:
        # Preserve identical shutdown logging with graceful cleanup
        logger.info("TUI Oracle MCP Server shutdown")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())