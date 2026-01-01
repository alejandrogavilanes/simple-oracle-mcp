"""
Test suite for enhanced configuration infrastructure
Tests the new configuration loading system with multiple sources
"""

import os
import tempfile
import pytest
from unittest.mock import patch, Mock
from config import (
    EnhancedConfigLoader, 
    MCPConfigSource, 
    DefaultSource,
    DatabaseConfig,
    MissingParameterError,
    ValidationError
)


class TestConfigSources:
    """Test individual configuration sources"""
    
    def test_default_source(self):
        """Test default source provides fallback values"""
        source = DefaultSource()
        
        assert source.is_available() is True
        assert source.get_source_name() == "Default Values"
        assert source.get_value("ORACLE_HOST") == "localhost"
        assert source.get_value("ORACLE_PORT") == "1521"
        assert source.get_value("NONEXISTENT_KEY") is None
    
    def test_mcp_config_source(self):
        """Test MCP config source reads environment variables"""
        source = MCPConfigSource()
        
        # Test with MCP variables
        with patch.dict(os.environ, {"MCP_ORACLE_HOST": "mcp-host"}):
            assert source.is_available() is True
            assert source.get_value("ORACLE_HOST") == "mcp-host"
            assert source.get_source_name() == "MCP Config Environment"


class TestEnhancedConfigLoader:
    """Test enhanced configuration loader"""
    
    def test_missing_required_parameter(self):
        """Test error handling for missing required parameters"""
        loader = EnhancedConfigLoader()
        
        # Remove all sources except defaults (which don't have username/password)
        loader.config_sources = [DefaultSource()]
        
        with pytest.raises(MissingParameterError) as exc_info:
            loader.load_config()
        
        assert "ORACLE_USERNAME" in str(exc_info.value)
        assert "Default Values" in str(exc_info.value)
    
    def test_validation_error_handling(self):
        """Test validation error for invalid port"""
        # Create environment with MCP prefix for the test
        clean_env = {
            "MCP_ORACLE_HOST": "test-host",
            "MCP_ORACLE_SERVICE_NAME": "test-service", 
            "MCP_ORACLE_USERNAME": "test-user",
            "MCP_ORACLE_PASSWORD": "test-pass",
            "MCP_ORACLE_PORT": "invalid_port"
        }
        
        # Patch environment without clearing to preserve system vars
        with patch.dict(os.environ, clean_env):
            loader = EnhancedConfigLoader()
            # Use only MCP source to avoid .env interference
            loader.config_sources = [MCPConfigSource()]
            
            with pytest.raises(ValidationError) as exc_info:
                loader.load_config()
            
            assert "port" in str(exc_info.value).lower()
            assert "integer" in str(exc_info.value).lower()
    


class TestDatabaseConfig:
    """Test enhanced DatabaseConfig model"""
    
    def test_source_tracking(self):
        """Test source tracking functionality"""
        config = DatabaseConfig(
            host="test-host",
            service_name="test-service",
            username="test-user", 
            password="test-pass"
        )
        
        # Test source tracking
        config.set_source_info("host", "MCP Config")
        config.set_source_info("port", "Default Values")
        
        sources = config.get_source_info()
        assert sources["host"] == "MCP Config"
        assert sources["port"] == "Default Values"
    
    def test_warning_tracking(self):
        """Test warning tracking functionality"""
        config = DatabaseConfig(
            host="test-host",
            service_name="test-service", 
            username="test-user",
            password="test-pass"
        )
        
        # Test warning tracking
        config.add_warning("Test warning 1")
        config.add_warning("Test warning 2")
        
        warnings = config.get_warnings()
        assert len(warnings) == 2
        assert "Test warning 1" in warnings
        assert "Test warning 2" in warnings
    
    def test_dsn_property(self):
        """Test DSN property generation"""
        config = DatabaseConfig(
            host="test-host",
            port=1521,
            service_name="test-service",
            username="test-user",
            password="test-pass"
        )
        
        assert config.dsn == "test-host:1521/test-service"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])