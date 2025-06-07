#!/usr/bin/env python3
"""
AGiXT Installer - Docker Module v1.7.2 (NO EZLOCALAI)
=====================================================

Simplified version that only installs AGiXT backend and frontend.
NO EzLocalAI service - clean, simple, reliable installation.
"""

import os
import subprocess
import time
from installer_utils import log, run_command

def generate_all_variables(config):
    """Generate variables for AGiXT Backend and Frontend only (NO EzLocalAI)"""
    
    log("🔧 Generating variables for AGiXT Backend and Frontend (NO EzLocalAI)...")
    
    # Start with customer config as base
    all_vars = config.copy()
    
    # Generate security keys
    from installer_utils import generate_secure_api_key
    if 'AGIXT_API_KEY' not in all_vars:
        all_vars['AGIXT_API_KEY'] = generate_secure_api_key()
        log("✅ Generated AGIXT_API_KEY")
    
    # === AGIXT BACKEND VARIABLES ===
    agixt_defaults = {
        'DATABASE_TYPE': 'sqlite',
        'DATABASE_NAME': 'models/agixt',
        'UVICORN_WORKERS': '10',
        'AGIXT_URI': 'http://agixt:7437',
        'WORKING_DIRECTORY': '/agixt/WORKSPACE',
        'REGISTRATION_DISABLED': 'false',
        'TOKENIZERS_PARALLELISM': 'false',
        'LOG_LEVEL': 'INFO',
        'STORAGE_BACKEND': 'local',
        'STORAGE_CONTAINER': 'agixt-workspace',
        'SEED_DATA': 'true',
        'AGIXT_AGENT': 'XT',
        'GRAPHIQL': 'true',
        'TZ': 'America/New_York',
        'ROTATION_EXCLUSIONS': '',
        'DISABLED_EXTENSIONS': '',
        'DISABLED_PROVIDERS': ''
    }
    
    # === FRONTEND VARIABLES (RESPECT USER CONFIG) ===
    frontend_defaults = {
        'MODE': 'production',
        'NEXT_TELEMETRY_DISABLED': '1',
        'AGIXT_FOOTER_MESSAGE': 'AGiXT 2025',
        'APP_DESCRIPTION': 'AGiXT is an advanced artificial intelligence agent orchestration agent.',
        'APP_NAME': 'AGiXT',
        'LOG_VERBOSITY_SERVER': '3',
        'AGIXT_FILE_UPLOAD_ENABLED': 'true',
        'AGIXT_VOICE_INPUT_ENABLED': 'true',
        'AGIXT_RLHF': 'true',
        'AGIXT_ALLOW_MESSAGE_EDITING': 'true',
        'AGIXT_ALLOW_MESSAGE_DELETION': 'true',
        'AGIXT_SHOW_OVERRIDE_SWITCHES': 'tts,websearch,analyze-user-input',
        'AGIXT_CONVERSATION_MODE': 'select',
        'INTERACTIVE_MODE': 'chat',
        'ALLOW_EMAIL_SIGN_IN': 'true'
        # NOTE: AGIXT_SERVER and APP_URI MUST come from user config
    }
    
    # Apply defaults (ONLY if not already in config)
    for key, default_value in agixt_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    for key, default_value in frontend_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    # Set ports
    all_vars['AGIXT_PORT'] = '7437'
    all_vars['AGIXT_INTERACTIVE_PORT'] = '3437'
    
    # CRITICAL: Ensure production URLs from config are preserved
    log("🔍 Checking URL configuration...")
    if 'AGIXT_SERVER' in config:
        log(f"✅ Using config AGIXT_SERVER: {config['AGIXT_SERVER']}")
    else:
        log("⚠️  No AGIXT_SERVER in config")
        
    if 'APP_URI' in config:
        log(f"✅ Using config APP_URI: {config['APP_URI']}")
    else:
        log("⚠️  No APP_URI in config")
    
    log(f"✅ Generated {len(all_vars)} variables for AGiXT services only")
    log("🚫 EzLocalAI completely skipped")
    
    return all_vars

def create_configuration(install_path, config):
    """Create .env and docker-compose.yml WITHOUT EzLocalAI"""
    
    try:
        log("🐳 Creating Docker configuration (NO EzLocalAI)...")
        
        # Generate variables for AGiXT services only
        all_vars = generate_all_variables(config)
        
        # Create simplified directory structure (no EzLocalAI dirs)
        log("📁 Creating directory structure...")
        directories = [
            "models",          # AGiXT database and models
            "WORKSPACE",       # Working directory
            "node_modules",    # Frontend dependencies
            "conversations"    # Conversations directory
        ]
        
        for directory in directories:
            dir_path = os.path.join(install_path, directory)
            try:
                os.makedirs(dir_path, exist_ok=True)
                os.chmod(dir_path, 0o755)
                log(f"✅ Created: {directory}")
            except Exception as e:
                log(f"❌ Failed to create {directory}: {e}", "ERROR")
                return False
        
        # Create .env file
        env_path = os.path.join(install_path, ".env")
        log("📄 Creating .env file (NO EzLocalAI variables)...")
        
        with open(env_path, 'w') as f:
            f.write("# AGiXT v1.7.2 Environment Configuration (NO EzLocalAI)\n")
            f.write("# Clean installation - Backend and Frontend only\n\n")
            
            for key, value in sorted(all_vars.items()):
                f.write(f"{key}={value}\n")
        
        log(f"✅ .env file created with {len(all_vars)} variables")
        
        # Create docker-compose.yml WITHOUT EzLocalAI service
        log("🐳 Creating docker-compose.yml (NO EzLocalAI service)...")
        
        docker_compose_content = """networks:
  agixt-network:
    external: true

services:
  agixt:
    image: joshxt/agixt:main
    init: true
    restart: unless-stopped
    environment:
      DATABASE_TYPE: ${DATABASE_TYPE:-sqlite}
      DATABASE_NAME: ${DATABASE_NAME:-models/agixt}
      UVICORN_WORKERS: ${UVICORN_WORKERS:-10}
      AGIXT_API_KEY: ${AGIXT_API_KEY:-None}
      AGIXT_URI: ${AGIXT_URI:-http://agixt:7437}
      APP_URI: ${APP_URI}
      WORKING_DIRECTORY: ${WORKING_DIRECTORY:-/agixt/WORKSPACE}
      REGISTRATION_DISABLED: ${REGISTRATION_DISABLED:-false}
      TOKENIZERS_PARALLELISM: "false"
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      STORAGE_BACKEND: ${STORAGE_BACKEND:-local}
      STORAGE_CONTAINER: ${STORAGE_CONTAINER:-agixt-workspace}
      SEED_DATA: ${SEED_DATA:-true}
      AGENT_NAME: ${AGIXT_AGENT:-XT}
      GRAPHIQL: ${GRAPHIQL:-true}
      TZ: ${TZ:-America/New_York}
    ports:
      - "${AGIXT_PORT:-7437}:7437"
    volumes:
      - ./models:/agixt/models
      - ./WORKSPACE:/agixt/WORKSPACE
      - ./conversations:/agixt/conversations
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - agixt-network

  agixtinteractive:
    image: joshxt/agixt-interactive:main
    init: true
    environment:
      MODE: ${MODE}
      NEXT_TELEMETRY_DISABLED: ${NEXT_TELEMETRY_DISABLED}
      AGIXT_AGENT: ${AGIXT_AGENT:-XT}
      AGIXT_FOOTER_MESSAGE: ${AGIXT_FOOTER_MESSAGE:-AGiXT 2025}
      AGIXT_SERVER: ${AGIXT_SERVER}
      APP_DESCRIPTION: ${APP_DESCRIPTION:-AGiXT is an advanced artificial intelligence agent orchestration agent.}
      APP_NAME: ${APP_NAME:-AGiXT}
      APP_URI: ${APP_URI}
      LOG_VERBOSITY_SERVER: ${LOG_VERBOSITY_SERVER:-3}
      AGIXT_FILE_UPLOAD_ENABLED: ${AGIXT_FILE_UPLOAD_ENABLED:-true}
      AGIXT_VOICE_INPUT_ENABLED: ${AGIXT_VOICE_INPUT_ENABLED:-true}
      AGIXT_RLHF: ${AGIXT_RLHF:-true}
      AGIXT_ALLOW_MESSAGE_EDITING: ${AGIXT_ALLOW_MESSAGE_EDITING:-true}
      AGIXT_ALLOW_MESSAGE_DELETION: ${AGIXT_ALLOW_MESSAGE_DELETION:-true}
      AGIXT_SHOW_OVERRIDE_SWITCHES: ${AGIXT_SHOW_OVERRIDE_SWITCHES:-tts,websearch,analyze-user-input}
      AGIXT_CONVERSATION_MODE: ${AGIXT_CONVERSATION_MODE:-select}
      INTERACTIVE_MODE: ${INTERACTIVE_MODE:-chat}
      ALLOW_EMAIL_SIGN_IN: ${ALLOW_EMAIL_SIGN_IN:-true}
      TZ: ${TZ:-America/New_York}
    ports:
      - "${AGIXT_INTERACTIVE_PORT:-3437}:3437"
    restart: unless-stopped
    volumes:
      - ./node_modules:/app/node_modules
    networks:
      - agixt-network
"""
        
        docker_compose_path = os.path.join(install_path, "docker-compose.yml")
        with open(docker_compose_path, 'w') as f:
            f.write(docker_compose_content)
        
        log("✅ docker-compose.yml created (NO EzLocalAI)")
        
        # Verify files
        required_files = [".env", "docker-compose.yml"]
        for file in required_files:
            file_path = os.path.join(install_path, file)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                log(f"✅ {file} created ({file_size} bytes)", "SUCCESS")
            else:
                log(f"❌ {file} creation failed", "ERROR")
                return False
        
        log("🔧 Docker configuration completed (NO EzLocalAI)", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error creating Docker configuration: {e}", "ERROR")
        return False

def start_services_simplified(install_path, config):
    """Start AGiXT services only (NO EzLocalAI)"""
    
    try:
        log("🚀 Starting AGiXT services (NO EzLocalAI)...")
        
        # Verify prerequisites
        docker_compose_path = os.path.join(install_path, "docker-compose.yml")
        env_path = os.path.join(install_path, ".env")
        
        for required_file in [docker_compose_path, env_path]:
            if not os.path.exists(required_file):
                log(f"❌ Required file not found: {required_file}", "ERROR")
                return False
        
        log("✅ Configuration files verified")
        
        # Stop any existing services
        log("🛑 Stopping any existing services...")
        try:
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            log("✅ Existing services stopped")
        except Exception as e:
            log(f"⚠️  Could not stop existing services: {e}", "WARN")
        
        # Start services
        log("🚀 Starting AGiXT backend and frontend...")
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                log("✅ AGiXT services started successfully")
                if result.stdout:
                    stdout_lines = result.stdout.strip().split('\n')[:3]
                    for line in stdout_lines:
                        if line.strip():
                            log(f"   {line}")
            else:
                log(f"❌ Service startup failed with return code {result.returncode}", "ERROR")
                if result.stderr:
                    for line in result.stderr.split('\n')[:3]:
                        if line.strip():
                            log(f"Error: {line}", "ERROR")
                return False
                
        except Exception as e:
            log(f"❌ Exception starting services: {e}", "ERROR")
            return False
        
        # Simple wait
        log("⏳ Allowing services to initialize (30 seconds)...")
        time.sleep(30)
        
        # Check container status
        log("📊 Checking container status...")
        try:
            result = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                log("📊 Container Status:")
                status_lines = result.stdout.split('\n')[1:]
                running_count = 0
                for line in status_lines:
                    if line.strip():
                        log(f"   {line}")
                        if 'running' in line.lower() or 'up' in line.lower():
                            running_count += 1
                
                if running_count >= 2:
                    log(f"✅ {running_count} AGiXT containers running", "SUCCESS")
                else:
                    log(f"⚠️  Only {running_count} containers running", "WARN")
                    
        except Exception as e:
            log(f"⚠️  Could not check container status: {e}", "WARN")
        
        log("✅ AGiXT startup completed (NO EzLocalAI)", "SUCCESS")
        log("🚫 EzLocalAI completely skipped - no model loading issues")
        return True
        
    except Exception as e:
        log(f"❌ Error starting AGiXT services: {e}", "ERROR")
        return False

# Compatibility functions
def start_services(install_path, config):
    return start_services_simplified(install_path, config)

def test_module():
    """Test this module"""
    log("🧪 Testing installer_docker module (NO EzLocalAI)...")
    
    functions_to_test = [
        generate_all_variables,
        create_configuration,
        start_services_simplified,
        start_services
    ]
    
    for func in functions_to_test:
        if callable(func):
            log(f"{func.__name__} function: ✓", "SUCCESS")
        else:
            log(f"{func.__name__} function: ✗", "ERROR")
    
    log("✅ installer_docker module (NO EzLocalAI) test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
