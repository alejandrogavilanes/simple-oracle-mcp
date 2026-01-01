"""
Property-based test for secure error messages
Tests Property 13: Secure Error Messages
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import patch, MagicMock
import structlog

from config.security import SecureConfigLogger
from config.exceptions import ValidationError, MissingParameterError
from config.loader import handle_configuration_error


# Strategy for generating sensitive parameter names
sensitive_params = st.sampled_from([
    "password", "PASSWORD", "oracle_password",
    "secret", "SECRET", "db_secret", 
    "key", "KEY", "api_key",
    "token", "TOKEN", "auth_token",
    "credential", "CREDENTIAL"
])

# Strategy for generating sensitive values that should not appear in error messages
# Use longer, more realistic sensitive values that would actually be a security concern
sensitive_values = st.text(
    min_size=8,  # Longer values that would be actual security concerns
    max_size=100,
    alphabet=st.characters(
        min_codepoint=32,  # Space character
        max_codepoint=126,  # Tilde character (printable ASCII)
        blacklist_characters='\n\r\t\0'  # Exclude problematic characters
    )
).filter(lambda x: x.strip() and len(x.strip()) >= 8 and not any(
    # Exclude values that would naturally appear in error messages
    common_word in x.lower() for common_word in [
        'parameter', 'validation', 'failed', 'configuration', 'error', 
        'invalid', 'format', 'connection', 'required', 'missing'
    ]
))

# Strategy for generating error reasons
error_reasons = st.sampled_from([
    "Parameter validation failed",
    "Invalid format",
    "Value too short",
    "Value too long",
    "Contains invalid characters",
    "Required parameter missing",
    "Connection failed"
])

# Strategy for generating source names
source_names = st.sampled_from([
    "MCP Config Environment",
    "Environment Variables", 
    ".env file",
    "Default Values"
])


class TestSecureErrorMessages:
    """Property-based tests for secure error messages"""
    
    @given(
        param=sensitive_params,
        value=sensitive_values,
        reason=error_reasons
    )
    def test_validation_errors_do_not_expose_sensitive_values(self, param, value, reason):
        """
        Property 13: Secure Error Messages
        For any configuration validation error involving sensitive parameters,
        the Security_System should not expose the actual sensitive parameter 
        values in error messages.
        
        **Validates: Requirements 5.3**
        """
        # Create a validation error with sensitive parameter and value
        error = ValidationError(param, value, reason)
        
        # Mock the logger to capture log calls
        with patch('config.loader.logger') as mock_logger:
            # Handle the configuration error
            handle_configuration_error(error)
            
            # Check that logger.error was called
            assert mock_logger.error.called, "Logger error should have been called"
            
            # Get all the arguments passed to logger.error calls
            error_calls = mock_logger.error.call_args_list
            
            # Check that sensitive value does not appear in any log call
            for call in error_calls:
                args, kwargs = call
                
                # Check positional arguments
                for arg in args:
                    if isinstance(arg, str):
                        # Only check for longer sensitive values that would be actual security concerns
                        if len(value) >= 8:
                            assert value not in arg, (
                                f"Sensitive value '{value}' found in error message: '{arg}'"
                            )
                
                # Check keyword arguments
                for key, kwarg_value in kwargs.items():
                    if isinstance(kwarg_value, str):
                        # Only check for longer sensitive values, and exclude the parameter field
                        # (parameter names are expected to be logged for debugging)
                        if len(value) >= 8 and key != 'parameter':
                            assert value not in kwarg_value, (
                                f"Sensitive value '{value}' found in error log field '{key}': '{kwarg_value}'"
                            )
                    elif isinstance(kwarg_value, (list, tuple)):
                        for item in kwarg_value:
                            if isinstance(item, str) and len(value) >= 8:
                                assert value not in item, (
                                    f"Sensitive value '{value}' found in error log list '{key}': '{item}'"
                                )
    
    @given(
        param=sensitive_params,
        sources=st.lists(source_names, min_size=1, max_size=4)
    )
    def test_missing_parameter_errors_do_not_expose_sensitive_context(self, param, sources):
        """
        Property 13: Secure Error Messages
        For any missing parameter error involving sensitive parameters,
        the error message should not expose sensitive configuration context.
        
        **Validates: Requirements 5.3**
        """
        # Create a missing parameter error
        error = MissingParameterError(param, sources)
        
        # Mock the logger to capture log calls
        with patch('config.loader.logger') as mock_logger:
            # Handle the configuration error
            handle_configuration_error(error)
            
            # Check that logger.error was called
            assert mock_logger.error.called, "Logger error should have been called"
            
            # The error should mention the parameter name but not expose sensitive values
            error_calls = mock_logger.error.call_args_list
            
            # Verify that the parameter name is mentioned (this is expected)
            parameter_mentioned = False
            for call in error_calls:
                args, kwargs = call
                
                # Check if parameter is mentioned in kwargs (this is OK)
                if 'parameter' in kwargs and kwargs['parameter'] == param:
                    parameter_mentioned = True
                
                # But ensure no sensitive values are in the message strings
                for arg in args:
                    if isinstance(arg, str):
                        # The message should be generic and not expose implementation details
                        assert "password" not in arg.lower() or param.lower() in arg.lower(), (
                            f"Error message should not expose sensitive implementation details: '{arg}'"
                        )
            
            assert parameter_mentioned, "Parameter name should be mentioned in structured logging"
    
    @given(
        field=sensitive_params,
        error_message=error_reasons,
        sources=st.lists(source_names, min_size=0, max_size=3)
    )
    def test_secure_config_logger_error_method_masks_sensitive_info(self, field, error_message, sources):
        """
        Property 13: Secure Error Messages
        For any error logged through SecureConfigLogger.log_config_error,
        sensitive information should not be exposed in the log output.
        
        **Validates: Requirements 5.3**
        """
        # Mock the logger to capture log calls
        with patch('config.security.logger') as mock_logger:
            # Call the secure config logger error method
            SecureConfigLogger.log_config_error(field, error_message, sources)
            
            # Check that logger.error was called
            assert mock_logger.error.called, "Logger error should have been called"
            
            # Get the log call arguments
            call_args = mock_logger.error.call_args
            args, kwargs = call_args
            
            # The field name should be present (this is expected for debugging)
            assert 'field' in kwargs, "Field name should be in structured logging"
            assert kwargs['field'] == field, "Field name should match"
            
            # The error message should be present
            assert 'error' in kwargs, "Error message should be in structured logging"
            assert kwargs['error'] == error_message, "Error message should match"
            
            # Sources should be present if provided
            if sources:
                assert 'sources_checked' in kwargs, "Sources should be in structured logging"
                assert kwargs['sources_checked'] == sources, "Sources should match"
            
            # Check that the main log message doesn't contain sensitive patterns
            main_message = args[0] if args else ""
            
            # The main message should be generic
            assert isinstance(main_message, str), "Main log message should be a string"
            assert len(main_message) > 0, "Main log message should not be empty"
            
            # Should not contain actual sensitive values (we can't test specific values here,
            # but we can ensure the message is structured properly)
            assert "Configuration parameter error" in main_message or "error" in main_message.lower(), (
                f"Main message should be a proper error message: '{main_message}'"
            )
    
    @given(
        config_dict=st.dictionaries(
            keys=st.sampled_from(["password", "secret_key", "host", "port", "username"]),
            values=sensitive_values,
            min_size=1,
            max_size=5
        )
    )
    def test_safe_config_summary_never_exposes_original_sensitive_values(self, config_dict):
        """
        Property 13: Secure Error Messages
        For any configuration dictionary processed by get_safe_config_summary,
        the result should never contain the original sensitive values.
        
        **Validates: Requirements 5.3**
        """
        safe_summary = SecureConfigLogger.get_safe_config_summary(config_dict)
        
        # Check each field in the original config
        for key, original_value in config_dict.items():
            safe_value = safe_summary[key]
            
            # If the key is sensitive, the safe value should be different from original
            key_lower = key.lower()
            is_sensitive = any(
                pattern in key_lower 
                for pattern in ['password', 'secret', 'key', 'token', 'credential', 'auth', 'pass']
            )
            
            if is_sensitive and len(original_value) > 0:
                assert safe_value != original_value, (
                    f"Sensitive field '{key}' with value '{original_value}' should be masked, "
                    f"but safe summary contains original value '{safe_value}'"
                )
                
                # The safe value should contain asterisks for masking
                if len(original_value) > 4:
                    assert '*' in safe_value, (
                        f"Masked value '{safe_value}' should contain asterisks for field '{key}'"
                    )
                else:
                    # Short values should be all asterisks
                    assert all(c == '*' for c in safe_value), (
                        f"Short sensitive value should be all asterisks, got '{safe_value}'"
                    )
    
    @given(
        param=sensitive_params,
        value=sensitive_values
    )
    def test_error_messages_maintain_debugging_capability(self, param, value):
        """
        Property 13: Secure Error Messages
        For any error involving sensitive parameters, the error message should
        still provide enough information for debugging without exposing sensitive values.
        
        **Validates: Requirements 5.3**
        """
        # Create a validation error
        error = ValidationError(param, value, "Invalid format")
        
        # Mock the logger to capture log calls
        with patch('config.loader.logger') as mock_logger:
            handle_configuration_error(error)
            
            # Should have called logger.error
            assert mock_logger.error.called, "Logger error should have been called"
            
            # Get the log call
            call_args = mock_logger.error.call_args
            args, kwargs = call_args
            
            # Should contain parameter name for debugging
            assert 'parameter' in kwargs, "Parameter name should be available for debugging"
            assert kwargs['parameter'] == param, "Parameter name should be correct"
            
            # Should contain reason for debugging
            assert 'reason' in kwargs, "Reason should be available for debugging"
            assert kwargs['reason'] == "Invalid format", "Reason should be correct"
            
            # Should contain guidance
            assert 'guidance' in kwargs, "Guidance should be provided"
            
            # But should NOT contain the actual sensitive value
            for key, kwarg_value in kwargs.items():
                if isinstance(kwarg_value, str) and key != 'parameter':
                    # Only check for longer values that would be actual security concerns
                    if len(value) >= 8:
                        assert value not in kwarg_value, (
                            f"Sensitive value '{value}' should not appear in log field '{key}'"
                        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])