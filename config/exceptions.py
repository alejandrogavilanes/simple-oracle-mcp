"""
Configuration exceptions for Oracle MCP Server
Defines custom exceptions for configuration loading and validation
"""

from typing import List


class ConfigurationError(Exception):
    """Base configuration error"""
    pass


class MissingParameterError(ConfigurationError):
    """Required parameter is missing"""
    
    def __init__(self, parameter: str, sources_checked: List[str]):
        self.parameter = parameter
        self.sources_checked = sources_checked
        super().__init__(
            f"Required parameter '{parameter}' not found in sources: "
            f"{', '.join(sources_checked)}"
        )


class ValidationError(ConfigurationError):
    """Parameter validation failed"""
    
    def __init__(self, parameter: str, value: str, reason: str):
        self.parameter = parameter
        self.value = value
        self.reason = reason
        super().__init__(f"Parameter '{parameter}' validation failed: {reason}")