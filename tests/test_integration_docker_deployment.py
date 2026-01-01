"""
Integration tests for Docker deployment scenarios
Tests Docker container deployment with environment parameters
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


class TestDockerDeploymentIntegration:
    """Test Docker deployment integration scenarios"""
    
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
        temp_dir = tempfile.mkdtemp(prefix="oracle_mcp_docker_test_")
        self.temp_dirs.append(temp_dir)
        
        # Create Docker-related files
        docker_files = {
            "Dockerfile": """
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y libaio1 curl && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock requirements.lock ./
COPY main.py ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Environment variables for configuration
ENV ORACLE_HOST=""
ENV ORACLE_PORT="1521"
ENV ORACLE_SERVICE_NAME=""
ENV ORACLE_USERNAME=""
ENV ORACLE_PASSWORD=""
ENV CONNECTION_TIMEOUT="30"
ENV QUERY_TIMEOUT="300"
ENV MAX_ROWS="1000"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python test_connection.py || exit 1

# Run application
CMD ["uv", "run", "python", "main.py"]
""",
            "docker-compose.yml": """
version: '3.8'

services:
  oracle-mcp-dev:
    build: .
    container_name: oracle-mcp-dev
    environment:
      - ORACLE_HOST=oracle-dev.company.com
      - ORACLE_SERVICE_NAME=DEV_SERVICE
      - ORACLE_USERNAME=dev_user
      - ORACLE_PASSWORD=dev_password
      - MAX_ROWS=500
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "test_connection.py"]
      interval: 30s
      timeout: 10s
      retries: 3

  oracle-mcp-prod:
    build: .
    container_name: oracle-mcp-prod
    environment:
      - ORACLE_HOST=oracle-prod.company.com
      - ORACLE_SERVICE_NAME=PROD_SERVICE
      - ORACLE_USERNAME=readonly_user
      - ORACLE_PASSWORD=${PROD_PASSWORD}
      - MAX_ROWS=1000
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "test_connection.py"]
      interval: 30s
      timeout: 10s
      retries: 3
""",
            "main.py": "# Test main.py for Docker\nprint('Oracle MCP Server Docker Test')",
            "test_connection.py": "# Test connection script\nprint('Connection test passed')",
            "pyproject.toml": "[project]\nname = 'oracle-mcp-docker'\nversion = '1.0.0'",
            "requirements.lock": "# Docker requirements"
        }
        
        for filename, content in docker_files.items():
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write(content)
        
        return temp_dir
    
    def test_dockerfile_environment_variables(self):
        """Test Dockerfile environment variable configuration"""
        project_dir = self.create_test_project()
        dockerfile_path = os.path.join(project_dir, "Dockerfile")
        
        # Read and validate Dockerfile
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check for required environment variables
        required_env_vars = [
            "ORACLE_HOST",
            "ORACLE_PORT", 
            "ORACLE_SERVICE_NAME",
            "ORACLE_USERNAME",
            "ORACLE_PASSWORD",
            "CONNECTION_TIMEOUT",
            "QUERY_TIMEOUT",
            "MAX_ROWS"
        ]
        
        for env_var in required_env_vars:
            assert f"ENV {env_var}=" in dockerfile_content
        
        # Check for health check
        assert "HEALTHCHECK" in dockerfile_content
        assert "test_connection.py" in dockerfile_content
        
        # Check for non-root user
        assert "useradd" in dockerfile_content
        assert "USER app" in dockerfile_content
    
    def test_docker_compose_configuration(self):
        """Test Docker Compose configuration structure"""
        project_dir = self.create_test_project()
        compose_path = os.path.join(project_dir, "docker-compose.yml")
        
        # Read Docker Compose file (YAML parsing would require PyYAML)
        with open(compose_path, 'r') as f:
            compose_content = f.read()
        
        # Check for required services
        assert "oracle-mcp-dev:" in compose_content
        assert "oracle-mcp-prod:" in compose_content
        
        # Check for environment variables
        assert "ORACLE_HOST=" in compose_content
        assert "ORACLE_SERVICE_NAME=" in compose_content
        assert "ORACLE_USERNAME=" in compose_content
        assert "ORACLE_PASSWORD=" in compose_content
        
        # Check for volume mounts
        assert "./logs:/app/logs" in compose_content
        
        # Check for health checks
        assert "healthcheck:" in compose_content
        assert "test_connection.py" in compose_content
        
        # Check for restart policy
        assert "restart: unless-stopped" in compose_content
    
    def test_docker_environment_parameter_injection(self):
        """Test Docker environment parameter injection"""
        
        # Simulate Docker container environment
        docker_env = {
            "ORACLE_HOST": "oracle-docker.company.com",
            "ORACLE_PORT": "1521",
            "ORACLE_SERVICE_NAME": "DOCKER_SERVICE",
            "ORACLE_USERNAME": "docker_user",
            "ORACLE_PASSWORD": "docker_password",
            "CONNECTION_TIMEOUT": "60",
            "QUERY_TIMEOUT": "600",
            "MAX_ROWS": "2000"
        }
        
        with patch.dict(os.environ, docker_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify Docker environment parameters are loaded
            assert config.host == "oracle-docker.company.com"
            assert config.port == 1521
            assert config.service_name == "DOCKER_SERVICE"
            assert config.username == "docker_user"
            assert config.password == "docker_password"
            assert config.connection_timeout == 60
            assert config.query_timeout == 600
            assert config.max_rows == 2000
            
            # Verify DSN generation
            assert config.dsn == "oracle-docker.company.com:1521/DOCKER_SERVICE"
    
    def test_docker_multi_environment_deployment(self):
        """Test Docker multi-environment deployment scenarios"""
        
        # Test development environment
        dev_docker_env = {
            "ORACLE_HOST": "oracle-dev-docker.company.com",
            "ORACLE_SERVICE_NAME": "DEV_DOCKER_SERVICE",
            "ORACLE_USERNAME": "dev_docker_user",
            "ORACLE_PASSWORD": "dev_docker_password",
            "MAX_ROWS": "500"
        }
        
        with patch.dict(os.environ, dev_docker_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            assert config.host == "oracle-dev-docker.company.com"
            assert config.service_name == "DEV_DOCKER_SERVICE"
            assert config.max_rows == 500
        
        # Test production environment
        prod_docker_env = {
            "ORACLE_HOST": "oracle-prod-docker.company.com",
            "ORACLE_SERVICE_NAME": "PROD_DOCKER_SERVICE",
            "ORACLE_USERNAME": "prod_docker_user",
            "ORACLE_PASSWORD": "prod_docker_password",
            "MAX_ROWS": "1000"
        }
        
        with patch.dict(os.environ, prod_docker_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            assert config.host == "oracle-prod-docker.company.com"
            assert config.service_name == "PROD_DOCKER_SERVICE"
            assert config.max_rows == 1000
    
    def test_kubernetes_deployment_configuration(self):
        """Test Kubernetes deployment configuration"""
        project_dir = self.create_test_project()
        
        # Create Kubernetes deployment manifest
        k8s_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "oracle-mcp-server",
                "labels": {"app": "oracle-mcp"}
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "oracle-mcp"}},
                "template": {
                    "metadata": {"labels": {"app": "oracle-mcp"}},
                    "spec": {
                        "containers": [{
                            "name": "oracle-mcp",
                            "image": "aops-oracle-mcp:latest",
                            "env": [
                                {"name": "ORACLE_HOST", "value": "oracle-k8s.company.com"},
                                {"name": "ORACLE_PORT", "value": "1521"},
                                {"name": "ORACLE_SERVICE_NAME", "value": "K8S_SERVICE"},
                                {
                                    "name": "ORACLE_USERNAME",
                                    "valueFrom": {
                                        "secretKeyRef": {
                                            "name": "oracle-db-secret",
                                            "key": "username"
                                        }
                                    }
                                },
                                {
                                    "name": "ORACLE_PASSWORD",
                                    "valueFrom": {
                                        "secretKeyRef": {
                                            "name": "oracle-db-secret",
                                            "key": "password"
                                        }
                                    }
                                },
                                {"name": "MAX_ROWS", "value": "1000"}
                            ],
                            "resources": {
                                "requests": {"memory": "256Mi", "cpu": "100m"},
                                "limits": {"memory": "512Mi", "cpu": "500m"}
                            },
                            "livenessProbe": {
                                "exec": {"command": ["python", "test_connection.py"]},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 60
                            }
                        }]
                    }
                }
            }
        }
        
        # Save Kubernetes manifest
        k8s_path = os.path.join(project_dir, "k8s-deployment.yaml")
        with open(k8s_path, 'w') as f:
            json.dump(k8s_deployment, f, indent=2)
        
        # Validate structure
        assert k8s_deployment["kind"] == "Deployment"
        assert k8s_deployment["spec"]["replicas"] == 2
        
        container = k8s_deployment["spec"]["template"]["spec"]["containers"][0]
        assert container["name"] == "oracle-mcp"
        assert container["image"] == "aops-oracle-mcp:latest"
        
        # Check environment variables
        env_vars = {env["name"]: env for env in container["env"]}
        assert "ORACLE_HOST" in env_vars
        assert "ORACLE_SERVICE_NAME" in env_vars
        assert "MAX_ROWS" in env_vars
        
        # Check secret references
        assert env_vars["ORACLE_USERNAME"]["valueFrom"]["secretKeyRef"]["name"] == "oracle-db-secret"
        assert env_vars["ORACLE_PASSWORD"]["valueFrom"]["secretKeyRef"]["name"] == "oracle-db-secret"
        
        # Check resource limits
        assert "resources" in container
        assert "limits" in container["resources"]
        assert "requests" in container["resources"]
        
        # Check health checks
        assert "livenessProbe" in container
        assert "test_connection.py" in str(container["livenessProbe"])
    
    def test_kubernetes_configmap_and_secret(self):
        """Test Kubernetes ConfigMap and Secret configuration"""
        project_dir = self.create_test_project()
        
        # Create ConfigMap
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "oracle-mcp-config"},
            "data": {
                "ORACLE_HOST": "oracle-k8s.company.com",
                "ORACLE_PORT": "1521",
                "ORACLE_SERVICE_NAME": "K8S_SERVICE",
                "CONNECTION_TIMEOUT": "30",
                "QUERY_TIMEOUT": "300",
                "MAX_ROWS": "1000"
            }
        }
        
        # Create Secret
        secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "oracle-db-secret"},
            "type": "Opaque",
            "data": {
                "username": "a3hzX3VzZXI=",  # base64 encoded "k8s_user"
                "password": "azhzX3Bhc3N3b3Jk"  # base64 encoded "k8s_password"
            }
        }
        
        # Save manifests
        configmap_path = os.path.join(project_dir, "k8s-configmap.yaml")
        secret_path = os.path.join(project_dir, "k8s-secret.yaml")
        
        with open(configmap_path, 'w') as f:
            json.dump(configmap, f, indent=2)
        
        with open(secret_path, 'w') as f:
            json.dump(secret, f, indent=2)
        
        # Validate ConfigMap
        assert configmap["kind"] == "ConfigMap"
        assert configmap["metadata"]["name"] == "oracle-mcp-config"
        assert "ORACLE_HOST" in configmap["data"]
        assert "ORACLE_SERVICE_NAME" in configmap["data"]
        
        # Validate Secret
        assert secret["kind"] == "Secret"
        assert secret["metadata"]["name"] == "oracle-db-secret"
        assert secret["type"] == "Opaque"
        assert "username" in secret["data"]
        assert "password" in secret["data"]
    
    def test_docker_health_check_integration(self):
        """Test Docker health check integration"""
        
        # Simulate successful health check environment
        healthy_env = {
            "ORACLE_HOST": "oracle-healthy.company.com",
            "ORACLE_SERVICE_NAME": "HEALTHY_SERVICE",
            "ORACLE_USERNAME": "healthy_user",
            "ORACLE_PASSWORD": "healthy_password"
        }
        
        with patch.dict(os.environ, healthy_env, clear=True):
            loader = EnhancedConfigLoader()
            config = loader.load_config()
            
            # Verify configuration loads successfully (simulates health check passing)
            assert config.host == "oracle-healthy.company.com"
            assert config.service_name == "HEALTHY_SERVICE"
            assert config.username == "healthy_user"
            
            # Verify DSN is properly formed (important for health checks)
            assert config.dsn == "oracle-healthy.company.com:1521/HEALTHY_SERVICE"
    
    def test_docker_environment_file_scenarios(self):
        """Test Docker environment file scenarios"""
        project_dir = self.create_test_project()
        
        # Create different environment files
        env_files = {
            ".env.development": """
ORACLE_HOST=oracle-dev-docker.company.com
ORACLE_SERVICE_NAME=DEV_DOCKER_SERVICE
ORACLE_USERNAME=dev_docker_user
ORACLE_PASSWORD=dev_docker_password
MAX_ROWS=500
""",
            ".env.production": """
ORACLE_HOST=oracle-prod-docker.company.com
ORACLE_SERVICE_NAME=PROD_DOCKER_SERVICE
ORACLE_USERNAME=prod_docker_user
ORACLE_PASSWORD=prod_docker_password
MAX_ROWS=1000
CONNECTION_TIMEOUT=60
QUERY_TIMEOUT=600
""",
            ".env.staging": """
ORACLE_HOST=oracle-staging-docker.company.com
ORACLE_SERVICE_NAME=STAGING_DOCKER_SERVICE
ORACLE_USERNAME=staging_docker_user
ORACLE_PASSWORD=staging_docker_password
MAX_ROWS=750
"""
        }
        
        for filename, content in env_files.items():
            env_path = os.path.join(project_dir, filename)
            with open(env_path, 'w') as f:
                f.write(content)
        
        # Verify files were created
        for filename in env_files.keys():
            env_path = os.path.join(project_dir, filename)
            assert os.path.exists(env_path)
            
            # Read and verify content
            with open(env_path, 'r') as f:
                content = f.read()
                assert "ORACLE_HOST=" in content
                assert "ORACLE_SERVICE_NAME=" in content
                assert "ORACLE_USERNAME=" in content
                assert "ORACLE_PASSWORD=" in content
    
    def test_docker_security_configuration(self):
        """Test Docker security configuration"""
        project_dir = self.create_test_project()
        dockerfile_path = os.path.join(project_dir, "Dockerfile")
        
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check security best practices
        assert "USER app" in dockerfile_content  # Non-root user
        assert "useradd" in dockerfile_content   # User creation
        assert "chown -R app:app" in dockerfile_content  # Proper ownership
        
        # Check that sensitive environment variables are empty by default
        assert 'ENV ORACLE_HOST=""' in dockerfile_content
        assert 'ENV ORACLE_USERNAME=""' in dockerfile_content
        assert 'ENV ORACLE_PASSWORD=""' in dockerfile_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])