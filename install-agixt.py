#!/usr/bin/env python3
"""
AGiXT Automated Installer - v1.1-proxy-no-local
================================================

Complete AGiXT installation with:
✅ Nginx reverse proxy integration (agixt.locod-ai.com / agixtui.locod-ai.com)
✅ External AI provider ready (OpenAI, Anthropic, etc.)
✅ Clean folder naming (/var/apps/agixt-v1.1-proxy-no-local)
✅ Docker network integration
✅ GraphQL management interface
✅ Professional production setup

Usage:
  python3 install-agixt-no-local.py [OPTIONS] [CONFIG_NAME] [GITHUB_TOKEN]

Examples:
  python3 install-agixt-no-local.py proxy
  python3 install-agixt-no-local.py --no-cleanup proxy
  python3 install-agixt-no-local.py proxy github_pat_xxx

Options:
  --no-cleanup, --skip-cleanup    Skip cleaning previous AGiXT installations
  
Arguments:
  CONFIG_NAME     Configuration name (default: proxy)
  GITHUB_TOKEN    GitHub token for private repos (optional)

Features v1.1-proxy-no-local:
- 🌐 Nginx proxy: https://agixt.locod-ai.com + https://agixtui.locod-ai.com
- 🤖 External AI providers: Ready for OpenAI, Anthropic, etc.
- 📁 Clean naming: /var/apps/agixt-v1.1-proxy-no-local
- 🔗 Docker networks: agixt-network integration
- 🔑 Secure API key generation
- 🎯 Optimized for: n8n workflows, server scripts, automation
"""

import os
import sys
import subprocess
import time
import shutil
import secrets
from datetime import datetime
from typing import Dict, Optional
import json

# Version info
VERSION = "v1.1-proxy-no-local"
INSTALL_FOLDER_NAME = f"agixt-{VERSION}"

def log(message: str, level: str = "INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(command: str, cwd: Optional[str] = None, timeout: int = 300) -> bool:
    """Execute a shell command with proper error handling"""
    try:
        log(f"Running: {command}")
        result = subprocess.run(
            command.split(), 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if result.stdout.strip():
            log(f"Output: {result.stdout.strip()}")
        
        if result.returncode == 0:
            return True
        else:
            log(f"Command failed with return code {result.returncode}", "ERROR")
            if result.stderr:
                log(f"Error: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"Command timed out after {timeout} seconds", "ERROR")
        return False
    except Exception as e:
        log(f"Error executing command: {e}", "ERROR")
        return False

def check_prerequisites() -> bool:
    """Check if all required tools are installed"""
    tools = {
        'git': 'git --version',
        'docker': 'docker --version', 
        'docker-compose': 'docker compose version'
    }
    
    log("Checking prerequisites...")
    for tool, command in tools.items():
        if run_command(command):
            log(f"{tool.title()} ✓", "SUCCESS")
        else:
            log(f"{tool.title()} not found or not working", "ERROR")
            return False
    
    return True

def check_docker_network() -> bool:
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
        log(f"Failed to create agixt-network: {result.stderr}", "ERROR")
        return False

def cleanup_previous_installations():
    """Clean up any previous AGiXT installations"""
    base_path = "/var/apps"
    
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
        log("Created /var/apps directory", "SUCCESS")
        return True
    
    log("Cleaning up previous installations...")
    
    cleanup_count = 0
    for item in os.listdir(base_path):
        if item.startswith("agixt-") or item.startswith("AGIXT_"):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                log(f"Cleaning up {item_path}")
                cleanup_count += 1
                
                try:
                    # Stop docker services if they exist
                    compose_file = os.path.join(item_path, "docker-compose.yml")
                    if os.path.exists(compose_file):
                        log(f"Stopping Docker services in {item}")
                        result = subprocess.run(
                            ["docker", "compose", "-f", compose_file, "down"], 
                            cwd=item_path,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode == 0:
                            log(f"Docker services stopped successfully", "SUCCESS")
                        else:
                            log(f"Warning: Could not stop services: {result.stderr}", "WARN")
                    
                    # Remove directory
                    log(f"Removing directory {item_path}")
                    shutil.rmtree(item_path, ignore_errors=True)
                    
                    if not os.path.exists(item_path):
                        log(f"Directory {item} removed successfully", "SUCCESS")
                    else:
                        log(f"Warning: Directory {item} still exists", "WARN")
                        
                except Exception as e:
                    log(f"Warning: Could not fully clean {item}: {e}", "WARN")
                    # Continue with other installations - don't fail
    
    if cleanup_count == 0:
        log("No previous AGiXT installations found")
    else:
        log(f"Cleanup completed - processed {cleanup_count} installations", "SUCCESS")
    
    return True  # Always return True - cleanup should never stop installation

def create_installation_directory(config_name: str = "proxy") -> Optional[str]:
    """Create the installation directory with clean naming"""
    install_path = f"/var/apps/{INSTALL_FOLDER_NAME}"
    
    try:
        os.makedirs(install_path, exist_ok=True)
        log(f"Created installation directory: {install_path}", "SUCCESS")
        return install_path
    except Exception as e:
        log(f"Failed to create directory {install_path}: {e}", "ERROR")
        return None

def clone_agixt_repository(install_path: str, github_token: Optional[str] = None) -> bool:
    """Clone the AGiXT repository"""
    try:
        if github_token:
            repo_url = f"https://{github_token}@github.com/Josh-XT/AGiXT.git"
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
            log(f"Failed to clone repository: {result.stderr}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Error cloning repository: {e}", "ERROR")
        return False

def generate_secure_api_key() -> str:
    """Generate a secure API key for AGiXT"""
    return secrets.token_urlsafe(32)

def get_env_config() -> Dict[str, str]:
    """Get the .env configuration for v1.1-proxy-no-local"""
    api_key = generate_secure_api_key()
    
    return {
        # Version info
        'AGIXT_VERSION': VERSION,
        'INSTALL_DATE': datetime.now().isoformat(),
        
        # Basic configuration - PROXY READY
        'AGIXT_AUTO_UPDATE': 'true',
        'AGIXT_API_KEY': api_key,  # FIXED: Generate secure API key
        'UVICORN_WORKERS': '6',
        'WORKING_DIRECTORY': './WORKSPACE',
        'TZ': 'Europe/Paris',
        
        # PROXY URLs - Professional domains
        'AGIXT_SERVER': 'https://agixt.locod-ai.com',
        'AGIXT_URI': 'http://agixt:7437',
        'APP_URI': 'https://agixtui.locod-ai.com',
        'AUTH_WEB': 'https://agixtui.locod-ai.com/user',
        
        # Interface management - Complete setup
        'APP_NAME': 'AGiXT Production Server v1.1-proxy-no-local',
        'APP_DESCRIPTION': 'AGiXT Production Server - External AI Provider Ready',
        'AGIXT_AGENT': 'CodeAssistant',
        'AGIXT_SHOW_SELECTION': 'agent,conversation',
        'AGIXT_SHOW_AGENT_BAR': 'true',
        'AGIXT_SHOW_APP_BAR': 'true',
        'AGIXT_CONVERSATION_MODE': 'select',
        'INTERACTIVE_MODE': 'chat',
        'THEME_NAME': 'doom',
        'AGIXT_FOOTER_MESSAGE': 'AGiXT v1.1-proxy-no-local - External Provider Ready',
        
        # Authentication & agents
        'AUTH_PROVIDER': 'magicalauth',
        'CREATE_AGENT_ON_REGISTER': 'true',
        'CREATE_AGIXT_AGENT': 'true',
        'ALLOW_EMAIL_SIGN_IN': 'true',
        
        # Advanced features
        'AGIXT_FILE_UPLOAD_ENABLED': 'true',
        'AGIXT_VOICE_INPUT_ENABLED': 'true',
        'AGIXT_RLHF': 'true',
        'AGIXT_ALLOW_MESSAGE_EDITING': 'true',
        'AGIXT_ALLOW_MESSAGE_DELETION': 'true',
        'AGIXT_SHOW_OVERRIDE_SWITCHES': 'tts,websearch,analyze-user-input',
        
        # System configuration
        'DATABASE_TYPE': 'sqlite',
        'DATABASE_NAME': 'models/agixt',
        'LOG_LEVEL': 'INFO',
        'LOG_FORMAT': '%(asctime)s | %(levelname)s | %(message)s',
        'ALLOWED_DOMAINS': '*',
        'AGIXT_BRANCH': 'stable',
        'AGIXT_REQUIRE_API_KEY': 'false',  # Keep disabled for easier setup
        
        # GraphQL Support
        'GRAPHIQL': 'true',
        'ENABLE_GRAPHQL': 'true',
        
        # External services
        'N8N_URI': 'http://n8n-prod:5678',  # Integration with existing n8n
    }

def create_env_file(install_path: str, config: Dict[str, str]) -> bool:
    """Create the .env file with all configurations"""
    env_file = os.path.join(install_path, ".env")
    
    try:
        with open(env_file, 'w') as f:
            f.write("# =============================================================================\n")
            f.write(f"# AGiXT Server Configuration - {VERSION}\n")
            f.write("# =============================================================================\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("# Features: Nginx Proxy + External AI Providers + GraphQL\n")
            f.write("# Domains: https://agixt.locod-ai.com + https://agixtui.locod-ai.com\n")
            f.write("# Optimization: Code generation, n8n workflows, server automation\n")
            f.write("# =============================================================================\n\n")
            
            # Group variables by category
            categories = {
                "VERSION & BASIC": ["AGIXT_VERSION", "INSTALL_DATE", "AGIXT_AUTO_UPDATE", "AGIXT_API_KEY", "UVICORN_WORKERS", "WORKING_DIRECTORY", "TZ"],
                "PROXY URLS": ["AGIXT_SERVER", "AGIXT_URI", "APP_URI", "AUTH_WEB"],
                "INTERFACE": ["APP_NAME", "APP_DESCRIPTION", "AGIXT_AGENT", "AGIXT_SHOW_SELECTION", "AGIXT_SHOW_AGENT_BAR", "AGIXT_SHOW_APP_BAR", "AGIXT_CONVERSATION_MODE", "INTERACTIVE_MODE", "THEME_NAME", "AGIXT_FOOTER_MESSAGE"],
                "AUTHENTICATION": ["AUTH_PROVIDER", "CREATE_AGENT_ON_REGISTER", "CREATE_AGIXT_AGENT", "ALLOW_EMAIL_SIGN_IN"],
                "FEATURES": ["AGIXT_FILE_UPLOAD_ENABLED", "AGIXT_VOICE_INPUT_ENABLED", "AGIXT_RLHF", "AGIXT_ALLOW_MESSAGE_EDITING", "AGIXT_ALLOW_MESSAGE_DELETION", "AGIXT_SHOW_OVERRIDE_SWITCHES"],
                "SYSTEM": ["DATABASE_TYPE", "DATABASE_NAME", "LOG_LEVEL", "LOG_FORMAT", "ALLOWED_DOMAINS", "AGIXT_BRANCH", "AGIXT_REQUIRE_API_KEY"],
                "GRAPHQL": ["GRAPHIQL", "ENABLE_GRAPHQL"],
                "EXTERNAL SERVICES": ["N8N_URI"]
            }
            
            for category, keys in categories.items():
                f.write(f"# {category}\n")
                for key in keys:
                    if key in config:
                        f.write(f"{key}={config[key]}\n")
                f.write("\n")
            
            f.write("# =============================================================================\n")
            f.write("# CONFIGURATION NOTES v1.1-proxy-no-local\n")
            f.write("# =============================================================================\n")
            f.write("# 🔑 SECURITY:\n")
            f.write("#    - Auto-generated secure API key for JWT authentication\n")
            f.write("#    - API key requirement disabled for easier setup\n")
            f.write("#\n")
            f.write("# 🌐 PROXY SETUP:\n")
            f.write("#    - Frontend: https://agixtui.locod-ai.com → http://agixtinteractive:3437\n")
            f.write("#    - Backend: https://agixt.locod-ai.com → http://agixt:7437\n")
            f.write("#\n")
            f.write("# 🤖 AI PROVIDERS - EXTERNAL READY:\n")
            f.write("#    - No local AI configured (clean start)\n")
            f.write("#    - Ready for OpenAI, Anthropic, Hugging Face, etc.\n")
            f.write("#    - Add provider configurations via AGiXT interface\n")
            f.write("#\n")
            f.write("# 🔗 INTEGRATIONS:\n")
            f.write("#    - n8n: Pre-configured for workflow automation\n")
            f.write("#    - GraphQL: Full management interface\n")
            f.write("#    - Docker Network: agixt-network for internal communication\n")
            f.write("#\n")
            f.write("# 🎯 NEXT STEPS:\n")
            f.write("#    1. Access AGiXT UI: https://agixtui.locod-ai.com (or http://162.55.213.90:3437)\n")
            f.write("#    2. Add external AI provider (OpenAI, Anthropic, etc.)\n")
            f.write("#    3. Create agents using your selected providers\n")
            f.write("#    4. Configure nginx for proxy domains\n")
            f.write("# =============================================================================\n")
        
        log(f"Created .env file with {len(config)} variables", "SUCCESS")
        log(f"Generated secure API key: {config['AGIXT_API_KEY'][:8]}...", "INFO")
        return True
        
    except Exception as e:
        log(f"Failed to create .env file: {e}", "ERROR")
        return False

def update_docker_compose(install_path: str) -> bool:
    """Update docker-compose.yml for proxy setup without local AI"""
    compose_file = os.path.join(install_path, "docker-compose.yml")
    
    if not os.path.exists(compose_file):
        log(f"docker-compose.yml not found at {compose_file}", "ERROR")
        return False
    
    try:
        log("Updating docker-compose.yml for v1.1-proxy-no-local...")
        
        # Read original docker-compose.yml
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Backup original
        backup_file = compose_file + f".backup-{VERSION}"
        with open(backup_file, 'w') as f:
            f.write(content)
        log(f"Backup created: {backup_file}")
        
        # Create the enhanced docker-compose.yml
        enhanced_compose = """
networks:
  agixt-network:
    external: true

services:
  # AGiXT Backend API
  agixt:
    image: joshxt/agixt:main
    container_name: agixt
    restart: unless-stopped
    environment:
      # Version & Basic Configuration
      - AGIXT_VERSION=${AGIXT_VERSION}
      - INSTALL_DATE=${INSTALL_DATE}
      - AGIXT_AUTO_UPDATE=${AGIXT_AUTO_UPDATE}
      - AGIXT_API_KEY=${AGIXT_API_KEY}
      - UVICORN_WORKERS=${UVICORN_WORKERS}
      - WORKING_DIRECTORY=${WORKING_DIRECTORY}
      - TZ=${TZ}
      # URLs
      - AGIXT_SERVER=${AGIXT_SERVER}
      - AGIXT_URI=${AGIXT_URI}
      # System Configuration
      - DATABASE_TYPE=${DATABASE_TYPE}
      - DATABASE_NAME=${DATABASE_NAME}
      - LOG_LEVEL=${LOG_LEVEL}
      - LOG_FORMAT=${LOG_FORMAT}
      - ALLOWED_DOMAINS=${ALLOWED_DOMAINS}
      - AGIXT_BRANCH=${AGIXT_BRANCH}
      - AGIXT_REQUIRE_API_KEY=${AGIXT_REQUIRE_API_KEY}
      # GraphQL Support
      - GRAPHIQL=${GRAPHIQL}
      - ENABLE_GRAPHQL=${ENABLE_GRAPHQL}
      # External Services
      - N8N_URI=${N8N_URI}
    ports:
      - "7437:7437"
    volumes:
      - ./models:/agixt/models
      - ./WORKSPACE:/agixt/WORKSPACE
      - ./agixt:/agixt
    networks:
      - agixt-network

  # AGiXT Frontend Interface
  agixtinteractive:
    image: joshxt/agixt-interactive:main
    container_name: agixtinteractive
    restart: unless-stopped
    depends_on:
      - agixt
    environment:
      # Interface Configuration
      - APP_NAME=${APP_NAME}
      - APP_DESCRIPTION=${APP_DESCRIPTION}
      - APP_URI=${APP_URI}
      - AUTH_WEB=${AUTH_WEB}
      - AGIXT_AGENT=${AGIXT_AGENT}
      - AGIXT_SHOW_SELECTION=${AGIXT_SHOW_SELECTION}
      - AGIXT_SHOW_AGENT_BAR=${AGIXT_SHOW_AGENT_BAR}
      - AGIXT_SHOW_APP_BAR=${AGIXT_SHOW_APP_BAR}
      - AGIXT_CONVERSATION_MODE=${AGIXT_CONVERSATION_MODE}
      - INTERACTIVE_MODE=${INTERACTIVE_MODE}
      - THEME_NAME=${THEME_NAME}
      - AGIXT_FOOTER_MESSAGE=${AGIXT_FOOTER_MESSAGE}
      # Authentication
      - AUTH_PROVIDER=${AUTH_PROVIDER}
      - CREATE_AGENT_ON_REGISTER=${CREATE_AGENT_ON_REGISTER}
      - CREATE_AGIXT_AGENT=${CREATE_AGIXT_AGENT}
      - ALLOW_EMAIL_SIGN_IN=${ALLOW_EMAIL_SIGN_IN}
      # Features
      - AGIXT_FILE_UPLOAD_ENABLED=${AGIXT_FILE_UPLOAD_ENABLED}
      - AGIXT_VOICE_INPUT_ENABLED=${AGIXT_VOICE_INPUT_ENABLED}
      - AGIXT_RLHF=${AGIXT_RLHF}
      - AGIXT_ALLOW_MESSAGE_EDITING=${AGIXT_ALLOW_MESSAGE_EDITING}
      - AGIXT_ALLOW_MESSAGE_DELETION=${AGIXT_ALLOW_MESSAGE_DELETION}
      - AGIXT_SHOW_OVERRIDE_SWITCHES=${AGIXT_SHOW_OVERRIDE_SWITCHES}
      # Backend Connection
      - AGIXT_SERVER=${AGIXT_SERVER}
      - AGIXT_URI=http://agixt:7437
      - TZ=${TZ}
    ports:
      - "3437:3437"
    volumes:
      - ./WORKSPACE:/app/WORKSPACE
    networks:
      - agixt-network
"""
        
        # Write the enhanced docker-compose.yml
        with open(compose_file, 'w') as f:
            f.write(enhanced_compose)
        
        log("docker-compose.yml updated for v1.1-proxy-no-local (no local AI)", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Failed to update docker-compose.yml: {e}", "ERROR")
        return False

def install_dependencies_and_start(install_path: str) -> bool:
    """Install dependencies and start all services"""
    try:
        os.chdir(install_path)
        
        log("🚀 Starting AGiXT v1.1-proxy-no-local services...", "INFO")
        log("📋 Configuration loaded from .env file", "INFO")
        log("🤖 No local AI configured - ready for external providers", "INFO")
        
        log("🐳 Starting Docker Compose services...", "INFO")
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            log("✅ Docker Compose started successfully", "SUCCESS")
            if result.stdout.strip():
                log(f"📝 Output: {result.stdout.strip()}", "INFO")
            
            # Show service status
            log("📊 Checking service status...", "INFO")
            status_result = subprocess.run(
                ["docker", "compose", "ps", "--format", "table"],
                cwd=install_path,
                capture_output=True,
                text=True
            )
            if status_result.returncode == 0 and status_result.stdout.strip():
                log("🐳 Container Status:", "INFO")
                for line in status_result.stdout.strip().split('\n'):
                    log(f"   {line}", "INFO")
            
            # Wait for services to start
            log("⏱️  Waiting for services to initialize...", "INFO")
            time.sleep(30)
            
            # Install GraphQL dependencies
            log("🔧 Installing GraphQL dependencies...", "INFO")
            graphql_success = install_graphql_dependencies(install_path)
            
            if graphql_success:
                log("✅ GraphQL dependencies installed", "SUCCESS")
                
                # Restart AGiXT to load GraphQL
                log("🔄 Restarting AGiXT to load GraphQL...", "INFO")
                restart_result = subprocess.run(
                    ["docker", "compose", "restart", "agixt"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if restart_result.returncode == 0:
                    log("✅ AGiXT restarted successfully", "SUCCESS")
                else:
                    log(f"⚠️  AGiXT restart warning: {restart_result.stderr}", "WARN")
            else:
                log("⚠️  GraphQL dependencies installation had issues", "WARN")
            
            # Final status check
            log("🔍 Final system status check...", "INFO")
            time.sleep(15)  # Wait for services to stabilize
            
            final_status = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=install_path,
                capture_output=True,
                text=True
            )
            
            if final_status.returncode == 0:
                log("📊 Final Service Status:", "INFO")
                for line in final_status.stdout.strip().split('\n'):
                    if line.strip():
                        log(f"   {line}", "INFO")
            
            return True
            
        else:
            log("❌ Failed to start Docker Compose services", "ERROR")
            log(f"💥 Error: {result.stderr}", "ERROR")
            if result.stdout.strip():
                log(f"📝 Output: {result.stdout.strip()}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log("⏰ Docker Compose startup timeout", "ERROR")
        log("🔍 Services may still be starting in background", "INFO")
        return False
    except Exception as e:
        log(f"💥 Unexpected error during service startup: {e}", "ERROR")
        return False

def install_graphql_dependencies(install_path: str) -> bool:
    """Install GraphQL dependencies in AGiXT container"""
    try:
        log("Installing GraphQL dependencies...")
        
        # Wait for container to be ready
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
            log(f"Warning: Could not install GraphQL dependencies: {result.stderr}", "WARN")
        
        return True
        
    except Exception as e:
        log(f"Could not install GraphQL dependencies: {e}", "WARN")
        return False

def verify_installation(install_path: str):
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
        import socket
        import urllib.request
        import urllib.error
        
        endpoints = {
            'AGiXT Frontend': 3437,
            'AGiXT API': 7437
        }
        
        for name, port in endpoints.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                log(f"{name} (port {port}) is accessible", "SUCCESS")
            else:
                log(f"{name} (port {port}) is not accessible yet", "WARN")
            sock.close()
        
        # Test GraphQL endpoint
        try:
            req = urllib.request.Request('http://localhost:7437/graphql')
            try:
                response = urllib.request.urlopen(req, timeout=5)
                log("GraphQL endpoint is accessible", "SUCCESS")
            except urllib.error.HTTPError as e:
                if e.code == 405:
                    log("GraphQL endpoint is accessible (GET method not allowed - normal)", "SUCCESS")
                else:
                    log
