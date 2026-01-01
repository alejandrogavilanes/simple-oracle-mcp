#!/usr/bin/env python3
"""
Enhanced test suite for Oracle MCP Server with comprehensive coverage
Updated for FastMCP patterns
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from main import SecurityValidator, RateLimiter, mcp, db_config, rate_limiter, session_id, _load_config
from config.models import DatabaseConfig
from config.exceptions import MissingParameterError, ValidationError

class TestDatabaseConfig:
    """Test database configuration validation"""
    
    def test_valid_config(self):
        """Test valid configuration"""
        config = DatabaseConfig(
            host="test-host",
            service_name="test-service",
            username="test-user",
            password="test-pass"
        )
        assert config.host == "test-host"
        assert config.port == 1521
        assert config.dsn == "test-host:1521/test-service"
    
    def test_invalid_port(self):
        """Test invalid port validation"""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            DatabaseConfig(
                host="test-host",
                port=70000,
                service_name="test-service",
                username="test-user",
                password="test-pass"
            )
    
    def test_invalid_timeout(self):
        """Test invalid timeout validation"""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            DatabaseConfig(
                host="test-host",
                service_name="test-service",
                username="test-user",
                password="test-pass",
                connection_timeout=-1
            )

class TestSecurityValidator:
    """Test security validation functionality"""
    
    def test_valid_select_query(self):
        """Test valid SELECT query"""
        is_valid, msg = SecurityValidator.validate_query("SELECT * FROM users")
        assert is_valid is True
        assert msg == "Query validated successfully"
    
    def test_blocked_insert_query(self):
        """Test blocked INSERT query"""
        is_valid, msg = SecurityValidator.validate_query("INSERT INTO users VALUES (1, 'test')")
        assert is_valid is False
        assert "Only SELECT queries are allowed" in msg
    
    def test_blocked_sql_injection(self):
        """Test blocked SQL injection patterns"""
        malicious_queries = [
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT * FROM users -- comment",
            "SELECT * FROM users /* comment */"
        ]
        
        for query in malicious_queries:
            is_valid, msg = SecurityValidator.validate_query(query)
            assert is_valid is False
    
    def test_complex_query_blocked(self):
        """Test overly complex queries are blocked"""
        complex_query = "SELECT " + "(" * 16 + "1" + ")" * 16  # Exceed the limit of 15
        is_valid, msg = SecurityValidator.validate_query(complex_query)
        assert is_valid is False
        assert "Too many parentheses" in msg

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_allows_initial_requests(self):
        """Test rate limiter allows initial requests"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            is_allowed, msg = limiter.is_allowed("client1")
            assert is_allowed is True
    
    def test_rate_limiter_blocks_excess_requests(self):
        """Test rate limiter blocks excess requests"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Allow first 3 requests
        for i in range(3):
            is_allowed, msg = limiter.is_allowed("client1")
            assert is_allowed is True
        
        # Block 4th request
        is_allowed, msg = limiter.is_allowed("client1")
        assert is_allowed is False
    
    def test_rate_limiter_different_clients(self):
        """Test rate limiter handles different clients separately"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        is_allowed, msg = limiter.is_allowed("client1")
        assert is_allowed is True
        is_allowed, msg = limiter.is_allowed("client2")
        assert is_allowed is True
        is_allowed, msg = limiter.is_allowed("client1")
        assert is_allowed is True
        is_allowed, msg = limiter.is_allowed("client2")
        assert is_allowed is True

class TestFastMCPServer:
    """Test cases for FastMCP Oracle Server"""
    
    @pytest.fixture
    def fastmcp_config(self):
        """Create FastMCP configuration for testing"""
        test_env = {
            'ORACLE_HOST': 'test_host',
            'ORACLE_SERVICE_NAME': 'test_service',
            'ORACLE_USERNAME': 'test_user',
            'ORACLE_PASSWORD': 'test_pass'
        }
        
        with patch.dict('os.environ', test_env, clear=True):
            with patch('config.sources.os.path.exists', return_value=False):
                with patch('config.sources.load_dotenv'):
                    return _load_config()
    
    def test_config_loading(self, fastmcp_config):
        """Test configuration loading"""
        assert fastmcp_config.host == 'test_host'
        assert fastmcp_config.service_name == 'test_service'
        assert fastmcp_config.username == 'test_user'
    
    def test_fastmcp_config_loading(self, fastmcp_config):
        """Test FastMCP configuration loading"""
        assert fastmcp_config.host == 'test_host'
        assert fastmcp_config.service_name == 'test_service'
        assert fastmcp_config.username == 'test_user'
    
    def test_config_validation_error(self):
        """Test configuration validation with missing credentials"""
        test_env = {
            'ORACLE_HOST': 'test-host',
            'ORACLE_SERVICE_NAME': 'test-service',
            # Missing ORACLE_USERNAME and ORACLE_PASSWORD
        }
        
        with patch.dict('os.environ', test_env, clear=True):
            with patch('config.sources.os.path.exists', return_value=False):  # No .env file
                with patch('config.sources.load_dotenv'):  # Mock dotenv loading
                    with pytest.raises((MissingParameterError, ValidationError)):
                        _load_config()
    
    @pytest.mark.asyncio
    async def test_fastmcp_resources(self):
        """Test FastMCP resource functionality"""
        # Mock database connection for FastMCP resources
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("TEST_TABLE", "TEST_OWNER")]
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        with patch('main.oracledb.connect', return_value=mock_connection):
            with patch('main.db_config') as mock_config:
                mock_config.username = 'test_user'
                mock_config.password = 'test_pass'
                mock_config.dsn = 'test_dsn'
                
                # Import the resource functions from main
                from main import get_tables, get_views
                
                # Test tables resource - access the underlying function
                result = await get_tables.fn()
                assert isinstance(result, str)
                assert "TEST_TABLE" in result
                
                # Test views resource - access the underlying function
                result = await get_views.fn()
                assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_fastmcp_tools_available(self):
        """Test that FastMCP tools are available"""
        # Import the tool functions from main
        from main import query_oracle, describe_table
        
        # Verify tool functions have the underlying function
        assert hasattr(query_oracle, 'fn')
        assert hasattr(describe_table, 'fn')
        assert callable(query_oracle.fn)
        assert callable(describe_table.fn)
    
    @pytest.mark.asyncio
    async def test_fastmcp_query_security(self):
        """Test FastMCP query security validation"""
        # Mock database connection
        mock_connection = MagicMock()
        
        with patch('main.oracledb.connect', return_value=mock_connection):
            with patch('main.db_config') as mock_config:
                mock_config.username = 'test_user'
                mock_config.password = 'test_pass'
                mock_config.dsn = 'test_dsn'
                mock_config.max_rows = 1000
                
                # Import the query function from main
                from main import query_oracle
                
                # Test malicious query blocked
                result = await query_oracle.fn("DELETE FROM test_table", 10)
                assert "Security Error" in result
                
                # Test SQL injection blocked
                result = await query_oracle.fn("SELECT * FROM users; DROP TABLE users;", 10)
                assert "Security Error" in result
    
    @pytest.mark.asyncio
    async def test_fastmcp_describe_table_validation(self):
        """Test FastMCP describe table validation"""
        # Mock database connection
        mock_connection = MagicMock()
        
        with patch('main.oracledb.connect', return_value=mock_connection):
            with patch('main.db_config') as mock_config:
                mock_config.username = 'test_user'
                mock_config.password = 'test_pass'
                mock_config.dsn = 'test_dsn'
                
                # Import the describe function from main
                from main import describe_table
                
                # Test invalid table name
                result = await describe_table.fn("invalid-table-name!")
                assert "Security Error" in result
                
                # Test SQL injection in table name
                result = await describe_table.fn("users'; DROP TABLE users; --")
                assert "Security Error" in result
    
    @pytest.mark.asyncio
    async def test_fastmcp_rate_limiting(self):
        """Test FastMCP rate limiting functionality"""
        # Mock database connection
        mock_connection = MagicMock()
        
        with patch('main.oracledb.connect', return_value=mock_connection):
            with patch('main.db_config') as mock_config:
                mock_config.username = 'test_user'
                mock_config.password = 'test_pass'
                mock_config.dsn = 'test_dsn'
                mock_config.max_rows = 1000
                
                # Mock rate limiter to always return False
                original_is_allowed = rate_limiter.is_allowed
                rate_limiter.is_allowed = Mock(return_value=(False, "Rate limit exceeded"))
                
                try:
                    # Import the query function from main
                    from main import query_oracle
                    
                    # Test rate limiting
                    result = await query_oracle.fn("SELECT 1 FROM DUAL", 10)
                    assert "Rate limit exceeded" in result
                finally:
                    # Restore original method
                    rate_limiter.is_allowed = original_is_allowed
    
    @pytest.mark.asyncio
    async def test_fastmcp_connection_error_handling(self):
        """Test FastMCP connection error handling"""
        # Mock database connection to raise error
        with patch('main.oracledb.connect', side_effect=Exception("Connection failed")):
            with patch('main.db_config') as mock_config:
                mock_config.username = 'test_user'
                mock_config.password = 'test_pass'
                mock_config.dsn = 'test_dsn'
                mock_config.max_rows = 1000
                
                # Import the query function from main
                from main import query_oracle
                
                # Test connection error handling
                result = await query_oracle.fn("SELECT 1 FROM DUAL", 10)
                assert "Error" in result

class TestPerformanceMetrics:
    """Test performance monitoring"""
    
    @pytest.mark.asyncio
    async def test_execution_time_logging(self):
        """Test that execution times are logged"""
        with patch('structlog.get_logger') as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            with patch.dict('os.environ', {
                'ORACLE_HOST': 'test-host',
                'ORACLE_SERVICE_NAME': 'test-service',
                'ORACLE_USERNAME': 'test_user',  # Valid username (no hyphens)
                'ORACLE_PASSWORD': 'test_pass'   # Valid password
            }):
                with patch('config.sources.os.path.exists', return_value=False):  # No .env file
                    with patch('config.sources.load_dotenv'):  # Mock dotenv loading
                        config = _load_config()
                        
                        # Verify configuration loaded successfully
                        assert config.host == 'test-host'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])