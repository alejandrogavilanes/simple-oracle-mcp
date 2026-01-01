"""
Configuration models for Oracle MCP Server
Enhanced DatabaseConfig with source tracking and validation
"""

from typing import Dict, List
from pydantic import BaseModel, Field, field_validator, PrivateAttr


class ConfigValidationResult:
    """Result of configuration validation"""
    
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.source_info: Dict[str, str] = {}  # parameter -> source mapping
    
    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
    
    def set_source(self, parameter: str, source: str):
        """Set source information for parameter"""
        self.source_info[parameter] = source


class DatabaseConfig(BaseModel):
    """Enhanced database configuration with source tracking"""
    
    # Existing configuration fields
    host: str = Field(..., description="Oracle database host")
    port: int = Field(default=1521, description="Oracle database port")
    service_name: str = Field(..., description="Oracle service name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    query_timeout: int = Field(default=300, description="Query timeout in seconds")
    max_rows: int = Field(default=1000, description="Maximum rows per query")
    
    # Private attributes for source tracking
    _config_sources: Dict[str, str] = PrivateAttr(default_factory=dict)
    _validation_warnings: List[str] = PrivateAttr(default_factory=list)
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate port number range"""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @field_validator('connection_timeout', 'query_timeout')
    @classmethod
    def validate_timeouts(cls, v):
        """Validate timeout values are positive"""
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v
    
    @field_validator('max_rows')
    @classmethod
    def validate_max_rows(cls, v):
        """Validate max rows range"""
        if not 1 <= v <= 10000:
            raise ValueError('Max rows must be between 1 and 10000')
        return v
    
    @property
    def dsn(self) -> str:
        """Generate Oracle DSN string"""
        return f"{self.host}:{self.port}/{self.service_name}"
    
    def set_source_info(self, field: str, source: str):
        """Track configuration source for field"""
        self._config_sources[field] = source
    
    def get_source_info(self) -> Dict[str, str]:
        """Get configuration source information"""
        return self._config_sources.copy()
    
    def add_warning(self, warning: str):
        """Add configuration warning"""
        self._validation_warnings.append(warning)
    
    def get_warnings(self) -> List[str]:
        """Get all configuration warnings"""
        return self._validation_warnings.copy()