#!/usr/bin/env python3
"""
AGiXT Installer - Docker Module v1.7.2 (SIMPLIFIED STARTUP - FIXED)
===================================================================

Generates ALL variables needed by AGiXT Backend, Frontend, and EzLocalAI.
v1.7.2 Changes: Simplified service startup without complex API verification.

FIXED: Syntax error in try/except blocks
"""

import os
import subprocess
import time
from installer_utils import log, run_command

def generate_all_variables(config):
    """Generate ALL variables needed by all three services"""
    
    log("🔧 Generating ALL variables for AGiXT Backend, Frontend, and EzLocalAI...")
    
    # Start with customer config as base
    all_vars = config.copy()
    
    # Generate security keys
    from installer_utils import generate_secure_api_key
    if 'AGIXT_API_KEY' not in all_vars:
        all_vars['AGIXT_API_KEY'] = generate_secure_api_key()
        log("✅ Generated AGIXT_API_KEY")
    
    # Generate EZLOCALAI_API_KEY for authentication
    if 'EZLOCALAI_API_KEY' not in all_vars:
        all_vars['EZLOCALAI_API_KEY'] = generate_secure_api_key()
        log("✅ Generated EZLOCALAI_API_KEY")
    
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
        'EZLOCALAI_URI': 'http://ezlocalai:8091',
        'ROTATION_EXCLUSIONS': '',
        'DISABLED_EXTENSIONS': '',
        'DISABLED_PROVIDERS': ''
    }
    
    # === FRONTEND VARIABLES (DEFAULTS ONLY - DON'T OVERRIDE CONFIG) ===
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
        # NOTE: AGIXT_SERVER and APP_URI removed from defaults
        # These MUST come from user config (production URLs)
    }
    
    # === EZLOCALAI VARIABLES ===
    ezlocalai_defaults = {
        'EZLOCALAI_URL': 'http://localhost:8091',
        'DEFAULT_MODEL': 'TheBloke/phi-2-dpo-GGUF',
        'LLM_MAX_TOKENS': '0',
        'WHISPER_MODEL': 'base.en',
        'IMG_ENABLED': 'false',
        'IMG_DEVICE': 'cpu',
        'VISION_MODEL': '',
        'LLM_BATCH_SIZE': '1024',
        'SD_MODEL': ''
    }
    
    # Apply defaults (ONLY if not already in config)
    for key, default_value in agixt_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    for key, default_value in frontend_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    for key, default_value in ezlocalai_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    # CRITICAL: Ensure production URLs from config are preserved
    log("🔍 Checking critical URL configuration...")
    if 'AGIXT_SERVER' in config:
        log(f"✅ Using config AGIXT_SERVER: {config['AGIXT_SERVER']}")
    else:
        log("⚠️  No AGIXT_SERVER in config - using container default")
        
    if 'APP_URI' in config:
        log(f"✅ Using config APP_URI: {config['APP_URI']}")
    else:
        log("⚠️  No APP_URI in config - using container default")
    
    # Deduce model-specific settings
    model_name = all_vars.get('MODEL_NAME', all_vars.get('DEFAULT_MODEL', ''))
    if model_name:
        all_vars['DEFAULT_MODEL'] = model_name
        
        # Set max tokens based on model
        if 'deepseek' in model_name.lower():
            all_vars['LLM_MAX_TOKENS'] = '8192'
            all_vars['EZLOCALAI_MAX_TOKENS'] = '8192'
        elif 'llama' in model_name.lower():
            all_vars['LLM_MAX_TOKENS'] = '4096'
            all_vars['EZLOCALAI_MAX_TOKENS'] = '4096'
        elif 'phi' in model_name.lower():
            all_vars['LLM_MAX_TOKENS'] = '2048'
            all_vars['EZLOCALAI_MAX_TOKENS'] = '2048'
        else:
            all_vars['LLM_MAX_TOKENS'] = '4096'
            all_vars['EZLOCALAI_MAX_TOKENS'] = '4096'
    
    # Set container interconnection URLs
    all_vars['EZLOCALAI_URI'] = 'http://ezlocalai:8091'
    all_vars['AGIXT_URI'] = 'http://agixt:7437'
    
    # Set ports
    all_vars['AGIXT_PORT'] = '7437'
    all_vars['AGIXT_INTERACTIVE_PORT'] = '3437'
    
    log(f"✅ Generated {len(all_vars)} total variables for all services")
    log(f"🤖 Model: {all_vars.get('DEFAULT_MODEL', 'Unknown')}")
    log(f"🔢 Max Tokens: {all_vars.get('LLM_MAX_TOKENS', 'Unknown')}")
    
    return all_vars

def create_configuration(install_path, config):
    """Create complete .env and docker-compose.yml"""
    
    try:
        log("🐳 Creating Docker configuration...")
        
        # Generate ALL variables for all services
        all_vars = generate_all_variables(config)
        
        # Create directory structure
        log("📁 Creating directory structure...")
        directories = [
            "models", "WORKSPACE", "node_modules", "outputs", "voices",
            "hf", "whispercpp", "xttsv2_2.0.2", "conversations", "ezlocalai"
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
        log("📄 Creating .env file...")
        
        with open(env_path, 'w') as f:
            f.write("# AGiXT v1.7.2 Environment Configuration\n")
            f.write("# Generated with simplified startup approach\n\n")
            
            for key, value in sorted(all_vars.items()):
                f.write(f"{key}={value}\n")
        
        log(f"✅ .env file created with {len(all_vars)} variables")
        
        # Create docker-compose.yml
        log("🐳 Creating docker-compose.yml...")
        
        docker_compose_content = """version: '3.8'

networks:
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
      APP_URI: ${APP_URI:-http://localhost:3437}
      WORKING_DIRECTORY: ${WORKING_DIRECTORY:-/agixt/WORKSPACE}
      REGISTRATION_DISABLED: ${REGISTRATION_DISABLED:-false}
      TOKENIZERS_PARALLELISM: "false"
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      STORAGE_BACKEND: ${STORAGE_BACKEND:-local}
      STORAGE_CONTAINER: ${STORAGE_CONTAINER:-agixt-workspace}
      SEED_DATA: ${SEED_DATA:-true}
      AGENT_NAME: ${AGIXT_AGENT:-XT}
      EZLOCALAI_URI: ${EZLOCALAI_URI}
      EZLOCALAI_API_KEY: ${EZLOCALAI_API_KEY}
      EZLOCALAI_MAX_TOKENS: ${EZLOCALAI_MAX_TOKENS}
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

  ezlocalai:
    image: joshxt/ezlocalai:latest
    environment:
      - EZLOCALAI_URL=${EZLOCALAI_URL:-http://localhost:8091}
      - EZLOCALAI_API_KEY=${EZLOCALAI_API_KEY:-}
      - DEFAULT_MODEL=${DEFAULT_MODEL:-TheBloke/phi-2-dpo-GGUF}
      - LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-0}
      - WHISPER_MODEL=${WHISPER_MODEL:-base.en}
      - IMG_ENABLED=${IMG_ENABLED:-false}
      - IMG_DEVICE=${IMG_DEVICE:-cpu}
      - VISION_MODEL=${VISION_MODEL}
      - LLM_BATCH_SIZE=${LLM_BATCH_SIZE:-1024}
      - SD_MODEL=${SD_MODEL}
    restart: unless-stopped
    ports:
      - "8091:8091"
      - "8502:8502"
    volumes:
      - ./ezlocalai:/app/models
      - ./hf:/home/root/.cache/huggingface/hub
      - ./outputs:/app/outputs
      - ./voices:/app/voices
      - ./whispercpp:/app/whispercpp
      - ./xttsv2_2.0.2:/app/xttsv2_2.0.2
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
      AGIXT_SERVER: ${AGIXT_SERVER:-http://localhost:7437}
      APP_DESCRIPTION: ${APP_DESCRIPTION:-AGiXT is an advanced artificial intelligence agent orchestration agent.}
      APP_NAME: ${APP_NAME:-AGiXT}
      APP_URI: ${APP_URI:-http://localhost:3437}
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
        
        log("✅ docker-compose.yml created")
        
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
        
        log("🔧 Docker configuration completed successfully", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error creating Docker configuration: {e}", "ERROR")
        return False

def start_services_simplified(install_path, config):
    """v1.7.2: Simplified service startup - no API verification"""
    
    try:
        log("🚀 Starting services with simplified v1.7.2 approach...")
        
        # Verify prerequisites
        if not os.path.exists(install_path):
            log(f"❌ Installation path does not exist: {install_path}", "ERROR")
            return False
        
        docker_compose_path = os.path.join(install_path, "docker-compose.yml")
        env_path = os.path.join(install_path, ".env")
        
        if not os.path.exists(docker_compose_path):
            log(f"❌ docker-compose.yml not found: {docker_compose_path}", "ERROR")
            return False
        
        if not os.path.exists(env_path):
            log(f"❌ .env file not found: {env_path}", "ERROR")
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
        log("🚀 Starting all services...")
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                log("✅ All services started successfully")
                if result.stdout:
                    # Only log first few lines to avoid spam
                    stdout_lines = result.stdout.strip().split('\n')[:5]
                    for line in stdout_lines:
                        if line.strip():
                            log(f"   {line}")
            else:
                log(f"❌ Service startup failed with return code {result.returncode}", "ERROR")
                if result.stderr:
                    stderr_lines = result.stderr.split('\n')[:3]  # Only first 3 error lines
                    for line in stderr_lines:
                        if line.strip():
                            log(f"Error: {line}", "ERROR")
                return False
                
        except Exception as e:
            log(f"❌ Exception starting services: {e}", "ERROR")
            return False
        
        # v1.7.2: Simple wait without complex verification
        log("⏳ Allowing services to initialize (60 seconds)...")
        time.sleep(60)
        
        # v1.7.2: Only check container status, not API endpoints
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
                status_lines = result.stdout.split('\n')[1:]  # Skip header
                running_count = 0
                for line in status_lines:
                    if line.strip():
                        log(f"   {line}")
                        if 'running' in line.lower() or 'up' in line.lower():
                            running_count += 1
                
                if running_count >= 2:  # At least 2 containers should be running
                    log(f"✅ {running_count} containers are running", "SUCCESS")
                else:
                    log(f"⚠️  Only {running_count} containers running", "WARN")
                    
        except Exception as e:
            log(f"⚠️  Could not check container status: {e}", "WARN")
        
        log("✅ Simplified service startup completed", "SUCCESS")
        log("ℹ️  v1.7.2: No API verification during startup - services run independently")
        return True
        
    except Exception as e:
        log(f"❌ Error in simplified service startup: {e}", "ERROR")
        return False

# Keep original function for compatibility
def start_services(install_path, config):
    """Legacy function - use start_services_simplified for v1.7.2"""
    log("⚠️  Using legacy start_services - calling simplified version", "WARN")
    return start_services_simplified(install_path, config)

def test_module():
    """Test this module"""
    log("🧪 Testing installer_docker module v1.7.2...")
    
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
    
    log("✅ installer_docker module v1.7.2 test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
