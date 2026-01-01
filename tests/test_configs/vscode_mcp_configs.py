"""
Test MCP configuration files for VS Code integration
Contains various VS Code MCP configuration scenarios for testing
"""

import json
from typing import Dict, Any


class VSCodeMCPConfigs:
    """VS Code MCP configuration templates for testing"""
    
    @staticmethod
    def get_single_environment_config(project_path: str) -> Dict[str, Any]:
        """Get single environment VS Code MCP configuration"""
        return {
            "servers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-test.company.com",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "TEST_SERVICE",
                        "ORACLE_USERNAME": "test_user",
                        "ORACLE_PASSWORD": "test_password",
                        "CONNECTION_TIMEOUT": "30",
                        "QUERY_TIMEOUT": "300",
                        "MAX_ROWS": "1000"
                    }
                }
            }
        }
    
    @staticmethod
    def get_multi_environment_config(project_path: str) -> Dict[str, Any]:
        """Get multi-environment VS Code MCP configuration"""
        return {
            "servers": {
                "oracle-dev": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-dev.company.com",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "DEV_SERVICE",
                        "ORACLE_USERNAME": "dev_user",
                        "ORACLE_PASSWORD": "dev_password",
                        "CONNECTION_TIMEOUT": "30",
                        "QUERY_TIMEOUT": "300",
                        "MAX_ROWS": "500"
                    }
                },
                "oracle-staging": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-staging.company.com",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "STAGING_SERVICE",
                        "ORACLE_USERNAME": "staging_user",
                        "ORACLE_PASSWORD": "staging_password",
                        "CONNECTION_TIMEOUT": "30",
                        "QUERY_TIMEOUT": "300",
                        "MAX_ROWS": "1000"
                    }
                },
                "oracle-prod": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-prod.company.com",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "PROD_SERVICE",
                        "ORACLE_USERNAME": "readonly_user",
                        "ORACLE_PASSWORD": "secure_production_password",
                        "CONNECTION_TIMEOUT": "30",
                        "QUERY_TIMEOUT": "300",
                        "MAX_ROWS": "1000"
                    }
                }
            }
        }
    
    @staticmethod
    def get_pip_based_config(project_path: str) -> Dict[str, Any]:
        """Get pip-based VS Code MCP configuration (alternative to UV)"""
        return {
            "servers": {
                "oracle-db": {
                    "command": "python",
                    "args": ["main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-pip.company.com",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "PIP_SERVICE",
                        "ORACLE_USERNAME": "pip_user",
                        "ORACLE_PASSWORD": "pip_password",
                        "MAX_ROWS": "1000"
                    }
                }
            }
        }
    
    @staticmethod
    def get_minimal_config(project_path: str) -> Dict[str, Any]:
        """Get minimal VS Code MCP configuration with only required parameters"""
        return {
            "servers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-minimal.company.com",
                        "ORACLE_SERVICE_NAME": "MINIMAL_SERVICE",
                        "ORACLE_USERNAME": "minimal_user",
                        "ORACLE_PASSWORD": "minimal_password"
                    }
                }
            }
        }
    
    @staticmethod
    def get_development_config(project_path: str) -> Dict[str, Any]:
        """Get development-optimized VS Code MCP configuration"""
        return {
            "servers": {
                "oracle-dev": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "localhost",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "XEPDB1",
                        "ORACLE_USERNAME": "dev_user",
                        "ORACLE_PASSWORD": "dev_password",
                        "CONNECTION_TIMEOUT": "10",
                        "QUERY_TIMEOUT": "60",
                        "MAX_ROWS": "100"
                    }
                }
            }
        }
    
    @staticmethod
    def get_production_config(project_path: str) -> Dict[str, Any]:
        """Get production-optimized VS Code MCP configuration"""
        return {
            "servers": {
                "oracle-prod": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-prod.company.com",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "PROD_SERVICE",
                        "ORACLE_USERNAME": "readonly_user",
                        "ORACLE_PASSWORD": "secure_production_password",
                        "CONNECTION_TIMEOUT": "60",
                        "QUERY_TIMEOUT": "600",
                        "MAX_ROWS": "5000"
                    }
                }
            }
        }
    
    @staticmethod
    def get_invalid_config_missing_required() -> Dict[str, Any]:
        """Get invalid VS Code MCP configuration missing required parameters"""
        return {
            "servers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": "/path/to/project",
                    "env": {
                        "ORACLE_HOST": "oracle-invalid.company.com",
                        # Missing ORACLE_SERVICE_NAME, ORACLE_USERNAME, ORACLE_PASSWORD
                        "MAX_ROWS": "1000"
                    }
                }
            }
        }
    
    @staticmethod
    def get_invalid_config_malformed_json() -> str:
        """Get malformed JSON configuration for testing error handling"""
        return '''
        {
            "servers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],
                    "cwd": "/path/to/project",
                    "env": {
                        "ORACLE_HOST": "oracle-malformed.company.com",
                        "ORACLE_SERVICE_NAME": "MALFORMED_SERVICE",
                        "ORACLE_USERNAME": "malformed_user",
                        "ORACLE_PASSWORD": "malformed_password"
                    }
                }
            }
            // Missing closing brace - invalid JSON
        '''
    
    @staticmethod
    def validate_config_structure(config: Dict[str, Any]) -> bool:
        """Validate VS Code MCP configuration structure"""
        try:
            # Check top-level structure
            if "servers" not in config:
                return False
            
            servers = config["servers"]
            if not isinstance(servers, dict):
                return False
            
            # Check each server configuration
            for server_name, server_config in servers.items():
                # Required fields
                required_fields = ["command", "args", "cwd"]
                for field in required_fields:
                    if field not in server_config:
                        return False
                
                # Check environment parameters if present
                if "env" in server_config:
                    env_params = server_config["env"]
                    if not isinstance(env_params, dict):
                        return False
                    
                    # Check for required Oracle parameters
                    oracle_required = ["ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"]
                    for param in oracle_required:
                        if param not in env_params:
                            return False
                        if not env_params[param]:  # Check not empty
                            return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def get_all_test_configs(project_path: str) -> Dict[str, Dict[str, Any]]:
        """Get all test configurations for comprehensive testing"""
        return {
            "single_environment": VSCodeMCPConfigs.get_single_environment_config(project_path),
            "multi_environment": VSCodeMCPConfigs.get_multi_environment_config(project_path),
            "pip_based": VSCodeMCPConfigs.get_pip_based_config(project_path),
            "minimal": VSCodeMCPConfigs.get_minimal_config(project_path),
            "development": VSCodeMCPConfigs.get_development_config(project_path),
            "production": VSCodeMCPConfigs.get_production_config(project_path),
            "invalid_missing_required": VSCodeMCPConfigs.get_invalid_config_missing_required()
        }
    
    @staticmethod
    def save_config_to_file(config: Dict[str, Any], file_path: str) -> None:
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def load_config_from_file(file_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)


# Example usage and validation
if __name__ == "__main__":
    # Test configuration validation
    test_project_path = "/path/to/test/project"
    
    # Test valid configurations
    valid_configs = [
        VSCodeMCPConfigs.get_single_environment_config(test_project_path),
        VSCodeMCPConfigs.get_multi_environment_config(test_project_path),
        VSCodeMCPConfigs.get_minimal_config(test_project_path)
    ]
    
    for i, config in enumerate(valid_configs):
        is_valid = VSCodeMCPConfigs.validate_config_structure(config)
        print(f"Config {i+1} validation: {'PASS' if is_valid else 'FAIL'}")
    
    # Test invalid configuration
    invalid_config = VSCodeMCPConfigs.get_invalid_config_missing_required()
    is_valid = VSCodeMCPConfigs.validate_config_structure(invalid_config)
    print(f"Invalid config validation: {'FAIL' if not is_valid else 'UNEXPECTED PASS'}")
    
    # Test JSON serialization
    test_config = VSCodeMCPConfigs.get_single_environment_config(test_project_path)
    json_str = json.dumps(test_config, indent=2)
    print(f"JSON serialization: {'PASS' if json_str else 'FAIL'}")