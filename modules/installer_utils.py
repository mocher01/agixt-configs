#!/usr/bin/env python3
"""
AGiXT Installer - Utilities Module
==================================

Common utilities and helper functions used by all installer modules.
This module provides logging, command execution, validation, and other
shared functionality.
"""

import os
import sys
import subprocess
import secrets
import socket
import shutil
from datetime import datetime

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("[" + timestamp + "] " + level + ": " + str(message))

def run_command(command, cwd=None, timeout=300):
    """Execute a shell command with proper error handling"""
    try:
        log("Running: " + command)
        result = subprocess.run(
            command.split(), 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if result.stdout.strip():
            log("Output: " + result.stdout.strip())
        
        if result.returncode == 0:
            return True
        else:
            log("Command failed with return code " + str(result.returncode), "ERROR")
            if result.stderr:
                log("Error: " + result.stderr, "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log("Command timed out after " + str(timeout) + " seconds", "ERROR")
        return False
    except Exception as e:
        log("Error executing command: " + str(e), "ERROR")
        return False

def generate_secure_api_key():
    """Generate a secure API key for AGiXT"""
    return secrets.token_urlsafe(32)

def check_prerequisites():
    """Check if all required tools are installed"""
    tools = {
        'git': 'git --version',
        'docker': 'docker --version', 
        'docker-compose': 'docker compose version'
    }
    
    log("Checking prerequisites...")
    for tool, command in tools.items():
        if run_command(command):
            log(tool.title() + " ✓", "SUCCESS")
        else:
            log(tool.title() + " not found or not working", "ERROR")
            return False
    
    return True

def check_docker_network():
    """Check if agixt-network exists, create if not"""
    log("Checking Docker network...")
    
    # Check if network exists
    result = subprocess.run(
        ["docker", "network", "ls", "--filter", "name=agixt-network", "--format", "{{.Name}}"],
        capture_output=True,
        text=True
    )
    
    if "agixt-network" in result.stdout:
        log("agixt-network already exists", "SUCCESS")
        return True
    
    # Create the network
    log("Creating agixt-network...")
    result = subprocess.run(
        ["docker", "network", "create", "agixt-network"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        log("agixt-network created successfully", "SUCCESS")
        return True
    else:
        log("Failed to create agixt-network: " + result.stderr, "ERROR")
        return False

def create_installation_directory(config):
    """Create the installation directory using config values"""
    version = config.get('AGIXT_VERSION', 'unknown')
    folder_prefix = config.get('INSTALL_FOLDER_PREFIX', 'agixt')
    base_path = config.get('INSTALL_BASE_PATH', '/var/apps')
    
    install_path = os.path.join(base_path, folder_prefix + "-" + version)
    
    try:
        os.makedirs(install_path, exist_ok=True)
        log("Created installation directory: " + install_path, "SUCCESS")
        return install_path
    except Exception as e:
        log("Failed to create directory " + install_path + ": " + str(e), "ERROR")
        return None

def clone_agixt_repository(install_path, github_token=None):
    """Clone the AGiXT repository"""
    try:
        if github_token:
            repo_url = "https://" + github_token + "@github.com/Josh-XT/AGiXT.git"
        else:
            repo_url = "https://github.com/Josh-XT/AGiXT.git"
        
        log("Cloning AGiXT repository...")
        result = subprocess.run(
            ["git", "clone", repo_url, "."],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            log("AGiXT repository cloned successfully", "SUCCESS")
            return True
        else:
            log("Failed to clone repository: " + result.stderr, "ERROR")
            return False
            
    except Exception as e:
        log("Error cloning repository: " + str(e), "ERROR")
        return False

def test_endpoints(install_path, config):
    """Test if all endpoints are accessible"""
    log("Testing API endpoints...")
    
    endpoints = {
        'AGiXT Frontend': 3437,
        'AGiXT API': 7437,
        'EzLocalAI API': 8091,
        'EzLocalAI UI': 8502
    }
    
    for name, port in endpoints.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                log(name + " (port " + str(port) + ") is accessible", "SUCCESS")
            else:
                log(name + " (port " + str(port) + ") is not accessible yet", "WARN")
            sock.close()
        except Exception as e:
            log(name + " test failed: " + str(e), "WARN")

def verify_installation(install_path, config):
    """Verify the installation is working"""
    log("Verifying installation...")
    
    try:
        # Check container status
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "table"],
            cwd=install_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            log("Container status:")
            print(result.stdout)
        
        # Test endpoints
        test_endpoints(install_path, config)
            
    except Exception as e:
        log("Could not verify installation: " + str(e), "WARN")

def install_graphql_dependencies(install_path):
    """Install GraphQL dependencies in AGiXT container"""
    try:
        log("Installing GraphQL dependencies...")
        
        # Wait for container to be ready
        import time
        time.sleep(30)
        
        # Install strawberry-graphql
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "agixt", "pip", "install", "strawberry-graphql", "broadcaster"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            log("GraphQL dependencies installed successfully", "SUCCESS")
        else:
            log("Warning: Could not install GraphQL dependencies: " + result.stderr, "WARN")
        
        return True
        
    except Exception as e:
        log("Could not install GraphQL dependencies: " + str(e), "WARN")
        return False

# Module test function
def test_module():
    """Test this module's functionality"""
    log("🧪 Testing installer_utils module...")
    
    # Test logging
    log("Testing log function", "SUCCESS")
    
    # Test API key generation
    api_key = generate_secure_api_key()
    if len(api_key) > 20:
        log("API key generation: ✓", "SUCCESS")
    else:
        log("API key generation: ✗", "ERROR")
    
    # Test basic command
    if run_command("echo test"):
        log("Command execution: ✓", "SUCCESS")
    else:
        log("Command execution: ✗", "ERROR")
    
    log("✅ installer_utils module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    # Run module test if executed directly
    test_module()
