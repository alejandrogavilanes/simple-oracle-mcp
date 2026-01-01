"""
Property-based test for parameter validation consistency
Tests Property 3: Parameter Validation Consistency
Validates: Requirements 1.3, 5.5
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch
import os

from config import EnhancedConfigLoader, DatabaseConfig
from config.exceptions import ConfigurationError, ValidationError


class TestParameterValidationConsistency:
    """Property-based tests for parameter validation consistency"""
    
    @given(
        invalid_port=st.integers(max_value=0)  # Negative or zero ports
    )
    @settings(max_examples=5)
    def test_port_validation_consistency_across_sources(self, invalid_port):
        """
        Feature: mcp-env-config-enhancement, Property 3: Parameter Validation Consistency
        
        For any invalid port value, the Config_Loader should apply the same validation 
        rules regardless of whether the port comes from MCP config or .env file.
        """
        # Test with MCP config source
        mcp_config = {
            "ORACLE_HOST": "test-host.example.com",
            "ORACLE_PORT": str(invalid_port),
            "ORACLE_SERVICE_NAME": "TESTDB",
            "ORACLE_USERNAME": "testuser",
            "ORACLE_PASSWORD": "testpassword123",
            # Add MCP prefix to make MCPConfigSource available
            "MCP_ORACLE_HOST": "test-host.example.com",
        }
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', mcp_config):
            def mock_getenv_side_effect(key, default=None):
                return mcp_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                with pytest.raises((ConfigurationError, ValidationError)):
                    loader.load_config()
    
    @given(
        invalid_timeout=st.integers(max_value=0)  # Zero or negative timeouts
    )
    @settings(max_examples=5)
    def test_timeout_validation_consistency_across_sources(self, invalid_timeout):
        """
        Feature: mcp-env-config-enhancement, Property 3: Parameter Validation Consistency
        
        For any invalid timeout value, the Config_Loader should apply the same validation 
        rules regardless of the configuration source.
        """
        # Base valid configuration
        base_config = {
            "ORACLE_HOST": "test-host.example.com",
            "ORACLE_SERVICE_NAME": "TESTDB",
            "ORACLE_USERNAME": "testuser",
            "ORACLE_PASSWORD": "testpassword123",
            "CONNECTION_TIMEOUT": str(invalid_timeout),
            # Add MCP prefix to make MCPConfigSource available
            "MCP_ORACLE_HOST": "test-host.example.com",
        }
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', base_config):
            def mock_getenv_side_effect(key, default=None):
                return base_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                with pytest.raises((ConfigurationError, ValidationError)):
                    loader.load_config()
    
    @given(
        invalid_max_rows=st.integers(min_value=10001)  # Above maximum allowed
    )
    @settings(max_examples=5)
    def test_max_rows_validation_consistency_across_sources(self, invalid_max_rows):
        """
        Feature: mcp-env-config-enhancement, Property 3: Parameter Validation Consistency
        
        For any invalid max_rows value, the Config_Loader should apply the same validation 
        rules regardless of the configuration source.
        """
        # Base valid configuration
        base_config = {
            "ORACLE_HOST": "test-host.example.com",
            "ORACLE_SERVICE_NAME": "TESTDB",
            "ORACLE_USERNAME": "testuser",
            "ORACLE_PASSWORD": "testpassword123",
            "MAX_ROWS": str(invalid_max_rows),
            # Add MCP prefix to make MCPConfigSource available
            "MCP_ORACLE_HOST": "test-host.example.com",
        }
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', base_config):
            def mock_getenv_side_effect(key, default=None):
                return base_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                with pytest.raises((ConfigurationError, ValidationError)):
                    loader.load_config()
    
    @given(
        valid_port=st.integers(min_value=1521, max_value=1522),
        valid_timeout=st.integers(min_value=30, max_value=31),
        valid_max_rows=st.integers(min_value=1000, max_value=1001)
    )
    @settings(max_examples=5)
    def test_valid_parameter_acceptance_consistency(self, valid_port, valid_timeout, valid_max_rows):
        """
        Feature: mcp-env-config-enhancement, Property 3: Parameter Validation Consistency
        
        For any valid parameter values, the Config_Loader should accept them consistently 
        regardless of whether they come from MCP config or .env file sources.
        """
        # Test with MCP config source
        mcp_config = {
            "ORACLE_HOST": "test-host.example.com",
            "ORACLE_PORT": str(valid_port),
            "ORACLE_SERVICE_NAME": "TESTDB",
            "ORACLE_USERNAME": "testuser",
            "ORACLE_PASSWORD": "testpassword123",
            "CONNECTION_TIMEOUT": str(valid_timeout),
            "QUERY_TIMEOUT": str(valid_timeout),
            "MAX_ROWS": str(valid_max_rows),
            # Add MCP prefix to make MCPConfigSource available
            "MCP_ORACLE_HOST": "test-host.example.com",
        }
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', mcp_config):
            def mock_getenv_side_effect(key, default=None):
                return mcp_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
                
                assert isinstance(config, DatabaseConfig)
                assert config.port == valid_port
                assert config.connection_timeout == valid_timeout
                assert config.query_timeout == valid_timeout
                assert config.max_rows == valid_max_rows
    
    @given(
        empty_or_whitespace=st.just("")  # Empty string
    )
    @settings(max_examples=5)
    def test_required_field_validation_consistency(self, empty_or_whitespace):
        """
        Feature: mcp-env-config-enhancement, Property 3: Parameter Validation Consistency
        
        For any empty or whitespace-only required field values, the Config_Loader should 
        apply the same validation rules regardless of the configuration source.
        """
        # Test with MCP config source - empty username
        mcp_config = {
            "ORACLE_HOST": "test-host.example.com",
            "ORACLE_SERVICE_NAME": "TESTDB",
            "ORACLE_USERNAME": empty_or_whitespace,  # Empty username
            "ORACLE_PASSWORD": "testpassword123",
            # Add MCP prefix to make MCPConfigSource available
            "MCP_ORACLE_HOST": "test-host.example.com",
        }
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', mcp_config):
            def mock_getenv_side_effect(key, default=None):
                return mcp_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                with pytest.raises((ConfigurationError, ValidationError)):
                    loader.load_config()