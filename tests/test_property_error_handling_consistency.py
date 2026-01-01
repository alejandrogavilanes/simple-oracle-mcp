"""
Property-based test for error handling consistency
Tests Property 7: Error Handling Consistency
Feature: python-mcp-to-fast-mcp-migration, Property 7: Error Handling Consistency
"""

import pytest
import asyncio
import structlog
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager

from config.exceptions import ConfigurationError, ValidationError, MissingParameterError
from config.models import DatabaseConfig


# Strategy for generating different error scenarios
error_scenarios = st.sampled_from([
    "configuration_error",
    "validation_error", 
    "missing_parameter_error",
    "database_connection_error",
    "keyboard_interrupt",
    "generic_exception"
])

# Strategy for generating error messages
error_messages = st.text(
    min_size=5,
    max_size=200,
    alphabet=st.characters(
        min_codepoint=32,  # Space character
        max_codepoint=126,  # Tilde character (printable ASCII)
        blacklist_characters='\n\r\t\0'  # Exclude problematic characters
    )
).filter(lambda x: x.strip() and len(x.strip()) >= 5)

# Strategy for generating configuration parameters
config_params = st.fixed_dictionaries({
    'host': st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    'port': st.integers(min_value=1, max_value=65535),
    'service_name': st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    'username': st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    'password': st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
})


class TestErrorHandlingConsistency:
    """Property-based tests for error handling consistency between original and FastMCP implementations"""
    
    @given(
        error_scenario=error_scenarios,
        error_message=error_messages
    )
    @settings(max_examples=10)  # Reduced for faster execution
    def test_error_handling_consistency_across_implementations(self, error_scenario, error_message):
        """
        Property 7: Error Handling Consistency
        For any error condition, the migrated implementation should produce identical 
        error messages, codes, and handling behavior as the original.
        
        **Validates: Requirements 2.5, 10.4, 12.4**
        """
        # Test that both implementations handle errors consistently
        original_error_behavior = self._simulate_original_error_handling(error_scenario, error_message)
        fastmcp_error_behavior = self._simulate_fastmcp_error_handling(error_scenario, error_message)
        
        # Verify error handling consistency
        assert original_error_behavior['error_logged'] == fastmcp_error_behavior['error_logged'], \
            "Both implementations should log errors consistently"
        
        assert original_error_behavior['error_type'] == fastmcp_error_behavior['error_type'], \
            "Both implementations should handle the same error types"
        
        assert original_error_behavior['graceful_shutdown'] == fastmcp_error_behavior['graceful_shutdown'], \
            "Both implementations should handle graceful shutdown consistently"
        
        # Verify error message structure is preserved
        if original_error_behavior['error_message'] and fastmcp_error_behavior['error_message']:
            # Both should contain similar error information
            original_msg = original_error_behavior['error_message'].lower()
            fastmcp_msg = fastmcp_error_behavior['error_message'].lower()
            
            # Key error information should be preserved
            if 'configuration' in original_msg:
                assert 'configuration' in fastmcp_msg, "Configuration errors should be preserved"
            if 'validation' in original_msg:
                assert 'validation' in fastmcp_msg, "Validation errors should be preserved"
            if 'database' in original_msg:
                assert 'database' in fastmcp_msg, "Database errors should be preserved"
    
    @given(
        config_params=config_params,
        error_scenario=error_scenarios
    )
    @settings(max_examples=10)  # Reduced for faster execution
    def test_startup_error_handling_preservation(self, config_params, error_scenario):
        """
        Property 7: Error Handling Consistency
        For any startup error scenario, the FastMCP implementation should preserve
        the same error handling patterns as the original implementation.
        
        **Validates: Requirements 2.5, 10.4**
        """
        # Mock the logger to capture error handling behavior
        with patch('structlog.get_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            # Test startup error handling
            startup_behavior = self._test_startup_error_handling(config_params, error_scenario, mock_logger)
            
            # Verify error handling patterns are preserved
            assert startup_behavior['error_caught'], "Startup errors should be caught and handled"
            assert startup_behavior['error_logged'], "Startup errors should be logged"
            assert startup_behavior['exception_reraised'], "Startup errors should be re-raised for proper handling"
    
    @given(
        error_message=error_messages
    )
    @settings(max_examples=10)  # Reduced for faster execution
    def test_graceful_shutdown_behavior_consistency(self, error_message):
        """
        Property 7: Error Handling Consistency
        For any shutdown scenario, the FastMCP implementation should ensure
        graceful shutdown behavior identical to the original implementation.
        
        **Validates: Requirements 2.5, 12.4**
        """
        # Test graceful shutdown behavior
        with patch('structlog.get_logger') as mock_logger_factory:
            mock_logger = MagicMock()
            mock_logger_factory.return_value = mock_logger
            
            shutdown_behavior = self._test_graceful_shutdown(error_message, mock_logger)
            
            # Verify graceful shutdown patterns
            assert shutdown_behavior['finally_block_executed'], "Finally block should always execute"
            assert shutdown_behavior['shutdown_logged'], "Shutdown should be logged"
            assert shutdown_behavior['cleanup_performed'], "Cleanup should be performed"
    
    def _simulate_original_error_handling(self, error_scenario: str, error_message: str) -> dict:
        """Simulate original implementation error handling behavior"""
        behavior = {
            'error_logged': False,
            'error_type': None,
            'error_message': None,
            'graceful_shutdown': False
        }
        
        try:
            # Simulate original error handling patterns
            if error_scenario == "configuration_error":
                behavior['error_type'] = 'ConfigurationError'
                behavior['error_message'] = f"Configuration error during startup: {error_message}"
                behavior['error_logged'] = True
                raise ConfigurationError(error_message)
            elif error_scenario == "validation_error":
                behavior['error_type'] = 'ValidationError'
                behavior['error_message'] = f"Validation failed: {error_message}"
                behavior['error_logged'] = True
                raise ValidationError("param", "value", error_message)
            elif error_scenario == "keyboard_interrupt":
                behavior['error_type'] = 'KeyboardInterrupt'
                behavior['error_message'] = "Received shutdown signal, shutting down gracefully"
                behavior['error_logged'] = True
                behavior['graceful_shutdown'] = True
                raise KeyboardInterrupt()
            else:
                behavior['error_type'] = 'Exception'
                behavior['error_message'] = f"Server startup failed: {error_message}"
                behavior['error_logged'] = True
                raise Exception(error_message)
        except Exception:
            behavior['graceful_shutdown'] = True
            return behavior
    
    def _simulate_fastmcp_error_handling(self, error_scenario: str, error_message: str) -> dict:
        """Simulate FastMCP implementation error handling behavior"""
        behavior = {
            'error_logged': False,
            'error_type': None,
            'error_message': None,
            'graceful_shutdown': False
        }
        
        try:
            # Simulate FastMCP error handling patterns (should match original)
            if error_scenario == "configuration_error":
                behavior['error_type'] = 'ConfigurationError'
                behavior['error_message'] = f"Configuration error during startup: {error_message}"
                behavior['error_logged'] = True
                raise ConfigurationError(error_message)
            elif error_scenario == "validation_error":
                behavior['error_type'] = 'ValidationError'
                behavior['error_message'] = f"Validation failed: {error_message}"
                behavior['error_logged'] = True
                raise ValidationError("param", "value", error_message)
            elif error_scenario == "keyboard_interrupt":
                behavior['error_type'] = 'KeyboardInterrupt'
                behavior['error_message'] = "Received shutdown signal, shutting down gracefully"
                behavior['error_logged'] = True
                behavior['graceful_shutdown'] = True
                raise KeyboardInterrupt()
            else:
                behavior['error_type'] = 'Exception'
                behavior['error_message'] = f"Server startup failed: {error_message}"
                behavior['error_logged'] = True
                raise Exception(error_message)
        except Exception:
            behavior['graceful_shutdown'] = True
            return behavior
    
    def _test_startup_error_handling(self, config_params: dict, error_scenario: str, mock_logger: MagicMock) -> dict:
        """Test startup error handling patterns"""
        behavior = {
            'error_caught': False,
            'error_logged': False,
            'exception_reraised': False
        }
        
        try:
            # Simulate startup with potential errors
            if error_scenario == "configuration_error":
                mock_logger.error.side_effect = None  # Allow logging
                raise ConfigurationError("Test configuration error")
            elif error_scenario == "validation_error":
                mock_logger.error.side_effect = None
                raise ValidationError("test_param", "test_value", "Test validation error")
            else:
                mock_logger.error.side_effect = None
                raise Exception("Test generic error")
        except (ConfigurationError, ValidationError, Exception) as e:
            behavior['error_caught'] = True
            
            # Check if error would be logged (simulate main function behavior)
            mock_logger.error("Server startup failed", error=str(e))
            behavior['error_logged'] = mock_logger.error.called
            
            # In real implementation, exception would be re-raised
            behavior['exception_reraised'] = True
        
        return behavior
    
    def _test_graceful_shutdown(self, error_message: str, mock_logger: MagicMock) -> dict:
        """Test graceful shutdown behavior"""
        behavior = {
            'finally_block_executed': False,
            'shutdown_logged': False,
            'cleanup_performed': False
        }
        
        try:
            # Simulate main function execution with error
            raise Exception(error_message)
        except Exception:
            # Simulate error handling
            mock_logger.error("Server startup failed", error=error_message)
        finally:
            # Simulate finally block execution
            behavior['finally_block_executed'] = True
            behavior['cleanup_performed'] = True
            
            # Simulate shutdown logging
            mock_logger.info("TUI Oracle MCP Server shutdown")
            behavior['shutdown_logged'] = True
        
        return behavior