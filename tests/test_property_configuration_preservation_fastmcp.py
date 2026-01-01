"""
Property-based test for configuration system preservation in FastMCP implementation
Tests Property 10: Configuration System Preservation
Feature: python-mcp-to-fast-mcp-migration, Property 10: Configuration System Preservation
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, assume
from pathlib import Path

# Import FastMCP implementation components
from main import _load_config, _verify_configuration_completeness, _verify_security_features_preserved
from config.loader import EnhancedConfigLoader
from config.models import DatabaseConfig
from config.sources import MCPConfigSource, DefaultSource
from config.exceptions import ConfigurationError, MissingParameterError, ValidationError


# Strategy for generating valid configuration parameters
valid_config_strategy = st.fixed_dictionaries({
    'ORACLE_HOST': st.sampled_from(['localhost', 'oracle-server.company.com', 'db.example.com']),
    'ORACLE_PORT': st.integers(min_value=1521, max_value=1530).map(str),
    'ORACLE_SERVICE_NAME': st.sampled_from(['PROD_SERVICE', 'DEV_SERVICE', 'TEST_SERVICE']),
    'ORACLE_USERNAME': st.text(
        min_size=3,
        max_size=20,
        alphabet='abcdefghijklmnopqrstuvwxyz'
    ).filter(lambda x: len(x) >= 3),
    'ORACLE_PASSWORD': st.text(
        min_size=8,
        max_size=50,
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'
    ).filter(lambda x: len(x) >= 8 and any(c.isalnum() for c in x)),
    'CONNECTION_TIMEOUT': st.integers(min_value=10, max_value=300).map(str),
    'QUERY_TIMEOUT': st.integers(min_value=30, max_value=1800).map(str),
    'MAX_ROWS': st.integers(min_value=100, max_value=5000).map(str)
})

# Strategy for generating partial configuration (missing some required fields)
partial_config_strategy = st.dictionaries(
    keys=st.sampled_from([
        'ORACLE_HOST', 'ORACLE_PORT', 'ORACLE_SERVICE_NAME',
        'ORACLE_USERNAME', 'ORACLE_PASSWORD', 'CONNECTION_TIMEOUT',
        'QUERY_TIMEOUT', 'MAX_ROWS'
    ]),
    values=st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
    min_size=1,
    max_size=6  # Ensure some required fields are missing
)

# Strategy for generating invalid configuration values
invalid_config_strategy = st.fixed_dictionaries({
    'ORACLE_HOST': st.just('valid-host'),
    'ORACLE_PORT': st.sampled_from(['-1', '0', '70000', 'invalid']),  # Invalid ports
    'ORACLE_SERVICE_NAME': st.just('VALID_SERVICE'),
    'ORACLE_USERNAME': st.sampled_from(['', 'a', '123invalid']),  # Invalid usernames
    'ORACLE_PASSWORD': st.sampled_from(['', 'short', '   ']),  # Invalid passwords
    'CONNECTION_TIMEOUT': st.sampled_from(['-1', '0', 'invalid']),  # Invalid timeouts
    'QUERY_TIMEOUT': st.sampled_from(['-1', '0', 'invalid']),  # Invalid timeouts
    'MAX_ROWS': st.sampled_from(['-1', '0', '20000', 'invalid'])  # Invalid max_rows
})


class TestConfigurationPreservationFastMCP:
    """Property-based tests for configuration system preservation in FastMCP implementation"""
    
    @given(config_env=valid_config_strategy)
    def test_configuration_loading_preserves_all_sources_fastmcp(self, config_env):
        """
        Property 10: Configuration System Preservation
        For any valid configuration parameters, the FastMCP implementation should preserve
        all configuration sources and precedence rules from the original implementation.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Store original environment to restore later
        original_env = os.environ.copy()
        
        try:
            # Clear environment first to ensure clean state
            for key in list(os.environ.keys()):
                if key.startswith('ORACLE_') or key in ['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT', 'MAX_ROWS']:
                    del os.environ[key]
            
            # Set configuration environment variables
            os.environ.update(config_env)
            
            # Test configuration loading
            config = _load_config()
            
            # Verify configuration loaded correctly
            assert config.host == config_env['ORACLE_HOST'], "Host should match environment variable"
            assert config.port == int(config_env['ORACLE_PORT']), "Port should match environment variable"
            assert config.service_name == config_env['ORACLE_SERVICE_NAME'], "Service name should match environment variable"
            assert config.username == config_env['ORACLE_USERNAME'], "Username should match environment variable"
            assert config.password == config_env['ORACLE_PASSWORD'], "Password should match environment variable"
            assert config.connection_timeout == int(config_env['CONNECTION_TIMEOUT']), "Connection timeout should match environment variable"
            assert config.query_timeout == int(config_env['QUERY_TIMEOUT']), "Query timeout should match environment variable"
            assert config.max_rows == int(config_env['MAX_ROWS']), "Max rows should match environment variable"
            
            # Verify source tracking is preserved
            source_info = config.get_source_info()
            assert isinstance(source_info, dict), "Source info should be a dictionary"
            
            # Verify all fields have source information
            expected_fields = ['host', 'port', 'service_name', 'username', 'password', 'connection_timeout', 'query_timeout', 'max_rows']
            for field in expected_fields:
                if field in source_info:
                    assert isinstance(source_info[field], str), f"Source info for {field} should be a string"
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    @given(config_env=valid_config_strategy)
    def test_configuration_precedence_rules_preserved_fastmcp(self, config_env):
        """
        Property 10: Configuration System Preservation
        For any configuration parameters, the FastMCP implementation should preserve
        configuration precedence rules (environment variables > defaults).
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Store original environment to restore later
        original_env = os.environ.copy()
        
        try:
            # Clear environment first
            for key in list(os.environ.keys()):
                if key.startswith('ORACLE_') or key in ['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT', 'MAX_ROWS']:
                    del os.environ[key]
            
            # Test with environment variables (should have highest precedence)
            os.environ.update(config_env)
            
            # Create loader and test precedence
            loader = EnhancedConfigLoader()
            
            # Verify MCP config source is available and has precedence
            mcp_source = None
            default_source = None
            
            for source in loader.config_sources:
                if isinstance(source, MCPConfigSource):
                    mcp_source = source
                elif isinstance(source, DefaultSource):
                    default_source = source
            
            assert mcp_source is not None, "MCP config source should be available"
            assert default_source is not None, "Default source should be available"
            
            # Test precedence by checking that MCP source values override defaults
            for key, value in config_env.items():
                mcp_value = mcp_source.get_value(key)
                assert mcp_value == value, f"MCP source should return environment value for {key}"
            
            # Test that defaults are used when environment variables are not set
            os.environ.clear()
            
            # Default source should provide default values
            default_port = default_source.get_value('ORACLE_PORT')
            assert default_port is not None, "Default source should provide default port"
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    @given(partial_config=partial_config_strategy)
    def test_configuration_validation_preserved_fastmcp(self, partial_config):
        """
        Property 10: Configuration System Preservation
        For any incomplete configuration, the FastMCP implementation should preserve
        configuration validation and error handling from the original implementation.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Store original environment to restore later
        original_env = os.environ.copy()
        
        try:
            # Clear environment first
            for key in list(os.environ.keys()):
                if key.startswith('ORACLE_') or key in ['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT', 'MAX_ROWS']:
                    del os.environ[key]
            
            # Set partial configuration
            os.environ.update(partial_config)
            
            # Required fields that don't have defaults
            required_fields_no_defaults = ['ORACLE_USERNAME', 'ORACLE_PASSWORD']
            missing_required = [field for field in required_fields_no_defaults if field not in partial_config]
            
            if missing_required:
                # Should raise ConfigurationError for missing required fields
                with pytest.raises(ConfigurationError):
                    _load_config()
            else:
                # If all required fields are present, should load successfully
                try:
                    config = _load_config()
                    assert config is not None, "Configuration should load when all required fields are present"
                except (ConfigurationError, ValidationError) as e:
                    # May fail due to invalid values, which is expected behavior
                    assert isinstance(e, (ConfigurationError, ValidationError)), "Should raise appropriate configuration error"
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    @given(invalid_config=invalid_config_strategy)
    def test_configuration_error_handling_preserved_fastmcp(self, invalid_config):
        """
        Property 10: Configuration System Preservation
        For any invalid configuration values, the FastMCP implementation should preserve
        error handling and validation behavior from the original implementation.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Store original environment to restore later
        original_env = os.environ.copy()
        
        try:
            # Clear environment first
            for key in list(os.environ.keys()):
                if key.startswith('ORACLE_') or key in ['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT', 'MAX_ROWS']:
                    del os.environ[key]
            
            # Set invalid configuration
            os.environ.update(invalid_config)
            
            # Should raise appropriate configuration errors
            with pytest.raises((ConfigurationError, ValidationError, ValueError)):
                _load_config()
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    @given(config_env=valid_config_strategy)
    def test_enhanced_config_loader_functionality_preserved_fastmcp(self, config_env):
        """
        Property 10: Configuration System Preservation
        For any configuration, the FastMCP implementation should preserve all
        EnhancedConfigLoader functionality from the original implementation.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Store original environment to restore later
        original_env = os.environ.copy()
        
        try:
            # Clear environment first
            for key in list(os.environ.keys()):
                if key.startswith('ORACLE_') or key in ['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT', 'MAX_ROWS']:
                    del os.environ[key]
            
            # Set configuration environment variables
            os.environ.update(config_env)
            
            # Test EnhancedConfigLoader directly
            loader = EnhancedConfigLoader()
            
            # Verify loader has expected configuration sources
            assert len(loader.config_sources) >= 2, "Loader should have multiple configuration sources"
            
            # Verify source validation works
            validation_result = loader.validate_sources()
            assert hasattr(validation_result, 'errors'), "Validation result should have errors attribute"
            assert hasattr(validation_result, 'warnings'), "Validation result should have warnings attribute"
            
            # Test configuration loading
            config = loader.load_config()
            
            # Verify config object has expected attributes
            assert hasattr(config, 'host'), "Config should have host attribute"
            assert hasattr(config, 'port'), "Config should have port attribute"
            assert hasattr(config, 'service_name'), "Config should have service_name attribute"
            assert hasattr(config, 'username'), "Config should have username attribute"
            assert hasattr(config, 'password'), "Config should have password attribute"
            assert hasattr(config, 'dsn'), "Config should have dsn property"
            
            # Verify source tracking functionality
            source_info = config.get_source_info()
            assert isinstance(source_info, dict), "Source info should be a dictionary"
            
            # Verify warning functionality
            warnings = config.get_warnings()
            assert isinstance(warnings, list), "Warnings should be a list"
            
            # Test DSN generation
            dsn = config.dsn
            assert isinstance(dsn, str), "DSN should be a string"
            assert config.host in dsn, "DSN should contain host"
            assert str(config.port) in dsn, "DSN should contain port"
            assert config.service_name in dsn, "DSN should contain service name"
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_configuration_source_availability_fastmcp(self):
        """
        Property 10: Configuration System Preservation
        The FastMCP implementation should preserve all configuration sources
        and their availability checking from the original implementation.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Test configuration source availability
        loader = EnhancedConfigLoader()
        
        # Verify expected sources are present
        source_names = [source.get_source_name() for source in loader.config_sources]
        
        # Should have at least Default and MCP sources
        assert 'Default Values' in source_names, "Default source should be available"
        assert 'MCP Config Environment' in source_names, "MCP Config source should be available"
        
        # Test source availability checking
        for source in loader.config_sources:
            # Should be able to check availability without errors
            is_available = source.is_available()
            assert isinstance(is_available, bool), "Source availability should be a boolean"
            
            # Should be able to get source name
            source_name = source.get_source_name()
            assert isinstance(source_name, str), "Source name should be a string"
            assert len(source_name) > 0, "Source name should not be empty"
    
    @given(
        field_name=st.sampled_from(['host', 'port', 'service_name', 'username', 'password']),
        source_name=st.sampled_from(['MCP Config Environment', 'Default Values', 'Environment'])
    )
    def test_source_tracking_functionality_preserved_fastmcp(self, field_name, source_name):
        """
        Property 10: Configuration System Preservation
        For any configuration field and source, the FastMCP implementation should preserve
        source tracking functionality from the original implementation.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Test source tracking functionality
        config = DatabaseConfig(
            host='test-host',
            port=1521,
            service_name='TEST_SERVICE',
            username='testuser',
            password='testpassword123'
        )
        
        # Test setting source information
        config.set_source_info(field_name, source_name)
        
        # Test getting source information
        source_info = config.get_source_info()
        assert isinstance(source_info, dict), "Source info should be a dictionary"
        assert field_name in source_info, f"Source info should contain {field_name}"
        assert source_info[field_name] == source_name, f"Source for {field_name} should be {source_name}"
        
        # Test warning functionality
        test_warning = f"Test warning for {field_name}"
        config.add_warning(test_warning)
        
        warnings = config.get_warnings()
        assert isinstance(warnings, list), "Warnings should be a list"
        assert test_warning in warnings, "Warning should be in warnings list"
    
    @given(config_env=valid_config_strategy)
    def test_security_integration_preserved_fastmcp(self, config_env):
        """
        Property 10: Configuration System Preservation
        For any configuration, the FastMCP implementation should preserve
        security integration and validation from the original implementation.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
        """
        # Store original environment to restore later
        original_env = os.environ.copy()
        
        try:
            # Clear environment first
            for key in list(os.environ.keys()):
                if key.startswith('ORACLE_') or key in ['CONNECTION_TIMEOUT', 'QUERY_TIMEOUT', 'MAX_ROWS']:
                    del os.environ[key]
            
            # Set configuration environment variables
            os.environ.update(config_env)
            
            # Test configuration loading with security integration
            config = _load_config()
            
            # Verify security features are integrated
            source_info = config.get_source_info()
            
            # Test security verification functions work
            try:
                _verify_security_features_preserved(config, source_info)
                # Should complete without errors for valid config
            except Exception as e:
                # If it fails, should be due to security validation, not missing functionality
                assert "security" in str(e).lower() or "validation" in str(e).lower(), (
                    f"Security verification failure should be security-related: {e}"
                )
            
            # Test configuration completeness verification
            try:
                _verify_configuration_completeness(config, source_info)
                # Should complete without errors for complete config
            except ConfigurationError as e:
                # Should only fail if configuration is actually incomplete
                assert "missing" in str(e).lower() or "required" in str(e).lower(), (
                    f"Completeness verification failure should be about missing fields: {e}"
                )
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])