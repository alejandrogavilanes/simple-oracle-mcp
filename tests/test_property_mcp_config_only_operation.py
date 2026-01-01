"""
Property-based test for MCP config only operation
Tests Property 2: MCP Config Only Operation
Validates: Requirements 1.2
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch
import os
import string

from config import EnhancedConfigLoader, DatabaseConfig


# Custom strategies for valid configuration values
def valid_hostname():
    """Generate valid hostnames"""
    return st.text(
        alphabet=string.ascii_lowercase + string.digits + '.-',
        min_size=5,
        max_size=50
    ).filter(
        lambda x: '.' in x and 
        not x.startswith('.') and 
        not x.endswith('.') and
        not x.startswith('-') and
        not x.endswith('-') and
        '..' not in x
    ).map(lambda x: x.replace('..', '.'))

def valid_service_name():
    """Generate valid Oracle service names"""
    return st.text(
        alphabet=string.ascii_uppercase + string.digits + '_',
        min_size=3,
        max_size=20
    )

def valid_username():
    """Generate valid database usernames"""
    return st.text(
        alphabet=string.ascii_lowercase + string.digits + '_',
        min_size=3,
        max_size=30
    ).filter(
        lambda x: x[0].isalpha() and  # Must start with a letter
        not x.startswith('_') and 
        not x.endswith('_') and
        '__' not in x  # No double underscores
    )

def valid_password():
    """Generate valid passwords"""
    return st.text(
        alphabet=string.ascii_letters + string.digits + '!@#$%^&*',
        min_size=8,
        max_size=50
    )


class TestMCPConfigOnlyOperation:
    """Property-based tests for MCP config only operation"""
    
    @given(
        oracle_host=valid_hostname(),
        oracle_port=st.integers(min_value=1521, max_value=65535),
        oracle_service=valid_service_name(),
        oracle_username=valid_username(),
        oracle_password=valid_password()
    )
    @settings(max_examples=20)
    def test_mcp_config_only_operation_without_env_file(self, oracle_host, oracle_port, 
                                                       oracle_service, oracle_username, oracle_password):
        """
        Feature: mcp-env-config-enhancement, Property 2: MCP Config Only Operation
        
        For any valid MCP configuration without a .env file present, the MCP_Server 
        should start and operate normally using only the environment parameters from the MCP config.
        """
        # Create MCP environment configuration with MCP prefix for is_available() check
        mcp_config = {
            "ORACLE_HOST": oracle_host,
            "ORACLE_PORT": str(oracle_port),
            "ORACLE_SERVICE_NAME": oracle_service,
            "ORACLE_USERNAME": oracle_username,
            "ORACLE_PASSWORD": oracle_password,
            # Add MCP prefix to make MCPConfigSource available
            "MCP_ORACLE_HOST": oracle_host,
        }
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', mcp_config):
            def mock_getenv_side_effect(key, default=None):
                return mcp_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            # Ensure .env file is not available
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
        
        # Verify configuration was created successfully
        assert isinstance(config, DatabaseConfig)
        assert config.host == oracle_host
        assert config.port == oracle_port
        assert config.service_name == oracle_service
        assert config.username == oracle_username
        assert config.password == oracle_password
        
        # Verify all parameters came from MCP config environment
        source_info = config.get_source_info()
        assert source_info.get("host") == "MCP Config Environment"
        assert source_info.get("port") == "MCP Config Environment"
        assert source_info.get("service_name") == "MCP Config Environment"
        assert source_info.get("username") == "MCP Config Environment"
        assert source_info.get("password") == "MCP Config Environment"
        
        # Verify no .env file deprecation warnings
        warnings = config.get_warnings()
        env_warnings = [w for w in warnings if ".env" in w.lower()]
        assert len(env_warnings) == 0, "Should not have .env deprecation warnings when no .env file is used"
    
    @given(
        config_params=st.fixed_dictionaries({
            "ORACLE_HOST": valid_hostname(),
            "ORACLE_SERVICE_NAME": valid_service_name(),
            "ORACLE_USERNAME": valid_username(),
            "ORACLE_PASSWORD": valid_password()
        })
    )
    @settings(max_examples=20)
    def test_mcp_config_operates_independently_of_env_file(self, config_params):
        """
        Feature: mcp-env-config-enhancement, Property 2: MCP Config Only Operation
        
        For any MCP configuration, the system should operate independently of .env files,
        using only MCP environment parameters when .env file is not present.
        """
        # Add MCP prefix to make MCPConfigSource available
        config_params["MCP_ORACLE_HOST"] = config_params["ORACLE_HOST"]
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', config_params):
            def mock_getenv_side_effect(key, default=None):
                return config_params.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            # Mock .env file as not existing
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
        
        # Verify configuration was created successfully
        assert isinstance(config, DatabaseConfig)
        
        # Verify provided parameters were loaded from MCP config
        source_info = config.get_source_info()
        
        # Check that all provided parameters came from MCP Config Environment
        assert source_info.get("host") == "MCP Config Environment"
        assert source_info.get("service_name") == "MCP Config Environment"
        assert source_info.get("username") == "MCP Config Environment"
        assert source_info.get("password") == "MCP Config Environment"
        
        # Verify no .env file warnings since no .env file is present
        warnings = config.get_warnings()
        env_warnings = [w for w in warnings if ".env" in w.lower()]
        assert len(env_warnings) == 0, "Should not have .env warnings when no .env file exists"
        
        # Verify provided parameters were loaded from MCP config
        source_info = config.get_source_info()
        
        # Check that all provided parameters came from MCP Config Environment
        field_mapping = {
            "ORACLE_HOST": "host",
            "ORACLE_PORT": "port", 
            "ORACLE_SERVICE_NAME": "service_name",
            "ORACLE_USERNAME": "username",
            "ORACLE_PASSWORD": "password",
            "CONNECTION_TIMEOUT": "connection_timeout",
            "QUERY_TIMEOUT": "query_timeout",
            "MAX_ROWS": "max_rows"
        }
        
        for param_key in config_params.keys():
            field_name = field_mapping.get(param_key)
            if field_name:
                # Parameters provided via MCP config should be sourced from MCP Config Environment
                assert source_info.get(field_name) == "MCP Config Environment", \
                    f"Parameter {field_name} should come from MCP Config Environment"
        
        # Verify no .env file warnings since no .env file is present
        warnings = config.get_warnings()
        env_warnings = [w for w in warnings if ".env" in w.lower()]
        assert len(env_warnings) == 0, "Should not have .env warnings when no .env file exists"
    
    @given(
        mcp_host=valid_hostname(),
        mcp_service=valid_service_name(),
        mcp_username=valid_username(),
        mcp_password=valid_password()
    )
    @settings(max_examples=20)
    def test_mcp_config_environment_source_identification(self, mcp_host, mcp_service, 
                                                         mcp_username, mcp_password):
        """
        Feature: mcp-env-config-enhancement, Property 2: MCP Config Only Operation
        
        For any MCP configuration parameters, the system should correctly identify 
        the source as "MCP Config Environment" when operating without .env files.
        """
        # Create MCP environment configuration with MCP prefix for is_available() check
        mcp_config = {
            "ORACLE_HOST": mcp_host,
            "ORACLE_SERVICE_NAME": mcp_service,
            "ORACLE_USERNAME": mcp_username,
            "ORACLE_PASSWORD": mcp_password,
            # Add MCP prefix to make MCPConfigSource available
            "MCP_ORACLE_HOST": mcp_host,
        }
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', mcp_config):
            def mock_getenv_side_effect(key, default=None):
                return mcp_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            # Ensure .env file is not available
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
        
        # Verify configuration was created successfully
        assert isinstance(config, DatabaseConfig)
        
        # Verify source identification is correct
        source_info = config.get_source_info()
        
        # All provided parameters should be identified as coming from MCP Config Environment
        assert source_info.get("host") == "MCP Config Environment"
        assert source_info.get("service_name") == "MCP Config Environment"
        assert source_info.get("username") == "MCP Config Environment"
        assert source_info.get("password") == "MCP Config Environment"
        
        # Default parameters should come from Default Values
        assert source_info.get("port") == "Default Values"
        assert source_info.get("connection_timeout") == "Default Values"
        assert source_info.get("query_timeout") == "Default Values"
        assert source_info.get("max_rows") == "Default Values"
        
        # Verify the loader correctly identifies that no .env values are being used
        assert not loader.has_dotenv_values(), "Should not detect .env values when no .env file exists"
    
    @given(
        complete_config=st.fixed_dictionaries({
            "ORACLE_HOST": valid_hostname(),
            "ORACLE_PORT": st.integers(min_value=1521, max_value=65535).map(str),
            "ORACLE_SERVICE_NAME": valid_service_name(),
            "ORACLE_USERNAME": valid_username(),
            "ORACLE_PASSWORD": valid_password(),
            "CONNECTION_TIMEOUT": st.integers(min_value=10, max_value=300).map(str),
            "QUERY_TIMEOUT": st.integers(min_value=60, max_value=3600).map(str),
            "MAX_ROWS": st.integers(min_value=100, max_value=10000).map(str)
        })
    )
    @settings(max_examples=20)
    def test_complete_mcp_config_operation_without_env_file(self, complete_config):
        """
        Feature: mcp-env-config-enhancement, Property 2: MCP Config Only Operation
        
        For any complete MCP configuration with all parameters, the system should 
        operate entirely from MCP config without requiring any .env file.
        """
        # Add MCP prefix to make MCPConfigSource available
        complete_config["MCP_ORACLE_HOST"] = complete_config["ORACLE_HOST"]
        
        # Mock the configuration sources to return our test data
        with patch('config.sources.os.getenv') as mock_getenv, \
             patch('config.sources.os.environ', complete_config):
            def mock_getenv_side_effect(key, default=None):
                return complete_config.get(key, default)
            mock_getenv.side_effect = mock_getenv_side_effect
            
            # Ensure .env file is not available
            with patch('config.sources.os.path.exists', return_value=False):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
        
        # Verify configuration was created successfully
        assert isinstance(config, DatabaseConfig)
        
        # Verify all parameters match the provided MCP config
        assert config.host == complete_config["ORACLE_HOST"]
        assert config.port == int(complete_config["ORACLE_PORT"])
        assert config.service_name == complete_config["ORACLE_SERVICE_NAME"]
        assert config.username == complete_config["ORACLE_USERNAME"]
        assert config.password == complete_config["ORACLE_PASSWORD"]
        assert config.connection_timeout == int(complete_config["CONNECTION_TIMEOUT"])
        assert config.query_timeout == int(complete_config["QUERY_TIMEOUT"])
        assert config.max_rows == int(complete_config["MAX_ROWS"])
        
        # Verify all parameters came from MCP Config Environment
        source_info = config.get_source_info()
        expected_mcp_fields = ["host", "port", "service_name", "username", "password", 
                              "connection_timeout", "query_timeout", "max_rows"]
        
        for field in expected_mcp_fields:
            assert source_info.get(field) == "MCP Config Environment", \
                f"Field {field} should come from MCP Config Environment"
        
        # Verify no .env file dependencies
        assert not loader.has_dotenv_values(), "Should not depend on .env file"
        
        # Verify no .env deprecation warnings
        warnings = config.get_warnings()
        env_warnings = [w for w in warnings if ".env" in w.lower()]
        assert len(env_warnings) == 0, "Should not have .env warnings when operating MCP-only"