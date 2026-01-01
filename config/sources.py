"""
Configuration sources for Oracle MCP Server
Implements different sources for configuration parameters with precedence handling
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Optional
import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)


class ConfigSource(ABC):
    """Abstract base class for configuration sources"""
    
    @abstractmethod
    def get_value(self, key: str) -> Optional[str]:
        """Get configuration value for key"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if configuration source is available"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get human-readable source name"""
        pass


class MCPConfigSource(ConfigSource):
    """Configuration source for MCP client environment parameters"""
    
    def __init__(self):
        self.mcp_env_prefix = "MCP_"
        self.logger = structlog.get_logger(__name__)
    
    def get_value(self, key: str) -> Optional[str]:
        """Get value from MCP environment parameters"""
        # Check for MCP-prefixed environment variables first
        mcp_key = f"{self.mcp_env_prefix}{key}"
        mcp_value = os.getenv(mcp_key)
        if mcp_value is not None:
            self.logger.debug("Found MCP config value", key=key, source="mcp_env")
            return mcp_value
        
        # Fall back to regular environment variable
        env_value = os.getenv(key)
        if env_value is not None:
            self.logger.debug("Found environment value", key=key, source="env")
            return env_value
        
        return None
    
    def is_available(self) -> bool:
        """Check if any MCP environment parameters exist"""
        # MCP config source is available if there are any environment variables
        # (either MCP-prefixed or regular ones that could be from MCP config)
        return len(os.environ) > 0
    
    def get_source_name(self) -> str:
        """Get human-readable source name"""
        return "MCP Config Environment"


class DotEnvSource(ConfigSource):
    """Configuration source for .env file backward compatibility"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.env_vars: Dict[str, str] = {}
        self.logger = structlog.get_logger(__name__)
        self._load_env_file()
    
    def _load_env_file(self):
        """Load environment variables from .env file (optional)"""
        try:
            if os.path.exists(self.env_file):
                # Read .env file directly to avoid polluting os.environ
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            self.env_vars[key.strip()] = value.strip()
                
                self.logger.debug("Loaded .env file", 
                                file=self.env_file, 
                                vars_count=len(self.env_vars))
            else:
                # .env file not found - this is now acceptable for MCP config only operation
                self.logger.debug(".env file not found - operating with MCP config only", 
                                file=self.env_file)
        except Exception as e:
            # .env file loading errors are no longer critical
            self.logger.debug("Failed to load .env file - continuing with MCP config", 
                              file=self.env_file, 
                              error=str(e))
    
    def get_value(self, key: str) -> Optional[str]:
        """Get value from .env file variables"""
        value = self.env_vars.get(key)
        if value is not None:
            self.logger.debug("Found .env value", key=key, source="dotenv")
        return value
    
    def is_available(self) -> bool:
        """Check if .env file exists and has variables"""
        return os.path.exists(self.env_file) and len(self.env_vars) > 0
    
    def get_source_name(self) -> str:
        """Get human-readable source name"""
        return f".env file ({self.env_file})"


class DefaultSource(ConfigSource):
    """Configuration source for fallback default values"""
    
    def __init__(self):
        self.defaults = {
            "ORACLE_HOST": "localhost",
            "ORACLE_PORT": "1521", 
            "ORACLE_SERVICE_NAME": "ORCL",
            "CONNECTION_TIMEOUT": "30",
            "QUERY_TIMEOUT": "300",
            "MAX_ROWS": "1000",
            "LOG_LEVEL": "INFO"
        }
        self.logger = structlog.get_logger(__name__)
    
    def get_value(self, key: str) -> Optional[str]:
        """Get default value for key"""
        value = self.defaults.get(key)
        if value is not None:
            self.logger.debug("Using default value", key=key, source="defaults")
        return value
    
    def is_available(self) -> bool:
        """Default source is always available"""
        return True
    
    def get_source_name(self) -> str:
        """Get human-readable source name"""
        return "Default Values"