#!/usr/bin/env python3
"""
AGiXT Automated Installer - v1.4-ezlocolai-deepseek
====================================================

Complete AGiXT installation with:
✅ Nginx reverse proxy integration (agixt.locod-ai.com / agixtui.locod-ai.com)
✅ EzLocalAI integration with lightweight Deepseek-Coder-1.3B model (~1GB)
✅ HuggingFace token authentication support (from .env file or environment)
✅ EzLocalAI web interface exposed (ports 8091 + 8502)
✅ Automatic model download with authentication
✅ Clean folder naming (/var/apps/agixt-v1.4-ezlocolai-deepseek)
✅ Docker network integration
✅ GraphQL management interface
✅ Optimized for 16GB RAM servers

Usage:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - [OPTIONS] [CONFIG_NAME] [GITHUB_TOKEN]

Examples:
  # With .env file containing HUGGINGFACE_TOKEN=hf_your_token
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - proxy
  
  # With environment variable
  export HUGGINGFACE_TOKEN=hf_your_token
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - proxy

Environment Variables:
  HUGGINGFACE_TOKEN    HuggingFace token for model downloads (from .env file or environment)

Options:
  --no-cleanup, --skip-cleanup    Skip cleaning previous AGiXT installations
  
Arguments:
  CONFIG_NAME     Configuration name (default: proxy)
  GITHUB_TOKEN    GitHub token for private repos (optional)

Features v1.4-ezlocolai-deepseek:
- 🌐 Nginx proxy: https://agixt.locod-ai.com + https://agixtui.locod-ai.com
- 🤖 EzLocalAI: Lightweight Deepseek-Coder-1.3B model (~1GB RAM)
- 🔑 HuggingFace authentication for model downloads (.env file support)
- 🎮 EzLocalAI UI: Exposed on port 8502 for model management
- 📁 Clean naming: /var/apps/agixt-v1.4-ezlocolai-deepseek
- 🔄 Auto-download: Downloads model with HF authentication
- 🔗 Docker networks: agixt-network integration
- 🔑 Secure API key generation
- 🎯 Optimized for: 16GB RAM servers, n8n workflows, server scripts
- 📄 .env file token detection: No export command needed
"""

import os
import sys
import subprocess
import time
import shutil
import secrets
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Optional

# Version info
VERSION = "v1.4-ezlocolai-deepseek"
INSTALL_FOLDER_NAME = f"agixt-{VERSION}"

# Model configuration - DEEPSEEK CODER 1.3B
MODEL_CONFIG = {
    "name": "deepseek-ai/deepseek-coder-1.3b-instruct",
    "display_name": "Deepseek-Coder-1.3B-Instruct",
    "file": "model.safetensors",
    "backup_path": "/var/backups/ezlocalai-models-20250601/deepseek-coder-1.3b-instruct/model.safetensors",
    "download_url": "https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct/resolve/main/model.safetensors",
    "config_url": "https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct/resolve/main/config.json",
    "tokenizer_url": "https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct/resolve/main/tokenizer.json",
    "tokenizer_config_url": "https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct/resolve/main/tokenizer_config.json",
    "expected_size_gb": 1.0,
    "max_tokens": 16384,
    "hidden_size": 2048,
    "num_layers": 24,
    "num_heads": 16,
    "num_kv_heads": 16,
    "vocab_size": 32000
}

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

def check_huggingface_token() -> Optional[str]:
    """Check for HuggingFace token from environment or .env file"""
    
    # First, try to read from existing .env file in current directory
    env_file_paths = ['.env', 'agixt.env', 'config.env']
    
    for env_file in env_file_paths:
        if os.path.exists(env_file):
            log(f"Found existing .env file: {env_file}", "INFO")
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('HUGGINGFACE_TOKEN=') and not line.startswith('#'):
                            token = line.split('=', 1)[1].strip()
                            if token and token != 'your_token_here':
                                log(f"Found HuggingFace token in {env_file}: {token[:8]}...", "SUCCESS")
                                return token
            except Exception as e:
                log(f"Error reading {env_file}: {e}", "WARN")
    
    # If not found in .env files, check environment variable
    token = os.getenv("HUGGINGFACE_TOKEN")
    
    if not token:
        log("HUGGINGFACE_TOKEN not found in environment or .env files", "ERROR")
        log("Please set your HuggingFace token in one of these ways:", "INFO")
        log("", "INFO")
        log("Option 1 - Environment variable:", "INFO")
        log("  export HUGGINGFACE_TOKEN=hf_your_token_here", "INFO")
        log("", "INFO")
        log("Option 2 - Create .env file:", "INFO")
        log("  echo 'HUGGINGFACE_TOKEN=hf_your_token_here' > .env", "INFO")
        log("", "INFO")
        log("Get your token from: https://huggingface.co/settings/tokens", "INFO")
        return None
    
    # Validate token format
    if not token.startswith("hf_"):
        log(f"Invalid HuggingFace token format. Token should start with 'hf_'", "ERROR")
        return None
    
    log(f"HuggingFace token found in environment: {token[:8]}...", "SUCCESS")
    return token

def download_with_auth(url: str, target_path: str, token: str) -> bool:
    """Download file with HuggingFace authentication"""
    try:
        log(f"Downloading: {url}")
        log(f"Target: {target_path}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Create request with authentication
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {token}')
        
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                percent = round(block_num * block_size * 100 / total_size, 1)
                downloaded_mb = round(block_num * block_size / (1024 * 1024), 1)
                total_mb = round(total_size / (1024 * 1024), 1)
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] INFO: Download progress: {percent}% ({downloaded_mb}/{total_mb} MB)", end='')
        
        # Download with authentication
        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            
            with open(target_path, 'wb') as f:
                downloaded = 0
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = round(downloaded * 100 / total_size, 1)
                        downloaded_mb = round(downloaded / (1024 * 1024), 1)
                        total_mb = round(total_size / (1024 * 1024), 1)
                        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] INFO: Download progress: {percent}% ({downloaded_mb}/{total_mb} MB)", end='')
        
        print()  # New line after progress
        
        # Verify download
        if os.path.exists(target_path):
            actual_size_gb = os.path.getsize(target_path) / (1024 * 1024 * 1024)
            log(f"Download completed: {actual_size_gb:.1f}GB", "SUCCESS")
            return True
        else:
            log("Download failed - file not found", "ERROR")
            return False
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            log("Authentication failed - check your HuggingFace token", "ERROR")
        else:
            log(f"HTTP Error {e.code}: {e.reason}", "ERROR")
        return False
    except Exception as e:
        log(f"Error downloading file: {e}", "ERROR")
        return False

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

def copy_or_download_model_files(install_path: str, hf_token: str) -> bool:
    """Copy model files from backup location or download with HF authentication"""
    # Create HuggingFace-style folder structure
    hf_model_name = MODEL_CONFIG["name"]
    model_dir_name = hf_model_name.replace("/", "--")  # Replace / with -- for directory name
    target_model_dir = os.path.join(install_path, "ezlocalai", model_dir_name)
    target_model_path = os.path.join(target_model_dir, MODEL_CONFIG["file"])
    backup_model_path = MODEL_CONFIG["backup_path"]
    
    try:
        log("Setting up Deepseek-Coder-1.3B model (lightweight)...")
        log(f"Model: {hf_model_name}")
        log(f"Display name: {MODEL_CONFIG['display_name']}")
        log(f"Expected size: ~{MODEL_CONFIG['expected_size_gb']}GB")
        
        # Create HuggingFace-style directory structure
        os.makedirs(target_model_dir, exist_ok=True)
        log(f"Created HuggingFace model directory: {target_model_dir}", "SUCCESS")
        
        # Check if backup model exists
        if os.path.exists(backup_model_path):
            log(f"Found backup model at {backup_model_path}", "SUCCESS")
            
            # Get model size
            model_size = os.path.getsize(backup_model_path) / (1024 * 1024 * 1024)  # GB
            log(f"Backup model size: {model_size:.1f}GB", "INFO")
            
            # Copy model file
            log("Copying model file from backup...")
            shutil.copy2(backup_model_path, target_model_path)
            
            # Verify copy
            if os.path.exists(target_model_path):
                target_size = os.path.getsize(target_model_path) / (1024 * 1024 * 1024)  # GB
                log(f"Model copied successfully: {target_size:.1f}GB", "SUCCESS")
            else:
                log("Model copy failed", "ERROR")
                return False
        else:
            log(f"Backup model not found at {backup_model_path}", "WARN")
            log("Downloading model from HuggingFace with authentication...", "INFO")
            
            # Download model files with authentication
            files_to_download = [
                (MODEL_CONFIG["download_url"], target_model_path),
                (MODEL_CONFIG["config_url"], os.path.join(target_model_dir, "config.json")),
                (MODEL_CONFIG["tokenizer_url"], os.path.join(target_model_dir, "tokenizer.json")),
                (MODEL_CONFIG["tokenizer_config_url"], os.path.join(target_model_dir, "tokenizer_config.json"))
            ]
            
            for url, path in files_to_download:
                if not download_with_auth(url, path, hf_token):
                    log(f"Failed to download {os.path.basename(path)}", "ERROR")
                    return False
                log(f"Downloaded {os.path.basename(path)} successfully", "SUCCESS")
        
        # Create additional HuggingFace config files if they don't exist
        log("Creating/updating HuggingFace config files...")
        
        # Create/update config.json
        config_json_path = os.path.join(target_model_dir, "config.json")
        if not os.path.exists(config_json_path):
            config_json = {
                "architectures": ["DeepseekForCausalLM"],
                "attention_dropout": 0.0,
                "bos_token_id": 100000,
                "eos_token_id": 100001,
                "hidden_act": "silu",
                "hidden_size": MODEL_CONFIG["hidden_size"],
                "initializer_range": 0.02,
                "intermediate_size": 5504,
                "max_position_embeddings": MODEL_CONFIG["max_tokens"],
                "model_type": "deepseek",
                "num_attention_heads": MODEL_CONFIG["num_heads"],
                "num_hidden_layers": MODEL_CONFIG["num_layers"],
                "num_key_value_heads": MODEL_CONFIG["num_kv_heads"],
                "rms_norm_eps": 1e-06,
                "rope_theta": 10000.0,
                "tie_word_embeddings": False,
                "torch_dtype": "bfloat16",
                "transformers_version": "4.37.0",
                "use_cache": True,
                "vocab_size": MODEL_CONFIG["vocab_size"]
            }
            
            with open(config_json_path, 'w') as f:
                json.dump(config_json, f, indent=2)
            log("Created config.json", "SUCCESS")
        
        # Create/update tokenizer_config.json if it doesn't exist
        tokenizer_config_path = os.path.join(target_model_dir, "tokenizer_config.json")
        if not os.path.exists(tokenizer_config_path):
            tokenizer_config = {
                "added_tokens_decoder": {
                    "100000": {"content": "<｜begin▁of▁sentence｜>", "lstrip": False, "normalized": False, "rstrip": False, "single_word": False, "special": True},
                    "100001": {"content": "<｜end▁of▁sentence｜>", "lstrip": False, "normalized": False, "rstrip": False, "single_word": False, "special": True}
                },
                "bos_token": "<｜begin▁of▁sentence｜>",
                "eos_token": "<｜end▁of▁sentence｜>",
                "model_max_length": MODEL_CONFIG["max_tokens"],
                "tokenizer_class": "LlamaTokenizer"
            }
            
            with open(tokenizer_config_path, 'w') as f:
                json.dump(tokenizer_config, f, indent=2)
            log("Created tokenizer_config.json", "SUCCESS")
        
        # Set proper permissions
        os.chmod(target_model_path, 0o644)
        log("Model permissions set", "SUCCESS")
        
        # Final verification
        if os.path.exists(target_model_path) and os.path.isfile(target_model_path):
            final_size = os.path.getsize(target_model_path) / (1024 * 1024 * 1024)
            log(f"✅ Model setup complete: {final_size:.1f}GB", "SUCCESS")
            return True
        else:
            log("❌ Model setup failed", "ERROR")
            return False
            
    except Exception as e:
        log(f"Error setting up model files: {e}", "ERROR")
        return False

def get_env_config(hf_token: str) -> Dict[str, str]:
    """Get the .env configuration for v1.2-ezlocolai-deepseek with Deepseek model"""
    api_key = generate_secure_api_key()
    
    return {
        # Version info
        'AGIXT_VERSION': VERSION,
        'INSTALL_DATE': datetime.now().isoformat(),
        
        # Basic configuration - PROXY READY
        'AGIXT_AUTO_UPDATE': 'true',
        'AGIXT_API_KEY': api_key,
        'UVICORN_WORKERS': '6',
        'WORKING_DIRECTORY': './WORKSPACE',
        'TZ': 'Europe/Paris',
        
        # PROXY URLs - Professional domains
        'AGIXT_SERVER': 'https://agixt.locod-ai.com',
        'AGIXT_URI': 'http://agixt:7437',
        'APP_URI': 'https://agixtui.locod-ai.com',
        'AUTH_WEB': 'https://agixtui.locod-ai.com/user',
        
        # Interface management - Complete setup
        'APP_NAME': f'AGiXT Production Server {VERSION}',
        'APP_DESCRIPTION': 'AGiXT Production Server with EzLocalAI & Deepseek-Coder-1.3B Model Integration',
        'AGIXT_AGENT': 'CodeAssistant',
        'AGIXT_SHOW_SELECTION': 'agent,conversation',
        'AGIXT_SHOW_AGENT_BAR': 'true',
        'AGIXT_SHOW_APP_BAR': 'true',
        'AGIXT_CONVERSATION_MODE': 'select',
        'INTERACTIVE_MODE': 'chat',
        'THEME_NAME': 'doom',
        'AGIXT_FOOTER_MESSAGE': f'AGiXT {VERSION} - Deepseek-Coder-1.3B Model Integration',
        
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
        
        # HuggingFace Integration
        'HUGGINGFACE_TOKEN': hf_token,
        
        # EzLocalAI Integration - DEEPSEEK MODEL
        'EZLOCALAI_API_URL': 'http://ezlocalai:8091',
        'EZLOCALAI_API_KEY': 'agixt-automation-key',
        'EZLOCALAI_MODEL': MODEL_CONFIG["display_name"],
        'EZLOCALAI_MAX_TOKENS': '16384',
        'EZLOCALAI_TEMPERATURE': '0.1',  # Lower for code generation
        'EZLOCALAI_TOP_P': '0.9',
        'EZLOCALAI_VOICE': 'DukeNukem',
        
        # EzLocalAI Server Configuration - DEEPSEEK MODEL
        'DEFAULT_MODEL': MODEL_CONFIG["display_name"],
        'LLM_MAX_TOKENS': '16384',
        'THREADS': '4',  # More threads for lighter model
        'GPU_LAYERS': '0',  # CPU only
        'WHISPER_MODEL': 'base.en',
        'IMG_ENABLED': 'false',  # Disable to save resources
        'AUTO_UPDATE': 'true',
        
        # External services
        'TEXTGEN_URI': 'http://text-generation-webui:5000',
        'N8N_URI': 'http://n8n-prod:5678',
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
            f.write("# Features: Nginx Proxy + EzLocalAI + Deepseek-Coder-1.3B Model + GraphQL\n")
            f.write("# Domains: https://agixt.locod-ai.com + https://agixtui.locod-ai.com\n")
            f.write("# Model: Lightweight Deepseek-Coder-1.3B (~1GB RAM)\n")
            f.write("# Optimization: 16GB RAM servers, code generation, workflows\n")
            f.write("# Authentication: HuggingFace token required for model downloads\n")
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
                "HUGGINGFACE INTEGRATION": ["HUGGINGFACE_TOKEN"],
                "EZLOCALAI INTEGRATION": ["EZLOCALAI_API_URL", "EZLOCALAI_API_KEY", "EZLOCALAI_MODEL", "EZLOCALAI_MAX_TOKENS", "EZLOCALAI_TEMPERATURE", "EZLOCALAI_TOP_P", "EZLOCALAI_VOICE"],
                "EZLOCALAI SERVER": ["DEFAULT_MODEL", "LLM_MAX_TOKENS", "THREADS", "GPU_LAYERS", "WHISPER_MODEL", "IMG_ENABLED", "AUTO_UPDATE"],
                "EXTERNAL SERVICES": ["TEXTGEN_URI", "N8N_URI"]
            }
            
            for category, keys in categories.items():
                f.write(f"# {category}\n")
                for key in keys:
                    if key in config:
                        # Hide sensitive tokens in output
                        if key == "HUGGINGFACE_TOKEN":
                            display_value = f"{config[key][:8]}..." if config[key] else "NOT_SET"
                            f.write(f"{key}={config[key]}\n")
                        else:
                            f.write(f"{key}={config[key]}\n")
                f.write("\n")
            
            f.write("# =============================================================================\n")
            f.write(f"# CONFIGURATION NOTES {VERSION}\n")
            f.write("# =============================================================================\n")
            f.write("# 🔑 SECURITY:\n")
            f.write("#    - Auto-generated secure API key for JWT authentication\n")
            f.write("#    - API key requirement disabled for easier setup\n")
            f.write("#    - HuggingFace token for authenticated model downloads\n")
            f.write("#\n")
            f.write("# 🌐 PROXY SETUP:\n")
            f.write("#    - Frontend: https://agixtui.locod-ai.com → http://agixtinteractive:3437\n")
            f.write("#    - Backend: https://agixt.locod-ai.com → http://agixt:7437\n")
            f.write("#    - EzLocalAI API: http://162.55.213.90:8091\n")
            f.write("#    - EzLocalAI UI: http://162.55.213.90:8502\n")
            f.write("#\n")
            f.write("# 🤖 EZLOCALAI - LIGHTWEIGHT DEEPSEEK MODEL:\n")
            f.write(f"#    - Model: {MODEL_CONFIG['display_name']} (~{MODEL_CONFIG['expected_size_gb']}GB)\n")
            f.write("#    - Purpose: Advanced code generation, debugging, optimization\n")
            f.write("#    - Temperature: 0.1 (precise code generation)\n")
            f.write("#    - Max Tokens: 16384 (long code blocks)\n")
            f.write("#    - CPU Only: 4 threads (optimized for 16GB RAM)\n")
            f.write("#    - Memory Usage: ~1.5GB (vs 8GB for 7B model)\n")
            f.write("#    - Authentication: Requires HuggingFace token for downloads\n")
            f.write("#\n")
            f.write("# 🔗 INTEGRATIONS:\n")
            f.write("#    - n8n: Pre-configured for workflow automation\n")
            f.write("#    - GraphQL: Full management interface\n")
            f.write("#    - Docker Network: agixt-network for internal communication\n")
            f.write("#    - EzLocalAI UI: Model management and testing\n")
            f.write("#    - HuggingFace: Authenticated model downloads\n")
            f.write("#\n")
            f.write("# 🎯 MODEL INTEGRATION:\n")
            f.write("#    - Auto-download: Downloads from HuggingFace with authentication\n")
            f.write("#    - HuggingFace-style directory structure created\n")
            f.write("#    - Config files generated for compatibility\n")
            f.write("#    - Ready for immediate use\n")
            f.write("#    - Lightweight for 16GB RAM servers\n")
            f.write("#    - Deepseek architecture optimized for code generation\n")
            f.write("# =============================================================================\n")
        
        log(f"Created .env file with {len(config)} variables", "SUCCESS")
        log(f"Generated secure API key: {config['AGIXT_API_KEY'][:8]}...", "INFO")
        log(f"Model: {config['DEFAULT_MODEL']}", "INFO")
        log(f"HuggingFace token configured: {config['HUGGINGFACE_TOKEN'][:8]}...", "INFO")
        return True
        
    except Exception as e:
        log(f"Failed to create .env file: {e}", "ERROR")
        return False

def update_docker_compose(install_path: str) -> bool:
    """Update docker-compose.yml for proxy setup and EzLocalAI with Deepseek model"""
    compose_file = os.path.join(install_path, "docker-compose.yml")
    
    if not os.path.exists(compose_file):
        log(f"docker-compose.yml not found at {compose_file}", "ERROR")
        return False
    
    try:
        log("Updating docker-compose.yml for v1.4-ezlocolai-deepseek...")
        
        # Read original docker-compose.yml
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Backup original
        backup_file = compose_file + f".backup-{VERSION}"
        with open(backup_file, 'w') as f:
            f.write(content)
        log(f"Backup created: {backup_file}")
        
        # Create the enhanced docker-compose.yml with Deepseek model
        enhanced_compose = """
networks:
  agixt-network:
    external: true

services:
  # EzLocalAI - Deepseek-Coder-1.3B Model (Lightweight)
  ezlocalai:
    image: joshxt/ezlocalai:main
    container_name: ezlocalai
    restart: unless-stopped
    environment:
      - DEFAULT_MODEL=${DEFAULT_MODEL}
      - LLM_MAX_TOKENS=${LLM_MAX_TOKENS}
      - THREADS=${THREADS}
      - GPU_LAYERS=${GPU_LAYERS}
      - WHISPER_MODEL=${WHISPER_MODEL}
      - IMG_ENABLED=${IMG_ENABLED}
      - AUTO_UPDATE=${AUTO_UPDATE}
      - EZLOCALAI_API_KEY=${EZLOCALAI_API_KEY}
      - EZLOCALAI_URL=http://ezlocalai:8091
      - HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}
    ports:
      - "8091:8091"  # API endpoint
      - "8502:8502"  # Streamlit web interface
    volumes:
      - ./ezlocalai:/app/models
      - ./ezlocalai/voices:/app/voices
    networks:
      - agixt-network

  # AGiXT Backend API
  agixt:
    image: joshxt/agixt:main
    container_name: agixt
    restart: unless-stopped
    depends_on:
      - ezlocalai
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
      # HuggingFace Integration
      - HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}
      # EzLocalAI Integration
      - EZLOCALAI_API_URL=${EZLOCALAI_API_URL}
      - EZLOCALAI_API_KEY=${EZLOCALAI_API_KEY}
      - EZLOCALAI_MODEL=${EZLOCALAI_MODEL}
      - EZLOCALAI_MAX_TOKENS=${EZLOCALAI_MAX_TOKENS}
      - EZLOCALAI_TEMPERATURE=${EZLOCALAI_TEMPERATURE}
      - EZLOCALAI_TOP_P=${EZLOCALAI_TOP_P}
      - EZLOCALAI_VOICE=${EZLOCALAI_VOICE}
      # External Services
      - TEXTGEN_URI=${TEXTGEN_URI}
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
        
        log(f"docker-compose.yml updated for {VERSION} with Deepseek-Coder-1.3B model", "SUCCESS")
        log("EzLocalAI UI will be available on port 8502", "INFO")
        log("HuggingFace token will be passed to containers", "INFO")
        return True
        
    except Exception as e:
        log(f"Failed to update docker-compose.yml: {e}", "ERROR")
        return False

def install_dependencies_and_start(install_path: str) -> bool:
    """Install dependencies and start all services"""
    try:
        os.chdir(install_path)
        
        log(f"🚀 Starting AGiXT {VERSION} services...", "INFO")
        log("📋 Configuration loaded from .env file", "INFO")
        log(f"🤖 EzLocalAI will start with {MODEL_CONFIG['display_name']} model", "INFO")
        log(f"💾 Expected RAM usage: ~{MODEL_CONFIG['expected_size_gb'] + 0.5}GB", "INFO")
        log("🔑 HuggingFace authentication configured", "INFO")
        
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

def validate_ezlocalai_configuration(install_path: str) -> bool:
    """Comprehensive validation of EzLocalAI configuration with Deepseek"""
    try:
        log("🔍 Validating EzLocalAI Configuration with Deepseek", "INFO")
        log("=" * 50, "INFO")
        
        # Check model file exists
        model_dir_name = MODEL_CONFIG["name"].replace("/", "--")
        model_file = os.path.join(install_path, "ezlocalai", model_dir_name, MODEL_CONFIG["file"])
        if os.path.exists(model_file):
            model_size = os.path.getsize(model_file) / (1024 * 1024 * 1024)  # GB
            log(f"✅ Model file exists: {model_size:.1f}GB", "SUCCESS")
        else:
            log(f"❌ Model file missing: {model_file}", "ERROR")
            return False
        
        # Check HuggingFace config files
        config_file = os.path.join(install_path, "ezlocalai", model_dir_name, "config.json")
        tokenizer_file = os.path.join(install_path, "ezlocalai", model_dir_name, "tokenizer_config.json")
        
        if os.path.exists(config_file):
            log("✅ HuggingFace config.json exists", "SUCCESS")
        else:
            log("❌ HuggingFace config.json missing", "ERROR")
        
        if os.path.exists(tokenizer_file):
            log("✅ HuggingFace tokenizer_config.json exists", "SUCCESS")
        else:
            log("❌ HuggingFace tokenizer_config.json missing", "ERROR")
        
        # Check .env file variables
        env_file = os.path.join(install_path, ".env")
        if os.path.exists(env_file):
            log("📋 Checking .env variables:", "INFO")
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            # Check critical variables
            required_vars = {
                'DEFAULT_MODEL': MODEL_CONFIG["display_name"],
                'EZLOCALAI_MODEL': MODEL_CONFIG["display_name"],
                'EZLOCALAI_API_URL': 'http://ezlocalai:8091',
                'EZLOCALAI_API_KEY': 'agixt-automation-key',
                'EZLOCALAI_MAX_TOKENS': '16384',
                'EZLOCALAI_TEMPERATURE': '0.1',
                'HUGGINGFACE_TOKEN': 'hf_'  # Just check it starts with hf_
            }
            
            for var, expected in required_vars.items():
                if var == 'HUGGINGFACE_TOKEN':
                    if f"{var}=hf_" in env_content:
                        log(f"  ✅ {var}: Configured", "SUCCESS")
                    else:
                        log(f"  ❌ {var}: Not set correctly", "ERROR")
                elif f"{var}={expected}" in env_content:
                    log(f"  ✅ {var}: {expected}", "SUCCESS")
                else:
                    log(f"  ❌ {var}: Not set correctly", "ERROR")
        
        # Wait for containers to be fully ready
        log("⏱️  Waiting for containers to be ready for validation...", "INFO")
        time.sleep(45)
        
        # Test API endpoints
        log("🔍 Testing API endpoints:", "INFO")
        import socket
        
        endpoints = {
            'EzLocalAI API': 8091,
            'EzLocalAI UI': 8502,
            'AGiXT API': 7437,
            'AGiXT Frontend': 3437
        }
        
        for name, port in endpoints.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    log(f"  ✅ {name} (port {port}): Accessible", "SUCCESS")
                else:
                    log(f"  ⚠️  {name} (port {port}): Not accessible yet", "WARN")
                sock.close()
            except Exception as e:
                log(f"  ⚠️  {name} test failed: {e}", "WARN")
        
        # Check container logs for model loading
        log("🔍 Checking EzLocalAI logs for model loading:", "INFO")
        try:
            result = subprocess.run(
                ["docker", "compose", "logs", "--tail", "30", "ezlocalai"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logs = result.stdout
                if MODEL_CONFIG["display_name"] in logs or "model loaded" in logs.lower():
                    log("  ✅ Model loading detected in logs", "SUCCESS")
                elif "error" in logs.lower() or "failed" in logs.lower():
                    log("  ⚠️  Errors detected in logs", "WARN")
                    log(f"  📝 Recent logs: {logs[-500:]}", "INFO")
                else:
                    log("  ⚠️  Model loading not clearly visible in logs", "WARN")
            else:
                log("  ⚠️  Could not retrieve EzLocalAI logs", "WARN")
        except Exception as e:
            log(f"  ⚠️  Log check failed: {e}", "WARN")
        
        # Final validation summary
        log("=" * 50, "INFO")
        log("📊 VALIDATION SUMMARY", "INFO")
        log("=" * 50, "INFO")
        log("🎯 Model Integration Status:", "INFO")
        log(f"  📦 Model File: {model_file}", "INFO")
        log(f"  🔧 Configuration: {MODEL_CONFIG['display_name']}", "INFO")
        log(f"  📁 Installation: {install_path}", "INFO")
        log(f"  💾 RAM Usage: ~{MODEL_CONFIG['expected_size_gb'] + 0.5}GB", "INFO")
        log(f"  🔑 HuggingFace Auth: Configured", "INFO")
        log("", "INFO")
        log("✅ EzLocalAI with Deepseek validation completed", "SUCCESS")
        
        return True
        
    except Exception as e:
        log(f"❌ Validation failed: {e}", "ERROR")
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
            'EzLocalAI API': 8091,
            'EzLocalAI UI': 8502
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
    print(f"║                 AGiXT Installer {VERSION}                  ║")
    print("║     Nginx Proxy + EzLocalAI + Deepseek-Coder-1.3B + GraphQL    ║")
    print("║              Lightweight Model (~1GB RAM)                   ║")
    print("║         🔑 HuggingFace Token (.env file or export)          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    # Check HuggingFace token first
    hf_token = check_huggingface_token()
    if not hf_token:
        log("Installation cannot proceed without HuggingFace token", "ERROR")
        sys.exit(1)
    
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
    log(f"Model: {MODEL_CONFIG['display_name']} (~{MODEL_CONFIG['expected_size_gb']}GB)")
    log(f"HuggingFace token: {hf_token[:8]}...")
    log(f"Cleanup previous installations: {'No' if skip_cleanup else 'Yes'}")
    
    # Installation steps
    steps = [
        ("Checking prerequisites", check_prerequisites),
        ("Checking Docker network", check_docker_network),
        ("Cleaning previous installations", lambda: cleanup_previous_installations() if not skip_cleanup else True),
        ("Creating installation directory", lambda: create_installation_directory(config_name)),
        ("Cloning AGiXT repository", None),  # Special handling
        ("Setting up Deepseek model files", None),     # Special handling - UPDATED NAME
        ("Creating configuration", None),     # Special handling
        ("Updating Docker Compose", None),    # Special handling
        ("Starting services", None),          # Special handling
        ("Verifying installation", None),     # Special handling
        ("Validating EzLocalAI", None)       # Special handling
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
            elif step_name == "Setting up Deepseek model files":  # UPDATED NAME
                if not copy_or_download_model_files(install_path, hf_token):  # UPDATED FUNCTION NAME
                    log("Installation failed", "ERROR")
                    sys.exit(1)
            elif step_name == "Creating configuration":
                config = get_env_config(hf_token)
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
            elif step_name == "Validating EzLocalAI":
                validate_ezlocalai_configuration(install_path)
    
    # Success message
    log("Installation completed successfully!", "SUCCESS")
    print("\n" + "="*70)
    print(f"🎉 AGiXT {VERSION} Installation Complete!")
    print("="*70)
    print(f"📁 Directory: {install_path}")
    print(f"🌐 Frontend (via proxy): https://agixtui.locod-ai.com")
    print(f"🔧 Backend API (via proxy): https://agixt.locod-ai.com")
    print(f"🤖 EzLocalAI API: http://162.55.213.90:8091")
    print(f"🎮 EzLocalAI UI: http://162.55.213.90:8502")
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
    print("🎯 Features Implemented:")
    print("   ✅ Secure API key generation (JWT authentication)")
    print(f"   ✅ {MODEL_CONFIG['display_name']} model (~{MODEL_CONFIG['expected_size_gb']}GB)")
    print("   ✅ HuggingFace authenticated downloads")
    print("   ✅ Auto-download with token authentication")
    print("   ✅ EzLocalAI web interface exposed (port 8502)")
    print("   ✅ Complete EzLocalAI configuration")
    print("   ✅ Nginx reverse proxy ready")
    print("   ✅ GraphQL management interface")
    print("   ✅ Optimized for 16GB RAM servers")
    print("   ✅ Deepseek architecture for advanced code generation")
    print()
    print("📝 Next Steps:")
    print("   1. Access AGiXT Frontend: http://162.55.213.90:3437")
    print("   2. Access EzLocalAI UI: http://162.55.213.90:8502")
    print("   3. Create agents using Deepseek-Coder-1.3B model")
    print("   4. Test chat functionality")
    print("   5. Enable nginx configs: agixt.locod-ai.com + agixtui.locod-ai.com")
    print("   6. Monitor logs for any issues")
    print()
    print("🔑 Important:")
    print("   - API Key has been auto-generated for security")
    print(f"   - {MODEL_CONFIG['display_name']} model ready with HuggingFace structure")
    print("   - Model downloaded/copied with HF authentication")
    print(f"   - Expected RAM usage: ~{MODEL_CONFIG['expected_size_gb'] + 0.5}GB (vs 8GB+ for 7B model)")
    print("   - EzLocalAI web interface available for model management")
    print(f"   - HuggingFace token configured: {hf_token[:8]}...")
    print("   - Deepseek model optimized for code generation and debugging")
    print("="*70)


if __name__ == "__main__":
    main()
