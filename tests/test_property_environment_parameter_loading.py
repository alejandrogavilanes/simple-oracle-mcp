"""
Property-based test for environment parameter loading
Tests Property 1: Environment Parameter Loading
Validates: Requirements 1.1
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import patch, MagicMock
import os

from config import EnhancedConfigLoader, DatabaseConfig


class TestEnvironmentParameterLoading:
    """Property-based tests for environment parameter loading"""
    
    @given(
        oracle_host=st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-')),
        oracle_port=st.integers(min_value=1521, max_value=65535),
        oracle_service=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
        oracle_username=st.from_regex(r'^[a-zA-Z][a-zA-Z0-9_]{1,29}$'),
        oracle_password=st.text(min_size=6, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_environment_parameters_loaded_successfully(self, oracle_host, oracle_port, 
                                                       oracle_service, oracle_username, oracle_password):
        """
        Feature: mcp-env-config-enhancement, Property 1: Environment Parameter Loading
        
        For any set of environment variables provided through MCP config, the Config_Loader 
        should successfully read and load all provided parameters into the configuration model.
        """
        # Create environment configuration with MCP prefix for is_available() check
        env_config = {
            "MCP_ORACLE_HOST": oracle_host,
            "MCP_ORACLE_PORT": str(oracle_port),
            "MCP_ORACLE_SERVICE_NAME": oracle_service,
            "MCP_ORACLE_USERNAME": oracle_username,
            "MCP_ORACLE_PASSWORD": oracle_password,
        }
        
        # Mock os.environ to include our MCP config
        with patch.dict(os.environ, env_config, clear=True):
            # Mock .env file as not existing
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
        
        # Verify all parameters were loaded correctly
        assert isinstance(config, DatabaseConfig)
        assert config.host == oracle_host
        assert config.port == oracle_port
        assert config.service_name == oracle_service
        assert config.username == oracle_username
        assert config.password == oracle_password
        
        # Verify source tracking shows MCP Config Environment as source
        source_info = config.get_source_info()
        assert source_info.get("host") == "MCP Config Environment"
        assert source_info.get("port") == "MCP Config Environment"
        assert source_info.get("service_name") == "MCP Config Environment"
        assert source_info.get("username") == "MCP Config Environment"
        assert source_info.get("password") == "MCP Config Environment"
    
    @given(
        config_subset=st.fixed_dictionaries({
            "MCP_ORACLE_HOST": st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-')),
            "MCP_ORACLE_SERVICE_NAME": st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
            "MCP_ORACLE_USERNAME": st.from_regex(r'^[a-zA-Z][a-zA-Z0-9_]{1,29}$'),
            "MCP_ORACLE_PASSWORD": st.text(min_size=6, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
        })
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_partial_environment_configuration_loads_available_parameters(self, config_subset):
        """
        Feature: mcp-env-config-enhancement, Property 1: Environment Parameter Loading
        
        For any subset of environment variables provided through MCP config, the Config_Loader 
        should successfully read and load all available parameters, using defaults for missing optional ones.
        """
        # Mock os.environ to include our MCP config
        with patch.dict(os.environ, config_subset, clear=True):
            # Mock .env file as not existing
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
        
        # Verify configuration was created successfully
        assert isinstance(config, DatabaseConfig)
        
        # Verify provided parameters were loaded (removing MCP_ prefix for comparison)
        assert config.host == config_subset["MCP_ORACLE_HOST"]
        assert config.service_name == config_subset["MCP_ORACLE_SERVICE_NAME"]
        assert config.username == config_subset["MCP_ORACLE_USERNAME"]
        assert config.password == config_subset["MCP_ORACLE_PASSWORD"]
        
        # Verify optional parameters use defaults
        assert config.port == 1521  # Default port
        assert config.connection_timeout == 30  # Default timeout
        assert config.query_timeout == 300  # Default query timeout
        assert config.max_rows == 1000  # Default max rows
        
        # Verify source tracking for provided parameters
        source_info = config.get_source_info()
        assert source_info.get("host") == "MCP Config Environment"
        assert source_info.get("service_name") == "MCP Config Environment"
        assert source_info.get("username") == "MCP Config Environment"
        assert source_info.get("password") == "MCP Config Environment"
        
        # Verify defaults came from Default Values
        assert source_info.get("port") == "Default Values"
        assert source_info.get("connection_timeout") == "Default Values"
        assert source_info.get("query_timeout") == "Default Values"
        assert source_info.get("max_rows") == "Default Values"
    
    @given(
        mcp_prefix_config=st.fixed_dictionaries({
            "MCP_ORACLE_HOST": st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-')),
            "MCP_ORACLE_SERVICE_NAME": st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
            "MCP_ORACLE_USERNAME": st.from_regex(r'^[a-zA-Z][a-zA-Z0-9_]{1,29}$'),
            "MCP_ORACLE_PASSWORD": st.text(min_size=6, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
        })
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mcp_prefixed_environment_parameters_loaded(self, mcp_prefix_config):
        """
        Feature: mcp-env-config-enhancement, Property 1: Environment Parameter Loading
        
        For any MCP-prefixed environment variables, the Config_Loader should successfully 
        read and load parameters with MCP_ prefix support.
        """
        # Mock os.environ to include our MCP config
        with patch.dict(os.environ, mcp_prefix_config, clear=True):
            # Mock .env file as not existing
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
        
        # Verify configuration was created successfully
        assert isinstance(config, DatabaseConfig)
        
        # Verify MCP-prefixed parameters were loaded (removing MCP_ prefix)
        assert config.host == mcp_prefix_config["MCP_ORACLE_HOST"]
        assert config.service_name == mcp_prefix_config["MCP_ORACLE_SERVICE_NAME"]
        assert config.username == mcp_prefix_config["MCP_ORACLE_USERNAME"]
        assert config.password == mcp_prefix_config["MCP_ORACLE_PASSWORD"]
        
        # Verify source tracking shows MCP Config Environment
        source_info = config.get_source_info()
        assert source_info.get("host") == "MCP Config Environment"
        assert source_info.get("service_name") == "MCP Config Environment"
        assert source_info.get("username") == "MCP Config Environment"
        assert source_info.get("password") == "MCP Config Environment"