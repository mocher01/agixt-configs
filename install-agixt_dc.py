#!/usr/bin/env python3
"""
AGiXT Automated Installer - VERSION 1 (Docker-compose override)
===============================================================

Cette version modifie le docker-compose.yml pour passer TOUTES les variables .env
aux containers sans utiliser start.py

Version: 1.0 - Override docker-compose
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
import socket
import platform
import time
import json
import re
import secrets
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configuration
GITHUB_REPO_BASE = "https://raw.githubusercontent.com/mocher01/agixt-configs/main"
AGIXT_REPO = "https://github.com/Josh-XT/AGiXT.git"
DEFAULT_BASE_PATH = "/var/apps"

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'

def print_step(message: str):
    """Print a step message in blue"""
    print(f"\n{Colors.BLUE}🚀 {message}{Colors.END}")

def print_success(message: str):
    """Print a success message in green"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message: str):
    """Print a warning message in yellow"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message: str):
    """Print an error message in red"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    """Print an info message in cyan"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def run_command(command: str, cwd: Optional[str] = None, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result"""
    try:
        print_info(f"Running: {command}")
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=capture_output, 
            text=True, 
            check=check
        )
        if result.stdout and capture_output:
            print(f"Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(f"Return code: {e.returncode}")
        if e.stderr:
            print_error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def download_file(url: str, filename: str) -> bool:
    """Download a file from URL with optional GitHub token support"""
    try:
        print_info(f"Downloading {filename} from {url}")
        
        github_token = os.environ.get('GITHUB_TOKEN')
        
        if github_token and ('github.com' in url or 'githubusercontent.com' in url):
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'token {github_token}')
            req.add_header('User-Agent', 'AGiXT-Installer/1.0')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(filename, 'wb') as f:
                    f.write(response.read())
        else:
            urllib.request.urlretrieve(url, filename)
            
        print_success(f"Downloaded {filename}")
        return True
    except Exception as e:
        print_error(f"Failed to download {filename}: {e}")
        return False

def check_prerequisites() -> bool:
    """Check if required tools are installed"""
    print_step("Checking prerequisites...")
    
    # Check Git
    result = run_command("git --version", check=False)
    if result.returncode != 0:
        print_error("Git is required but not installed")
        return False
    print_success("Git ✓")
    
    # Check Docker
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print_error("Docker is required but not installed")
        return False
    print_success("Docker ✓")
    
    # Check Docker Compose
    result = run_command("docker compose version", check=False)
    if result.returncode != 0:
        print_error("Docker Compose is required but not installed")
        return False
    print_success("Docker Compose ✓")
    
    return True

def load_env_config(env_file: str) -> Dict[str, str]:
    """Load environment variables from .env file"""
    config = {}
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                config[key] = value
                
        print_success(f"Loaded {len(config)} configuration variables")
        return config
        
    except Exception as e:
        print_error(f"Failed to load {env_file}: {e}")
        sys.exit(1)

def create_installation_directory(install_folder_name: str) -> str:
    """Create and prepare the installation directory"""
    install_path = os.path.join(DEFAULT_BASE_PATH, install_folder_name)
    print_step(f"Creating installation directory: {install_path}")
    
    try:
        os.makedirs(install_path, exist_ok=True)
        print_success(f"Created directory: {install_path}")
        return install_path
    except Exception as e:
        print_error(f"Failed to create directory: {e}")
        sys.exit(1)

def clone_agixt_repository(install_path: str, config: Dict[str, str]) -> bool:
    """Clone or update the AGiXT repository"""
    print_step("Setting up AGiXT repository...")
    
    branch = config.get('AGIXT_BRANCH', 'main')
    print_info(f"Using branch: {branch}")
    
    clone_cmd = f"git clone --branch {branch} --depth 1 {AGIXT_REPO} ."
    result = run_command(clone_cmd, cwd=install_path, check=False)
    
    if result.returncode != 0:
        print_warning(f"Failed to clone {branch} branch, trying main...")
        clone_cmd = f"git clone --branch main --depth 1 {AGIXT_REPO} ."
        result = run_command(clone_cmd, cwd=install_path)
    
    print_success("Repository cloned successfully")
    return True

def create_env_file(config: Dict[str, str], install_path: str) -> str:
    """Create .env file in the installation directory"""
    env_file = os.path.join(install_path, '.env')
    
    print_step(f"Creating .env file: {env_file}")
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# AGiXT Configuration - Version 1 (Docker Override)\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in config.items():
                f.write(f'{key}={value}\n')
        
        os.chmod(env_file, 0o600)
        print_success("Environment file created")
        return env_file
        
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        sys.exit(1)

def create_docker_override(config: Dict[str, str], install_path: str) -> bool:
    """Create docker-compose.override.yml to pass ALL environment variables"""
    print_step("Creating docker-compose override with ALL variables...")
    
    override_file = os.path.join(install_path, 'docker-compose.override.yml')
    
    # Variables spécifiques pour agixtinteractive
    ui_vars = [
        'AGIXT_SHOW_SELECTION', 'AGIXT_SHOW_AGENT_BAR', 'AGIXT_SHOW_APP_BAR',
        'THEME_NAME', 'AUTH_PROVIDER', 'INTERACTIVE_MODE',
        'AGIXT_CONVERSATION_MODE', 'AGIXT_FOOTER_MESSAGE'
    ]
    
    try:
        with open(override_file, 'w') as f:
            f.write("# Docker Compose Override - Version 1\n")
            f.write("# Forces ALL environment variables to be passed to containers\n\n")
            f.write("version: '3.7'\nservices:\n")
            
            # Service agixtinteractive
            f.write("  agixtinteractive:\n")
            f.write("    environment:\n")
            
            for var in ui_vars:
                if var in config:
                    f.write(f"      {var}: ${{{var}}}\n")
            
            # Ajouter toutes les autres variables aussi
            for key in config:
                if key not in ui_vars:
                    f.write(f"      {key}: ${{{key}}}\n")
        
        print_success("Docker override created with ALL variables")
        return True
        
    except Exception as e:
        print_error(f"Failed to create docker override: {e}")
        return False

def start_agixt_services(install_path: str) -> bool:
    """Start AGiXT services using Docker Compose with override"""
    print_step("Starting AGiXT services with custom configuration...")
    
    original_cwd = os.getcwd()
    os.chdir(install_path)
    
    try:
        # Stop existing containers
        run_command("docker compose down", check=False, capture_output=False)
        
        # Pull latest images
        print_info("Pulling Docker images...")
        run_command("docker compose pull", check=False, capture_output=False)
        
        # Start services with override
        print_info("Starting services with override...")
        result = run_command("docker compose up -d", capture_output=False)
        
        if result.returncode == 0:
            print_success("AGiXT services started successfully!")
            return True
        else:
            print_error("Failed to start AGiXT services")
            return False
            
    finally:
        os.chdir(original_cwd)

def wait_for_services(config: Dict[str, str], timeout: int = 60):
    """Wait for services to be ready"""
    print_step("Waiting for services to be ready...")
    time.sleep(10)  # Simple wait for version 1

def show_installation_summary(install_path: str, config: Dict[str, str]):
    """Display installation summary"""
    print("\n" + "="*70)
    print(f"{Colors.GREEN}{Colors.BOLD}🎉 AGiXT Installation Complete - Version 1!{Colors.END}")
    print("="*70)
    
    print(f"\n📁 Installation: {install_path}")
    print(f"🎨 Theme: {config.get('THEME_NAME', 'default')}")
    print(f"🎯 Selection: {config.get('AGIXT_SHOW_SELECTION', 'not set')}")
    print(f"🔐 Auth Provider: {config.get('AUTH_PROVIDER', 'not set')}")
    
    web_url = config.get('APP_URI', 'http://localhost:3437')
    api_url = config.get('AGIXT_URI', 'http://localhost:7437')
    
    print(f"\n🌐 URLs:")
    print(f"   Web: {web_url}")
    print(f"   API: {api_url}")
    
    print(f"\n✅ Version 1 - Docker Override Method Used")

def cleanup_temp_files(*files):
    """Clean up temporary files"""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print_info(f"Cleaned up: {file}")
        except Exception:
            pass

def main():
    """Main installation function - Version 1"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║            AGiXT Installer - Version 1 (Override)            ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    if len(sys.argv) < 2:
        print_error("Usage: python3 script.py CONFIG_NAME [GITHUB_TOKEN]")
        sys.exit(1)
    
    config_name = sys.argv[1]
    github_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    install_folder_name = f"{config_name}_v1"
    
    if github_token:
        os.environ['GITHUB_TOKEN'] = github_token
    
    env_url = f"{GITHUB_REPO_BASE}/{config_name}.env"
    env_file = f"{config_name}.env"
    
    try:
        # Step 1: Prerequisites
        if not check_prerequisites():
            sys.exit(1)
        
        # Step 2: Download config
        if not download_file(env_url, env_file):
            sys.exit(1)
        
        # Step 3: Load config
        config = load_env_config(env_file)
        
        # Step 4: Create directory
        install_path = create_installation_directory(install_folder_name)
        
        # Step 5: Clone repository
        if not clone_agixt_repository(install_path, config):
            sys.exit(1)
        
        # Step 6: Create .env
        create_env_file(config, install_path)
        
        # Step 7: Create docker override (VERSION 1 SPECIFIC)
        if not create_docker_override(config, install_path):
            sys.exit(1)
        
        # Step 8: Start services
        if not start_agixt_services(install_path):
            sys.exit(1)
        
        # Step 9: Wait for services
        wait_for_services(config)
        
        # Step 10: Summary
        show_installation_summary(install_path, config)
        
        print(f"\n{Colors.GREEN}✨ Version 1 installation completed!{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Installation cancelled{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)
    finally:
        cleanup_temp_files(env_file)

if __name__ == "__main__":
    main()
