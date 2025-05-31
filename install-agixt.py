#!/usr/bin/env python3
"""
AGiXT Automated Installer - v1.1-proxy
======================================

Complete AGiXT installation with:
✅ Nginx reverse proxy integration (agixt.locod-ai.com / agixtui.locod-ai.com)
✅ EzLocalAI integration with CodeQwen2.5-7B for automation/scripting
✅ Clean folder naming (/var/apps/agixt-v1.1-proxy)
✅ Docker network integration
✅ GraphQL management interface
✅ Professional production setup

Usage:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - [OPTIONS] [CONFIG_NAME] [GITHUB_TOKEN]

Examples:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - proxy
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - --no-cleanup proxy
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - proxy github_pat_xxx

Options:
  --no-cleanup, --skip-cleanup    Skip cleaning previous AGiXT installations
  
Arguments:
  CONFIG_NAME     Configuration name (default: proxy)
  GITHUB_TOKEN    GitHub token for private repos (optional)

Features v1.1-proxy:
- 🌐 Nginx proxy: https://agixt.locod-ai.com + https://agixtui.locod-ai.com
- 🤖 EzLocalAI: CodeQwen2.5-7B for code generation & automation
- 📁 Clean naming: /var/apps/agixt-v1.1-proxy
- 🔗 Docker networks: agixt-network integration
- 🎯 Optimized for: n8n workflows, server scripts, automation
"""

import os
import sys
import subprocess
import time
import shutil
from datetime import datetime
from typing import Dict, Optional
import json

# Version info
VERSION = "v1.1-proxy"
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

def get_env_config() -> Dict[str, str]:
    """Get the .env configuration for v1.1-proxy with EzLocalAI"""
    return {
        # Version info
        'AGIXT_VERSION': VERSION,
        'INSTALL_DATE': datetime.now().isoformat(),
        
        # Basic configuration - PROXY READY
        'AGIXT_AUTO_UPDATE': 'true',
        'AGIXT_API_KEY': '',
        'UVICORN_WORKERS': '6',  # Reduced for EzLocalAI
        'WORKING_DIRECTORY': './WORKSPACE',
        'TZ': 'Europe/Paris',
        
        # PROXY URLs - Professional domains
        'AGIXT_SERVER': 'https://agixt.locod-ai.com',
        'AGIXT_URI': 'http://agixt:7437',
        'APP_URI': 'https://agixtui.locod-ai.com',
        'AUTH_WEB': 'https://agixtui.locod-ai.com/user',
        
        # Interface management - Complete setup
        'APP_NAME': 'AGiXT Production Server v1.1-proxy',
        'APP_DESCRIPTION': 'AGiXT Production Server with EzLocalAI & Code Automation',
        'AGIXT_AGENT': 'CodeAssistant',
        'AGIXT_SHOW_SELECTION': 'agent,conversation',
        'AGIXT_SHOW_AGENT_BAR': 'true',
        'AGIXT_SHOW_APP_BAR': 'true',
        'AGIXT_CONVERSATION_MODE': 'select',
        'INTERACTIVE_MODE': 'chat',
        'THEME_NAME': 'doom',
        'AGIXT_FOOTER_MESSAGE': 'AGiXT v1.1-proxy - Code Automation & n8n Workflows',
        
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
        'AGIXT_REQUIRE_API_KEY': 'false',
        
        # GraphQL Support
        'GRAPHIQL': 'true',
        'ENABLE_GRAPHQL': 'true',
        
        # EzLocalAI Integration - OPTIMIZED FOR CODE
        'EZLOCALAI_API_URL': 'http://ezlocalai:8091',
        'EZLOCALAI_API_KEY': 'agixt-automation-key',
        'EZLOCALAI_MODEL': 'CodeQwen2.5-7B-Instruct',
        'EZLOCALAI_MAX_TOKENS': '16384',
        'EZLOCALAI_TEMPERATURE': '0.3',  # Lower for code generation
        'EZLOCALAI_TOP_P': '0.9',
        'EZLOCALAI_VOICE': 'DukeNukem',
        
        # EzLocalAI Server Configuration
        'DEFAULT_MODEL': 'Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/qwen2.5-coder-7b-instruct-q4_k_m.gguf',
        'LLM_MAX_TOKENS': '16384',
        'THREADS': '3',  # Leave 1 core for system
        'GPU_LAYERS': '0',  # CPU only
        'WHISPER_MODEL': 'base.en',
        'IMG_ENABLED': 'false',  # Disable to save resources
        'AUTO_UPDATE': 'true',
        
        # External services
        'TEXTGEN_URI': 'http://text-generation-webui:5000',
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
            f.write("# Features: Nginx Proxy + EzLocalAI + CodeQwen2.5 + GraphQL\n")
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
                "EZLOCALAI INTEGRATION": ["EZLOCALAI_API_URL", "EZLOCALAI_API_KEY", "EZLOCALAI_MODEL", "EZLOCALAI_MAX_TOKENS", "EZLOCALAI_TEMPERATURE", "EZLOCALAI_TOP_P", "EZLOCALAI_VOICE"],
                "EZLOCALAI SERVER": ["DEFAULT_MODEL", "LLM_MAX_TOKENS", "THREADS", "GPU_LAYERS", "WHISPER_MODEL", "IMG_ENABLED", "AUTO_UPDATE"],
                "EXTERNAL SERVICES": ["TEXTGEN_URI", "N8N_URI"]
            }
            
            for category, keys in categories.items():
                f.write(f"# {category}\n")
                for key in keys:
                    if key in config:
                        f.write(f"{key}={config[key]}\n")
                f.write("\n")
            
            f.write("# =============================================================================\n")
            f.write("# END CONFIGURATION\n")
            f.write("# =============================================================================\n")
        
        log(f"Created .env file with {len(config)} variables", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Failed to create .env file: {e}", "ERROR")
        return False

def update_docker_compose(install_path: str) -> bool:
    """Update docker-compose.yml for proxy setup and EzLocalAI"""
    compose_file = os.path.join(install_path, "docker-compose.yml")
    
    if not os.path.exists(compose_file):
        log(f"docker-compose.yml not found at {compose_file}", "ERROR")
        return False
    
    try:
        log("Updating docker-compose.yml for v1.1-proxy...")
        
        # Read original docker-compose.yml
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Backup original
        backup_file = compose_file + f".backup-{VERSION}"
        with open(backup_file, 'w') as f:
            f.write(content)
        log(f"Backup created: {backup_file}")
        
        # Create the enhanced docker-compose.yml
        enhanced_compose = """version: '3.8'

networks:
  agixt-network:
    external: true

services:
  # EzLocalAI - Code Generation & Automation
  ezlocalai:
    image: joshxt/ezlocalai:main
    container_name: ezlocalai
    restart: unless-stopped
    environment:
      - DEFAULT_MODEL=${DEFAULT_MODEL:-Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/qwen2.5-coder-7b-instruct-q4_k_m.gguf}
      - LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-16384}
      - THREADS=${THREADS:-3}
      - GPU_LAYERS=${GPU_LAYERS:-0}
      - WHISPER_MODEL=${WHISPER_MODEL:-base.en}
      - IMG_ENABLED=${IMG_ENABLED:-false}
      - AUTO_UPDATE=${AUTO_UPDATE:-true}
      - EZLOCALAI_API_KEY=${EZLOCALAI_API_KEY:-agixt-automation-key}
      - EZLOCALAI_URL=http://ezlocalai:8091
    ports:
      - "8091:8091"
    volumes:
      - ./ezlocalai:/app/models
      - ./ezlocalai/voices:/app/voices
    networks:
      - agixt-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8091/health || exit 1"]
      interval: 60s
      timeout: 10s
      retries: 10
      start_period: 600s  # Wait 10 minutes before starting health checks

  # AGiXT Backend API
  agixt:
    image: joshxt/agixt:main
    container_name: agixt
    restart: unless-stopped
    depends_on:
      - ezlocalai
    environment:
      # Pass ALL environment variables from .env
      - AGIXT_VERSION=${AGIXT_VERSION}
      - AGIXT_AUTO_UPDATE=${AGIXT_AUTO_UPDATE:-true}
      - AGIXT_API_KEY=${AGIXT_API_KEY}
      - UVICORN_WORKERS=${UVICORN_WORKERS:-6}
      - WORKING_DIRECTORY=${WORKING_DIRECTORY:-./WORKSPACE}
      - TZ=${TZ:-UTC}
      - AGIXT_SERVER=${AGIXT_SERVER}
      - AGIXT_URI=${AGIXT_URI:-http://agixt:7437}
      - DATABASE_TYPE=${DATABASE_TYPE:-sqlite}
      - DATABASE_NAME=${DATABASE_NAME:-models/agixt}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_FORMAT=${LOG_FORMAT}
      - ALLOWED_DOMAINS=${ALLOWED_DOMAINS:-*}
      - AGIXT_BRANCH=${AGIXT_BRANCH:-stable}
      - AGIXT_REQUIRE_API_KEY=${AGIXT_REQUIRE_API_KEY:-false}
      - GRAPHIQL=${GRAPHIQL:-true}
      - ENABLE_GRAPHQL=${ENABLE_GRAPHQL:-true}
      # EzLocalAI Integration
      - EZLOCALAI_API_URL=${EZLOCALAI_API_URL}
      - EZLOCALAI_API_KEY=${EZLOCALAI_API_KEY}
      - EZLOCALAI_MODEL=${EZLOCALAI_MODEL}
      - EZLOCALAI_MAX_TOKENS=${EZLOCALAI_MAX_TOKENS}
      - EZLOCALAI_TEMPERATURE=${EZLOCALAI_TEMPERATURE}
      - EZLOCALAI_TOP_P=${EZLOCALAI_TOP_P}
      - EZLOCALAI_VOICE=${EZLOCALAI_VOICE}
      # External services
      - TEXTGEN_URI=${TEXTGEN_URI}
      - N8N_URI=${N8N_URI}
    ports:
      - "7437:7437"
    volumes:
      - ./models:/agixt/models
      - ./WORKSPACE:/agixt/WORKSPACE
      - ./agixt:/agixt  # Mount latest code for GraphQL
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
      # Interface configuration
      - APP_NAME=${APP_NAME:-AGiXT Production Server v1.1-proxy}
      - APP_DESCRIPTION=${APP_DESCRIPTION}
      - APP_URI=${APP_URI}
      - AUTH_WEB=${AUTH_WEB}
      - AGIXT_AGENT=${AGIXT_AGENT:-CodeAssistant}
      - AGIXT_SHOW_SELECTION=${AGIXT_SHOW_SELECTION:-agent,conversation}
      - AGIXT_SHOW_AGENT_BAR=${AGIXT_SHOW_AGENT_BAR:-true}
      - AGIXT_SHOW_APP_BAR=${AGIXT_SHOW_APP_BAR:-true}
      - AGIXT_CONVERSATION_MODE=${AGIXT_CONVERSATION_MODE:-select}
      - INTERACTIVE_MODE=${INTERACTIVE_MODE:-chat}
      - THEME_NAME=${THEME_NAME:-doom}
      - AGIXT_FOOTER_MESSAGE=${AGIXT_FOOTER_MESSAGE}
      # Authentication
      - AUTH_PROVIDER=${AUTH_PROVIDER:-magicalauth}
      - CREATE_AGENT_ON_REGISTER=${CREATE_AGENT_ON_REGISTER:-true}
      - CREATE_AGIXT_AGENT=${CREATE_AGIXT_AGENT:-true}
      - ALLOW_EMAIL_SIGN_IN=${ALLOW_EMAIL_SIGN_IN:-true}
      # Features
      - AGIXT_FILE_UPLOAD_ENABLED=${AGIXT_FILE_UPLOAD_ENABLED:-true}
      - AGIXT_VOICE_INPUT_ENABLED=${AGIXT_VOICE_INPUT_ENABLED:-true}
      - AGIXT_RLHF=${AGIXT_RLHF:-true}
      - AGIXT_ALLOW_MESSAGE_EDITING=${AGIXT_ALLOW_MESSAGE_EDITING:-true}
      - AGIXT_ALLOW_MESSAGE_DELETION=${AGIXT_ALLOW_MESSAGE_DELETION:-true}
      - AGIXT_SHOW_OVERRIDE_SWITCHES=${AGIXT_SHOW_OVERRIDE_SWITCHES}
      # Backend connection
      - AGIXT_SERVER=${AGIXT_SERVER}
      - AGIXT_URI=http://agixt:7437
      - TZ=${TZ:-UTC}
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
        
        log("docker-compose.yml updated for v1.1-proxy with EzLocalAI", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Failed to update docker-compose.yml: {e}", "ERROR")
        return False

def install_dependencies_and_start(install_path: str) -> bool:
    """Install dependencies and start all services with better progress tracking"""
    try:
        os.chdir(install_path)
        
        log("Starting AGiXT v1.1-proxy services...")
        log("⚠️  This will download CodeQwen2.5-7B model (~4GB) - may take 10-15 minutes", "INFO")
        
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes for model download
        )
        
        if result.returncode == 0:
            log("Docker Compose started successfully", "SUCCESS")
            if result.stdout:
                log(f"Output: {result.stdout}")
            
            log("Waiting for EzLocalAI model download...")
            log("You can monitor progress with: docker logs ezlocalai -f", "INFO")
            
            # Monitor EzLocalAI startup with better feedback
            max_wait_time = 900  # 15 minutes
            wait_interval = 30   # Check every 30 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                log(f"Checking EzLocalAI status... ({elapsed_time//60}m {elapsed_time%60}s elapsed)")
                
                # Check container status
                status_result = subprocess.run(
                    ["docker", "inspect", "ezlocalai", "--format", "{{.State.Health.Status}}"],
                    capture_output=True,
                    text=True
                )
                
                if status_result.returncode == 0:
                    health_status = status_result.stdout.strip()
                    log(f"EzLocalAI health status: {health_status}")
                    
                    if health_status == "healthy":
                        log("EzLocalAI is ready!", "SUCCESS")
                        break
                    elif health_status == "unhealthy":
                        # Check logs for specific error
                        log("EzLocalAI health check failed, checking logs...")
                        logs_result = subprocess.run(
                            ["docker", "logs", "ezlocalai", "--tail", "10"],
                            capture_output=True,
                            text=True
                        )
                        if "downloading" in logs_result.stdout.lower() or "loading" in logs_result.stdout.lower():
                            log("Model still downloading/loading, continuing to wait...")
                        else:
                            log(f"EzLocalAI logs:\n{logs_result.stdout}", "WARN")
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            if elapsed_time >= max_wait_time:
                log("EzLocalAI startup timeout, but continuing installation...", "WARN")
                log("You can check status later with: docker logs ezlocalai -f", "INFO")
            
            # Install GraphQL dependencies in AGiXT container
            log("Installing GraphQL dependencies...")
            install_graphql_dependencies(install_path)
            
            # Restart AGiXT to load GraphQL
            log("Restarting AGiXT with GraphQL support...")
            restart_result = subprocess.run(
                ["docker", "compose", "restart", "agixt"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if restart_result.returncode == 0:
                log("AGiXT service restarted successfully", "SUCCESS")
            else:
                log(f"Warning: Could not restart AGiXT service: {restart_result.stderr}", "WARN")
            
            # Final wait for services
            log("Waiting for all services to be ready...")
            time.sleep(30)
            
            return True
        else:
            log(f"Failed to start services:", "ERROR")
            log(f"Error output: {result.stderr}", "ERROR")
            if result.stdout:
                log(f"Standard output: {result.stdout}")
            return False
        
    except subprocess.TimeoutExpired:
        log("Service startup timeout (15 minutes) - model download may still be in progress", "WARN")
        log("Check status with: docker compose ps && docker logs ezlocalai -f", "INFO")
        return True  # Continue as download might still be happening
    except Exception as e:
        log(f"Error starting services: {e}", "ERROR")
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
            'AGiXT API': 7437,
            'EzLocalAI': 8091
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
                    log(f"GraphQL endpoint returned HTTP {e.code}", "WARN")
        except Exception as e:
            log(f"GraphQL endpoint test failed: {e}", "WARN")
            
    except Exception as e:
        log(f"Could not verify installation: {e}", "WARN")

def main():
    """Main installation function"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print(f"║                    AGiXT Installer {VERSION}                    ║")
    print("║      Nginx Proxy + EzLocalAI + CodeQwen2.5 + GraphQL        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    # Parse command line arguments
    config_name = "proxy"
    github_token = None
    skip_cleanup = False
    
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--no-cleanup" or arg == "--skip-cleanup":
                skip_cleanup = True
                log("Cleanup disabled via command line flag", "INFO")
            elif arg.startswith("github_pat_") or arg.startswith("ghp_"):
                github_token = arg
            elif not arg.startswith("-"):
                config_name = arg
    
    log(f"Configuration: {config_name}")
    log(f"Version: {VERSION}")
    log(f"Target folder: /var/apps/{INSTALL_FOLDER_NAME}")
    log(f"Cleanup previous installations: {'No' if skip_cleanup else 'Yes'}")
    
    # Installation steps
    steps = [
        ("Checking prerequisites", check_prerequisites),
        ("Checking Docker network", check_docker_network),
        ("Cleaning previous installations", lambda: cleanup_previous_installations() if not skip_cleanup else True),
        ("Creating installation directory", lambda: create_installation_directory(config_name)),
        ("Cloning AGiXT repository", None),  # Special handling
        ("Creating configuration", None),     # Special handling
        ("Updating Docker Compose", None),    # Special handling
        ("Starting services", None),          # Special handling
        ("Verifying installation", None)      # Special handling
    ]
    
    install_path = None
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        # Skip cleanup step if disabled
        if step_name == "Cleaning previous installations" and skip_cleanup:
            log(f"Step {i}/{len(steps)}: {step_name}... SKIPPED")
            continue
            
        log(f"Step {i}/{len(steps)}: {step_name}...")
        
        if step_func:
            if step_name == "Creating installation directory":
                install_path = step_func()
                if not install_path:
                    log("Installation failed", "ERROR")
                    sys.exit(1)
            else:
                if not step_func():
                    log(f"Step failed: {step_name}", "ERROR")
                    sys.exit(1)
        else:
            # Handle special steps
            if step_name == "Cloning AGiXT repository":
                if not clone_agixt_repository(install_path, github_token):
                    log("Installation failed", "ERROR")
                    sys.exit(1)
            elif step_name == "Creating configuration":
                config = get_env_config()
                if not create_env_file(install_path, config):
                    log("Installation failed", "ERROR")
                    sys.exit(1)
            elif step_name == "Updating Docker Compose":
                if not update_docker_compose(install_path):
                    log("Installation failed", "ERROR")
                    sys.exit(1)
            elif step_name == "Starting services":
                if not install_dependencies_and_start(install_path):
                    log("Installation failed", "ERROR")
                    sys.exit(1)
            elif step_name == "Verifying installation":
                verify_installation(install_path)
    
    # Success message
    log("Installation completed successfully!", "SUCCESS")
    print("\n" + "="*70)
    print("🎉 AGiXT v1.1-proxy Installation Complete!")
    print("="*70)
    print(f"📁 Directory: {install_path}")
    print(f"🌐 Frontend (via proxy): https://agixtui.locod-ai.com")
    print(f"🔧 Backend API (via proxy): https://agixt.locod-ai.com")
    print(f"🤖 EzLocalAI: http://162.55.213.90:8091")
    print(f"🧬 GraphQL: https://agixt.locod-ai.com/graphql")
    print()
    print("🔗 Direct Access (for testing):")
    print(f"   Frontend: http://162.55.213.90:3437")
    print(f"   Backend: http://162.55.213.90:7437")
    print()
    print("📋 Management Commands:")
    print(f"   Status: cd {install_path} && docker compose ps")
    print(f"   Logs: cd {install_path} && docker compose logs -f")
    print(f"   Stop: cd {install_path} && docker compose down")
    print(f"   Restart: cd {install_path} && docker compose restart")
    print()
    print("🎯 Features Enabled:")
    print("   ✅ Nginx reverse proxy ready")
    print("   ✅ EzLocalAI with CodeQwen2.5-7B")
    print("   ✅ GraphQL management interface")
    print("   ✅ Code generation & automation")
    print("   ✅ n8n workflow integration")
    print()
    print("⚠️  Next Steps:")
    print("   1. Enable nginx configs: agixt.locod-ai.com + agixtui.locod-ai.com")
    print("   2. Wait for CodeQwen2.5 model download (may take 10-15 minutes)")
    print("   3. Test proxy URLs once nginx is configured")
    print("   4. Create agents using EzLocalAI provider")
    print("="*70)


if __name__ == "__main__":
    main()
