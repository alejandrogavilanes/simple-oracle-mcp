"""
Property-based test for configuration source precedence
Tests Property 16: Configuration Source Precedence Implementation
"""

import os
import tempfile
from hypothesis import given, strategies as st
from unittest.mock import patch
import pytest

from config import (
    EnhancedConfigLoader,
    MCPConfigSource,
    DotEnvSource,
    DefaultSource
)


# Strategy for generating valid configuration parameter names
config_params = st.sampled_from([
    "ORACLE_HOST",
    "ORACLE_PORT", 
    "ORACLE_SERVICE_NAME",
    "ORACLE_USERNAME",
    "ORACLE_PASSWORD",
    "CONNECTION_TIMEOUT",
    "QUERY_TIMEOUT",
    "MAX_ROWS"
])

# Strategy for generating valid configuration values
config_values = st.text(
    min_size=1, 
    max_size=50,
    alphabet=st.characters(
        min_codepoint=32,  # Space character
        max_codepoint=126,  # Tilde character (printable ASCII)
        blacklist_characters='\n\r\t\0='  # Exclude problematic characters
    )
).filter(lambda x: x.strip() and not x.startswith(' ') and not x.endswith(' '))


class TestConfigurationSourcePrecedence:
    """Property-based tests for configuration source precedence"""
    
    @given(
        param=config_params,
        mcp_value=config_values,
        dotenv_value=config_values,
        default_value=config_values
    )
    def test_mcp_config_precedence_over_dotenv_and_defaults(
        self, param, mcp_value, dotenv_value, default_value
    ):
        """
        Property 16: Configuration Source Precedence Implementation
        For any configuration parameter that exists in multiple sources 
        (MCP config, .env, defaults), the system should follow the 
        precedence order: MCP config > .env > defaults.
        
        **Validates: Requirements 7.3**
        """
        # Create temporary .env file with dotenv value
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(f"{param}={dotenv_value}\n")
            temp_env_file = f.name
        
        try:
            # Set up MCP environment variable
            mcp_param = f"MCP_{param}"
            test_env = {mcp_param: mcp_value}
            
            with patch.dict(os.environ, test_env):
                # Create loader with custom sources
                loader = EnhancedConfigLoader()
                
                # Create custom default source with our test value
                class TestDefaultSource(DefaultSource):
                    def __init__(self, test_param, test_value):
                        super().__init__()
                        self.defaults[test_param] = test_value
                
                # Replace sources with test sources
                loader.config_sources = [
                    TestDefaultSource(param, default_value),  # Lowest precedence
                    DotEnvSource(temp_env_file),              # Medium precedence
                    MCPConfigSource()                         # Highest precedence
                ]
                
                # Get value with source tracking
                value, source = loader.get_value_with_source(param)
                
                # MCP config should always take precedence when present
                assert value == mcp_value, (
                    f"Expected MCP value '{mcp_value}' but got '{value}' "
                    f"from source '{source}'"
                )
                assert source == "MCP Config Environment", (
                    f"Expected MCP Config Environment source but got '{source}'"
                )
        
        finally:
            os.unlink(temp_env_file)
    
    @given(
        param=config_params,
        dotenv_value=config_values,
        default_value=config_values
    )
    def test_dotenv_precedence_over_defaults_when_no_mcp(
        self, param, dotenv_value, default_value
    ):
        """
        Property 16: Configuration Source Precedence Implementation
        When MCP config is not present, .env should take precedence over defaults.
        
        **Validates: Requirements 7.3**
        """
        # Create temporary .env file with dotenv value
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(f"{param}={dotenv_value}\n")
            temp_env_file = f.name
        
        try:
            # Ensure no MCP environment variable is set
            mcp_param = f"MCP_{param}"
            clean_env = {k: v for k, v in os.environ.items() if k != mcp_param and k != param}
            
            with patch.dict(os.environ, clean_env, clear=True):
                # Create loader with custom sources
                loader = EnhancedConfigLoader()
                
                # Create custom default source with our test value
                class TestDefaultSource(DefaultSource):
                    def __init__(self, test_param, test_value):
                        super().__init__()
                        self.defaults[test_param] = test_value
                
                # Replace sources with test sources (no MCP source)
                loader.config_sources = [
                    TestDefaultSource(param, default_value),  # Lowest precedence
                    DotEnvSource(temp_env_file)               # Higher precedence
                ]
                
                # Get value with source tracking
                value, source = loader.get_value_with_source(param)
                
                # .env should take precedence over defaults
                assert value == dotenv_value, (
                    f"Expected .env value '{dotenv_value}' but got '{value}' "
                    f"from source '{source}'"
                )
                assert temp_env_file in source, (
                    f"Expected .env file source but got '{source}'"
                )
        
        finally:
            os.unlink(temp_env_file)
    
    @given(
        param=config_params,
        default_value=config_values
    )
    def test_defaults_used_when_no_other_sources(self, param, default_value):
        """
        Property 16: Configuration Source Precedence Implementation
        When no MCP config or .env values are present, defaults should be used.
        
        **Validates: Requirements 7.3**
        """
        # Ensure no MCP or regular environment variables are set
        mcp_param = f"MCP_{param}"
        clean_env = {k: v for k, v in os.environ.items() 
                    if k != mcp_param and k != param}
        
        with patch.dict(os.environ, clean_env, clear=True):
            # Create loader with only default source
            loader = EnhancedConfigLoader()
            
            # Create custom default source with our test value
            class TestDefaultSource(DefaultSource):
                def __init__(self, test_param, test_value):
                    super().__init__()
                    self.defaults[test_param] = test_value
            
            # Use only default source
            loader.config_sources = [TestDefaultSource(param, default_value)]
            
            # Get value with source tracking
            value, source = loader.get_value_with_source(param)
            
            # Default should be used
            assert value == default_value, (
                f"Expected default value '{default_value}' but got '{value}' "
                f"from source '{source}'"
            )
            assert source == "Default Values", (
                f"Expected Default Values source but got '{source}'"
            )
    
    @given(
        param=config_params,
        mcp_value=config_values,
        env_value=config_values
    )
    def test_mcp_precedence_over_regular_env_vars(self, param, mcp_value, env_value):
        """
        Property 16: Configuration Source Precedence Implementation
        MCP-prefixed environment variables should take precedence over 
        regular environment variables.
        
        **Validates: Requirements 7.3**
        """
        mcp_param = f"MCP_{param}"
        test_env = {
            mcp_param: mcp_value,
            param: env_value
        }
        
        with patch.dict(os.environ, test_env):
            loader = EnhancedConfigLoader()
            loader.config_sources = [MCPConfigSource()]
            
            # Get value with source tracking
            value, source = loader.get_value_with_source(param)
            
            # MCP-prefixed value should take precedence
            assert value == mcp_value, (
                f"Expected MCP value '{mcp_value}' but got '{value}' "
                f"from source '{source}'"
            )
            assert source == "MCP Config Environment", (
                f"Expected MCP Config Environment source but got '{source}'"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])