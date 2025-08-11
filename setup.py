#!/usr/bin/env python3
"""Simple setup script for production deployment without Poetry."""

import sys
import subprocess
import os


def check_python_version():
    """Check if Python version is 3.12 or higher."""
    if sys.version_info < (3, 12):
        print(f"Error: Python 3.12 or higher is required. Current version: {sys.version}")
        print("Please install Python 3.12+ or use Ubuntu 24.04+ which includes Python 3.12")
        sys.exit(1)
    print(f"Python {sys.version} detected (>= 3.12 required) ✓")


def install_dependencies():
    """Install dependencies from requirements.txt."""
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found")
        sys.exit(1)

    print("Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"
        ])
        print("Dependencies installed successfully ✓")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)


def main():
    """Main setup function."""
    print("Setting up Slack Canvas Creator from Threads...")
    check_python_version()
    install_dependencies()
    print("\nSetup completed successfully!")
    print("Make sure to configure your .env file before running the application.")


if __name__ == "__main__":
    main()
