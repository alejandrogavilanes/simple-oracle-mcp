"""
Security enhancements for configuration management
Implements credential masking, secure logging, and environment validation
"""

import re
import os
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class SecureConfigLogger:
    """Secure logging for configuration with credential masking"""
    
    # Sensitive parameter patterns (case-insensitive)
    SENSITIVE_PATTERNS = [
        r'password',
        r'secret',
        r'key',
        r'token',
        r'credential',
        r'auth',
        r'pass'
    ]
    
    @classmethod
    def mask_sensitive_value(cls, key: str, value: str) -> str:
        """
        Mask sensitive configuration values for secure logging
        
        Args:
            key: Configuration parameter name
            value: Configuration parameter value
            
        Returns:
            Masked value if sensitive, original value otherwise
        """
        if not value:
            return value
            
        # Check if key contains sensitive patterns
        key_lower = key.lower()
        is_sensitive = any(
            re.search(pattern, key_lower) 
            for pattern in cls.SENSITIVE_PATTERNS
        )
        
        if is_sensitive:
            if len(value) <= 4:
                # For very short values, mask completely
                return "*" * len(value)
            else:
                # Show first 2 and last 2 characters, mask the middle
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
        
        return value
    
    @classmethod
    def log_config_source(cls, field: str, value: str, source: str) -> None:
        """
        Log configuration source with credential masking
        
        Args:
            field: Configuration field name
            value: Configuration field value
            source: Source where value was loaded from
        """
        masked_value = cls.mask_sensitive_value(field, value)
        
        logger.info(
            "Configuration parameter loaded",
            field=field,
            value=masked_value,
            source=source,
            is_masked=masked_value != value
        )
    
    @classmethod
    def log_config_error(cls, field: str, error_message: str, 
                        sources_checked: Optional[List[str]] = None) -> None:
        """
        Log configuration error without exposing sensitive information
        
        Args:
            field: Configuration field name that failed
            error_message: Error message (should not contain sensitive data)
            sources_checked: List of sources that were checked
        """
        logger.error(
            "Configuration parameter error",
            field=field,
            error=error_message,
            sources_checked=sources_checked or [],
            # Never log the actual value in error messages
        )
    
    @classmethod
    def get_safe_config_summary(cls, config_dict: Dict[str, Any]) -> Dict[str, str]:
        """
        Get a safe summary of configuration for logging
        
        Args:
            config_dict: Dictionary of configuration parameters
            
        Returns:
            Dictionary with masked sensitive values
        """
        safe_summary = {}
        
        for key, value in config_dict.items():
            if isinstance(value, str):
                safe_summary[key] = cls.mask_sensitive_value(key, value)
            else:
                # For non-string values, convert to string first
                safe_summary[key] = cls.mask_sensitive_value(key, str(value))
        
        return safe_summary


def validate_environment_security(config_dict: Dict[str, Any]) -> List[str]:
    """
    Validate environment configuration for security issues
    
    Args:
        config_dict: Dictionary containing configuration parameters
        
    Returns:
        List of security warnings
    """
    warnings = []
    
    # Check password strength
    password = config_dict.get('password', '')
    if password:
        if len(password) < 8:
            warnings.append("Database password is shorter than 8 characters")
        
        # Check for common weak passwords
        weak_patterns = [
            r'^password\d*$',
            r'^admin\d*$', 
            r'^test\d*$',
            r'^123+$',
            r'^oracle\d*$'
        ]
        
        password_lower = password.lower()
        for pattern in weak_patterns:
            if re.match(pattern, password_lower):
                warnings.append("Database password appears to use a common weak pattern")
                break
    
    # Check for localhost in production
    host = config_dict.get('host', '')
    environment = os.getenv('ENVIRONMENT', '').lower()
    
    if host == 'localhost' and environment in ['production', 'prod']:
        warnings.append("Using localhost database host in production environment")
    
    # Check for default ports in production
    port = config_dict.get('port')
    if port == 1521 and environment in ['production', 'prod']:
        warnings.append("Using default Oracle port (1521) in production environment")
    
    # Check for unencrypted connections (basic check)
    host_lower = host.lower() if host else ''
    if host_lower and not any(indicator in host_lower for indicator in ['ssl', 'tls', 'secure']):
        if environment in ['production', 'prod']:
            warnings.append("Database connection may not be using SSL/TLS encryption in production")
    
    # Check for empty or default usernames
    username = config_dict.get('username', '')
    if username:
        default_usernames = ['admin', 'oracle', 'test', 'user', 'root']
        if username.lower() in default_usernames:
            warnings.append(f"Using potentially insecure default username: {username}")
    
    # Check timeout values
    connection_timeout = config_dict.get('connection_timeout')
    if connection_timeout and connection_timeout > 300:  # 5 minutes
        warnings.append("Connection timeout is very high, may cause resource issues")
    
    query_timeout = config_dict.get('query_timeout')
    if query_timeout and query_timeout > 1800:  # 30 minutes
        warnings.append("Query timeout is very high, may cause resource issues")
    
    # Check max_rows for potential DoS
    max_rows = config_dict.get('max_rows')
    if max_rows and max_rows > 10000:
        warnings.append("Maximum rows limit is very high, may cause performance issues")
    
    return warnings


def validate_credential_format(username: str, password: str) -> List[str]:
    """
    Validate credential format and security requirements
    
    Args:
        username: Database username
        password: Database password
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Username validation
    if not username:
        errors.append("Username cannot be empty")
    elif len(username) < 2:
        errors.append("Username must be at least 2 characters long")
    elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        errors.append("Username must start with a letter and contain only letters, numbers, and underscores")
    
    # Password validation
    if not password:
        errors.append("Password cannot be empty")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    
    # Check for password complexity (basic)
    if password and len(password) >= 6:
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper or has_lower or has_digit):
            errors.append("Password should contain at least one letter or digit")
    
    return errors