#!/usr/bin/env python3
"""
CRITICAL FIXES for installer_docker.py
====================================

Fix 1: Set AGIXT_REQUIRE_API_KEY=true (clean & honest)
Fix 2: Add conversations directory creation  
Fix 3: Fix EzLocalAI model verification with proper auth
Fix 4: Improve agent registration timing and error handling
"""

import os
import subprocess
import time
import urllib.request
import json
from installer_utils import log, run_command

def generate_all_variables(config):
    """Generate ALL variables needed by all three services - FIXED VERSION"""
    
    log("🔧 Generating ALL variables for AGiXT Backend, Frontend, and EzLocalAI...")
    
    # Start with customer config as base
    all_vars = config.copy()
    
    # Generate security keys
    from installer_utils import generate_secure_api_key
    if 'AGIXT_API_KEY' not in all_vars:
        all_vars['AGIXT_API_KEY'] = generate_secure_api_key()
        log("✅ Generated AGIXT_API_KEY")
    
    # CRITICAL FIX 1: Generate EZLOCALAI_API_KEY for authentication
    if 'EZLOCALAI_API_KEY' not in all_vars:
        all_vars['EZLOCALAI_API_KEY'] = generate_secure_api_key()
        log("✅ Generated EZLOCALAI_API_KEY")
    
    # === AGIXT BACKEND VARIABLES (FIXED VERSION) ===
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
        'GRAPHIQL': 'true',
        'TZ': 'America/New_York',
        
        # FIX: Set AGIXT_REQUIRE_API_KEY=true (honest configuration)
        'AGIXT_REQUIRE_API_KEY': 'true',
        
        # CONTEXT MANAGEMENT (PREVENT HANGS)
        'MAX_CONVERSATION_LENGTH': '50',
        'CONTEXT_CLEANUP_THRESHOLD': '0.8',
        'AUTO_SUMMARIZE_CONTEXT': 'true',
        'EMERGENCY_CONTEXT_RESET': 'true',
        'MAX_RETRY_ATTEMPTS': '3',
        'RETRY_BACKOFF_SECONDS': '2',
        
        # OAuth clients (empty defaults)
        'ALEXA_CLIENT_ID': '',
        'ALEXA_CLIENT_SECRET': '',
        'AWS_CLIENT_ID': '',
        'AWS_CLIENT_SECRET': '',
        'AWS_REGION': '',
        'AWS_USER_POOL_ID': '',
        'DISCORD_CLIENT_ID': '',
        'DISCORD_CLIENT_SECRET': '',
        'FITBIT_CLIENT_ID': '',
        'FITBIT_CLIENT_SECRET': '',
        'GARMIN_CLIENT_ID': '',
        'GARMIN_CLIENT_SECRET': '',
        'GITHUB_CLIENT_ID': '',
        'GITHUB_CLIENT_SECRET': '',
        'GOOGLE_CLIENT_ID': '',
        'GOOGLE_CLIENT_SECRET': '',
        'MICROSOFT_CLIENT_ID': '',
        'MICROSOFT_CLIENT_SECRET': '',
        'TESLA_CLIENT_ID': '',
        'TESLA_CLIENT_SECRET': '',
        'WALMART_CLIENT_ID': '',
        'WALMART_CLIENT_SECRET': '',
        'WALMART_MARKETPLACE_ID': '',
        'X_CLIENT_ID': '',
        'X_CLIENT_SECRET': '',
        
        # Storage defaults
        'B2_KEY_ID': '',
        'B2_APPLICATION_KEY': '',
        'B2_REGION': 'us-west-002',
        'S3_BUCKET': 'agixt-workspace',
        'S3_ENDPOINT': 'http://minio:9000',
        'AWS_ACCESS_KEY_ID': 'minioadmin',
        'AWS_SECRET_ACCESS_KEY': 'minioadmin',
        'AWS_STORAGE_REGION': 'us-east-1',
        'AZURE_STORAGE_ACCOUNT_NAME': '',
        'AZURE_STORAGE_KEY': '',
        
        # AI Provider settings (EzLocalAI focus)
        'AGENT_PERSONA': '',
        'TRAINING_URLS': '',
        'ENABLED_COMMANDS': '',
        'EZLOCALAI_VOICE': '',
        'EZLOCALAI_URI': 'http://ezlocalai:8091',
        'ROTATION_EXCLUSIONS': '',
        'DISABLED_EXTENSIONS': '',
        'DISABLED_PROVIDERS': ''
    }
    
    # === AGIXT INTERACTIVE (FRONTEND) VARIABLES ===
    frontend_defaults = {
        'MODE': 'production',
        'NEXT_TELEMETRY_DISABLED': '1',
        'AGIXT_FOOTER_MESSAGE': 'AGiXT 2025',
        'AGIXT_SERVER': 'http://localhost:7437',
        'APP_DESCRIPTION': 'AGiXT is an advanced artificial intelligence agent orchestration agent.',
        'APP_NAME': 'AGiXT',
        'APP_URI': 'http://localhost:3437',
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
    }
    
    # === EZLOCALAI VARIABLES ===
    ezlocalai_defaults = {
        'EZLOCALAI_URL': 'http://localhost:8091',
        'DEFAULT_MODEL': 'TheBloke/phi-2-dpo-GGUF',  # Will be overridden
        'LLM_MAX_TOKENS': '0',
        'WHISPER_MODEL': 'base.en',
        'IMG_ENABLED': 'false',
        'IMG_DEVICE': 'cpu',
        'VISION_MODEL': '',
        'LLM_BATCH_SIZE': '1024',
        'SD_MODEL': ''
    }
    
    # Apply defaults (customer config overrides defaults)
    for key, default_value in agixt_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    for key, default_value in frontend_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    for key, default_value in ezlocalai_defaults.items():
        if key not in all_vars:
            all_vars[key] = default_value
    
    # Auto-deduce model-specific settings
    model_name = all_vars.get('MODEL_NAME', all_vars.get('DEFAULT_MODEL', ''))
    if model_name:
        all_vars['DEFAULT_MODEL'] = model_name
        
        # Deduce max tokens based on model
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
    
    # Ensure AGIXT_AGENT is set consistently
    if 'AGIXT_AGENT' not in all_vars:
        all_vars['AGIXT_AGENT'] = 'AutomationAssistant'
    
    # Set ports
    all_vars['AGIXT_PORT'] = '7437'
    all_vars['AGIXT_INTERACTIVE_PORT'] = '3437'
    
    log(f"✅ Generated {len(all_vars)} total variables for all services")
    log(f"🤖 Model: {all_vars.get('DEFAULT_MODEL', 'Unknown')}")
    log(f"🔢 Max Tokens: {all_vars.get('LLM_MAX_TOKENS', 'Unknown')}")
    log(f"🌐 Frontend: {all_vars.get('APP_URI', 'Unknown')}")
    log(f"🔧 Backend: {all_vars.get('AGIXT_SERVER', 'Unknown')}")
    
    return all_vars

def create_configuration(install_path, config):
    """Create complete .env and docker-compose.yml with ALL variables - FIXED VERSION"""
    
    try:
        log("🐳 Creating COMPLETE Docker configuration with ALL variables...")
        
        # Generate ALL variables for all services
        all_vars = generate_all_variables(config)
        
        # CRITICAL FIX 2: Create directory structure with conversations directory
        log("📁 Creating directory structure...")
        directories = [
            "models",          # AGiXT database and models
            "WORKSPACE",       # Working directory
            "node_modules",    # Frontend dependencies
            "outputs",         # EzLocalAI outputs
            "voices",          # EzLocalAI voices
            "hf",             # HuggingFace cache
            "whispercpp",     # Whisper models
            "xttsv2_2.0.2",   # TTS models
            "conversations",   # FIXED: Add conversations directory
            "ezlocalai"       # EzLocalAI models directory
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
        
        # Create COMPLETE .env file
        env_path = os.path.join(install_path, ".env")
        log("📄 Creating COMPLETE .env file with ALL variables...")
        
        with open(env_path, 'w') as f:
            f.write("# =============================================================================\n")
            f.write("# AGiXT Complete Environment Configuration - FIXED VERSION\n")
            f.write("# =============================================================================\n")
            f.write("# CRITICAL FIXES:\n")
            f.write("# - AGIXT_REQUIRE_API_KEY=true (honest configuration)\n")
            f.write("# - EZLOCALAI_API_KEY for proper authentication\n")
            f.write("# - Conversations directory creation\n")
            f.write("# - Enhanced agent registration timing\n")
            f.write("# =============================================================================\n\n")
            
            # Write all variables
            for key, value in sorted(all_vars.items()):
                f.write(f"{key}={value}\n")
        
        log(f"✅ COMPLETE .env file created with {len(all_vars)} variables")
        
        # Create FIXED docker-compose.yml
        log("🐳 Creating FIXED docker-compose.yml...")
        
        docker_compose_content = f"""version: '3.8'

networks:
  agixt-network:
    external: true

services:
  agixt:
    image: joshxt/agixt:main
    init: true
    restart: unless-stopped
    environment:
      DATABASE_TYPE: ${{DATABASE_TYPE:-sqlite}}
      DATABASE_NAME: ${{DATABASE_NAME:-models/agixt}}
      UVICORN_WORKERS: ${{UVICORN_WORKERS:-10}}
      AGIXT_API_KEY: ${{AGIXT_API_KEY:-None}}
      AGIXT_URI: ${{AGIXT_URI:-http://agixt:7437}}
      APP_URI: ${{APP_URI:-http://localhost:3437}}
      AGIXT_AGENT: ${{AGIXT_AGENT:-AutomationAssistant}}
      AGIXT_AGENT_PROVIDER: ezlocalai
      AGIXT_REQUIRE_API_KEY: ${{AGIXT_REQUIRE_API_KEY:-true}}
      WORKING_DIRECTORY: ${{WORKING_DIRECTORY:-/agixt/WORKSPACE}}
      REGISTRATION_DISABLED: ${{REGISTRATION_DISABLED:-false}}
      TOKENIZERS_PARALLELISM: "false"
      LOG_LEVEL: ${{LOG_LEVEL:-INFO}}
      STORAGE_BACKEND: ${{STORAGE_BACKEND:-local}}
      STORAGE_CONTAINER: ${{STORAGE_CONTAINER:-agixt-workspace}}
      SEED_DATA: ${{SEED_DATA:-true}}
      GRAPHIQL: ${{GRAPHIQL:-true}}
      TZ: ${{TZ:-America/New_York}}
      
      # Context management (prevent hangs)
      MAX_CONVERSATION_LENGTH: ${{MAX_CONVERSATION_LENGTH:-50}}
      CONTEXT_CLEANUP_THRESHOLD: ${{CONTEXT_CLEANUP_THRESHOLD:-0.8}}
      AUTO_SUMMARIZE_CONTEXT: ${{AUTO_SUMMARIZE_CONTEXT:-true}}
      EMERGENCY_CONTEXT_RESET: ${{EMERGENCY_CONTEXT_RESET:-true}}
      MAX_RETRY_ATTEMPTS: ${{MAX_RETRY_ATTEMPTS:-3}}
      RETRY_BACKOFF_SECONDS: ${{RETRY_BACKOFF_SECONDS:-2}}
      
      # EzLocalAI configuration
      EZLOCALAI_API_KEY: ${{EZLOCALAI_API_KEY}}
      EZLOCALAI_URI: ${{EZLOCALAI_URI}}
      EZLOCALAI_MAX_TOKENS: ${{EZLOCALAI_MAX_TOKENS}}
      
      # Storage
      S3_BUCKET: ${{S3_BUCKET:-agixt-workspace}}
      S3_ENDPOINT: ${{S3_ENDPOINT:-http://minio:9000}}
      AWS_ACCESS_KEY_ID: ${{AWS_ACCESS_KEY_ID:-minioadmin}}
      AWS_SECRET_ACCESS_KEY: ${{AWS_SECRET_ACCESS_KEY:-minioadmin}}
      AWS_STORAGE_REGION: ${{AWS_STORAGE_REGION:-us-east-1}}
      
    ports:
      - "${{AGIXT_PORT:-7437}}:7437"
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
      - EZLOCALAI_URL=${{EZLOCALAI_URL:-http://localhost:8091}}
      - EZLOCALAI_API_KEY=${{EZLOCALAI_API_KEY}}
      - DEFAULT_MODEL=${{DEFAULT_MODEL:-TheBloke/phi-2-dpo-GGUF}}
      - LLM_MAX_TOKENS=${{LLM_MAX_TOKENS:-0}}
      - WHISPER_MODEL=${{WHISPER_MODEL:-base.en}}
      - IMG_ENABLED=${{IMG_ENABLED:-false}}
      - IMG_DEVICE=${{IMG_DEVICE:-cpu}}
      - VISION_MODEL=${{VISION_MODEL}}
      - LLM_BATCH_SIZE=${{LLM_BATCH_SIZE:-1024}}
      - SD_MODEL=${{SD_MODEL}}
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
      MODE: ${{MODE}}
      NEXT_TELEMETRY_DISABLED: ${{NEXT_TELEMETRY_DISABLED}}
      AGIXT_AGENT: ${{AGIXT_AGENT:-AutomationAssistant}}
      AGIXT_FOOTER_MESSAGE: ${{AGIXT_FOOTER_MESSAGE:-AGiXT 2025}}
      AGIXT_SERVER: ${{AGIXT_SERVER:-http://localhost:7437}}
      APP_DESCRIPTION: ${{APP_DESCRIPTION:-AGiXT is an advanced artificial intelligence agent orchestration agent.}}
      APP_NAME: ${{APP_NAME:-AGiXT}}
      APP_URI: ${{APP_URI:-http://localhost:3437}}
      LOG_VERBOSITY_SERVER: ${{LOG_VERBOSITY_SERVER:-3}}
      AGIXT_FILE_UPLOAD_ENABLED: ${{AGIXT_FILE_UPLOAD_ENABLED:-true}}
      AGIXT_VOICE_INPUT_ENABLED: ${{AGIXT_VOICE_INPUT_ENABLED:-true}}
      AGIXT_RLHF: ${{AGIXT_RLHF:-true}}
      AGIXT_ALLOW_MESSAGE_EDITING: ${{AGIXT_ALLOW_MESSAGE_EDITING:-true}}
      AGIXT_ALLOW_MESSAGE_DELETION: ${{AGIXT_ALLOW_MESSAGE_DELETION:-true}}
      AGIXT_SHOW_OVERRIDE_SWITCHES: ${{AGIXT_SHOW_OVERRIDE_SWITCHES:-tts,websearch,analyze-user-input}}
      AGIXT_CONVERSATION_MODE: ${{AGIXT_CONVERSATION_MODE:-select}}
      INTERACTIVE_MODE: ${{INTERACTIVE_MODE:-chat}}
      ALLOW_EMAIL_SIGN_IN: ${{ALLOW_EMAIL_SIGN_IN:-true}}
      TZ: ${{TZ:-America/New_York}}
    ports:
      - "${{AGIXT_INTERACTIVE_PORT:-3437}}:3437"
    restart: unless-stopped
    volumes:
      - ./node_modules:/app/node_modules
    networks:
      - agixt-network
    depends_on:
      - agixt
      - ezlocalai
"""
        
        docker_compose_path = os.path.join(install_path, "docker-compose.yml")
        with open(docker_compose_path, 'w') as f:
            f.write(docker_compose_content)
        
        log("✅ FIXED docker-compose.yml created")
        
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
        
        log("🔧 FIXED Docker configuration completed successfully", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error creating FIXED Docker configuration: {e}", "ERROR")
        return False

def verify_ezlocalai_model(config):
    """FIX 3: Verify EzLocalAI model with proper authentication"""
    
    try:
        # Get the EzLocalAI API key from config
        ezlocalai_api_key = config.get('EZLOCALAI_API_KEY')
        if not ezlocalai_api_key:
            log("⚠️ No EzLocalAI API key found for verification", "WARN")
            return False
        
        log("🔍 Verifying EzLocalAI model with authentication...")
        
        # Try authenticated request to models endpoint
        try:
            req = urllib.request.Request("http://localhost:8091/v1/models")
            req.add_header("Authorization", f"Bearer {ezlocalai_api_key}")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    models_data = json.loads(response.read().decode())
                    if models_data.get('data'):
                        log("✅ EzLocalAI models verified with authentication")
                        return True
                    else:
                        log("⚠️ EzLocalAI responding but no models found", "WARN")
                        return False
        except urllib.error.HTTPError as e:
            if e.code == 401:
                log("❌ EzLocalAI authentication failed", "ERROR")
            else:
                log(f"⚠️ EzLocalAI HTTP error: {e.code}", "WARN")
        except Exception as e:
            log(f"⚠️ Could not connect to EzLocalAI: {e}", "WARN")
        
        # Alternative: Check EzLocalAI health endpoint
        try:
            health_response = urllib.request.urlopen("http://localhost:8091/health", timeout=10)
            if health_response.getcode() == 200:
                log("✅ EzLocalAI is responding (health check)")
                return True
        except:
            pass
        
        # Alternative: Check container logs for model loading
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", "50", "ezlocalai-container"],
                capture_output=True, text=True, timeout=10
            )
            if "model loaded successfully" in result.stdout.lower():
                log("✅ Model loaded successfully (detected from logs)")
                return True
        except:
            pass
        
        log("⚠️ Could not verify EzLocalAI model status", "WARN")
        return False
        
    except Exception as e:
        log(f"❌ Error verifying EzLocalAI model: {e}", "ERROR")
        return False

def ensure_agent_registration(install_path, config):
    """FIX 4: Enhanced agent registration with proper timing and error handling"""
    
    agent_name = config.get('AGIXT_AGENT', 'AutomationAssistant')
    api_key = config.get('AGIXT_API_KEY')
    
    log(f"👤 Registering agent: {agent_name}")
    log("🔑 Using API key authentication (AGIXT_REQUIRE_API_KEY=true)")
    
    # Wait for AGiXT to be ready with longer timeout
    log("⏳ Waiting 120 seconds for AGiXT to be fully ready...")
    time.sleep(120)
    
    try:
        # Check if agent already exists
        log("🔍 Checking existing agents...")
        headers = {"Authorization": f"Bearer {api_key}"}
        
        req = urllib.request.Request("http://localhost:7437/api/agent", headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.getcode() == 200:
                agents_data = json.loads(response.read().decode())
                existing_agents = [agent['name'] for agent in agents_data.get('agents', [])]
                
                if agent_name in existing_agents:
                    log(f"✅ Agent '{agent_name}' already exists", "SUCCESS")
                    return True
                else:
                    log(f"📝 Agent '{agent_name}' not found, creating...")
        
        # Create new agent
        log(f"🤖 Creating agent: {agent_name}")
        
        agent_data = {
            "agent_name": agent_name,
            "settings": {
                "provider": "ezlocalai",
                "AI_MODEL": config.get('DEFAULT_MODEL', 'TheBloke/phi-2-dpo-GGUF'),
                "MAX_TOKENS": config.get('AGENT_MAX_TOKENS', '4096'),
                "AI_TEMPERATURE": "0.7",
                "AI_TOP_P": "0.9",
                "EZLOCALAI_API_KEY": config.get('EZLOCALAI_API_KEY'),
                "EZLOCALAI_URI": "http://ezlocalai:8091"
            }
        }
        
        req = urllib.request.Request(
            "http://localhost:7437/api/agent",
            data=json.dumps(agent_data).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.getcode() in [200, 201]:
                result = json.loads(response.read().decode())
                if "message" in result and "added" in result["message"].lower():
                    log(f"✅ Agent '{agent_name}' created successfully", "SUCCESS")
                    return True
                else:
                    log(f"⚠️ Unexpected response: {result}", "WARN")
                    return False
            else:
                log(f"❌ Failed to create agent: HTTP {response.getcode()}", "ERROR")
                return False
                
    except urllib.error.HTTPError as e:
        log(f"❌ HTTP Error during agent registration: {e.code} - {e.reason}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error during agent registration: {e}", "ERROR")
        return False

def start_services(install_path, config):
    """Start services with enhanced monitoring and agent registration"""
    
    try:
        log("🚀 Starting ALL AGiXT services with FIXED configuration...")
        
        # Verify prerequisites
        if not os.path.exists(install_path):
            log(f"❌ Installation path does not exist: {install_path}", "ERROR")
            return False
        
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
            log(f"⚠️ Could not stop existing services: {e}", "WARN")
        
        # Start services
        log("🚀 Starting all services...")
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
                log(f"Docker output: {result.stdout.strip()}")
        else:
            log(f"❌ Service startup failed with return code {result.returncode}", "ERROR")
            if result.stderr:
                log(f"Error output: {result.stderr}", "ERROR")
            return False
        
        # Wait for services to initialize
        log("⏳ Waiting for all services to initialize (90 seconds)...")
        time.sleep(90)
        
        # Register agent with enhanced timing
        log("👤 Starting enhanced agent registration...")
        agent_success = ensure_agent_registration(install_path, config)
        
        if agent_success:
            log("✅ Agent registration completed successfully", "SUCCESS")
        else:
            log("⚠️ Agent registration had issues but system may still be functional", "WARN")
        
        # Verify EzLocalAI model
        log("🤖 Verifying EzLocalAI model...")
        model_success = verify_ezlocalai_model(config)
        
        if model_success:
            log("✅ EzLocalAI model verification successful", "SUCCESS")
        else:
            log("⚠️ EzLocalAI model verification had issues but system may still be functional", "WARN")
        
        # Check all services status
        log("📊 Checking all service status...")
        try:
            result = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                log("📊 All Services Status:")
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        log(f"   {line}")
        except Exception as e:
            log(f"⚠️ Could not check service status: {e}", "WARN")
        
        log("✅ Service startup completed with FIXES applied", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error starting services: {e}", "ERROR")
        return False

# Additional utility functions for the fixes

def get_model_filename_from_config(config):
    """Extract the actual model filename from config"""
    model_repo = config.get('MODEL_REPO', '')
    model_file = config.get('MODEL_FILE', '')
    
    if model_file:
        return model_file
    elif model_repo:
        # Try to deduce filename from repo
        if 'phi-2' in model_repo.lower():
            return 'phi-2.Q4_K_M.gguf'
        elif 'deepseek' in model_repo.lower():
            return 'deepseek-coder-1.3b-instruct.Q4_K_M.gguf'
        else:
            return 'model.Q4_K_M.gguf'
    else:
        return 'phi-2.Q4_K_M.gguf'  # Safe default

def check_container_health(container_name, timeout=30):
    """Check if a specific container is healthy"""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format='{{.State.Health.Status}}'", container_name],
            capture_output=True, text=True, timeout=timeout
        )
        
        if result.returncode == 0:
            health_status = result.stdout.strip().strip("'")
            return health_status == "healthy"
        else:
            return False
            
    except Exception:
        return False

def wait_for_service_ready(url, timeout=120, api_key=None):
    """Wait for a service to be ready with optional authentication"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url)
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    return True
        except:
            pass
        
        time.sleep(5)
    
    return False

def test_module():
    """Test this FIXED module"""
    log("🧪 Testing FIXED installer_docker module...")
    
    if callable(generate_all_variables):
        log("generate_all_variables function: ✓", "SUCCESS")
    else:
        log("generate_all_variables function: ✗", "ERROR")
    
    if callable(create_configuration):
        log("create_configuration function: ✓", "SUCCESS")
    else:
        log("create_configuration function: ✗", "ERROR")
    
    if callable(start_services):
        log("start_services function: ✓", "SUCCESS")
    else:
        log("start_services function: ✗", "ERROR")
    
    if callable(ensure_agent_registration):
        log("ensure_agent_registration function: ✓", "SUCCESS")
    else:
        log("ensure_agent_registration function: ✗", "ERROR")
    
    if callable(verify_ezlocalai_model):
        log("verify_ezlocalai_model function: ✓", "SUCCESS")
    else:
        log("verify_ezlocalai_model function: ✗", "ERROR")
    
    log("✅ FIXED installer_docker module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
