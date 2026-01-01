"""
Property-based test for fallback configuration behavior
Tests Property 9: Fallback Configuration Behavior
Validates: Requirements 3.4
"""

import os
import tempfile
from hypothesis import given, strategies as st, settings
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


class TestFallbackConfigurationBehavior:
    """Property-based tests for fallback configuration behavior"""
    
    @given(
        mcp_params=st.lists(
            st.tuples(config_params, config_values),
            min_size=1,
            max_size=4,
            unique_by=lambda x: x[0]  # Unique parameter names
        ),
        dotenv_params=st.lists(
            st.tuples(config_params, config_values),
            min_size=1,
            max_size=4,
            unique_by=lambda x: x[0]  # Unique parameter names
        ),
        default_params=st.lists(
            st.tuples(config_params, config_values),
            min_size=1,
            max_size=4,
            unique_by=lambda x: x[0]  # Unique parameter names
        )
    )
    @settings(max_examples=10)
    def test_partial_configuration_fallback_behavior(
        self, mcp_params, dotenv_params, default_params
    ):
        """
        Property 9: Fallback Configuration Behavior
        For any configuration where MCP config provides some parameters and .env file 
        provides others, the Config_Loader should use MCP config values where available 
        and fall back to .env file values for missing parameters.
        
        **Validates: Requirements 3.4**
        """
        # Convert parameter lists to dictionaries
        mcp_config = dict(mcp_params)
        dotenv_config = dict(dotenv_params)
        default_config = dict(default_params)
        
        # Create temporary .env file with dotenv values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            for param, value in dotenv_config.items():
                f.write(f"{param}={value}\n")
            temp_env_file = f.name
        
        try:
            # Set up MCP environment variables
            mcp_env = {}
            for param, value in mcp_config.items():
                mcp_env[f"MCP_{param}"] = value
            
            with patch.dict(os.environ, mcp_env):
                # Create loader with custom sources
                loader = EnhancedConfigLoader()
                
                # Create custom default source with our test values
                class TestDefaultSource(DefaultSource):
                    def __init__(self, test_defaults):
                        super().__init__()
                        self.defaults.update(test_defaults)
                
                # Replace sources with test sources
                loader.config_sources = [
                    TestDefaultSource(default_config),    # Lowest precedence
                    DotEnvSource(temp_env_file),          # Medium precedence
                    MCPConfigSource()                     # Highest precedence
                ]
                
                # Test fallback behavior for each parameter
                all_params = set(mcp_config.keys()) | set(dotenv_config.keys()) | set(default_config.keys())
                
                for param in all_params:
                    value, source = loader.get_value_with_source(param)
                    
                    # Determine expected value based on precedence
                    if param in mcp_config:
                        expected_value = mcp_config[param]
                        expected_source = "MCP Config Environment"
                    elif param in dotenv_config:
                        expected_value = dotenv_config[param]
                        expected_source = f".env file ({temp_env_file})"
                    elif param in default_config:
                        expected_value = default_config[param]
                        expected_source = "Default Values"
                    else:
                        expected_value = None
                        expected_source = None
                    
                    if expected_value is not None:
                        assert value == expected_value, (
                            f"Parameter {param}: expected '{expected_value}' from {expected_source}, "
                            f"but got '{value}' from '{source}'"
                        )
                        assert source == expected_source, (
                            f"Parameter {param}: expected source '{expected_source}', "
                            f"but got '{source}'"
                        )
                    else:
                        assert value is None, (
                            f"Parameter {param}: expected None but got '{value}' from '{source}'"
                        )
        
        finally:
            os.unlink(temp_env_file)
    
    @given(
        mcp_param=config_params,
        mcp_value=config_values,
        dotenv_param=config_params,
        dotenv_value=config_values,
        default_param=config_params,
        default_value=config_values
    )
    def test_single_parameter_fallback_precedence(
        self, mcp_param, mcp_value, dotenv_param, dotenv_value, default_param, default_value
    ):
        """
        Property 9: Fallback Configuration Behavior
        For any single parameter, the system should use the highest precedence source 
        available and fall back to lower precedence sources when higher ones are unavailable.
        
        **Validates: Requirements 3.4**
        """
        # Test parameter that exists in all sources
        test_param = "ORACLE_HOST"
        
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(f"{test_param}={dotenv_value}\n")
            temp_env_file = f.name
        
        try:
            # Set up MCP environment variable
            mcp_env = {f"MCP_{test_param}": mcp_value}
            
            with patch.dict(os.environ, mcp_env):
                # Create loader with custom sources
                loader = EnhancedConfigLoader()
                
                # Create custom default source
                class TestDefaultSource(DefaultSource):
                    def __init__(self, test_value):
                        super().__init__()
                        self.defaults[test_param] = test_value
                
                # Test with all sources available
                loader.config_sources = [
                    TestDefaultSource(default_value),     # Lowest precedence
                    DotEnvSource(temp_env_file),          # Medium precedence
                    MCPConfigSource()                     # Highest precedence
                ]
                
                value, source = loader.get_value_with_source(test_param)
                
                # Should use MCP config (highest precedence)
                assert value == mcp_value, (
                    f"Expected MCP value '{mcp_value}' but got '{value}'"
                )
                assert source == "MCP Config Environment", (
                    f"Expected MCP Config Environment source but got '{source}'"
                )
                
                # Test with only .env and defaults (no MCP)
                clean_env = {k: v for k, v in os.environ.items() 
                           if not k.startswith("MCP_") and k != test_param}
                
                with patch.dict(os.environ, clean_env, clear=True):
                    loader.config_sources = [
                        TestDefaultSource(default_value),     # Lowest precedence
                        DotEnvSource(temp_env_file)           # Higher precedence
                    ]
                    
                    value, source = loader.get_value_with_source(test_param)
                    
                    # Should use .env file (higher precedence than defaults)
                    assert value == dotenv_value, (
                        f"Expected .env value '{dotenv_value}' but got '{value}'"
                    )
                    assert temp_env_file in source, (
                        f"Expected .env file source but got '{source}'"
                    )
                    
                    # Test with only defaults
                    loader.config_sources = [TestDefaultSource(default_value)]
                    
                    value, source = loader.get_value_with_source(test_param)
                    
                    # Should use default value
                    assert value == default_value, (
                        f"Expected default value '{default_value}' but got '{value}'"
                    )
                    assert source == "Default Values", (
                        f"Expected Default Values source but got '{source}'"
                    )
        
        finally:
            os.unlink(temp_env_file)
    
    @given(
        required_params=st.lists(
            st.tuples(
                st.sampled_from(["ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"]),
                config_values
            ),
            min_size=2,
            max_size=4,
            unique_by=lambda x: x[0]
        ),
        optional_params=st.lists(
            st.tuples(
                st.sampled_from(["ORACLE_PORT", "CONNECTION_TIMEOUT", "QUERY_TIMEOUT", "MAX_ROWS"]),
                config_values
            ),
            min_size=1,
            max_size=4,
            unique_by=lambda x: x[0]
        )
    )
    @settings(max_examples=5)
    def test_mixed_source_configuration_fallback(self, required_params, optional_params):
        """
        Property 9: Fallback Configuration Behavior
        For any configuration with required parameters from one source and optional 
        parameters from another source, the system should correctly combine values 
        from multiple sources using fallback behavior.
        
        **Validates: Requirements 3.4**
        """
        required_config = dict(required_params)
        optional_config = dict(optional_params)
        
        # Put required params in MCP config and optional params in .env file
        mcp_env = {}
        for param, value in required_config.items():
            mcp_env[f"MCP_{param}"] = value
        
        # Create temporary .env file with optional params
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            for param, value in optional_config.items():
                f.write(f"{param}={value}\n")
            temp_env_file = f.name
        
        try:
            with patch.dict(os.environ, mcp_env):
                # Create loader
                loader = EnhancedConfigLoader()
                loader.config_sources = [
                    DefaultSource(),                      # Lowest precedence
                    DotEnvSource(temp_env_file),          # Medium precedence
                    MCPConfigSource()                     # Highest precedence
                ]
                
                # Test that required params come from MCP config
                for param, expected_value in required_config.items():
                    value, source = loader.get_value_with_source(param)
                    
                    assert value == expected_value, (
                        f"Required param {param}: expected '{expected_value}' but got '{value}'"
                    )
                    assert source == "MCP Config Environment", (
                        f"Required param {param}: expected MCP source but got '{source}'"
                    )
                
                # Test that optional params come from .env file
                for param, expected_value in optional_config.items():
                    value, source = loader.get_value_with_source(param)
                    
                    assert value == expected_value, (
                        f"Optional param {param}: expected '{expected_value}' but got '{value}'"
                    )
                    assert temp_env_file in source, (
                        f"Optional param {param}: expected .env source but got '{source}'"
                    )
        
        finally:
            os.unlink(temp_env_file)
    
    @given(
        available_param=config_params,
        available_value=config_values,
        missing_param=config_params
    )
    def test_fallback_to_none_when_no_sources_available(self, available_param, available_value, missing_param):
        """
        Property 9: Fallback Configuration Behavior
        For any parameter that is not available in any source, the system should 
        return None and no source, demonstrating proper fallback behavior.
        
        **Validates: Requirements 3.4**
        """
        # Ensure we have different parameters
        if available_param == missing_param:
            missing_param = "ORACLE_HOST" if available_param != "ORACLE_HOST" else "ORACLE_PORT"
        
        # Create loader with only one parameter available
        mcp_env = {f"MCP_{available_param}": available_value}
        
        with patch.dict(os.environ, mcp_env):
            loader = EnhancedConfigLoader()
            loader.config_sources = [MCPConfigSource()]
            
            # Test available parameter
            value, source = loader.get_value_with_source(available_param)
            assert value == available_value, (
                f"Available param {available_param}: expected '{available_value}' but got '{value}'"
            )
            assert source == "MCP Config Environment", (
                f"Available param {available_param}: expected MCP source but got '{source}'"
            )
            
            # Test missing parameter
            value, source = loader.get_value_with_source(missing_param)
            assert value is None, (
                f"Missing param {missing_param}: expected None but got '{value}'"
            )
            assert source is None, (
                f"Missing param {missing_param}: expected None source but got '{source}'"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])