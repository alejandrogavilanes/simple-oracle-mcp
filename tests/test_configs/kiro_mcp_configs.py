"""
Test MCP configuration files for Kiro integration
Contains various Kiro MCP configuration scenarios for testing
"""

import json
from typing import Dict, Any, List


class KiroMCPConfigs:
    """Kiro MCP configuration templates for testing"""
    
    @staticmethod
    def get_single_environment_config(project_path: str) -> Dict[str, Any]:
        """Get single environment Kiro MCP configuration"""
        return {
            "mcpServers": {
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
                    },
                    "disabled": False,
                    "autoApprove": []
                }
            }
        }
    
    @staticmethod
    def get_multi_environment_config(project_path: str) -> Dict[str, Any]:
        """Get multi-environment Kiro MCP configuration"""
        return {
            "mcpServers": {
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
                        "MAX_ROWS": "500"
                    },
                    "disabled": False,
                    "autoApprove": []
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
                        "MAX_ROWS": "1000"
                    },
                    "disabled": False,
                    "autoApprove": ["query_oracle"]
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
                        "MAX_ROWS": "1000"
                    },
                    "disabled": False,
                    "autoApprove": ["query_oracle", "describe_table"]
                }
            }
        }
    
    @staticmethod
    def get_auto_approve_config(project_path: str) -> Dict[str, Any]:
        """Get Kiro MCP configuration with auto-approve settings"""
        return {
            "mcpServers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-auto.company.com",
                        "ORACLE_SERVICE_NAME": "AUTO_SERVICE",
                        "ORACLE_USERNAME": "auto_user",
                        "ORACLE_PASSWORD": "auto_password",
                        "MAX_ROWS": "1000"
                    },
                    "disabled": False,
                    "autoApprove": [
                        "query_oracle",
                        "describe_table"
                    ]
                }
            }
        }
    
    @staticmethod
    def get_disabled_server_config(project_path: str) -> Dict[str, Any]:
        """Get Kiro MCP configuration with disabled server"""
        return {
            "mcpServers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-disabled.company.com",
                        "ORACLE_SERVICE_NAME": "DISABLED_SERVICE",
                        "ORACLE_USERNAME": "disabled_user",
                        "ORACLE_PASSWORD": "disabled_password"
                    },
                    "disabled": True,
                    "autoApprove": []
                }
            }
        }
    
    @staticmethod
    def get_pip_based_config(project_path: str) -> Dict[str, Any]:
        """Get pip-based Kiro MCP configuration (alternative to UV)"""
        return {
            "mcpServers": {
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
                    },
                    "disabled": False,
                    "autoApprove": []
                }
            }
        }
    
    @staticmethod
    def get_minimal_config(project_path: str) -> Dict[str, Any]:
        """Get minimal Kiro MCP configuration with only required parameters"""
        return {
            "mcpServers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": "oracle-minimal.company.com",
                        "ORACLE_SERVICE_NAME": "MINIMAL_SERVICE",
                        "ORACLE_USERNAME": "minimal_user",
                        "ORACLE_PASSWORD": "minimal_password"
                    },
                    "disabled": False
                }
            }
        }
    
    @staticmethod
    def get_development_config(project_path: str) -> Dict[str, Any]:
        """Get development-optimized Kiro MCP configuration"""
        return {
            "mcpServers": {
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
                    },
                    "disabled": False,
                    "autoApprove": [
                        "query_oracle",
                        "describe_table"
                    ]
                }
            }
        }
    
    @staticmethod
    def get_production_config(project_path: str) -> Dict[str, Any]:
        """Get production-optimized Kiro MCP configuration"""
        return {
            "mcpServers": {
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
                    },
                    "disabled": False,
                    "autoApprove": []  # No auto-approve for production
                }
            }
        }
    
    @staticmethod
    def get_workspace_specific_config(project_path: str, workspace_name: str) -> Dict[str, Any]:
        """Get workspace-specific Kiro MCP configuration"""
        return {
            "mcpServers": {
                f"oracle-{workspace_name}": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": project_path,
                    "env": {
                        "ORACLE_HOST": f"oracle-{workspace_name}.company.com",
                        "ORACLE_SERVICE_NAME": f"{workspace_name.upper()}_SERVICE",
                        "ORACLE_USERNAME": f"{workspace_name}_user",
                        "ORACLE_PASSWORD": f"{workspace_name}_password",
                        "MAX_ROWS": "1000"
                    },
                    "disabled": False,
                    "autoApprove": []
                }
            }
        }
    
    @staticmethod
    def get_invalid_config_missing_required() -> Dict[str, Any]:
        """Get invalid Kiro MCP configuration missing required parameters"""
        return {
            "mcpServers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],  # Updated for FastMCP
                    "cwd": "/path/to/project",
                    "env": {
                        "ORACLE_HOST": "oracle-invalid.company.com",
                        # Missing ORACLE_SERVICE_NAME, ORACLE_USERNAME, ORACLE_PASSWORD
                        "MAX_ROWS": "1000"
                    },
                    "disabled": False,
                    "autoApprove": []
                }
            }
        }
    
    @staticmethod
    def get_invalid_config_malformed_json() -> str:
        """Get malformed JSON configuration for testing error handling"""
        return '''
        {
            "mcpServers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main_fastmcp.py"],
                    "cwd": "/path/to/project",
                    "env": {
                        "ORACLE_HOST": "oracle-malformed.company.com",
                        "ORACLE_SERVICE_NAME": "MALFORMED_SERVICE",
                        "ORACLE_USERNAME": "malformed_user",
                        "ORACLE_PASSWORD": "malformed_password"
                    },
                    "disabled": false,
                    "autoApprove": []
                }
            }
            // Missing closing brace - invalid JSON
        '''
    
    @staticmethod
    def validate_config_structure(config: Dict[str, Any]) -> bool:
        """Validate Kiro MCP configuration structure"""
        try:
            # Check top-level structure
            if "mcpServers" not in config:
                return False
            
            servers = config["mcpServers"]
            if not isinstance(servers, dict):
                return False
            
            # Check each server configuration
            for server_name, server_config in servers.items():
                # Required fields
                required_fields = ["command", "args", "cwd", "disabled"]
                for field in required_fields:
                    if field not in server_config:
                        return False
                
                # Check disabled field type
                if not isinstance(server_config["disabled"], bool):
                    return False
                
                # Check autoApprove field if present
                if "autoApprove" in server_config:
                    if not isinstance(server_config["autoApprove"], list):
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
            "single_environment": KiroMCPConfigs.get_single_environment_config(project_path),
            "multi_environment": KiroMCPConfigs.get_multi_environment_config(project_path),
            "auto_approve": KiroMCPConfigs.get_auto_approve_config(project_path),
            "disabled_server": KiroMCPConfigs.get_disabled_server_config(project_path),
            "pip_based": KiroMCPConfigs.get_pip_based_config(project_path),
            "minimal": KiroMCPConfigs.get_minimal_config(project_path),
            "development": KiroMCPConfigs.get_development_config(project_path),
            "production": KiroMCPConfigs.get_production_config(project_path),
            "workspace_specific": KiroMCPConfigs.get_workspace_specific_config(project_path, "test"),
            "invalid_missing_required": KiroMCPConfigs.get_invalid_config_missing_required()
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
    
    @staticmethod
    def get_kiro_specific_features() -> Dict[str, Any]:
        """Get Kiro-specific MCP configuration features"""
        return {
            "features": {
                "autoApprove": {
                    "description": "List of tool names that don't require user approval",
                    "type": "array",
                    "items": "string",
                    "examples": ["query_oracle", "describe_table"]
                },
                "disabled": {
                    "description": "Whether the MCP server is disabled",
                    "type": "boolean",
                    "default": False
                }
            },
            "supported_tools": [
                "query_oracle",
                "describe_table"
            ],
            "configuration_locations": [
                ".kiro/settings/mcp.json",
                "~/.kiro/settings/mcp.json"
            ]
        }


# Example usage and validation
if __name__ == "__main__":
    # Test configuration validation
    test_project_path = "/path/to/test/project"
    
    # Test valid configurations
    valid_configs = [
        KiroMCPConfigs.get_single_environment_config(test_project_path),
        KiroMCPConfigs.get_multi_environment_config(test_project_path),
        KiroMCPConfigs.get_minimal_config(test_project_path)
    ]
    
    for i, config in enumerate(valid_configs):
        is_valid = KiroMCPConfigs.validate_config_structure(config)
        print(f"Config {i+1} validation: {'PASS' if is_valid else 'FAIL'}")
    
    # Test invalid configuration
    invalid_config = KiroMCPConfigs.get_invalid_config_missing_required()
    is_valid = KiroMCPConfigs.validate_config_structure(invalid_config)
    print(f"Invalid config validation: {'FAIL' if not is_valid else 'UNEXPECTED PASS'}")
    
    # Test JSON serialization
    test_config = KiroMCPConfigs.get_single_environment_config(test_project_path)
    json_str = json.dumps(test_config, indent=2)
    print(f"JSON serialization: {'PASS' if json_str else 'FAIL'}")
    
    # Test Kiro-specific features
    features = KiroMCPConfigs.get_kiro_specific_features()
    print(f"Kiro features loaded: {'PASS' if features else 'FAIL'}")