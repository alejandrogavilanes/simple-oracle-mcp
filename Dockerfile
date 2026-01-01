FROM python:3.11-slim

# Install system dependencies for Oracle client
RUN apt-get update && apt-get install -y \
    libaio1t64 \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    curl -o instantclient-basic-linux.x64-19.21.0.0.0dbru.zip \
         https://download.oracle.com/otn_software/linux/instantclient/1921000/instantclient-basic-linux.x64-19.21.0.0.0dbru.zip && \
    unzip instantclient-basic-linux.x64-19.21.0.0.0dbru.zip && \
    rm instantclient-basic-linux.x64-19.21.0.0.0dbru.zip

# Set Oracle environment variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_19_21:$LD_LIBRARY_PATH
ENV PATH=/opt/oracle/instantclient_19_21:$PATH

# Install UV package manager for faster dependency management
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml uv.lock requirements.lock requirements.txt ./

# Install dependencies using UV for faster installation
RUN uv sync --frozen --no-install-project

# Copy source code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    chown -R app:app /app && \
    mkdir -p /app/logs && \
    chown -R app:app /app/logs

# Switch to non-root user
USER app

# Default environment variables for configuration
# These are fallback values - actual values provided via MCP configuration
# No Oracle-specific credentials in the container by default
ENV ORACLE_HOST=""
ENV ORACLE_PORT="1521"
ENV ORACLE_SERVICE_NAME=""
ENV ORACLE_USERNAME=""
ENV ORACLE_PASSWORD=""
ENV CONNECTION_TIMEOUT="30"
ENV QUERY_TIMEOUT="300"
ENV MAX_ROWS="1000"

# Container deployment mode - indicates this is a generic container
ENV DEPLOYMENT_MODE="generic"
ENV MCP_CONFIG_SOURCE="environment"

# Create a connection test script that works with MCP environment variables
RUN echo '#!/usr/bin/env python3\n\
import sys\n\
import os\n\
sys.path.insert(0, "/app")\n\
\n\
def test_connection():\n\
    try:\n\
        from config.loader import EnhancedConfigLoader\n\
        import oracledb\n\
        \n\
        # Load configuration using the enhanced loader\n\
        loader = EnhancedConfigLoader()\n\
        config = loader.load_config()\n\
        \n\
        # Check if we have valid Oracle configuration\n\
        if not config.host or not config.service_name or not config.username or not config.password:\n\
            print("⚠️  Oracle configuration incomplete - provide via MCP environment variables")\n\
            print(f"   Host: {config.host or \"NOT SET\"}")\n\
            print(f"   Service: {config.service_name or \"NOT SET\"}")\n\
            print(f"   Username: {config.username or \"NOT SET\"}")\n\
            print(f"   Password: {\"SET\" if config.password else \"NOT SET\"}")\n\
            print("   Container ready for MCP configuration")\n\
            sys.exit(0)  # Exit success - container is ready, just needs MCP config\n\
        \n\
        # Test connection with provided configuration\n\
        connection = oracledb.connect(\n\
            user=config.username,\n\
            password=config.password,\n\
            dsn=config.dsn\n\
        )\n\
        cursor = connection.cursor()\n\
        cursor.execute("SELECT 1 FROM dual")\n\
        result = cursor.fetchone()\n\
        connection.close()\n\
        \n\
        if result and result[0] == 1:\n\
            print("✅ Oracle connection test successful")\n\
            print(f"   Connected to: {config.host}:{config.port}/{config.service_name}")\n\
            print(f"   Username: {config.username}")\n\
            print(f"   Max rows: {config.max_rows}")\n\
            sys.exit(0)\n\
        else:\n\
            print("❌ Oracle connection test failed - unexpected result")\n\
            sys.exit(1)\n\
            \n\
    except Exception as e:\n\
        # Check if this is a configuration issue vs connection issue\n\
        if "configuration" in str(e).lower() or "missing" in str(e).lower():\n\
            print(f"⚠️  Configuration issue: {e}")\n\
            print("   Provide Oracle configuration via MCP environment variables")\n\
            sys.exit(0)  # Container ready, needs MCP config\n\
        else:\n\
            print(f"❌ Oracle connection test failed: {e}")\n\
            sys.exit(1)\n\
\n\
if __name__ == "__main__":\n\
    test_connection()\n\
' > /app/test_connection.py && chmod +x /app/test_connection.py

# Health check - container is healthy if ready for MCP configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python test_connection.py || exit 1

# Expose port for monitoring (optional)
EXPOSE 8000

# Run the FastMCP Oracle server
CMD ["uv", "run", "python", "main.py"]