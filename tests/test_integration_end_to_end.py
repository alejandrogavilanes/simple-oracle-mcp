"""
End-to-end integration tests for MCP client functionality
Tests complete workflows from MCP configuration to server operation
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
from tests.test_configs.vscode_mcp_configs import VSCodeMCPConfigs
from tests.test_configs.kiro_mcp_configs import KiroMCPConfigs
from main import _load_config, mcp


class TestEndToEndIntegration:
    """End-to-end integration tests for MCP client workflows"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dirs = []
        self.test_project_dir = None
    
    def teardown_method(self):
        """Cleanup test environment"""
        for temp_dir in self.temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_test_project(self) -> str:
        """Create a complete test project directory"""
        temp_dir = tempfile.mkdtemp(prefix="oracle_mcp_e2e_test_")
        self.temp_dirs.append(temp_dir)
        self.test_project_dir = temp_dir
        
        # Create complete project structure
        project_files = {
            "main_fastmcp.py": """#!/usr/bin/env python3
# Test Oracle MCP Server - FastMCP Implementation
import os
import asyncio
from config.loader import EnhancedConfigLoader
from main_fastmcp import _load_config, mcp

async def main():
    print("Oracle MCP Server Test (FastMCP) - Starting")
    try:
        config = _load_config()
        print(f"Configuration loaded: {config.host}:{config.port}/{config.service_name}")
        print("Oracle MCP Server Test (FastMCP) - Success")
    except Exception as e:
        print(f"Oracle MCP Server Test (FastMCP) - Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
""",
            "test_connection.py": """#!/usr/bin/env python3
# Test connection script for health checks
import os
from config.loader import EnhancedConfigLoader

def test_connection():
    try:
        loader = EnhancedConfigLoader()
        config = loader.load_config()
        print(f"Connection test: {config.dsn}")
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
""",
            "pyproject.toml": """[project]
name = "oracle-mcp-test"
version = "1.0.0"
description = "Test Oracle MCP Server"
dependencies = [
    "fastmcp>=0.1.0",
    "oracledb>=1.4.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "structlog>=23.0.0"
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
""",
            "requirements.lock": """# Test requirements
fastmcp==0.1.0
oracledb==1.4.0
python-dotenv==1.0.0
pydantic==2.0.0
structlog==23.0.0
""",
            "uv.lock": "# UV lock file placeholder",
            ".gitignore": """
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.env
.env.*
logs/
*.log
""",
            "README.md": """# Test Oracle MCP Server

Test project for Oracle MCP Server integration testing with FastMCP.

## Usage

```bash
uv run python main_fastmcp.py
```
"""
        }
        
        # Create config directory structure
        config_dir = os.path.join(temp_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        # Create logs directory
        logs_dir = os.path.join(temp_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Write all project files
        for filename, content in project_files.items():
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        return temp_dir
    
    def test_vscode_complete_workflow(self):
        """Test complete VS Code MCP workflow from configuration to execution"""
        project_dir = self.create_test_project()
        
        # Create VS Code MCP configuration
        vscode_config = VSCodeMCPConfigs.get_single_environment_config(project_dir)
        
        # Validate configuration structure
        assert VSCodeMCPConfigs.validate_config_structure(vscode_config)
        
        # Extract environment parameters from VS Code config
        server_config = vscode_config["servers"]["oracle-db"]
        env_params = server_config["env"]
        
        # Test configuration loading with VS Code environment parameters
        with patch.dict(os.environ, env_params, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify configuration matches VS Code parameters
            assert config.host == env_params["ORACLE_HOST"]
            assert config.port == int(env_params["ORACLE_PORT"])
            assert config.service_name == env_params["ORACLE_SERVICE_NAME"]
            assert config.username == env_params["ORACLE_USERNAME"]
            assert config.password == env_params["ORACLE_PASSWORD"]
            assert config.max_rows == int(env_params["MAX_ROWS"])
            
            # Verify source tracking
            sources = config.get_source_info()
            for field in ["host", "port", "service_name", "username", "password"]:
                assert sources.get(field) in ["MCP Config Environment", "environment"]
    
    def test_kiro_complete_workflow(self):
        """Test complete Kiro MCP workflow from configuration to execution"""
        project_dir = self.create_test_project()
        
        # Create Kiro MCP configuration
        kiro_config = KiroMCPConfigs.get_single_environment_config(project_dir)
        
        # Validate configuration structure
        assert KiroMCPConfigs.validate_config_structure(kiro_config)
        
        # Extract environment parameters from Kiro config
        server_config = kiro_config["mcpServers"]["oracle-db"]
        env_params = server_config["env"]
        
        # Test configuration loading with Kiro environment parameters
        with patch.dict(os.environ, env_params, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify configuration matches Kiro parameters
            assert config.host == env_params["ORACLE_HOST"]
            assert config.port == int(env_params["ORACLE_PORT"])
            assert config.service_name == env_params["ORACLE_SERVICE_NAME"]
            assert config.username == env_params["ORACLE_USERNAME"]
            assert config.password == env_params["ORACLE_PASSWORD"]
            assert config.max_rows == int(env_params["MAX_ROWS"])
            
            # Verify Kiro-specific settings
            assert server_config["disabled"] is False
            assert isinstance(server_config["autoApprove"], list)
    
    def test_multi_environment_workflow(self):
        """Test multi-environment workflow with different MCP configurations"""
        project_dir = self.create_test_project()
        
        # Test VS Code multi-environment configuration
        vscode_multi_config = VSCodeMCPConfigs.get_multi_environment_config(project_dir)
        assert VSCodeMCPConfigs.validate_config_structure(vscode_multi_config)
        
        # Test each environment
        environments = ["oracle-dev", "oracle-staging", "oracle-prod"]
        
        for env_name in environments:
            server_config = vscode_multi_config["servers"][env_name]
            env_params = server_config["env"]
            
            with patch.dict(os.environ, env_params, clear=True):
                loader = EnhancedConfigLoader()
                config = loader.load_config()
                
                # Verify environment-specific configuration
                assert config.host == env_params["ORACLE_HOST"]
                assert config.service_name == env_params["ORACLE_SERVICE_NAME"]
                assert config.username == env_params["ORACLE_USERNAME"]
                
                # Verify environment-specific values
                if env_name == "oracle-dev":
                    assert "dev" in config.host
                    assert config.max_rows == 500
                elif env_name == "oracle-staging":
                    assert "staging" in config.host
                    assert config.max_rows == 1000
                elif env_name == "oracle-prod":
                    assert "prod" in config.host
                    assert config.max_rows == 1000
    
    def test_configuration_migration_workflow(self):
        """Test MCP configuration workflow (no .env file support)"""
        project_dir = self.create_test_project()
        
        # Test MCP configuration only (no .env file support)
        mcp_env = {
            "ORACLE_HOST": "mcp-host.company.com",
            "ORACLE_SERVICE_NAME": "MCP_SERVICE",
            "ORACLE_USERNAME": "mcp_user",
            "ORACLE_PASSWORD": "mcp_password",
            "MAX_ROWS": "1000"
        }
        
        with patch.dict(os.environ, mcp_env, clear=True):
            with patch('config.sources.os.path.exists', return_value=False):  # No .env file
                loader = EnhancedConfigLoader()
                config = loader.load_config()
                
                # Verify MCP configuration
                assert config.host == "mcp-host.company.com"
                assert config.service_name == "MCP_SERVICE"
                assert config.username == "mcp_user"
                assert config.max_rows == 1000
                
                # Verify no .env file values are used
                assert loader.has_dotenv_values() is False
    
    def test_docker_deployment_workflow(self):
        """Test Docker deployment workflow with environment parameters"""
        project_dir = self.create_test_project()
        
        # Create Docker-related files
        dockerfile_content = """
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.lock
ENV ORACLE_HOST=""
ENV ORACLE_SERVICE_NAME=""
ENV ORACLE_USERNAME=""
ENV ORACLE_PASSWORD=""
CMD ["python", "main.py"]
"""
        
        docker_compose_content = """
version: '3.8'
services:
  oracle-mcp:
    build: .
    environment:
      - ORACLE_HOST=oracle-docker.company.com
      - ORACLE_SERVICE_NAME=DOCKER_SERVICE
      - ORACLE_USERNAME=docker_user
      - ORACLE_PASSWORD=docker_password
      - MAX_ROWS=1000
"""
        
        # Write Docker files
        with open(os.path.join(project_dir, "Dockerfile"), 'w') as f:
            f.write(dockerfile_content)
        
        with open(os.path.join(project_dir, "docker-compose.yml"), 'w') as f:
            f.write(docker_compose_content)
        
        # Test Docker environment parameter loading
        docker_env = {
            "ORACLE_HOST": "oracle-docker.company.com",
            "ORACLE_SERVICE_NAME": "DOCKER_SERVICE",
            "ORACLE_USERNAME": "docker_user",
            "ORACLE_PASSWORD": "docker_password",
            "MAX_ROWS": "1000"
        }
        
        with patch.dict(os.environ, docker_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify Docker configuration
            assert config.host == "oracle-docker.company.com"
            assert config.service_name == "DOCKER_SERVICE"
            assert config.username == "docker_user"
            assert config.max_rows == 1000
            
            # Verify DSN generation for Docker
            assert config.dsn == "oracle-docker.company.com:1521/DOCKER_SERVICE"
    
    def test_error_handling_workflow(self):
        """Test error handling workflow for various failure scenarios"""
        project_dir = self.create_test_project()
        
        # Test 1: Missing required parameters
        incomplete_env = {
            "ORACLE_HOST": "test-host.company.com",
            # Missing required parameters: ORACLE_SERVICE_NAME, ORACLE_USERNAME, ORACLE_PASSWORD
        }
        
        with patch.dict(os.environ, incomplete_env, clear=True):
            loader = EnhancedConfigLoader()
            
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_config()
            
            # Verify error message contains helpful information
            error_msg = str(exc_info.value)
            assert "ORACLE_SERVICE_NAME" in error_msg or "ORACLE_USERNAME" in error_msg
        
        # Test 2: Invalid parameter values
        invalid_env = {
            "ORACLE_HOST": "test-host.company.com",
            "ORACLE_SERVICE_NAME": "TEST_SERVICE",
            "ORACLE_USERNAME": "test_user",
            "ORACLE_PASSWORD": "test_password",
            "ORACLE_PORT": "invalid_port"
        }
        
        with patch.dict(os.environ, invalid_env, clear=True):
            loader = EnhancedConfigLoader()
            
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_config()
            
            # Verify error message indicates validation failure
            error_msg = str(exc_info.value)
            assert "port" in error_msg.lower() or "integer" in error_msg.lower()
        
        # Test 3: Configuration validation with warnings
        warning_env = {
            "ORACLE_HOST": "localhost",  # May trigger security warning
            "ORACLE_SERVICE_NAME": "TEST_SERVICE",
            "ORACLE_USERNAME": "test_user",
            "ORACLE_PASSWORD": "weak_password",  # Short password may trigger warning
            "MAX_ROWS": "10000"  # High limit may trigger warning
        }
        
        with patch.dict(os.environ, warning_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Configuration should load but may have warnings
            assert config.host == "localhost"
            assert config.service_name == "TEST_SERVICE"
            
            # Check for warnings (implementation may vary)
            warnings = config.get_warnings()
            # Warnings may be present but configuration should still work
    
    def test_configuration_validation_workflow(self):
        """Test configuration validation workflow"""
        project_dir = self.create_test_project()
        
        # Test valid VS Code configuration
        vscode_config = VSCodeMCPConfigs.get_single_environment_config(project_dir)
        assert VSCodeMCPConfigs.validate_config_structure(vscode_config)
        
        # Test valid Kiro configuration
        kiro_config = KiroMCPConfigs.get_single_environment_config(project_dir)
        assert KiroMCPConfigs.validate_config_structure(kiro_config)
        
        # Test invalid configurations
        invalid_vscode = VSCodeMCPConfigs.get_invalid_config_missing_required()
        assert not VSCodeMCPConfigs.validate_config_structure(invalid_vscode)
        
        invalid_kiro = KiroMCPConfigs.get_invalid_config_missing_required()
        assert not KiroMCPConfigs.validate_config_structure(invalid_kiro)
        
        # Test JSON serialization/deserialization
        vscode_json = json.dumps(vscode_config, indent=2)
        vscode_parsed = json.loads(vscode_json)
        assert VSCodeMCPConfigs.validate_config_structure(vscode_parsed)
        
        kiro_json = json.dumps(kiro_config, indent=2)
        kiro_parsed = json.loads(kiro_json)
        assert KiroMCPConfigs.validate_config_structure(kiro_parsed)
    
    def test_security_workflow(self):
        """Test security-related workflow scenarios"""
        project_dir = self.create_test_project()
        
        # Test credential masking in logs
        secure_env = {
            "ORACLE_HOST": "secure-host.company.com",
            "ORACLE_SERVICE_NAME": "SECURE_SERVICE",
            "ORACLE_USERNAME": "secure_user",
            "ORACLE_PASSWORD": "very_secure_password_123",
            "MAX_ROWS": "1000"
        }
        
        with patch.dict(os.environ, secure_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify configuration loads
            assert config.host == "secure-host.company.com"
            assert config.password == "very_secure_password_123"
            
            # Test that source tracking works for security audit
            sources = config.get_source_info()
            assert "password" in sources
            assert sources["password"] in ["MCP Config Environment", "environment"]
        
        # Test parameter validation for security
        security_test_cases = [
            {
                "name": "weak_password",
                "env": {
                    "ORACLE_HOST": "test-host.company.com",
                    "ORACLE_SERVICE_NAME": "TEST_SERVICE",
                    "ORACLE_USERNAME": "test_user",
                    "ORACLE_PASSWORD": "weak_password",  # Valid but weak password
                    "MAX_ROWS": "1000"
                },
                "should_load": True  # Should load but may have warnings
            },
            {
                "name": "high_max_rows",
                "env": {
                    "ORACLE_HOST": "test-host.company.com",
                    "ORACLE_SERVICE_NAME": "TEST_SERVICE",
                    "ORACLE_USERNAME": "test_user",
                    "ORACLE_PASSWORD": "secure_password",
                    "MAX_ROWS": "50000"  # Very high limit
                },
                "should_load": False  # Should fail validation
            }
        ]
        
        for test_case in security_test_cases:
            with patch.dict(os.environ, test_case["env"], clear=True):
                loader = EnhancedConfigLoader()
                
                if test_case["should_load"]:
                    config = loader.load_config()
                    assert config is not None
                else:
                    with pytest.raises(ConfigurationError):
                        loader.load_config()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])