"""
Property-based test for structured error logging
Tests Property 17: Structured Error Logging
Validates: Requirements 7.5
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import patch, MagicMock
import structlog
import os

from config import handle_configuration_error, MissingParameterError, ValidationError, ConfigurationError


class TestStructuredErrorLogging:
    """Property-based tests for structured error logging"""
    
    @given(
        parameter=st.sampled_from([
            "ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"
        ]),
        sources=st.lists(
            st.sampled_from(["default", "dotenv", "mcp_config"]),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    def test_missing_parameter_error_logging_structure(self, parameter, sources):
        """
        Feature: mcp-env-config-enhancement, Property 17: Structured Error Logging
        
        For any configuration error that occurs, the system should provide 
        structured logging with clear error messages and relevant context information.
        """
        # Create a MissingParameterError
        error = MissingParameterError(parameter, sources)
        
        # Mock the logger to capture structured log calls
        mock_logger = MagicMock()
        
        with patch('config.loader.logger', mock_logger):
            handle_configuration_error(error)
        
        # Verify structured logging was called
        assert mock_logger.error.called
        
        # Get the call arguments
        call_args = mock_logger.error.call_args
        
        # Verify the log message
        log_message = call_args[0][0]
        assert "Missing required configuration parameter" in log_message
        
        # Verify structured data was included
        log_kwargs = call_args[1]
        assert "parameter" in log_kwargs
        assert log_kwargs["parameter"] == parameter
        assert "sources_checked" in log_kwargs
        assert log_kwargs["sources_checked"] == sources
        assert "guidance" in log_kwargs
        assert "MCP config env section" in log_kwargs["guidance"]
        
        # Verify info log for help was also called
        assert mock_logger.info.called
        info_call_args = mock_logger.info.call_args
        assert "Configuration help available" in info_call_args[0][0]
    
    @given(
        parameter=st.sampled_from(["port", "connection_timeout", "query_timeout", "max_rows"]),
        value=st.text(
            min_size=1, 
            max_size=20,
            alphabet=st.characters(
                min_codepoint=32,
                max_codepoint=126,
                blacklist_characters='\n\r\t\0'
            )
        ).filter(lambda x: x.strip() and '\x00' not in x),
        reason=st.text(
            min_size=5, 
            max_size=100,
            alphabet=st.characters(
                min_codepoint=32,
                max_codepoint=126,
                blacklist_characters='\n\r\t\0'
            )
        ).filter(lambda x: x.strip() and '\x00' not in x)
    )
    def test_validation_error_logging_structure(self, parameter, value, reason):
        """
        Feature: mcp-env-config-enhancement, Property 17: Structured Error Logging
        
        For any validation error, the structured logging should include parameter,
        reason, and guidance information in a machine-readable format.
        """
        # Create a ValidationError
        error = ValidationError(parameter, value, reason)
        
        # Mock the logger to capture structured log calls
        mock_logger = MagicMock()
        
        with patch('config.loader.logger', mock_logger):
            handle_configuration_error(error)
        
        # Verify structured logging was called
        assert mock_logger.error.called
        
        # Get the call arguments
        call_args = mock_logger.error.call_args
        
        # Verify the log message
        log_message = call_args[0][0]
        assert "Configuration parameter validation failed" in log_message
        
        # Verify structured data was included
        log_kwargs = call_args[1]
        assert "parameter" in log_kwargs
        assert log_kwargs["parameter"] == parameter
        assert "reason" in log_kwargs
        assert log_kwargs["reason"] == reason
        assert "guidance" in log_kwargs
        assert "parameter format" in log_kwargs["guidance"]
        
        # Verify info log for help was also called
        assert mock_logger.info.called
    
    @given(
        error_message=st.text(
            min_size=10, 
            max_size=100,
            alphabet=st.characters(
                min_codepoint=32,
                max_codepoint=126,
                blacklist_characters='\n\r\t\0'
            )
        ).filter(lambda x: x.strip() and '\x00' not in x)
    )
    def test_generic_configuration_error_logging_structure(self, error_message):
        """
        Feature: mcp-env-config-enhancement, Property 17: Structured Error Logging
        
        For any generic configuration error, the structured logging should include
        error type, message, and guidance in a structured format.
        """
        # Create a generic ConfigurationError
        error = ConfigurationError(error_message)
        
        # Mock the logger to capture structured log calls
        mock_logger = MagicMock()
        
        with patch('config.loader.logger', mock_logger):
            handle_configuration_error(error)
        
        # Verify structured logging was called
        assert mock_logger.error.called
        
        # Get the call arguments
        call_args = mock_logger.error.call_args
        
        # Verify the log message
        log_message = call_args[0][0]
        assert "Configuration error occurred" in log_message
        
        # Verify structured data was included
        log_kwargs = call_args[1]
        assert "error_type" in log_kwargs
        assert log_kwargs["error_type"] == "ConfigurationError"
        assert "error_message" in log_kwargs
        assert log_kwargs["error_message"] == error_message
        assert "guidance" in log_kwargs
        assert "configuration parameters" in log_kwargs["guidance"]
        
        # Verify info log for help was also called
        assert mock_logger.info.called
    
    @given(
        error_type=st.sampled_from(["MissingParameterError", "ValidationError", "ConfigurationError"])
    )
    def test_all_error_types_include_help_guidance(self, error_type):
        """
        Feature: mcp-env-config-enhancement, Property 17: Structured Error Logging
        
        For any configuration error type, the logging should always include
        helpful guidance pointing to documentation.
        """
        # Create appropriate error based on type
        if error_type == "MissingParameterError":
            error = MissingParameterError("ORACLE_HOST", ["default", "dotenv"])
        elif error_type == "ValidationError":
            error = ValidationError("port", "invalid", "must be numeric")
        else:
            error = ConfigurationError("Generic configuration error")
        
        # Mock the logger to capture structured log calls
        mock_logger = MagicMock()
        
        with patch('config.loader.logger', mock_logger):
            handle_configuration_error(error)
        
        # Verify both error and info logs were called
        assert mock_logger.error.called
        assert mock_logger.info.called
        
        # Verify info log contains help guidance
        info_call_args = mock_logger.info.call_args
        info_message = info_call_args[0][0]
        assert "Configuration help available" in info_message
        assert "docs/deployment-guide.md" in info_message
    
    @given(
        parameters=st.lists(
            st.sampled_from([
                "ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"
            ]),
            min_size=1,
            max_size=4,
            unique=True
        )
    )
    def test_logging_context_preservation(self, parameters):
        """
        Feature: mcp-env-config-enhancement, Property 17: Structured Error Logging
        
        For any configuration error, the structured logging should preserve
        all relevant context information without losing data.
        """
        # Test with the first parameter from the list
        parameter = parameters[0]
        sources = ["default", "dotenv", "mcp_config"]
        
        error = MissingParameterError(parameter, sources)
        
        # Mock the logger to capture structured log calls
        mock_logger = MagicMock()
        
        with patch('config.loader.logger', mock_logger):
            handle_configuration_error(error)
        
        # Verify all context is preserved in structured format
        call_args = mock_logger.error.call_args
        log_kwargs = call_args[1]
        
        # Verify no information is lost
        assert log_kwargs["parameter"] == parameter
        assert log_kwargs["sources_checked"] == sources
        assert len(log_kwargs["sources_checked"]) == len(sources)
        
        # Verify guidance is actionable
        guidance = log_kwargs["guidance"]
        assert isinstance(guidance, str)
        assert len(guidance) > 0
        assert "MCP config" in guidance or "env section" in guidance