#!/usr/bin/env python3
"""
AGiXT Installer - Docker Module v1.7.2 (SIMPLIFIED STARTUP)
===========================================================

Generates ALL variables needed by AGiXT Backend, Frontend, and EzLocalAI.
v1.7.2 Changes: Simplified service startup without complex API verification.

Key Changes:
- Keeps all environment variable generation intact
- Simplifies service startup process
- Removes API verification that causes failures
- Focuses on container health, not API connectivity
"""

import os
import subprocess
import time
from installer_utils import log, run_command

def generate_all_variables(config):
    """Generate ALL variables needed by all three services - unchanged from v1.7"""
    
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
    
    # === AGIXT BACKEND VARIABLES (from AGiXT source) ===
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
        'B2_REGION': 'us-west-002',
        'S3_BUCKET': 'agixt-workspace',
        'S3_ENDPOINT': 'http://minio:9000',
        'AWS_ACCESS_KEY_ID': 'minioadmin',
        'AWS_SECRET_ACCESS_KEY': 'minioadmin',
        'AWS_STORAGE_REGION': 'us-east-1',
        'SEED_DATA': 'true',
        'AGIXT_AGENT': 'XT',
        'GRAPHIQL': 'true',
        'TZ': 'America/New_York',
        
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
        'AZURE_STORAGE_ACCOUNT_NAME': '',
        'AZURE_STORAGE_KEY': '',
        
        # AI Provider settings (empty defaults, will be configured based on model)
        'AGENT_PERSONA': '',
        'TRAINING_URLS': '',
        'ENABLED_COMMANDS': '',
        'EZLOCALAI_VOICE': '',
        'DEEPSEEK_MODEL': '',
        'AZURE_MODEL': '',
        'GOOGLE_MODEL': '',
        'OPENAI_MODEL': '',
        'XAI_MODEL': '',
        'EZLOCALAI_MAX_TOKENS': '',
        'DEEPSEEK_MAX_TOKENS': '',
        'AZURE_MAX_TOKENS': '',
        'XAI_MAX_TOKENS': '',
        'OPENAI_MAX_TOKENS': '',
        'ANTHROPIC_MAX_TOKENS': '',
        'GOOGLE_MAX_TOKENS': '',
        'AZURE_API_KEY': '',
        'GOOGLE_API_KEY': '',
        'OPENAI_API_KEY': '',
        'ANTHROPIC_API_KEY': '',
        'DEEPSEEK_API_KEY': '',
        'XAI_API_KEY': '',
        'AZURE_OPENAI_ENDPOINT': '',
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
        'AGIXT_SERVER': 'http://localhost:7437',  # Will be overridden by customer config
        'APP_DESCRIPTION': 'AGiXT is an advanced artificial intelligence agent orchestration agent.',
        'APP_NAME': 'AGiXT',  # Will be overridden by customer config
        'APP_URI': 'http://localhost:3437',  # Will be overridden by customer config
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
    
    # === AUTO-DEDUCE VALUES BASED ON CUSTOMER CONFIG ===
    
    # Deduce model-specific settings
    model_name = all_vars.get('MODEL_NAME', all_vars.get('DEFAULT_MODEL', ''))
    if model_name:
        # Set DEFAULT_MODEL for EzLocalAI
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
            all_vars['LLM_MAX_TOKENS'] = '4096'  # Safe default
            all_vars['EZLOCALAI_MAX_TOKENS'] = '4096'
    
    # Auto-deduce hardware settings
    threads = all_vars.get('THREADS', '4')
    gpu_layers = all_vars.get('GPU_LAYERS', '0')
    
    # If no GPU, ensure CPU optimization
    if gpu_layers == '0':
        all_vars['IMG_DEVICE'] = 'cpu'
    
    # Set container interconnection URLs
    all_vars['EZLOCALAI_URI'] = 'http://ezlocalai:8091'
    all_vars['AGIXT_URI'] = 'http://agixt:7437'
    
    # Ensure AGIXT_AGENT is set consistently
    if 'AGIXT_AGENT' not in all_vars:
        all_vars['AGIXT_AGENT'] = 'XT'
    
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
    """Create complete .env and docker-compose.yml with ALL variables - unchanged from v1.7"""
    
    try:
        log("🐳 Creating COMPLETE Docker configuration with ALL variables...")
        
        # Generate ALL variables for all services
        all_vars = generate_all_variables(config)
        
        # Create directory structure
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
            "conversations",  # Conversations directory
            "ezlocalai"       # EzLocalAI models
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
            f.write("# AGiXT Complete Environment Configuration v1.7.2\n")
            f.write("# =============================================================================\n")
            f.write("# Generated with ALL variables needed by AGiXT Backend, Frontend, and EzLocalAI\n")
            f.write("# Customer settings merged with auto-generated technical requirements\n")
            f.write("# v1.7.2: Simplified startup approach\n")
            f.write("# =============================================================================\n\n")
            
            # Write all variables
            for key, value in sorted(all_vars.items()):
                f.write(f"{key}={value}\n")
        
        log(f"✅ COMPLETE .env file created with {len(all_vars)} variables")
        
        # Create docker-compose.yml with EXACT structure from AGiXT source
        log("🐳 Creating docker-compose.yml with simplified startup...")
        
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
      DISABLED_EXTENSIONS: ${{DISABLED_EXTENSIONS}}
      DISABLED_PROVIDERS: ${{DISABLED_PROVIDERS}}
      WORKING_DIRECTORY: ${{WORKING_DIRECTORY:-/agixt/WORKSPACE}}
      REGISTRATION_DISABLED: ${{REGISTRATION_DISABLED:-false}}
      TOKENIZERS_PARALLELISM: "false"
      LOG_LEVEL: ${{LOG_LEVEL:-INFO}}
      ALEXA_CLIENT_ID: ${{ALEXA_CLIENT_ID}}
      ALEXA_CLIENT_SECRET: ${{ALEXA_CLIENT_SECRET}}
      AWS_CLIENT_ID: ${{AWS_CLIENT_ID}}
      AWS_CLIENT_SECRET: ${{AWS_CLIENT_SECRET}}
      AWS_REGION: ${{AWS_REGION}}
      AWS_USER_POOL_ID: ${{AWS_USER_POOL_ID}}
      DISCORD_CLIENT_ID: ${{DISCORD_CLIENT_ID}}
      DISCORD_CLIENT_SECRET: ${{DISCORD_CLIENT_SECRET}}
      FITBIT_CLIENT_ID: ${{FITBIT_CLIENT_ID}}
      FITBIT_CLIENT_SECRET: ${{FITBIT_CLIENT_SECRET}}
      GARMIN_CLIENT_ID: ${{GARMIN_CLIENT_ID}}
      GARMIN_CLIENT_SECRET: ${{GARMIN_CLIENT_SECRET}}
      GITHUB_CLIENT_ID: ${{GITHUB_CLIENT_ID}}
      GITHUB_CLIENT_SECRET: ${{GITHUB_CLIENT_SECRET}}
      GOOGLE_CLIENT_ID: ${{GOOGLE_CLIENT_ID}}
      GOOGLE_CLIENT_SECRET: ${{GOOGLE_CLIENT_SECRET}}
      MICROSOFT_CLIENT_ID: ${{MICROSOFT_CLIENT_ID}}
      MICROSOFT_CLIENT_SECRET: ${{MICROSOFT_CLIENT_SECRET}}
      TESLA_CLIENT_ID: ${{TESLA_CLIENT_ID}}
      TESLA_CLIENT_SECRET: ${{TESLA_CLIENT_SECRET}}
      WALMART_CLIENT_ID: ${{WALMART_CLIENT_ID}}
      WALMART_CLIENT_SECRET: ${{WALMART_CLIENT_SECRET}}
      WALMART_MARKETPLACE_ID: ${{WALMART_MARKETPLACE_ID}}
      X_CLIENT_ID: ${{X_CLIENT_ID}}
      X_CLIENT_SECRET: ${{X_CLIENT_SECRET}}
      STORAGE_BACKEND: ${{STORAGE_BACKEND:-local}}
      STORAGE_CONTAINER: ${{STORAGE_CONTAINER:-agixt-workspace}}
      B2_KEY_ID: ${{B2_KEY_ID:-}}
      B2_APPLICATION_KEY: ${{B2_APPLICATION_KEY:-}}
      B2_REGION: ${{B2_REGION:-us-west-002}}
      S3_BUCKET: ${{S3_BUCKET:-agixt-workspace}}
      S3_ENDPOINT: ${{S3_ENDPOINT:-http://minio:9000}}
      AWS_ACCESS_KEY_ID: ${{AWS_ACCESS_KEY_ID:-minioadmin}}
      AWS_SECRET_ACCESS_KEY: ${{AWS_SECRET_ACCESS_KEY:-minioadmin}}
      AWS_STORAGE_REGION: ${{AWS_STORAGE_REGION:-us-east-1}}
      AZURE_STORAGE_ACCOUNT_NAME: ${{AZURE_STORAGE_ACCOUNT_NAME:-}}
      AZURE_STORAGE_KEY: ${{AZURE_STORAGE_KEY:-}}
      SEED_DATA: ${{SEED_DATA:-true}}
      AGENT_NAME: ${{AGIXT_AGENT:-XT}}
      AGENT_PERSONA: ${{AGENT_PERSONA}}
      TRAINING_URLS: ${{TRAINING_URLS}}
      ENABLED_COMMANDS: ${{ENABLED_COMMANDS}}
      EZLOCALAI_VOICE: ${{EZLOCALAI_VOICE}}
      ANTHROPIC_MODEL: ${{ANTHROPIC_MODEL}}
      DEEPSEEK_MODEL: ${{DEEPSEEK_MODEL}}
      AZURE_MODEL: ${{AZURE_MODEL}}
      GOOGLE_MODEL: ${{GOOGLE_MODEL}}
      OPENAI_MODEL: ${{OPENAI_MODEL}}
      XAI_MODEL: ${{XAI_MODEL}}
      EZLOCALAI_MAX_TOKENS: ${{EZLOCALAI_MAX_TOKENS}}
      DEEPSEEK_MAX_TOKENS: ${{DEEPSEEK_MAX_TOKENS}}
      AZURE_MAX_TOKENS: ${{AZURE_MAX_TOKENS}}
      XAI_MAX_TOKENS: ${{XAI_MAX_TOKENS}}
      OPENAI_MAX_TOKENS: ${{OPENAI_MAX_TOKENS}}
      ANTHROPIC_MAX_TOKENS: ${{ANTHROPIC_MAX_TOKENS}}
      GOOGLE_MAX_TOKENS: ${{GOOGLE_MAX_TOKENS}}
      AZURE_API_KEY: ${{AZURE_API_KEY}}
      GOOGLE_API_KEY: ${{GOOGLE_API_KEY}}
      OPENAI_API_KEY: ${{OPENAI_API_KEY}}
      ANTHROPIC_API_KEY: ${{ANTHROPIC_API_KEY}}
      EZLOCALAI_API_KEY: ${{EZLOCALAI_API_KEY}}
      DEEPSEEK_API_KEY: ${{DEEPSEEK_API_KEY}}
      XAI_API_KEY: ${{XAI_API_KEY}}
      AZURE_OPENAI_ENDPOINT: ${{AZURE_OPENAI_ENDPOINT}}
      EZLOCALAI_URI: ${{EZLOCALAI_URI}}
      ROTATION_EXCLUSIONS: ${{ROTATION_EXCLUSIONS}}
      GRAPHIQL: ${{GRAPHIQL:-true}}
      TZ: ${{TZ:-America/New_York}}
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
      - EZLOCALAI_URL=${{EZLOCALAI_URL-http://localhost:8091}}
      - EZLOCALAI_API_KEY=${{EZLOCALAI_API_KEY-}}
      - DEFAULT_MODEL=${{DEFAULT_MODEL-TheBloke/phi-2-dpo-GGUF}}
      - LLM_MAX_TOKENS=${{LLM_MAX_TOKENS-0}}
      - WHISPER_MODEL=${{WHISPER_MODEL-base.en}}
      - IMG_ENABLED=${{IMG_ENABLED-false}}
      - IMG_DEVICE=${{IMG_DEVICE-cpu}}
      - VISION_MODEL=${{VISION_MODEL}}
      - LLM_BATCH_SIZE=${{LLM_BATCH_SIZE-1024}}
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
      AGIXT_AGENT: ${{AGIXT_AGENT:-XT}}
      AGIXT_FOOTER_MESSAGE: ${{AGIXT_FOOTER_MESSAGE:-AGiXT 2025}}
      AGIXT_SERVER: ${{AGIXT_SERVER:-http://localhost:7437}}
      APP_DESCRIPTION: ${{APP_DESCRIPTION-AGiXT is an advanced artificial intelligence agent orchestration agent.}}
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
"""
