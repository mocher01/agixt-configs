#!/usr/bin/env python3
"""
AGiXT Installer - Docker Module (FIXED - Correct Agent Configuration)
===================================================================

FIXED: Agent provider set to 'ezlocalai' instead of 'rotation'
FIXED: Proper DEFAULT_MODEL as HuggingFace repo path
FIXED: Remove manual model management complexity
FIXED: Don't override AGIXT_AGENT from config

This creates the correct configuration that matches the working Phi-2 setup.
"""

import os
import subprocess
import time
from installer_utils import log, generate_secure_api_key

def generate_all_variables(config):
    """Generate all variables with FIXED agent configuration"""
    
    log("🔧 Generating variables with CORRECT agent configuration...")
    
    # Start with customer config
    all_vars = config.copy()
    
    # Generate security keys
    if 'AGIXT_API_KEY' not in all_vars:
        all_vars['AGIXT_API_KEY'] = generate_secure_api_key()
        log("✅ Generated AGIXT_API_KEY")
    
    if 'EZLOCALAI_API_KEY' not in all_vars:
        all_vars['EZLOCALAI_API_KEY'] = generate_secure_api_key()
        log("✅ Generated EZLOCALAI_API_KEY")
    
    # === CRITICAL FIXES ===
    
    # FIX 1: Use HuggingFace repo path for DEFAULT_MODEL (not filename)
    model_repo = all_vars.get('DEFAULT_MODEL', 'TheBloke/phi-2-dpo-GGUF')
    all_vars['DEFAULT_MODEL'] = model_repo
    log(f"🎯 DEFAULT_MODEL set to: {model_repo}")
    
    # FIX 2: Set max tokens based on model type
    if 'deepseek' in model_repo.lower():
        max_tokens = '8192'
    elif 'llama' in model_repo.lower() or 'mistral' in model_repo.lower():
        max_tokens = '4096'  
    elif 'phi' in model_repo.lower():
        max_tokens = '2048'
    else:
        max_tokens = '4096'
    
    all_vars['LLM_MAX_TOKENS'] = max_tokens
    all_vars['EZLOCALAI_MAX_TOKENS'] = max_tokens
    log(f"🔢 Max tokens set to: {max_tokens}")
    
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
        'GRAPHIQL': 'true',
        'TZ': 'America/New_York',
        
        # OAuth and API keys (empty defaults)
        'ALEXA_CLIENT_ID': '',
        'ALEXA_CLIENT_SECRET': '',
        'AWS_CLIENT_ID': '',
        'AWS_CLIENT_SECRET': '',
        'DISCORD_CLIENT_ID': '',
        'DISCORD_CLIENT_SECRET': '',
        'GITHUB_CLIENT_ID': '',
        'GITHUB_CLIENT_SECRET': '',
        'GOOGLE_CLIENT_ID': '',
        'GOOGLE_CLIENT_SECRET': '',
        'MICROSOFT_CLIENT_ID': '',
        'MICROSOFT_CLIENT_SECRET': '',
        'AZURE_API_KEY': '',
        'GOOGLE_API_KEY': '',
        'OPENAI_API_KEY': '',
        'ANTHROPIC_API_KEY': '',
        'DEEPSEEK_API_KEY': '',
        
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
        
        # AI Provider settings
        'EZLOCALAI_URI': 'http://ezlocalai:8091',
        'ROTATION_EXCLUSIONS': '',
        'DISABLED_EXTENSIONS': '',
        'DISABLED_PROVIDERS': ''
    }
    
    # === FRONTEND VARIABLES ===
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
    }
    
    # === EZLOCALAI VARIABLES ===
    ezlocalai_defaults = {
        'EZLOCALAI_URL': 'http://localhost:8091',
        'WHISPER_MODEL': 'base.en',
        'IMG_ENABLED': 'false',
        'IMG_DEVICE': 'cpu',
        'VISION_MODEL': '',
        'LLM_BATCH_SIZE': '1024',
        'SD_MODEL': ''
    }
    
    # Apply defaults (customer config overrides)
    for defaults in [agixt_defaults, frontend_defaults, ezlocalai_defaults]:
        for key, default_value in defaults.items():
            if key not in all_vars:
                all_vars[key] = default_value
    
    # === AGENT CONFIGURATION (CRITICAL FIX) ===
    
    # FIX 3: DON'T OVERRIDE AGIXT_AGENT from config - only set default if missing
    if 'AGIXT_AGENT' not in all_vars:
        all_vars['AGIXT_AGENT'] = 'XT'  # Only set default if not in config
    
    # Set container URLs
    all_vars['EZLOCALAI_URI'] = 'http://ezlocalai:8091'
    all_vars['AGIXT_URI'] = 'http://agixt:7437'
    
    # Set ports
    all_vars['AGIXT_PORT'] = '7437'
    all_vars['AGIXT_INTERACTIVE_PORT'] = '3437'
    
    log(f"✅ Generated {len(all_vars)} total variables")
    log(f"🤖 Model: {all_vars.get('DEFAULT_MODEL', 'Unknown')}")
    log(f"🔢 Max Tokens: {all_vars.get('LLM_MAX_TOKENS', 'Unknown')}")
    log(f"👤 Agent: {all_vars.get('AGIXT_AGENT', 'Unknown')}")
    
    return all_vars

def create_agent_configuration(install_path, config):
    """Create the correct agent configuration that sets provider to ezlocalai"""
    
    try:
        log("👤 Creating CORRECT agent configuration...")
        
        # Create agents directory
        agents_dir = os.path.join(install_path, "models", "agents")
        os.makedirs(agents_dir, exist_ok=True)
        
        agent_name = config.get('AGIXT_AGENT', 'XT')
        agent_file = os.path.join(agents_dir, f"{agent_name}.json")
        
        # CRITICAL: Create agent config with ezlocalai provider (not rotation)
        agent_config = {
            "settings": {
                "provider": "ezlocalai",  # THIS IS THE KEY FIX!
                "embeddings_provider": "default",
                "tts_provider": "None",
                "transcription_provider": "default",
                "translation_provider": "default",
                "image_provider": "None",
                "vision_provider": "gpt4vision",
                "AI_MODEL": config.get('DEFAULT_MODEL', 'TheBloke/phi-2-dpo-GGUF'),
                "EZLOCALAI_API_KEY": config.get('EZLOCALAI_API_KEY', ''),
                "MAX_TOKENS": config.get('LLM_MAX_TOKENS', '2048'),
                "AI_TEMPERATURE": "0.7",
                "AI_TOP_P": "0.9",
                "VOICE": "DukeNukem",
                "WEBSEARCH_TIMEOUT": "0",
                "WAIT_BETWEEN_REQUESTS": "1",
                "WAIT_AFTER_FAILURE": "3",
                "stream": False,
                "WORKING_DIRECTORY_RESTRICTED": True,
                "AUTONOMOUS_EXECUTION": True
            },
            "commands": {
                "Custom Commands": False
            },
            "training_urls": []
        }
        
        # Write agent configuration
        import json
        with open(agent_file, 'w') as f:
            json.dump(agent_config, f, indent=2)
        
        log(f"✅ Created agent config: {agent_file}", "SUCCESS")
        log(f"🎯 Agent provider set to: ezlocalai", "SUCCESS")
        log(f"🤖 Agent model set to: {agent_config['settings']['AI_MODEL']}", "SUCCESS")
        
        return True
        
    except Exception as e:
        log(f"❌ Error creating agent configuration: {e}", "ERROR")
        return False

def create_configuration(install_path, config):
    """Create complete Docker configuration with FIXED agent setup"""
    
    try:
        log("🐳 Creating FIXED Docker configuration...")
        
        # Generate all variables with fixes
        all_vars = generate_all_variables(config)
        
        # Create directory structure
        log("📁 Creating directory structure...")
        directories = [
            "models",
            "models/agents",  # For agent configurations
            "WORKSPACE",
            "node_modules", 
            "outputs",
            "voices",
            "hf",
            "whispercpp",
            "xttsv2_2.0.2",
            "conversations"
        ]
        
        for directory in directories:
            dir_path = os.path.join(install_path, directory)
            os.makedirs(dir_path, exist_ok=True)
            os.chmod(dir_path, 0o755)
            log(f"✅ Created: {directory}")
        
        # Create FIXED agent configuration
        if not create_agent_configuration(install_path, all_vars):
            return False
        
        # Create .env file
        env_path = os.path.join(install_path, ".env")
        log("📄 Creating .env file with FIXED configuration...")
        
        with open(env_path, 'w') as f:
            f.write("# AGiXT Configuration (FIXED)\n")
            f.write("# Agent provider correctly set to ezlocalai\n")
            f.write("# DEFAULT_MODEL set to HuggingFace repo path\n\n")
            
            for key, value in sorted(all_vars.items()):
                f.write(f"{key}={value}\n")
        
        log(f"✅ Created .env with {len(all_vars)} variables")
        
        # Create docker-compose.yml with FIXED environment variables
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
      AGIXT_AGENT: ${{AGIXT_AGENT:-XT}}
      AGIXT_AGENT_PROVIDER: ezlocalai
      WORKING_DIRECTORY: ${{WORKING_DIRECTORY:-/agixt/WORKSPACE}}
      REGISTRATION_DISABLED: ${{REGISTRATION_DISABLED:-false}}
      TOKENIZERS_PARALLELISM: "false"
      LOG_LEVEL: ${{LOG_LEVEL:-INFO}}
      STORAGE_BACKEND: ${{STORAGE_BACKEND:-local}}
      STORAGE_CONTAINER: ${{STORAGE_CONTAINER:-agixt-workspace}}
      SEED_DATA: ${{SEED_DATA:-true}}
      EZLOCALAI_API_KEY: ${{EZLOCALAI_API_KEY}}
      EZLOCALAI_URI: ${{EZLOCALAI_URI}}
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
      - EZLOCALAI_URL=${{EZLOCALAI_URL:-http://localhost:8091}}
      - EZLOCALAI_API_KEY=${{EZLOCALAI_API_KEY}}
      - DEFAULT_MODEL=${{DEFAULT_MODEL:-TheBloke/phi-2-dpo-GGUF}}
      - LLM_MAX_TOKENS=${{LLM_MAX_TOKENS:-2048}}
      - WHISPER_MODEL=${{WHISPER_MODEL:-base.en}}
      - IMG_ENABLED=${{IMG_ENABLED:-false}}
      - IMG_DEVICE=${{IMG_DEVICE:-cpu}}
      - LLM_BATCH_SIZE=${{LLM_BATCH_SIZE:-1024}}
    restart: unless-stopped
    ports:
      - "8091:8091"
      - "8502:8502"
    volumes:
      - ./models:/app/models
      - ./hf:/home/root/.cache/huggingface/hub
      - ./outputs:/app/outputs
      - ./voices:/app/voices
      - ./whispercpp:/app/whispercpp
      - ./xttsv2_2.0.2:/app/xttsv2_2.0.2
    networks:
      - agixt-network
    depends_on:
      - agixt

  agixtinteractive:
    image: joshxt/agixt-interactive:main
    init: true
    environment:
      MODE: ${{MODE}}
      NEXT_TELEMETRY_DISABLED: ${{NEXT_TELEMETRY_DISABLED}}
      AGIXT_AGENT: ${{AGIXT_AGENT:-XT}}
      AGIXT_FOOTER_MESSAGE: ${{AGIXT_FOOTER_MESSAGE:-AGiXT 2025}}
      AGIXT_SERVER: ${{AGIXT_SERVER:-http://localhost:7437}}
      APP_NAME: ${{APP_NAME:-AGiXT}}
      APP_URI: ${{APP_URI:-http://localhost:3437}}
      AGIXT_FILE_UPLOAD_ENABLED: ${{AGIXT_FILE_UPLOAD_ENABLED:-true}}
      AGIXT_VOICE_INPUT_ENABLED: ${{AGIXT_VOICE_INPUT_ENABLED:-true}}
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
        
        log("✅ Created FIXED docker-compose.yml")
        
        # Verify files
        required_files = [".env", "docker-compose.yml"]
        for file in required_files:
            file_path = os.path.join(install_path, file)
            if os.path.exists(file_path):
                log(f"✅ {file} verified", "SUCCESS")
            else:
                log(f"❌ {file} missing", "ERROR")
                return False
        
        log("🎉 FIXED Docker configuration complete!", "SUCCESS")
        log("🎯 Key fixes applied:", "SUCCESS")
        log("   • Agent provider set to 'ezlocalai'", "SUCCESS")
        log("   • DEFAULT_MODEL is HuggingFace repo path", "SUCCESS")
        log("   • AGIXT_AGENT respects config value", "SUCCESS")
        log("   • No manual model downloads", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error creating FIXED configuration: {e}", "ERROR")
        return False

def start_services(install_path, config):
    """Start services with the FIXED configuration"""
    
    try:
        log("🚀 Starting services with FIXED configuration...")
        
        # Verify files exist
        required_files = ["docker-compose.yml", ".env"]
        for file in required_files:
            file_path = os.path.join(install_path, file)
            if not os.path.exists(file_path):
                log(f"❌ Missing: {file_path}", "ERROR")
                return False
        
        # Stop existing services
        log("🛑 Stopping existing services...")
        try:
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=install_path,
                capture_output=True,
                timeout=60
            )
        except:
            pass
        
        # Start services
        log("🚀 Starting all services...")
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            log(f"❌ Service startup failed: {result.stderr}", "ERROR")
            return False
        
        log("✅ Services started successfully")
        
        # Wait for initialization
        log("⏳ Waiting for services to initialize (90 seconds)...")
        time.sleep(90)
        
        # Check status
        try:
            result = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                log("📊 Service Status:")
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        log(f"   {line}")
        except:
            log("⚠️ Could not check service status", "WARN")
        
        log("🎉 Service startup complete with FIXED configuration!", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error starting services: {e}", "ERROR")
        return False

def test_module():
    """Test the fixed module"""
    log("🧪 Testing FIXED installer_docker module...")
    
    # Test variable generation
    test_config = {
        'MODEL_NAME': 'phi-2',
        'AGIXT_AGENT': 'AutomationAssistant'  # Test that this is preserved
    }
    
    vars = generate_all_variables(test_config)
    
    # Check critical fixes
    if vars.get('DEFAULT_MODEL') == 'TheBloke/phi-2-dpo-GGUF':
        log("DEFAULT_MODEL fix: ✓", "SUCCESS")
    else:
        log("DEFAULT_MODEL fix: ✗", "ERROR")
    
    if vars.get('AGIXT_AGENT') == 'AutomationAssistant':  # Should preserve config value
        log("AGIXT_AGENT fix: ✓", "SUCCESS")
    else:
        log("AGIXT_AGENT fix: ✗", "ERROR")
    
    log("✅ FIXED installer_docker module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
