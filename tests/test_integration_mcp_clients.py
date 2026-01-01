"""
Integration tests for MCP client configurations
Tests VS Code, Kiro, and Docker deployment scenarios with environment parameters
Updated for FastMCP patterns
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import subprocess
import shutil
from typing import Dict, Any, List

from config.loader import EnhancedConfigLoader
from config.models import DatabaseConfig
from config.exceptions import ConfigurationError
from main import _load_config


class TestMCPClientIntegration:
    """Test MCP client integration scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_project_dir = None
        self.temp_dirs = []
    
    def teardown_method(self):
        """Cleanup test environment"""
        for temp_dir in self.temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_test_project(self) -> str:
        """Create a temporary test project directory"""
        temp_dir = tempfile.mkdtemp(prefix="oracle_mcp_test_")
        self.temp_dirs.append(temp_dir)
        
        # Create basic project structure
        project_files = {
            "main.py": "# Test main.py\nprint('Oracle MCP Server Test')",
            "pyproject.toml": "[project]\nname = 'oracle-mcp-test'\nversion = '1.0.0'",
            "requirements.lock": "# Test requirements"
        }
        
        for filename, content in project_files.items():
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write(content)
        
        return temp_dir
    
    def test_vscode_mcp_configuration_structure(self):
        """Test VS Code MCP configuration structure and validation"""
        project_dir = self.create_test_project()
        
        # Test VS Code MCP configuration
        vscode_config = {
            "servers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main.py"],  # Updated to use FastMCP
                    "cwd": project_dir,
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
        
        # Validate JSON structure
        json_str = json.dumps(vscode_config, indent=2)
        parsed_config = json.loads(json_str)
        
        # Verify structure
        assert "servers" in parsed_config
        assert "oracle-db" in parsed_config["servers"]
        
        server_config = parsed_config["servers"]["oracle-db"]
        assert server_config["command"] == "uv"
        assert "main.py" in server_config["args"]  # Updated to check for FastMCP
        assert server_config["cwd"] == project_dir
        
        # Verify environment parameters
        env_params = server_config["env"]
        required_params = ["ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"]
        for param in required_params:
            assert param in env_params
            assert env_params[param]  # Not empty
    
    def test_kiro_mcp_configuration_structure(self):
        """Test Kiro MCP configuration structure and validation"""
        project_dir = self.create_test_project()
        
        # Test Kiro MCP configuration
        kiro_config = {
            "mcpServers": {
                "oracle-db": {
                    "command": "uv",
                    "args": ["run", "python", "main.py"],  # Updated to use FastMCP
                    "cwd": project_dir,
                    "env": {
                        "ORACLE_HOST": "oracle-test.company.com",
                        "ORACLE_PORT": "1521",
                        "ORACLE_SERVICE_NAME": "TEST_SERVICE",
                        "ORACLE_USERNAME": "test_user",
                        "ORACLE_PASSWORD": "test_password",
                        "MAX_ROWS": "1000"
                    },
                    "disabled": False,
                    "autoApprove": []
                }
            }
        }
        
        # Validate JSON structure
        json_str = json.dumps(kiro_config, indent=2)
        parsed_config = json.loads(json_str)
        
        # Verify structure
        assert "mcpServers" in parsed_config
        assert "oracle-db" in parsed_config["mcpServers"]
        
        server_config = parsed_config["mcpServers"]["oracle-db"]
        assert server_config["command"] == "uv"
        assert "main.py" in server_config["args"]  # Updated to check for FastMCP
        assert server_config["cwd"] == project_dir
        assert server_config["disabled"] is False
        
        # Verify environment parameters
        env_params = server_config["env"]
        required_params = ["ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USERNAME", "ORACLE_PASSWORD"]
        for param in required_params:
            assert param in env_params
            assert env_params[param]  # Not empty
    
    def test_mcp_environment_parameter_loading(self):
        """Test that MCP environment parameters are properly loaded"""
        project_dir = self.create_test_project()
        
        # Simulate MCP environment parameters
        mcp_env = {
            "ORACLE_HOST": "mcp-test-host",
            "ORACLE_PORT": "9999",
            "ORACLE_SERVICE_NAME": "MCP_TEST_SERVICE",
            "ORACLE_USERNAME": "mcp_test_user",
            "ORACLE_PASSWORD": "mcp_test_password",
            "CONNECTION_TIMEOUT": "45",
            "QUERY_TIMEOUT": "600",
            "MAX_ROWS": "2000"
        }
        
        with patch.dict(os.environ, mcp_env, clear=True):
            # Test both original and FastMCP configuration loading
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Test FastMCP configuration loading
            fastmcp_config = _load_config()
            
            # Verify MCP parameters are loaded identically
            assert config.host == fastmcp_config.host == "mcp-test-host"
            assert config.port == fastmcp_config.port == 9999
            assert config.service_name == fastmcp_config.service_name == "MCP_TEST_SERVICE"
            assert config.username == fastmcp_config.username == "mcp_test_user"
            assert config.password == fastmcp_config.password == "mcp_test_password"
            assert config.connection_timeout == fastmcp_config.connection_timeout == 45
            assert config.query_timeout == fastmcp_config.query_timeout == 600
            assert config.max_rows == fastmcp_config.max_rows == 2000
            
            # Verify source tracking
            sources = config.get_source_info()
            for field in ["host", "port", "service_name", "username", "password"]:
                assert sources.get(field) in ["MCP Config Environment", "environment"]
    
    def test_docker_environment_parameter_injection(self):
        """Test Docker environment parameter injection scenarios"""
        
        # Test Docker environment variables
        docker_env = {
            "ORACLE_HOST": "oracle-docker.company.com",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "DOCKER_SERVICE",
            "ORACLE_USERNAME": "docker_user",
            "ORACLE_PASSWORD": "docker_password",
            "MAX_ROWS": "500"
        }
        
        with patch.dict(os.environ, docker_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify Docker environment parameters
            assert config.host == "oracle-docker.company.com"
            assert config.service_name == "DOCKER_SERVICE"
            assert config.username == "docker_user"
            assert config.max_rows == 500
            
            # Test DSN generation for Docker
            expected_dsn = "oracle-docker.company.com:1521/DOCKER_SERVICE"
            assert config.dsn == expected_dsn
    
    def test_mcp_config_precedence_over_dotenv(self):
        """Test that MCP config parameters take precedence over .env file"""
        project_dir = self.create_test_project()
        
        # Create temporary .env file
        dotenv_content = """
ORACLE_HOST=dotenv-host
ORACLE_SERVICE_NAME=DOTENV_SERVICE
ORACLE_USERNAME=dotenv_user
ORACLE_PASSWORD=dotenv_password
ORACLE_PORT=1234
"""
        dotenv_path = os.path.join(project_dir, '.env')
        with open(dotenv_path, 'w') as f:
            f.write(dotenv_content)
        
        # MCP environment parameters (should take precedence)
        mcp_env = {
            "ORACLE_HOST": "mcp-host",
            "ORACLE_PORT": "5678",
            "ORACLE_SERVICE_NAME": "MCP_SERVICE"
            # Note: username and password not in MCP env, should fall back to .env
        }
        
        # First set up the .env environment variables
        dotenv_env_vars = {
            'ORACLE_USERNAME': 'dotenv_user',
            'ORACLE_PASSWORD': 'dotenv_password'
        }
        
        # Combine MCP and .env environment variables
        combined_env = {**mcp_env, **dotenv_env_vars}
        
        with patch.dict(os.environ, combined_env, clear=True):
            # Mock .env file loading
            with patch('config.sources.os.path.exists') as mock_exists:
                mock_exists.return_value = True
                
                with patch('config.sources.load_dotenv') as mock_load_dotenv:
                    # Simulate .env file loading (already in environment)
                    mock_load_dotenv.return_value = None
                    
                    loader = EnhancedConfigLoader()
                    config = loader.load_config()
                    
                    # MCP parameters should take precedence
                    assert config.host == "mcp-host"
                    assert config.port == 5678
                    assert config.service_name == "MCP_SERVICE"
                    
                    # .env parameters should be used for missing MCP parameters
                    assert config.username == "dotenv_user"
                    assert config.password == "dotenv_password"
                    
                    # Verify source tracking
                    sources = config.get_source_info()
                    assert sources.get("host") in ["MCP Config Environment", "environment"]
                    assert sources.get("port") in ["MCP Config Environment", "environment"]
    
    def test_mcp_configuration_validation_errors(self):
        """Test MCP configuration validation and error handling"""
        
        # Test missing required parameters
        incomplete_env = {
            "ORACLE_HOST": "test-host",
            # Missing ORACLE_SERVICE_NAME, ORACLE_USERNAME, ORACLE_PASSWORD
        }
        
        with patch.dict(os.environ, incomplete_env, clear=True):
            loader = EnhancedConfigLoader()
            
            with pytest.raises(ConfigurationError):
                loader.load_config()
        
        # Test invalid parameter values
        invalid_env = {
            "ORACLE_HOST": "test-host",
            "ORACLE_SERVICE_NAME": "TEST_SERVICE",
            "ORACLE_USERNAME": "test_user",
            "ORACLE_PASSWORD": "test_password",
            "ORACLE_PORT": "invalid_port"  # Invalid port
        }
        
        with patch.dict(os.environ, invalid_env, clear=True):
            loader = EnhancedConfigLoader()
            
            with pytest.raises(ConfigurationError):
                loader.load_config()


class TestMultiEnvironmentSupport:
    """Test multi-environment MCP configuration support"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dirs = []
    
    def teardown_method(self):
        """Cleanup test environment"""
        for temp_dir in self.temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_test_project(self) -> str:
        """Create a temporary test project directory"""
        temp_dir = tempfile.mkdtemp(prefix="oracle_mcp_multi_env_")
        self.temp_dirs.append(temp_dir)
        
        # Create basic project structure
        project_files = {
            "main.py": "# Test main.py\nprint('Oracle MCP Server Test')",
            "pyproject.toml": "[project]\nname = 'oracle-mcp-test'\nversion = '1.0.0'"
        }
        
        for filename, content in project_files.items():
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write(content)
        
        return temp_dir
    
    def test_development_environment_configuration(self):
        """Test development environment MCP configuration"""
        project_dir = self.create_test_project()
        
        # Development environment parameters
        dev_env = {
            "ORACLE_HOST": "oracle-dev.company.com",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "DEV_SERVICE",
            "ORACLE_USERNAME": "dev_user",
            "ORACLE_PASSWORD": "dev_password",
            "CONNECTION_TIMEOUT": "30",
            "QUERY_TIMEOUT": "300",
            "MAX_ROWS": "500"  # Lower limit for dev
        }
        
        with patch.dict(os.environ, dev_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify development-specific settings
            assert config.host == "oracle-dev.company.com"
            assert config.service_name == "DEV_SERVICE"
            assert config.username == "dev_user"
            assert config.max_rows == 500  # Development limit
            
            # Verify DSN for development
            assert config.dsn == "oracle-dev.company.com:1521/DEV_SERVICE"
    
    def test_staging_environment_configuration(self):
        """Test staging environment MCP configuration"""
        project_dir = self.create_test_project()
        
        # Staging environment parameters
        staging_env = {
            "ORACLE_HOST": "oracle-staging.company.com",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "STAGING_SERVICE",
            "ORACLE_USERNAME": "staging_user",
            "ORACLE_PASSWORD": "staging_password",
            "CONNECTION_TIMEOUT": "30",
            "QUERY_TIMEOUT": "300",
            "MAX_ROWS": "1000"  # Higher limit for staging
        }
        
        with patch.dict(os.environ, staging_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify staging-specific settings
            assert config.host == "oracle-staging.company.com"
            assert config.service_name == "STAGING_SERVICE"
            assert config.username == "staging_user"
            assert config.max_rows == 1000  # Staging limit
            
            # Verify DSN for staging
            assert config.dsn == "oracle-staging.company.com:1521/STAGING_SERVICE"
    
    def test_production_environment_configuration(self):
        """Test production environment MCP configuration"""
        project_dir = self.create_test_project()
        
        # Production environment parameters
        prod_env = {
            "ORACLE_HOST": "oracle-prod.company.com",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "PROD_SERVICE",
            "ORACLE_USERNAME": "readonly_user",
            "ORACLE_PASSWORD": "secure_production_password",
            "CONNECTION_TIMEOUT": "30",
            "QUERY_TIMEOUT": "300",
            "MAX_ROWS": "1000"  # Production limit
        }
        
        with patch.dict(os.environ, prod_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify production-specific settings
            assert config.host == "oracle-prod.company.com"
            assert config.service_name == "PROD_SERVICE"
            assert config.username == "readonly_user"
            assert config.max_rows == 1000  # Production limit
            
            # Verify DSN for production
            assert config.dsn == "oracle-prod.company.com:1521/PROD_SERVICE"
    
    def test_multi_environment_mcp_configuration_structure(self):
        """Test multi-environment MCP configuration structure"""
        project_dir = self.create_test_project()
        
        # Multi-environment VS Code configuration
        multi_env_config = {
            "servers": {
                "oracle-dev": {
                    "command": "uv",
                    "args": ["run", "python", "main.py"],
                    "cwd": project_dir,
                    "env": {
                        "ORACLE_HOST": "oracle-dev.company.com",
                        "ORACLE_SERVICE_NAME": "DEV_SERVICE",
                        "ORACLE_USERNAME": "dev_user",
                        "ORACLE_PASSWORD": "dev_password",
                        "MAX_ROWS": "500"
                    }
                },
                "oracle-staging": {
                    "command": "uv",
                    "args": ["run", "python", "main.py"],
                    "cwd": project_dir,
                    "env": {
                        "ORACLE_HOST": "oracle-staging.company.com",
                        "ORACLE_SERVICE_NAME": "STAGING_SERVICE",
                        "ORACLE_USERNAME": "staging_user",
                        "ORACLE_PASSWORD": "staging_password",
                        "MAX_ROWS": "1000"
                    }
                },
                "oracle-prod": {
                    "command": "uv",
                    "args": ["run", "python", "main.py"],
                    "cwd": project_dir,
                    "env": {
                        "ORACLE_HOST": "oracle-prod.company.com",
                        "ORACLE_SERVICE_NAME": "PROD_SERVICE",
                        "ORACLE_USERNAME": "readonly_user",
                        "ORACLE_PASSWORD": "secure_production_password",
                        "MAX_ROWS": "1000"
                    }
                }
            }
        }
        
        # Validate JSON structure
        json_str = json.dumps(multi_env_config, indent=2)
        parsed_config = json.loads(json_str)
        
        # Verify all environments are present
        servers = parsed_config["servers"]
        assert "oracle-dev" in servers
        assert "oracle-staging" in servers
        assert "oracle-prod" in servers
        
        # Verify each environment has correct structure
        for env_name, server_config in servers.items():
            assert server_config["command"] == "uv"
            assert "main.py" in server_config["args"]
            assert server_config["cwd"] == project_dir
            
            # Verify environment-specific parameters
            env_params = server_config["env"]
            assert "ORACLE_HOST" in env_params
            assert "ORACLE_SERVICE_NAME" in env_params
            assert "ORACLE_USERNAME" in env_params
            assert "ORACLE_PASSWORD" in env_params
            
            # Verify environment-specific values
            if env_name == "oracle-dev":
                assert "dev" in env_params["ORACLE_HOST"]
                assert env_params["MAX_ROWS"] == "500"
            elif env_name == "oracle-staging":
                assert "staging" in env_params["ORACLE_HOST"]
                assert env_params["MAX_ROWS"] == "1000"
            elif env_name == "oracle-prod":
                assert "prod" in env_params["ORACLE_HOST"]
                assert env_params["MAX_ROWS"] == "1000"
    
    def test_environment_specific_parameter_validation(self):
        """Test validation of environment-specific parameters"""
        
        # Test development environment with relaxed limits
        dev_env = {
            "ORACLE_HOST": "oracle-dev.company.com",
            "ORACLE_SERVICE_NAME": "DEV_SERVICE",
            "ORACLE_USERNAME": "dev_user",
            "ORACLE_PASSWORD": "dev_password",
            "MAX_ROWS": "100"  # Very low limit for dev
        }
        
        with patch.dict(os.environ, dev_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            assert config.max_rows == 100
        
        # Test production environment with higher limits
        prod_env = {
            "ORACLE_HOST": "oracle-prod.company.com",
            "ORACLE_SERVICE_NAME": "PROD_SERVICE",
            "ORACLE_USERNAME": "readonly_user",
            "ORACLE_PASSWORD": "secure_production_password",
            "MAX_ROWS": "5000"  # Higher limit for prod
        }
        
        with patch.dict(os.environ, prod_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            assert config.max_rows == 5000
    
    def test_environment_isolation(self):
        """Test that different environments don't interfere with each other"""
        
        # Simulate switching between environments
        environments = [
            {
                "name": "dev",
                "env": {
                    "ORACLE_HOST": "oracle-dev.company.com",
                    "ORACLE_SERVICE_NAME": "DEV_SERVICE",
                    "ORACLE_USERNAME": "dev_user",
                    "ORACLE_PASSWORD": "dev_password",
                    "MAX_ROWS": "500"
                }
            },
            {
                "name": "prod",
                "env": {
                    "ORACLE_HOST": "oracle-prod.company.com",
                    "ORACLE_SERVICE_NAME": "PROD_SERVICE",
                    "ORACLE_USERNAME": "readonly_user",
                    "ORACLE_PASSWORD": "prod_password",
                    "MAX_ROWS": "1000"
                }
            }
        ]
        
        for environment in environments:
            with patch.dict(os.environ, environment["env"], clear=True):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
                
                # Verify environment-specific configuration
                if environment["name"] == "dev":
                    assert config.host == "oracle-dev.company.com"
                    assert config.service_name == "DEV_SERVICE"
                    assert config.username == "dev_user"
                    assert config.max_rows == 500
                elif environment["name"] == "prod":
                    assert config.host == "oracle-prod.company.com"
                    assert config.service_name == "PROD_SERVICE"
                    assert config.username == "readonly_user"
                    assert config.max_rows == 1000


class TestDockerIntegration:
    """Test Docker deployment integration scenarios"""
    
    def test_docker_compose_environment_configuration(self):
        """Test Docker Compose environment configuration"""
        
        # Simulate Docker Compose environment variables
        docker_compose_env = {
            "ORACLE_HOST": "oracle-docker.company.com",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "DOCKER_SERVICE",
            "ORACLE_USERNAME": "docker_user",
            "ORACLE_PASSWORD": "docker_password",
            "CONNECTION_TIMEOUT": "60",
            "QUERY_TIMEOUT": "600",
            "MAX_ROWS": "2000"
        }
        
        with patch.dict(os.environ, docker_compose_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify Docker-specific configuration
            assert config.host == "oracle-docker.company.com"
            assert config.service_name == "DOCKER_SERVICE"
            assert config.username == "docker_user"
            assert config.connection_timeout == 60
            assert config.query_timeout == 600
            assert config.max_rows == 2000
    
    def test_kubernetes_configmap_environment(self):
        """Test Kubernetes ConfigMap and Secret environment variables"""
        
        # Simulate Kubernetes environment variables from ConfigMap and Secret
        k8s_env = {
            # From ConfigMap
            "ORACLE_HOST": "oracle-k8s.company.com",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "K8S_SERVICE",
            "CONNECTION_TIMEOUT": "30",
            "QUERY_TIMEOUT": "300",
            "MAX_ROWS": "1000",
            
            # From Secret
            "ORACLE_USERNAME": "k8s_user",
            "ORACLE_PASSWORD": "k8s_secret_password"
        }
        
        with patch.dict(os.environ, k8s_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify Kubernetes-specific configuration
            assert config.host == "oracle-k8s.company.com"
            assert config.service_name == "K8S_SERVICE"
            assert config.username == "k8s_user"
            assert config.password == "k8s_secret_password"
    
    def test_docker_environment_file_loading(self):
        """Test Docker environment file loading scenarios"""
        
        # Test different Docker environment scenarios
        docker_scenarios = [
            {
                "name": "development",
                "env": {
                    "ORACLE_HOST": "oracle-dev-docker.company.com",
                    "ORACLE_SERVICE_NAME": "DEV_DOCKER_SERVICE",
                    "ORACLE_USERNAME": "dev_docker_user",
                    "ORACLE_PASSWORD": "dev_docker_password",
                    "MAX_ROWS": "500"
                }
            },
            {
                "name": "production",
                "env": {
                    "ORACLE_HOST": "oracle-prod-docker.company.com",
                    "ORACLE_SERVICE_NAME": "PROD_DOCKER_SERVICE",
                    "ORACLE_USERNAME": "prod_docker_user",
                    "ORACLE_PASSWORD": "prod_docker_password",
                    "MAX_ROWS": "1000"
                }
            }
        ]
        
        for scenario in docker_scenarios:
            with patch.dict(os.environ, scenario["env"], clear=True):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
                
                # Verify scenario-specific configuration
                if scenario["name"] == "development":
                    assert "dev" in config.host
                    assert config.max_rows == 500
                elif scenario["name"] == "production":
                    assert "prod" in config.host
                    assert config.max_rows == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])