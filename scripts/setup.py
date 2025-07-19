#!/usr/bin/env python3

# Setup script for development environment
# Usage: python scripts/setup.py

import os
import sys
import subprocess
import secrets
from pathlib import Path

def run_command(command, description):
    """Run a shell command with error handling."""
    print(f"{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def create_env_file():
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return
    
    # Read template
    with open(env_example, 'r') as f:
        content = f.read()
    
    # Generate secret key
    secret_key = secrets.token_urlsafe(32)
    content = content.replace('your-super-secret-key-change-this-in-production', secret_key)
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file with generated secret key")

def setup_directories():
    """Create necessary directories."""
    directories = [
        "data/faiss_index",
        "uploads",
        "logs",
        "tests/__pycache__",
        "app/__pycache__"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")

def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ required, found {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} is compatible")

def install_dependencies():
    """Install Python dependencies."""
    # Check if Poetry is available
    if run_command("poetry --version", "Checking Poetry installation"):
        return run_command("poetry install", "Installing dependencies with Poetry")
    
    # Fallback to pip
    print("Poetry not found, using pip...")
    requirements_file = "requirements/dev.txt" if Path("requirements/dev.txt").exists() else "requirements.txt"
    return run_command(f"pip install -r {requirements_file}", "Installing dependencies with pip")

def setup_pre_commit():
    """Setup pre-commit hooks."""
    if Path(".pre-commit-config.yaml").exists():
        return run_command("pre-commit install", "Setting up pre-commit hooks")
    print("⏭️  No pre-commit configuration found, skipping")

def run_initial_tests():
    """Run initial tests to verify setup."""
    if Path("tests").exists():
        return run_command("python -m pytest tests/ -v", "Running initial tests")
    print("⏭️  No tests directory found, skipping")

def main():
    """Main setup function."""
    print("Setting up FastAPI LLM Application development environment")
    
    # Check prerequisites
    check_python_version()
    
    # Setup environment
    create_env_file()
    setup_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Optional setup
    setup_pre_commit()
    
    # Verify installation
    print("\nVerifying installation...")
    
    try:
        import fastapi
        import uvicorn
        import sqlmodel
        print("✅ Core dependencies are working")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    
    # Run tests
    run_initial_tests()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("   1. Review and update .env file if needed")
    print("   2. Start the development server: uvicorn app.main:app --reload")
    print("   3. Visit http://localhost:8000 to test the application")
    print("   4. Run tests: pytest")
    print("\nDocumentation:")
    print("   - API docs: http://localhost:8000/api/docs")
    print("   - Health check: http://localhost:8000/health")

if __name__ == "__main__":
    main()
