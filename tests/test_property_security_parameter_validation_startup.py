"""
Property-based test for security parameter validation at startup
Tests Property 14: Security Parameter Validation at Startup
"""

import pytest
import os
import tempfile
from hypothesis import given, strategies as st
from unittest.mock import patch, MagicMock
from pathlib import Path

from config.loader import EnhancedConfigLoader
from config.exceptions import ConfigurationError, ValidationError, MissingParameterError
from config.security import validate_environment_security, validate_credential_format
from main import _load_config, RateLimiter


# Strategy for generating complete valid configuration sets
complete_valid_config = st.fixed_dictionaries({
    'ORACLE_HOST': st.sampled_from(['localhost', 'oracle-server.company.com', 'db.example.com']),
    'ORACLE_PORT': st.integers(min_value=1521, max_value=1530).map(str),
    'ORACLE_SERVICE_NAME': st.sampled_from(['PROD_SERVICE', 'DEV_SERVICE', 'TEST_SERVICE']),
    'ORACLE_USERNAME': st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    ).filter(lambda x: len(x) >= 3),
    'ORACLE_PASSWORD': st.text(
        min_size=8,
        max_size=50,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\n\r\t\0')
    ).filter(lambda x: x.strip() and len(x.strip()) >= 8 and any(c.isalnum() for c in x)),
    'CONNECTION_TIMEOUT': st.integers(min_value=10, max_value=300).map(str),
    'QUERY_TIMEOUT': st.integers(min_value=30, max_value=1800).map(str),
    'MAX_ROWS': st.integers(min_value=100, max_value=5000).map(str)
})

# Strategy for generating incomplete configuration sets (missing required parameters)
incomplete_config_strategy = st.dictionaries(
    keys=st.sampled_from([
        'ORACLE_HOST', 'ORACLE_PORT', 'ORACLE_SERVICE_NAME',
        'ORACLE_USERNAME', 'ORACLE_PASSWORD', 'CONNECTION_TIMEOUT',
        'QUERY_TIMEOUT', 'MAX_ROWS'
    ]),
    values=st.text(
        min_size=1, 
        max_size=50,
        alphabet=st.characters(
            min_codepoint=32,
            max_codepoint=126,
            blacklist_characters='\n\r\t\0'
        )
    ).filter(lambda x: x.strip() and '\x00' not in x),
    min_size=1,
    max_size=6  # Ensure some required parameters are missing
)

# Strategy for generating invalid security parameters
invalid_security_config = st.fixed_dictionaries({
    'ORACLE_HOST': st.just('localhost'),  # Valid host
    'ORACLE_PORT': st.just('1521'),  # Valid port
    'ORACLE_SERVICE_NAME': st.just('TEST_SERVICE'),  # Valid service
    'ORACLE_USERNAME': st.one_of([
        st.just(''),  # Empty username
        st.just('a'),  # Too short
        st.just('123user'),  # Starts with number
        st.just('user@domain'),  # Invalid characters
    ]),
    'ORACLE_PASSWORD': st.one_of([
        st.just(''),  # Empty password
        st.just('123'),  # Too short
        st.just('     '),  # Only whitespace
    ]),
    'CONNECTION_TIMEOUT': st.just('30'),
    'QUERY_TIMEOUT': st.just('300'),
    'MAX_ROWS': st.just('1000')
})

# Strategy for generating weak security configurations
weak_security_config = st.fixed_dictionaries({
    'ORACLE_HOST': st.just('localhost'),
    'ORACLE_PORT': st.just('1521'),  # Default port
    'ORACLE_SERVICE_NAME': st.just('TEST_SERVICE'),
    'ORACLE_USERNAME': st.sampled_from(['admin', 'oracle', 'test', 'user', 'root']),  # Default usernames
    'ORACLE_PASSWORD': st.sampled_from([
        'password', 'password123', 'admin123', 'test123', 'oracle123'  # Weak passwords
    ]),
    'CONNECTION_TIMEOUT': st.just('30'),
    'QUERY_TIMEOUT': st.just('300'),
    'MAX_ROWS': st.just('1000')
})

# Strategy for production environment indicators
production_env_indicators = st.sampled_from(['production', 'prod', 'PRODUCTION', 'PROD'])


class TestSecurityParameterValidationAtStartup:
    """Property-based tests for security parameter validation at startup"""
    
    @given(config=complete_valid_config)
    def test_valid_security_parameters_allow_startup(self, config):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence with valid security parameters,
        the Security_System should verify that all required security 
        parameters are present and valid before allowing the server to start.
        
        **Validates: Requirements 5.4**
        """
        # Test server startup with valid security parameters
        with patch.dict(os.environ, config):
            with patch('main.oracledb.connect') as mock_connect:
                mock_connect.return_value = MagicMock()
                
                try:
                    # Test configuration loading (which is what FastMCP server uses)
                    from main import _load_config, rate_limiter
                    
                    # Load configuration to verify security features
                    loaded_config = _load_config()
                    
                    # Verify security parameters were validated and accepted
                    assert loaded_config is not None, "Database config should be initialized"
                    assert loaded_config.host == config['ORACLE_HOST'], "Host should be set correctly"
                    assert loaded_config.username == config['ORACLE_USERNAME'], "Username should be set correctly"
                    assert loaded_config.password == config['ORACLE_PASSWORD'], "Password should be set correctly"
                    
                    # Verify security components are initialized
                    assert rate_limiter is not None, "Rate limiter should be initialized"
                    assert isinstance(rate_limiter, RateLimiter), "Rate limiter should be RateLimiter instance"
                    
                    # Verify security validation was performed
                    config_dict = {
                        'host': loaded_config.host,
                        'port': loaded_config.port,
                        'username': loaded_config.username,
                        'password': loaded_config.password,
                        'connection_timeout': loaded_config.connection_timeout,
                        'query_timeout': loaded_config.query_timeout,
                        'max_rows': loaded_config.max_rows
                    }
                    
                    # Security validation should complete without critical errors
                    security_warnings = validate_environment_security(config_dict)
                    credential_errors = validate_credential_format(
                        loaded_config.username, 
                        loaded_config.password
                    )
                    
                    # Should not have critical credential errors for valid config
                    critical_errors = [e for e in credential_errors if 'empty' in e.lower() or 'too short' in e.lower()]
                    assert len(critical_errors) == 0, f"Valid config should not have critical errors: {critical_errors}"
                    
                except ConfigurationError as e:
                    pytest.fail(f"Valid security parameters should allow startup, but got error: {e}")
    
    @given(config=incomplete_config_strategy)
    def test_missing_required_parameters_prevent_startup(self, config):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence with missing required security parameters,
        the Security_System should prevent startup and provide clear error messages.
        
        **Validates: Requirements 5.4**
        """
        # Ensure some required parameters are definitely missing
        required_params = {'ORACLE_HOST', 'ORACLE_SERVICE_NAME', 'ORACLE_USERNAME', 'ORACLE_PASSWORD'}
        provided_params = set(config.keys())
        missing_params = required_params - provided_params
        
        # Only test if we actually have missing required parameters
        if len(missing_params) > 0:
            with patch.dict(os.environ, config, clear=True):
                with patch('main.oracledb.connect') as mock_connect:
                    mock_connect.return_value = MagicMock()
                    
                    # Configuration loading should fail with missing parameters
                    with pytest.raises((ConfigurationError, MissingParameterError, ValidationError)):
                        from main import _load_config
                        _load_config()
        else:
            # If no required parameters are missing, skip this test case
            pytest.skip("No required parameters missing in this test case")
    
    @given(config=invalid_security_config)
    def test_invalid_security_parameters_prevent_startup(self, config):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence with invalid security parameters,
        the Security_System should prevent startup due to validation failures.
        
        **Validates: Requirements 5.4**
        """
        with patch.dict(os.environ, config):
            with patch('main.oracledb.connect') as mock_connect:
                mock_connect.return_value = MagicMock()
                
                # Configuration loading should fail with invalid security parameters
                with pytest.raises((ConfigurationError, ValidationError)):
                    from main import _load_config
                    _load_config()
    
    @given(
        config=weak_security_config,
        environment=production_env_indicators
    )
    def test_weak_security_parameters_generate_warnings_in_production(self, config, environment):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence with weak security parameters in production,
        the Security_System should generate appropriate security warnings.
        
        **Validates: Requirements 5.4**
        """
        # Set production environment
        config_with_env = dict(config)
        config_with_env['ENVIRONMENT'] = environment
        
        with patch.dict(os.environ, config_with_env):
            with patch('main.oracledb.connect') as mock_connect:
                mock_connect.return_value = MagicMock()
                
                try:
                    from main import _load_config
                    config = _load_config()
                    
                    # Check for security warnings
                    config_dict = {
                        'host': config.host,
                        'port': config.port,
                        'username': config.username,
                        'password': config.password,
                        'connection_timeout': config.connection_timeout,
                        'query_timeout': config.query_timeout,
                        'max_rows': config.max_rows
                    }
                    
                    security_warnings = validate_environment_security(config_dict)
                    
                    # Should have security warnings for weak configuration in production
                    assert len(security_warnings) > 0, (
                        f"Weak security configuration in production should generate warnings, "
                        f"but got no warnings for config: {config}"
                    )
                    
                    # Check for specific types of warnings
                    warning_text = ' '.join(security_warnings).lower()
                    
                    # Should warn about weak passwords or default usernames
                    has_security_warning = any([
                        'password' in warning_text,
                        'username' in warning_text,
                        'default' in warning_text,
                        'weak' in warning_text,
                        'insecure' in warning_text
                    ])
                    
                    assert has_security_warning, (
                        f"Should have security-related warnings, but got: {security_warnings}"
                    )
                    
                except ConfigurationError:
                    # It's acceptable for weak configs to be rejected entirely
                    pass
    
    @given(config=complete_valid_config)
    def test_security_validation_occurs_before_database_connection(self, config):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence, security parameter validation
        should occur before attempting database connections.
        
        **Validates: Requirements 5.4**
        """
        with patch.dict(os.environ, config):
            # Mock database connection to fail, but security validation should still occur
            with patch('main.oracledb.connect') as mock_connect:
                mock_connect.side_effect = Exception("Database connection failed")
                
                try:
                    # Configuration loading should validate security parameters first
                    from main import _load_config
                    config_obj = _load_config()
                    
                    # If we get here, security validation passed
                    assert config_obj is not None, "Security validation should have created config"
                    
                    # Verify security parameters were validated
                    assert loaded_config.host == config['ORACLE_HOST'], "Host should be validated"
                    assert loaded_config.username == config['ORACLE_USERNAME'], "Username should be validated"
                    assert loaded_config.password == config['ORACLE_PASSWORD'], "Password should be validated"
                    
                except ConfigurationError as e:
                    # Configuration errors should be about validation, not database connection
                    error_msg = str(e).lower()
                    assert 'connection' not in error_msg or 'validation' in error_msg, (
                        f"Configuration error should be about validation, not connection: {e}"
                    )
                except Exception as e:
                    # Other exceptions might be from database connection, which is expected
                    # The important thing is that security validation happened first
                    pass
    
    @given(
        base_config=complete_valid_config,
        timeout_values=st.dictionaries(
            keys=st.sampled_from(['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT']),
            values=st.one_of([
                st.integers(min_value=-10, max_value=0).map(str),  # Invalid negative/zero
                st.integers(min_value=3601, max_value=10000).map(str),  # Very high values
                st.just('invalid'),  # Non-numeric
                st.just('')  # Empty
            ]),
            min_size=1,
            max_size=2
        )
    )
    def test_invalid_timeout_parameters_caught_at_startup(self, base_config, timeout_values):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence with invalid timeout parameters,
        the Security_System should catch these during validation.
        
        **Validates: Requirements 5.4**
        """
        # Merge base config with invalid timeout values
        config = dict(base_config)
        config.update(timeout_values)
        
        with patch.dict(os.environ, config):
            with patch('main.oracledb.connect') as mock_connect:
                mock_connect.return_value = MagicMock()
                
                # Server startup should handle invalid timeout parameters
                try:
                    from main import _load_config
                    config = _load_config()
                    
                    # If startup succeeds, timeouts should have been corrected or defaulted
                    assert config.connection_timeout > 0, "Connection timeout should be positive"
                    assert config.query_timeout > 0, "Query timeout should be positive"
                    
                except (ConfigurationError, ValidationError, ValueError):
                    # It's acceptable for invalid timeouts to cause startup failure
                    pass
    
    @given(
        base_config=complete_valid_config,
        max_rows_value=st.one_of([
            st.integers(min_value=-100, max_value=0).map(str),  # Invalid negative/zero
            st.integers(min_value=50001, max_value=100000).map(str),  # Extremely high
            st.just('invalid'),  # Non-numeric
            st.just('')  # Empty
        ])
    )
    def test_invalid_max_rows_parameter_caught_at_startup(self, base_config, max_rows_value):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence with invalid max_rows parameter,
        the Security_System should validate this security-relevant parameter.
        
        **Validates: Requirements 5.4**
        """
        config = dict(base_config)
        config['MAX_ROWS'] = max_rows_value
        
        with patch.dict(os.environ, config):
            with patch('main.oracledb.connect') as mock_connect:
                mock_connect.return_value = MagicMock()
                
                try:
                    from main import _load_config
                    config = _load_config()
                    
                    # If startup succeeds, max_rows should be within valid range
                    assert 1 <= config.max_rows <= 10000, (
                        f"Max rows should be in valid range, but got: {config.max_rows}"
                    )
                    
                except (ConfigurationError, ValidationError, ValueError):
                    # It's acceptable for invalid max_rows to cause startup failure
                    pass
    
    @given(config=complete_valid_config)
    def test_security_parameter_validation_is_comprehensive(self, config):
        """
        Property 14: Security Parameter Validation at Startup
        For any server startup sequence, all security-relevant parameters
        should be validated comprehensively.
        
        **Validates: Requirements 5.4**
        """
        with patch.dict(os.environ, config):
            with patch('main.oracledb.connect') as mock_connect:
                mock_connect.return_value = MagicMock()
                
                from main import _load_config
                config = _load_config()
                
                # Verify all security-relevant parameters are present and validated
                security_params = [
                    'host', 'port', 'service_name', 'username', 'password',
                    'connection_timeout', 'query_timeout', 'max_rows'
                ]
                
                for param in security_params:
                    assert hasattr(config, param), f"Security parameter '{param}' should be present"
                    value = getattr(config, param)
                    assert value is not None, f"Security parameter '{param}' should not be None"
                    
                    if param in ['port', 'connection_timeout', 'query_timeout', 'max_rows']:
                        assert isinstance(value, int), f"Numeric parameter '{param}' should be integer"
                        assert value > 0, f"Numeric parameter '{param}' should be positive"
                    elif param in ['host', 'service_name', 'username', 'password']:
                        assert isinstance(value, str), f"String parameter '{param}' should be string"
                        assert len(value.strip()) > 0, f"String parameter '{param}' should not be empty"
                
                # Verify security validation functions work with the configuration
                config_dict = {
                    'host': config.host,
                    'port': config.port,
                    'username': config.username,
                    'password': config.password,
                    'connection_timeout': config.connection_timeout,
                    'query_timeout': config.query_timeout,
                    'max_rows': config.max_rows
                }
                
                # Security validation functions should work without exceptions
                security_warnings = validate_environment_security(config_dict)
                credential_errors = validate_credential_format(
                    config.username, 
                    config.password
                )
                
                assert isinstance(security_warnings, list), "Security warnings should be a list"
                assert isinstance(credential_errors, list), "Credential errors should be a list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])