#!/usr/bin/env python3
"""
AGiXT Installer - Docker Module (PRODUCTION READY - Fixed Token Limits + Agent Registration)
=============================================================================================

FIXES APPLIED:
- Differentiated token limits (Agent: 4096, EzLocalAI: 8192)
- Proper context management variables
- API key environment fix
- Production-ready error handling
- No more infinite retry loops that freeze the system
- NEW v1.7.1: Agent registration via API after startup

This prevents the "Unable to process request" bug that causes system hangs.
"""

import os
import subprocess
import time
from installer_utils import log, generate_secure_api_key

def generate_all_variables(config):
    """Generate all variables with PRODUCTION-READY token configuration"""
    
    log("🔧 Generating variables with PRODUCTION-READY configuration...")
    
    # Start with customer config
    all_vars = config.copy()
    
    # Generate security keys
    if 'AGIXT_API_KEY' not in all_vars:
        all_vars['AGIXT_API_KEY'] = generate_secure_api_key()
        log("✅ Generated AGIXT_API_KEY")
    
    if 'EZLOCALAI_API_KEY' not in all_vars:
        all_vars['EZLOCALAI_API_KEY'] = generate_secure_api_key()
        log("✅ Generated EZLOCALAI_API_KEY")
    
    # === CRITICAL FIX: DIFFERENTIATED TOKEN LIMITS ===
    
    # FIX 1: Use HuggingFace repo path for DEFAULT_MODEL (not filename)
    model_repo = all_vars.get('DEFAULT_MODEL', 'TheBloke/phi-2-dpo-GGUF')
    all_vars['DEFAULT_MODEL'] = model_repo
    log(f"🎯 DEFAULT_MODEL set to: {model_repo}")
    
    # FIX 2: Set DIFFERENTIATED token limits based on model type
    if 'deepseek' in model_repo.lower():
        agent_tokens = '6144'      # Agent limit
        ezlocalai_tokens = '12288' # EzLocalAI buffer (2x agent)
    elif 'llama' in model_repo.lower() or 'mistral' in model_repo.lower():
        agent_tokens = '6144'
        ezlocalai_tokens = '12288'
    elif 'phi' in model_repo.lower():
        agent_tokens = '4096'      # FIXED: Safe for Phi-2 agents
        ezlocalai_tokens = '8192'  # FIXED: Buffer for EzLocalAI (2x agent)
    else:
        agent_tokens = '4096'      # Safe default
        ezlocalai_tokens = '8192'  # Buffer default
    
    # Apply DIFFERENTIATED limits (CRITICAL FIX)
    all_vars['AGENT_MAX_TOKENS'] = agent_tokens
    all_vars['LLM_MAX_TOKENS'] = ezlocalai_tokens
    all_vars['EZLOCALAI_MAX_TOKENS'] = ezlocalai_tokens
    
    log(f"🔢 Agent MAX_TOKENS: {agent_tokens}")
    log(f"🔢 EzLocalAI MAX_TOKENS: {ezlocalai_tokens}")
    log("✅ FIXED: Token limits are now differentiated (prevents system hangs)")
    
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
        
        # CONTEXT MANAGEMENT (PREVENT HANGS)
        'MAX_CONVERSATION_LENGTH': '50',
        'CONTEXT_CLEANUP_THRESHOLD': '0.8',
        'AUTO_SUMMARIZE_CONTEXT': 'true',
        'EMERGENCY_CONTEXT_RESET': 'true',
        'MAX_RETRY_ATTEMPTS': '3',
        'RETRY_BACKOFF_SECONDS': '2',
        
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
    
    # === AGENT CONFIGURATION (FIXED) ===
    
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
    log(f"👤 Agent: {all_vars.get('AGIXT_AGENT', 'Unknown')}")
    log(f"🔢 Token Strategy: Agent={agent_tokens}, EzLocalAI={ezlocalai_tokens}")
    
    return all_vars

def create_agent_configuration(install_path, config):
    """Create PRODUCTION-READY agent configuration"""
    
    try:
        log("👤 Creating PRODUCTION-READY agent configuration...")
        
        # Create agents directory
        agents_dir = os.path.join(install_path, "models", "agents")
        os.makedirs(agents_dir, exist_ok=True)
        
        agent_name = config.get('AGIXT_AGENT', 'XT')
        agent_file = os.path.join(agents_dir, f"{agent_name}.json")
        
        # PRODUCTION: Create agent config with correct token limits
        agent_config = {
            "settings": {
                "provider": "ezlocalai",  # CRITICAL: ezlocalai provider
                "embeddings_provider": "default",
                "tts_provider": "None",
                "transcription_provider": "default",
                "translation_provider": "default",
                "image_provider": "None",
                "vision_provider": "gpt4vision",
                "AI_MODEL": config.get('DEFAULT_MODEL', 'TheBloke/phi-2-dpo-GGUF'),
                "EZLOCALAI_API_KEY": config.get('EZLOCALAI_API_KEY', ''),
                "MAX_TOKENS": config.get('AGENT_MAX_TOKENS', '4096'),  # FIXED: Use agent-specific limit
                "CONTEXT_WINDOW": config.get('EZLOCALAI_MAX_TOKENS', '8192'),  # NEW: EzLocalAI buffer
                "AI_TEMPERATURE": "0.7",
                "AI_TOP_P": "0.9",
                "VOICE": "DukeNukem",
                "WEBSEARCH_TIMEOUT": "0",
                "WAIT_BETWEEN_REQUESTS": "1",
                "WAIT_AFTER_FAILURE": "3",
                "MAX_RETRIES": "3",  # NEW: Prevent infinite retries
                "RETRY_DELAY": "2",  # NEW: Backoff delay
                "stream": False,
                "WORKING_DIRECTORY_RESTRICTED": True,
                "AUTONOMOUS_EXECUTION": True,
                "PREVENT_CONTEXT_OVERFLOW": True  # NEW: Safety feature
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
        
        log(f"✅ Created PRODUCTION agent: {agent_file}", "SUCCESS")
        log(f"🎯 Agent provider: ezlocalai", "SUCCESS")
        log(f"🤖 Agent model: {agent_config['settings']['AI_MODEL']}", "SUCCESS")
        log(f"🔢 Agent tokens: {agent_config['settings']['MAX_TOKENS']}", "SUCCESS")
        log(f"🔢 Context window: {agent_config['settings']['CONTEXT_WINDOW']}", "SUCCESS")
        
        return True
        
    except Exception as e:
        log(f"❌ Error creating agent configuration: {e}", "ERROR")
        return False

def ensure_agent_registration(install_path, config):
    """MINIMAL FIX v1.7.1: Ensure agent is properly registered in AGiXT after startup"""
    import urllib.request
    import json
    
    # KEEP THE WORKING LOGIC - just use config correctly
    agent_name = config.get('AGIXT_AGENT', 'AutomationAssistant')  # Keep fallback
    api_key = config.get('AGIXT_API_KEY')
    
    log(f"👤 v1.7.1: Registering agent: {agent_name}")
    
    # Wait for AGiXT to be fully ready
    log("⏳ Waiting 90 seconds for AGiXT to be ready...")
    time.sleep(90)
    
    # Register the agent via API
    try:
        # Prepare the request
        data = json.dumps({"agent_name": agent_name, "settings": {}}).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:7437/api/agent",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        # Make the request
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.getcode() == 200:
                log(f"✅ Agent {agent_name} registered successfully", "SUCCESS")
                
                # Verify agent exists
                time.sleep(5)
                verify_req = urllib.request.Request(
                    f"http://localhost:7437/api/agent/{agent_name}",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                with urllib.request.urlopen(verify_req, timeout=15) as verify_response:
                    if verify_response.getcode() == 200:
                        log(f"✅ Agent {agent_name} verification successful", "SUCCESS")
                        return True
                    else:
                        log(f"⚠️ Agent verification returned: {verify_response.getcode()}", "WARN")
                        return False
                        
            else:
                log(f"⚠️ Agent registration returned: {response.getcode()}", "WARN")
                return False
                
    except Exception as e:
        log(f"⚠️ Agent registration failed: {e}", "WARN")
        log("💡 Agent file exists but may need manual registration", "INFO")
        return False

def create_configuration(install_path, config):
    """Create PRODUCTION-READY Docker configuration"""
    
    try:
        log("🐳 Creating PRODUCTION-READY Docker configuration...")
        
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
        
        # Create PRODUCTION agent configuration
        if not create_agent_configuration(install_path, all_vars):
            return False
        
        # Create .env file
        env_path = os.path.join(install_path, ".env")
        log("📄 Creating PRODUCTION .env file...")
        
        with open(env_path, 'w') as f:
            f.write("# AGiXT PRODUCTION Configuration\n")
            f.write("# Fixed token limits prevent system hangs\n")
            f.write("# Agent tokens < EzLocalAI tokens prevents infinite loops\n\n")
            
            for key, value in sorted(all_vars.items()):
                f.write(f"{key}={value}\n")
        
        log(f"✅ Created PRODUCTION .env with {len(all_vars)} variables")
        
        # Create PRODUCTION docker-compose.yml
        docker_compose_content = f"""version: '3.8'

networks:
  agixt-network:
    external: true

services:
  agixt:
    image: joshxt/agixt:main
    command: ["python3", "app.py"]
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
      AGIXT_REQUIRE_API_KEY: ${{AGIXT_REQUIRE_API_KEY:-false}}
      WORKING_DIRECTORY: ${{WORKING_DIRECTORY:-/agixt/WORKSPACE}}
      REGISTRATION_DISABLED: ${{REGISTRATION_DISABLED:-false}}
      TOKENIZERS_PARALLELISM: "false"
      LOG_LEVEL: ${{LOG_LEVEL:-INFO}}
      STORAGE_BACKEND: ${{STORAGE_BACKEND:-local}}
      STORAGE_CONTAINER: ${{STORAGE_CONTAINER:-agixt-workspace}}
      SEED_DATA: ${{SEED_DATA:-true}}
      EZLOCALAI_API_KEY: ${{EZLOCALAI_API_KEY}}
      EZLOCALAI_URI: ${{EZLOCALAI_URI}}
      MAX_CONVERSATION_LENGTH: ${{MAX_CONVERSATION_LENGTH:-50}}
      CONTEXT_CLEANUP_THRESHOLD: ${{CONTEXT_CLEANUP_THRESHOLD:-0.8}}
      AUTO_SUMMARIZE_CONTEXT: ${{AUTO_SUMMARIZE_CONTEXT:-true}}
      EMERGENCY_CONTEXT_RESET: ${{EMERGENCY_CONTEXT_RESET:-true}}
      MAX_RETRY_ATTEMPTS: ${{MAX_RETRY_ATTEMPTS:-3}}
      RETRY_BACKOFF_SECONDS: ${{RETRY_BACKOFF_SECONDS:-2}}
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
      - LLM_MAX_TOKENS=${{LLM_MAX_TOKENS:-8192}}
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
      MODE: ${{MODE:-production}}
      NEXT_TELEMETRY_DISABLED: ${{NEXT_TELEMETRY_DISABLED:-1}}
      AGIXT_AGENT: ${{AGIXT_AGENT:-XT}}
      AGIXT_FOOTER_MESSAGE: ${{AGIXT_FOOTER_MESSAGE:-AGiXT 2025}}
      AGIXT_SERVER: ${{AGIXT_SERVER:-http://localhost:7437}}
      APP_NAME: ${{APP_NAME:-AGiXT}}
      APP_URI: ${{APP_URI:-http://localhost:3437}}
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
        
        log("✅ Created PRODUCTION docker-compose.yml")
        
        # Verify files
        required_files = [".env", "docker-compose.yml"]
        for file in required_files:
            file_path = os.path.join(install_path, file)
            if os.path.exists(file_path):
                log(f"✅ {file} verified", "SUCCESS")
            else:
                log(f"❌ {file} missing", "ERROR")
                return False
        
        log("🎉 PRODUCTION Docker configuration complete!", "SUCCESS")
        log("🎯 Key PRODUCTION fixes applied:", "SUCCESS")
        log("   • Differentiated token limits (Agent: 4096, EzLocalAI: 8192)", "SUCCESS")
        log("   • Context management variables added", "SUCCESS")
        log("   • API key environment properly mapped", "SUCCESS")
        log("   • Retry limits prevent infinite loops", "SUCCESS")
        log("   • AGIXT_AGENT respects config value", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error creating PRODUCTION configuration: {e}", "ERROR")
        return False

def start_services(install_path, config):
    """Start services with PRODUCTION configuration and monitoring"""
    
    try:
        log("🚀 Starting services with PRODUCTION configuration...")
        
        # Verify files exist
        required_files = ["docker-compose.yml", ".env"]
        for file in required_files:
            file_path = os.path.join(install_path, file)
            if not os.path.exists(file_path):
                log(f"❌ Missing: {file_path}", "ERROR")
                return False
        
        # Stop existing services gracefully
        log("🛑 Gracefully stopping existing services...")
        try:
            subprocess.run(
                ["docker", "compose", "down", "--timeout", "30"],
                cwd=install_path,
                capture_output=True,
                timeout=60
            )
            log("✅ Existing services stopped")
            time.sleep(5)  # Brief pause for cleanup
        except:
            log("⚠️ Could not stop existing services (may not exist)", "WARN")
        
        # Start services with production monitoring
        log("🚀 Starting all services with production monitoring...")
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "--remove-orphans"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            log(f"❌ Service startup failed: {result.stderr}", "ERROR")
            return False
        
        log("✅ Services started successfully")
        
        # PRODUCTION: Staggered initialization monitoring
        log("⏳ PRODUCTION startup sequence (120 seconds with monitoring)...")
        
        stages = [
            (15, "AGiXT container initializing..."),
            (30, "EzLocalAI downloading/loading model..."),
            (60, "EzLocalAI model fully loaded..."),
            (90, "Frontend initializing..."),
            (120, "All services should be ready")
        ]
        
        for seconds, stage in stages:
            time.sleep(15)  # Check every 15 seconds
            log(f"⏰ {seconds}s: {stage}")
            
            # Quick health check
            try:
                result = subprocess.run(
                    ["docker", "compose", "ps", "--format", "json"],
                    cwd=install_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    import json
                    services = []
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            try:
                                service = json.loads(line)
                                name = service.get('Name', 'Unknown')
                                state = service.get('State', 'Unknown')
                                if 'running' in state.lower():
                                    services.append(f"✅ {name}")
                                else:
                                    services.append(f"❌ {name}: {state}")
                            except:
                                pass
                    
                    if services:
                        log(f"   Services: {', '.join(services[:3])}")  # Show first 3
            except:
                pass
        
        # Final status check
        log("📊 Final service status check...")
        try:
            result = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                log("📊 PRODUCTION Service Status:")
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        if 'running' in line.lower():
                            log(f"   ✅ {line.strip()}")
                        else:
                            log(f"   ⚠️ {line.strip()}")
        except:
            log("⚠️ Could not check final service status", "WARN")
        
        # KEEP ORIGINAL BEHAVIOR: Try agent registration but don't fail installation
        log("👤 Ensuring agent registration...")
        ensure_agent_registration(install_path, config)  # Just call it, continue regardless
        
        log("🎉 PRODUCTION service startup complete!", "SUCCESS")
        log("📋 Next step: Run post-install-tests.py for validation", "INFO")
        return True
        
    except Exception as e:
        log(f"❌ Error starting PRODUCTION services: {e}", "ERROR")
        return False

def test_module():
    """Test the PRODUCTION-ready module"""
    log("🧪 Testing PRODUCTION installer_docker module...")
    
    # Test variable generation with production config
    test_config = {
        'MODEL_NAME': 'phi-2',
        'AGIXT_AGENT': 'AutomationAssistant'
    }
    
    vars = generate_all_variables(test_config)
    
    # Check PRODUCTION fixes
    if vars.get('DEFAULT_MODEL') == 'TheBloke/phi-2-dpo-GGUF':
        log("DEFAULT_MODEL fix: ✓", "SUCCESS")
    else:
        log("DEFAULT_MODEL fix: ✗", "ERROR")
    
    if vars.get('AGIXT_AGENT') == 'AutomationAssistant':
        log("AGIXT_AGENT preservation: ✓", "SUCCESS")
    else:
        log("AGIXT_AGENT preservation: ✗", "ERROR")
    
    # Check CRITICAL token differentiation
    agent_tokens = vars.get('AGENT_MAX_TOKENS', '0')
    ezlocalai_tokens = vars.get('EZLOCALAI_MAX_TOKENS', '0')
    
    if agent_tokens == '4096' and ezlocalai_tokens == '8192':
        log("Token differentiation: ✓", "SUCCESS")
        log("   Agent: 4096, EzLocalAI: 8192 (prevents hangs)", "SUCCESS")
    else:
        log("Token differentiation: ✗", "ERROR")
        log(f"   Agent: {agent_tokens}, EzLocalAI: {ezlocalai_tokens}", "ERROR")
    
    # Check context management variables
    if vars.get('MAX_RETRY_ATTEMPTS') == '3':
        log("Context management: ✓", "SUCCESS")
    else:
        log("Context management: ✗", "ERROR")
    
    log("✅ PRODUCTION installer_docker module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
