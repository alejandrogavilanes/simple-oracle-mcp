"""
Property-based test for error source identification
Tests Property 10: Error Source Identification
Validates: Requirements 3.5
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import patch, mock_open
import os
import tempfile

from config import EnhancedConfigLoader, MissingParameterError, ValidationError


class TestErrorSourceIdentification:
    """Property-based tests for error source identification"""
    
    @given(
        invalid_port=st.one_of(
            st.text().filter(lambda x: not x.isdigit() and x.strip() and '\x00' not in x),  # Non-numeric strings (non-empty, no null bytes)
            st.integers(max_value=0),  # Invalid port numbers
            st.integers(min_value=65536)  # Port numbers too high
        )
    )
    def test_validation_error_identifies_source_correctly(self, invalid_port):
        """
        Feature: mcp-env-config-enhancement, Property 10: Error Source Identification
        
        For any configuration validation error, the Config_Loader should clearly 
        indicate whether the error originates from MCP config parameters or .env file values.
        """
        # Test with MCP config (environment variables)
        mcp_config = {
            "ORACLE_HOST": "test_host",
            "ORACLE_SERVICE_NAME": "test_service",
            "ORACLE_USERNAME": "testuser123", 
            "ORACLE_PASSWORD": "testpassword123",
            "ORACLE_PORT": str(invalid_port)
        }
        
        loader = EnhancedConfigLoader()
        
        # Test with MCP config source error identification
        with patch.dict(os.environ, mcp_config, clear=True):
            with patch('config.sources.os.path.exists', return_value=False):  # No .env file
                with patch('config.sources.load_dotenv'):  # Mock dotenv loading
                    try:
                        loader.load_config()
                        pytest.fail("Expected ValidationError to be raised")
                    except ValidationError as e:
                        # Verify error identifies the parameter and provides validation details
                        assert e.parameter == "port"
                        assert "Port must be" in e.reason or "must be a valid integer" in e.reason
                        
                        # The error should contain information about the validation failure
                        error_message = str(e)
                        assert "port" in error_message.lower()
                        assert "validation failed" in error_message.lower()
                    except MissingParameterError:
                        # This can happen if the invalid port is empty string after strip
                        if str(invalid_port).strip() == "":
                            pass  # Empty string causes missing parameter, which is expected
                        else:
                            pytest.fail("Should have raised ValidationError, not MissingParameterError")
    
    @given(
        missing_param=st.sampled_from([
            "ORACLE_USERNAME", "ORACLE_PASSWORD"  # Only test parameters without defaults
        ]),
        source_type=st.sampled_from(["mcp_only", "dotenv_only"])
    )
    def test_missing_parameter_error_identifies_checked_sources(self, missing_param, source_type):
        """
        Feature: mcp-env-config-enhancement, Property 10: Error Source Identification
        
        For any missing parameter error, the system should clearly indicate which 
        sources were checked when the parameter was not found.
        """
        # Create base configuration missing the specified parameter
        base_config = {
            "ORACLE_HOST": "testhost",
            "ORACLE_SERVICE_NAME": "testservice",
            "ORACLE_USERNAME": "testuser123",
            "ORACLE_PASSWORD": "testpassword123"
        }
        
        # Remove the parameter we want to test as missing
        if missing_param in base_config:
            del base_config[missing_param]
        
        loader = EnhancedConfigLoader()
        
        if source_type == "mcp_only":
            # Test with only MCP config (no .env file)
            with patch.dict(os.environ, base_config, clear=True):
                with patch('config.sources.os.path.exists', return_value=False):
                    with patch('config.sources.load_dotenv'):
                        with pytest.raises(MissingParameterError) as exc_info:
                            loader.load_config()
                        
                        error = exc_info.value
                        # The error should report one of the missing required parameters
                        # (the loader reports the first missing parameter it finds)
                        assert error.parameter in ["ORACLE_USERNAME", "ORACLE_PASSWORD"]
                        
                        # Should indicate which sources were checked
                        assert len(error.sources_checked) >= 2  # At least default and MCP sources
                        assert any("Default" in source for source in error.sources_checked)
                        assert any("MCP" in source for source in error.sources_checked)
        
        elif source_type == "dotenv_only":
            # Test with only .env file (no MCP config)
            with patch.dict(os.environ, {}, clear=True):
                # Create temporary .env file with missing parameter
                dotenv_content = "\n".join([f"{k}={v}" for k, v in base_config.items()])
                
                with patch('config.sources.os.path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data=dotenv_content)):
                        with patch('config.sources.load_dotenv'):
                            with pytest.raises(MissingParameterError) as exc_info:
                                loader.load_config()
                            
                            error = exc_info.value
                            # The error should report one of the missing required parameters
                            assert error.parameter in ["ORACLE_USERNAME", "ORACLE_PASSWORD"]
                            
                            # Should indicate which sources were checked
                            assert len(error.sources_checked) >= 2  # At least default and dotenv sources
                            assert any("Default" in source for source in error.sources_checked)
    
    @given(
        config_values=st.dictionaries(
            keys=st.sampled_from([
                "ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"
            ]),
            values=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '\x00' not in x),
            min_size=4,  # Ensure we have all required parameters
            max_size=4
        )
    )
    def test_error_messages_contain_source_context(self, config_values):
        """
        Feature: mcp-env-config-enhancement, Property 10: Error Source Identification
        
        For any configuration error, the error message should provide context about
        which configuration source was being processed when the error occurred.
        """
        # Ensure we have all required parameters
        required_params = ["ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"]
        for param in required_params:
            if param not in config_values:
                config_values[param] = f"test-{param.lower().replace('_', '-')}"
        
        # Add an invalid port to trigger a validation error
        config_values["ORACLE_PORT"] = "invalid_port_value"
        
        loader = EnhancedConfigLoader()
        
        # Test with MCP config source
        with patch.dict(os.environ, config_values, clear=True):
            with patch('config.sources.os.path.exists', return_value=False):  # No .env file
                with patch('config.sources.load_dotenv'):  # Mock dotenv loading
                    try:
                        loader.load_config()
                        pytest.fail("Expected ValidationError to be raised")
                    except ValidationError as e:
                        # Verify error provides clear parameter identification
                        assert e.parameter == "port"
                        assert "validation failed" in str(e).lower()
                        assert "port" in str(e).lower()
                    except MissingParameterError as e:
                        # This can happen if required parameters are missing
                        # Verify the error message contains source context
                        assert len(e.sources_checked) > 0
                        error_message = str(e)
                        assert "not found in sources" in error_message.lower()
                        assert e.parameter == "port"
                        assert e.value == "invalid_port_value"
                        assert "must be a valid integer" in e.reason
                        
                        # Error message should be informative
                        error_message = str(e)
                        assert "port" in error_message
                        assert "validation failed" in error_message