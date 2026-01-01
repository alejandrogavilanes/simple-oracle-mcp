"""
Enhanced configuration loader for Oracle MCP Server
Implements precedence-based configuration loading from multiple sources
"""

from typing import Dict, List, Optional, Tuple
import structlog
from pydantic import ValidationError as PydanticValidationError

from .sources import ConfigSource, MCPConfigSource, DefaultSource
from .models import DatabaseConfig, ConfigValidationResult
from .exceptions import ConfigurationError, MissingParameterError, ValidationError
from .security import SecureConfigLogger, validate_environment_security, validate_credential_format

logger = structlog.get_logger(__name__)


def handle_configuration_error(error: ConfigurationError) -> None:
    """Handle configuration errors with appropriate logging and user guidance"""
    
    if isinstance(error, MissingParameterError):
        # Use secure logging for error messages
        SecureConfigLogger.log_config_error(
            field=error.parameter,
            error_message="Required parameter not found",
            sources_checked=error.sources_checked
        )
        logger.error("Missing required configuration parameter",
                    parameter=error.parameter,
                    sources_checked=error.sources_checked,
                    guidance="Add the parameter to your MCP config env section or set as environment variable")
    
    elif isinstance(error, ValidationError):
        # Use secure logging to avoid exposing sensitive values in error messages
        SecureConfigLogger.log_config_error(
            field=error.parameter,
            error_message=error.reason
        )
        logger.error("Configuration parameter validation failed",
                    parameter=error.parameter,
                    reason=error.reason,
                    guidance="Check parameter format and allowed values")
    
    else:
        logger.error("Configuration error occurred",
                    error_type=type(error).__name__,
                    error_message=str(error),
                    guidance="Check your configuration parameters")
    
    # Provide helpful configuration examples
    logger.info("Configuration help available at: docs/deployment-guide.md")


class EnhancedConfigLoader:
    """Enhanced configuration loader with multiple source support"""
    
    # Configuration parameter mapping
    CONFIG_PARAMETER_MAP = {
        "host": "ORACLE_HOST",
        "port": "ORACLE_PORT", 
        "service_name": "ORACLE_SERVICE_NAME",
        "username": "ORACLE_USERNAME",
        "password": "ORACLE_PASSWORD",
        "connection_timeout": "CONNECTION_TIMEOUT",
        "query_timeout": "QUERY_TIMEOUT",
        "max_rows": "MAX_ROWS"
    }
    
    def __init__(self):
        # Initialize configuration sources in precedence order
        # Higher index = higher precedence
        # Note: .env file support removed - using only environment variables and defaults
        self.config_sources: List[ConfigSource] = [
            DefaultSource(),      # Lowest precedence
            MCPConfigSource()     # Highest precedence - environment variables only
        ]
        self.logger = structlog.get_logger(__name__)
    
    def load_config(self) -> DatabaseConfig:
        """Load configuration with precedence handling"""
        self.logger.info("Starting enhanced configuration loading")
        
        # Load configuration values with source tracking
        config_values = {}
        source_tracking = {}
        
        for field, env_key in self.CONFIG_PARAMETER_MAP.items():
            value, source = self.get_value_with_source(env_key)
            if value is not None:
                # Convert string values to appropriate types
                if field == "port":
                    try:
                        config_values[field] = int(value)
                    except ValueError:
                        raise ValidationError("port", value, "Port must be a valid integer")
                elif field in ["connection_timeout", "query_timeout", "max_rows"]:
                    try:
                        config_values[field] = int(value)
                    except ValueError:
                        raise ValidationError(field, value, f"{field} must be a valid integer")
                else:
                    config_values[field] = value
                
                source_tracking[field] = source
                
                # Use secure logging for configuration parameters
                SecureConfigLogger.log_config_source(field, value, source)
        
        # Store source tracking for has_dotenv_values() method
        self._last_source_tracking = source_tracking.copy()
        
        # Validate required fields
        required_fields = ["host", "service_name", "username", "password"]
        missing_fields = []
        
        for field in required_fields:
            if field not in config_values or not config_values[field]:
                env_key = self.CONFIG_PARAMETER_MAP[field]
                sources_checked = [source.get_source_name() for source in self.config_sources]
                missing_fields.append(field)
        
        if missing_fields:
            # Report the first missing field
            field = missing_fields[0]
            env_key = self.CONFIG_PARAMETER_MAP[field]
            sources_checked = [source.get_source_name() for source in self.config_sources]
            raise MissingParameterError(env_key, sources_checked)
        
        # Validate credentials format and security
        username = config_values.get('username', '')
        password = config_values.get('password', '')
        
        credential_errors = validate_credential_format(username, password)
        if credential_errors:
            # Use the first credential error
            raise ValidationError('credentials', 'invalid', credential_errors[0])
        
        # Create and validate config
        try:
            # Pre-validate port range before creating DatabaseConfig
            if 'port' in config_values:
                port_value = config_values['port']
                if not isinstance(port_value, int) or port_value <= 0 or port_value > 65535:
                    raise ValidationError('port', str(port_value), 'Port must be between 1 and 65535')
            
            # Pre-validate other numeric fields
            for field in ['connection_timeout', 'query_timeout']:
                if field in config_values:
                    value = config_values[field]
                    if not isinstance(value, int) or value <= 0:
                        raise ValidationError(field, str(value), f'{field} must be a positive integer')
            
            if 'max_rows' in config_values:
                value = config_values['max_rows']
                if not isinstance(value, int) or value <= 0 or value > 10000:
                    raise ValidationError('max_rows', str(value), 'max_rows must be between 1 and 10000')
            
            config = DatabaseConfig(**config_values)
            
            # Set source tracking
            for field, source in source_tracking.items():
                config.set_source_info(field, source)
            
            # Log successful configuration with masked sensitive data
            safe_summary = SecureConfigLogger.get_safe_config_summary(config_values)
            self.logger.info("Configuration loaded successfully", 
                           sources_used=list(set(source_tracking.values())),
                           fields_loaded=list(config_values.keys()),
                           config_summary=safe_summary)
            
            return config
            
        except PydanticValidationError as e:
            self.logger.error("Configuration validation failed", errors=str(e))
            raise ConfigurationError(f"Invalid configuration: {e}")
    
    def get_value_with_source(self, key: str) -> Tuple[Optional[str], Optional[str]]:
        """Get configuration value with source information"""
        # Check sources in reverse order (highest precedence first)
        for source in reversed(self.config_sources):
            if source.is_available():
                value = source.get_value(key)
                if value is not None:
                    self.logger.debug("Configuration value found", 
                                    key=key, 
                                    source=source.get_source_name(),
                                    # Don't log the actual value for security
                                    value_length=len(str(value)))
                    return value, source.get_source_name()
        
        self.logger.debug("Configuration value not found", key=key)
        return None, None
    
    def has_dotenv_values(self) -> bool:
        """Check if any values are coming from .env file - always returns False since .env support is disabled"""
        return False
    
    def validate_sources(self) -> ConfigValidationResult:
        """Validate all configuration sources"""
        result = ConfigValidationResult()
        
        for source in self.config_sources:
            try:
                if source.is_available():
                    self.logger.debug("Configuration source available", 
                                    source=source.get_source_name())
                else:
                    self.logger.debug("Configuration source not available", 
                                    source=source.get_source_name())
            except Exception as e:
                result.add_error(f"Source {source.get_source_name()} validation failed: {e}")
        
        return result