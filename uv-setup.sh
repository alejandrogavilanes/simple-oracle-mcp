#!/bin/bash

# Simple Oracle MCP Server - UV Setup Script used for Developers to build locallying using Python UV,
# main way for deployment in via containers using docker or podman.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        log_warn "uv not found. Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
        log_info "uv installed successfully"
    else
        log_info "uv is already installed"
    fi
}

# Setup project
setup_project() {
    log_info "Setting up Simple Oracle MCP Server with uv..."
    
    # Install dependencies
    log_info "Installing dependencies..."
    uv sync
    
    # Install development dependencies
    log_info "Installing development dependencies..."
    uv sync --group dev
    
    # Install security tools
    log_info "Installing security tools..."
    uv sync --group security
    
    log_info "Project setup completed!"
}


# Run the server
run_server() {
    setup_env
    log_info "Starting Simple Oracle MCP Server..."
    uv run python main.py
}

# Run tests
run_tests() {
    log_info "Running tests with uv..."
    uv run pytest --cov=. --cov-report=html --cov-report=term
}

# Format code
format_code() {
    log_info "Formatting code with black and isort..."
    uv run black .
    uv run isort .
}

# Lint code
lint_code() {
    log_info "Linting code with flake8..."
    uv run flake8 --max-line-length=88 .
}

# Security scan
security_scan() {
    log_info "Running security scans..."
    uv run bandit -r . -f json -o bandit-report.json
    uv run safety check
}

# Show help
show_help() {
    echo "Simple Oracle MCP Server - UV Management Script"
    echo ""
    echo "Usage: $0 {setup|run|test|format|lint|security|help}"
    echo ""
    echo "Commands:"
    echo "  setup     - Install uv and setup project dependencies"
    echo "  run       - Run the MCP server"
    echo "  test      - Run tests with coverage"
    echo "  format    - Format code with black and isort"
    echo "  lint      - Lint code with flake8"
    echo "  security  - Run security scans (bandit, safety)"
    echo "  help      - Show this help message"
    echo ""
}

# Main script
case "$1" in
    setup)
        check_uv
        setup_project
        setup_env
        ;;
    run)
        run_server
        ;;
    test)
        run_tests
        ;;
    format)
        format_code
        ;;
    lint)
        lint_code
        ;;
    security)
        security_scan
        ;;
    help|*)
        show_help
        ;;
esac