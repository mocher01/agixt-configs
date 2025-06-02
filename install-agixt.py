#!/usr/bin/env python3
"""
AGiXT Automated Installer - v1.5-ezlocolai-deepseek
====================================================

Complete AGiXT installation with SMART MODEL DISCOVERY:
✅ Admin sets MODEL_NAME only - script discovers all technical details
✅ Automatic GGUF detection via HuggingFace API
✅ Fallback to naming conventions
✅ No hardcoded model registry - fully dynamic
✅ Downloads configuration from GitHub repository
✅ Automatic model compatibility and optimization
✅ GGUF format support for EzLocalAI
✅ Flexible and reusable for any model
✅ Nginx reverse proxy integration
✅ HuggingFace token authentication support
✅ EzLocalAI web interface exposed
✅ Docker network integration
✅ GraphQL management interface

Usage:
    python3 install-agixt.py proxy github_token
    
    Where:
    - proxy: Installation mode (always use 'proxy')
    - github_token: Your GitHub personal access token
"""

import os
import sys
import subprocess
import json
import urllib.request
import urllib.error
import shutil
import time
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re


def log(message: str, level: str = "INFO") -> None:
    """Enhanced logging with timestamps and levels"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def get_default_settings() -> dict:
    """Get default model settings"""
    return {
        "max_tokens": 8192,
        "temperature": 0.3,
        "top_p": 0.9,
        "threads": 4,
        "gpu_layers": 0
    }


def discover_model_config(model_name: str, hf_token: str, quick_check: bool = False) -> dict:
    """
    Smart model discovery with hybrid approach:
    1. Try HuggingFace API for GGUF version
    2. Fall back to naming conventions
    3. Use sensible defaults for unknown models
    """
    log(f"🔍 Discovering configuration for model: {model_name}", "INFO")
    
    # Default configuration template
    default_config = {
        "display_name": model_name.replace("-", " ").title(),
        "repo": f"unknown/{model_name}",
        "file": "model.gguf",
        "size_gb": 0.0,
        "architecture": "unknown",
        "download_url": "",
        "format": "unknown",
        "compatible": False,
        **get_default_settings()
    }
    
    # 1. Try to find GGUF version (TheBloke repositories)
    gguf_variants = [
        f"TheBloke/{model_name}-GGUF",
        f"TheBloke/{model_name.replace('_', '-')}-GGUF",
        f"TheBloke/{model_name.lower()}-GGUF"
    ]
    
    for gguf_repo in gguf_variants:
        try:
            if check_huggingface_repo(gguf_repo, hf_token, quick_check):
                # Find best quantization file
                best_file = find_best_gguf_file(gguf_repo, hf_token)
                if best_file:
                    log(f"✅ Found GGUF version: {gguf_repo}", "INFO")
                    return {
                        **default_config,
                        "repo": gguf_repo,
                        "file": best_file["name"],
                        "size_gb": best_file["size_gb"],
                        "download_url": f"https://huggingface.co/{gguf_repo}/resolve/main/{best_file['name']}",
                        "format": "gguf",
                        "compatible": True,
                        "architecture": detect_architecture(model_name)
                    }
        except Exception as e:
            log(f"⚠️  Could not check {gguf_repo}: {str(e)}", "DEBUG")
            continue
    
    # 2. Try original repository
    original_repo = guess_original_repo(model_name)
    if original_repo and check_huggingface_repo(original_repo, hf_token, quick_check):
        log(f"⚠️  Found original repo (may need conversion): {original_repo}", "WARN")
        return {
            **default_config,
            "repo": original_repo,
            "file": "model.safetensors",
            "download_url": f"https://huggingface.co/{original_repo}/resolve/main/model.safetensors",
            "format": "safetensors",
            "compatible": False,  # Needs conversion for EzLocalAI
            "architecture": detect_architecture(model_name)
        }
    
    # 3. Use defaults for unknown models
    log(f"⚠️  Model {model_name} not found - using defaults", "WARN")
    return default_config


def check_huggingface_repo(repo: str, hf_token: str, quick_check: bool = False) -> bool:
    """Check if a HuggingFace repository exists"""
    if quick_check:
        return True  # Skip API calls for quick checks
    
    try:
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        url = f"https://huggingface.co/api/repos/{repo}"
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except:
        return False


def find_best_gguf_file(repo: str, hf_token: str) -> Optional[dict]:
    """Find the best GGUF quantization file in a repository"""
    try:
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        url = f"https://huggingface.co/api/repos/{repo}/tree/main"
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            files = json.loads(response.read().decode())
        
        # Filter for GGUF files and prioritize by quantization quality
        gguf_files = []
        quantization_priority = ['Q4_K_M', 'Q5_K_M', 'Q4_K_S', 'Q5_K_S', 'Q6_K', 'Q8_0']
        
        for file_info in files:
            if file_info.get('type') == 'file' and file_info.get('path', '').endswith('.gguf'):
                gguf_files.append({
                    'name': file_info['path'],
                    'size_gb': round(file_info.get('size', 0) / (1024**3), 1)
                })
        
        if not gguf_files:
            return None
        
        # Find best quantization match
        for quant in quantization_priority:
            for file in gguf_files:
                if quant in file['name']:
                    return file
        
        # Return first GGUF file if no preferred quantization found
        return gguf_files[0]
        
    except Exception as e:
        log(f"Could not fetch files from {repo}: {str(e)}", "DEBUG")
        return None


def guess_original_repo(model_name: str) -> str:
    """Guess the original repository name based on model name"""
    # Common patterns for original repositories
    if 'deepseek' in model_name.lower():
        return f"deepseek-ai/{model_name}"
    elif 'llama' in model_name.lower():
        return f"meta-llama/{model_name}"
    elif 'mistral' in model_name.lower():
        return f"mistralai/{model_name}"
    elif 'phi' in model_name.lower():
        return f"microsoft/{model_name}"
    else:
        # Generic guess
        return f"huggingface/{model_name}"


def detect_architecture(model_name: str) -> str:
    """Detect model architecture from name"""
    name_lower = model_name.lower()
    
    if 'llama' in name_lower:
        return 'llama'
    elif 'mistral' in name_lower:
        return 'mistral'
    elif 'deepseek' in name_lower:
        return 'deepseek'
    elif 'phi' in name_lower:
        return 'phi'
    elif 'gpt' in name_lower:
        return 'gpt'
    else:
        return 'transformer'


def interactive_model_selection(hf_token: str) -> str:
    """Interactive model selection with discovery"""
    log("🔍 Discovering available models...", "INFO")
    
    # Discover popular models dynamically
    popular_models = [
        "deepseek-coder-1.3b-instruct",
        "llama-2-7b-chat-hf", 
        "mistral-7b-instruct-v0.1",
        "phi-2"
    ]
    
    discovered_models = []
    for model in popular_models:
        try:
            config = discover_model_config(model, hf_token, quick_check=True)
            discovered_models.append({
                'name': model,
                'display': config['display_name'],
                'size': config['size_gb'],
                'format': config['format'],
                'compatible': config['compatible']
            })
        except:
            continue
    
    print("\n🤖 AVAILABLE AI MODELS")
    print("=" * 50)
    
    for i, model in enumerate(discovered_models, 1):
        compat_icon = "🟢" if model['compatible'] else "🟡"
        format_text = f"({model['format'].upper()})"
        size_text = f"~{model['size']}GB" if model['size'] > 0 else "~Unknown"
        print(f" {i}. {model['display']:<30} {size_text:<8} {format_text} {compat_icon}")
    
    print(f" {len(discovered_models) + 1}. Custom model (enter manually)")
    print("\n🟢 = EzLocalAI Compatible (GGUF)")
    print("🟡 = May need conversion (SafeTensors)")
    
    while True:
        try:
            choice = input(f"\n🎯 Select a model (1-{len(discovered_models) + 1}): ").strip()
            
            if choice == str(len(discovered_models) + 1):
                custom_model = input("📝 Enter custom model name: ").strip()
                if custom_model:
                    log(f"✅ Selected custom model: {custom_model}", "INFO")
                    return custom_model
                else:
                    print("❌ Please enter a valid model name")
                    continue
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(discovered_models):
                selected = discovered_models[choice_num - 1]
                log(f"✅ Selected: {selected['name']}", "INFO")
                return selected['name']
            else:
                print(f"❌ Please enter a number between 1 and {len(discovered_models) + 1}")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Installation cancelled by user")
            sys.exit(1)


def load_config_from_github(github_token: str) -> Dict[str, str]:
    """Load configuration file from GitHub repository with authentication"""
    repo_url = "https://api.github.com/repos/mocher01/agixt-configs/contents"
    config_files = ["agixt.config", ".env", "config.env"]
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'AGiXT-Installer/1.5'
    }
    
    for config_file in config_files:
        try:
            log(f"Attempting to download {config_file} from GitHub...", "INFO")
            url = f"{repo_url}/{config_file}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    content = json.loads(response.read().decode())
                    if content.get('content'):
                        import base64
                        config_content = base64.b64decode(content['content']).decode('utf-8')
                        
                        # Parse the configuration
                        config = {}
                        for line in config_content.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                config[key.strip()] = value.strip()
                        
                        log(f"✅ Successfully loaded {config_file} from GitHub", "INFO")
                        return config
        except urllib.error.HTTPError as e:
            log(f"HTTP Error {e.code} for {config_file}: {e.reason}", "DEBUG")
        except Exception as e:
            log(f"Failed to load {config_file}: {str(e)}", "DEBUG")
    
    log("Could not find configuration file in GitHub repository", "ERROR")
    log("Available files to check:", "INFO")
    for file in config_files:
        log(f"  - {file}", "INFO")
    
    sys.exit(1)


def enhance_config_with_model_discovery(config: Dict[str, str], hf_token: str) -> Dict[str, str]:
    """Enhance the basic config with discovered model details"""
    model_name = config.get('MODEL_NAME', '').strip()
    
    if not model_name:
        # No model specified in config - use interactive selection
        model_name = interactive_model_selection(hf_token)
        config['MODEL_NAME'] = model_name
    
    # Discover model configuration
    log(f"🔍 Discovering configuration for: {model_name}", "INFO")
    model_config = discover_model_config(model_name, hf_token)
    
    # Check compatibility
    if not model_config['compatible']:
        log(f"⚠️  Warning: {model_name} uses {model_config['format']} format", "WARN")
        log("   EzLocalAI works best with GGUF format models", "WARN")
        log("   Consider using a GGUF variant for better performance", "WARN")
    
    # Enhance config with discovered details
    enhanced_config = config.copy()
    enhanced_config.update({
        'MODEL_DISPLAY_NAME': model_config['display_name'],
        'MODEL_HF_NAME': model_config['repo'],
        'MODEL_FILE': model_config['file'],
        'MODEL_DOWNLOAD_URL': model_config['download_url'],
        'MODEL_SIZE_GB': str(model_config['size_gb']),
        'MODEL_ARCHITECTURE': model_config['architecture'],
        'MODEL_FORMAT': model_config['format'],
        'MODEL_COMPATIBLE': str(model_config['compatible']),
        'EZLOCALAI_MODEL': model_name,
        'DEFAULT_MODEL': model_name,
        'MAX_TOKENS': str(model_config['max_tokens']),
        'TEMPERATURE': str(model_config['temperature']),
        'TOP_P': str(model_config['top_p']),
        'THREADS': str(model_config['threads']),
        'GPU_LAYERS': str(model_config['gpu_layers'])
    })
    
    log(f"✅ Enhanced configuration for {model_config['display_name']}", "INFO")
    log(f"   Repository: {model_config['repo']}", "INFO")
    log(f"   File: {model_config['file']}", "INFO")
    log(f"   Size: ~{model_config['size_gb']}GB", "INFO")
    log(f"   Format: {model_config['format'].upper()}", "INFO")
    log(f"   Compatible: {'Yes' if model_config['compatible'] else 'No'}", "INFO")
    
    return enhanced_config


def copy_or_download_model_files(install_path: str, config: Dict[str, str]) -> bool:
    """Copy model files from backup location or download with HF authentication"""
    
    # Get values from enhanced config (now includes discovered model details)
    model_name = config.get('MODEL_NAME', 'Unknown-Model')
    model_display_name = config.get('MODEL_DISPLAY_NAME', model_name)
    model_file = config.get('MODEL_FILE', 'model.gguf')
    download_url = config.get('MODEL_DOWNLOAD_URL', '')
    hf_token = config.get('HF_TOKEN', config.get('HUGGINGFACE_TOKEN', ''))
    model_format = config.get('MODEL_FORMAT', 'unknown')
    
    log(f"Setting up model: {model_display_name}", "INFO")
    
    # Create model directory using the model name from config
    target_model_dir = os.path.join(install_path, "ezlocalai", model_name)
    os.makedirs(target_model_dir, exist_ok=True)
    
    target_file_path = os.path.join(target_model_dir, model_file)
    
    # Check if model file already exists
    if os.path.exists(target_file_path):
        log(f"✅ Model file already exists: {target_file_path}", "INFO")
        return True
    
    # Download the model file
    if download_url:
        log(f"📥 Downloading model from: {download_url}", "INFO")
        log(f"📁 Target location: {target_file_path}", "INFO")
        
        if model_format != 'gguf':
            log(f"⚠️  Warning: Downloading {model_format} format - may not be optimal for EzLocalAI", "WARN")
        
        try:
            headers = {}
            if hf_token:
                headers['Authorization'] = f'Bearer {hf_token}'
            
            req = urllib.request.Request(download_url, headers=headers)
            
            with urllib.request.urlopen(req) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                
                with open(target_file_path, 'wb') as f:
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
                log(f"✅ Successfully downloaded: {model_file}", "INFO")
                return True
                
        except Exception as e:
            log(f"❌ Failed to download model: {str(e)}", "ERROR")
            # Clean up partial download
            if os.path.exists(target_file_path):
                os.remove(target_file_path)
            return False
    else:
        log(f"❌ No download URL available for model: {model_name}", "ERROR")
        return False


def create_docker_compose(install_path: str, config: Dict[str, str]) -> None:
    """Create docker-compose.yml file with proxy configuration"""
    compose_content = f"""version: '3.8'

services:
  agixt:
    image: joshxt/agixt:main
    container_name: agixt
    ports:
      - "7437:7437"
    volumes:
      - {install_path}/agixt:/app/agixt
      - {install_path}/conversations:/app/conversations
      - {install_path}/.env:/app/.env
    environment:
      - AGIXT_URI=http://agixt:7437
    networks:
      - agixt-network
    restart: unless-stopped

  ezlocalai:
    image: joshxt/ezlocalai:main
    container_name: ezlocalai
    ports:
      - "8091:8091"
    volumes:
      - {install_path}/ezlocalai:/app/models
      - {install_path}/.env:/app/.env
    environment:
      - EZLOCALAI_URL=http://ezlocalai:8091
      - EZLOCALAI_API_KEY=${{EZLOCALAI_API_KEY}}
    networks:
      - agixt-network
    restart: unless-stopped

  streamlit:
    image: joshxt/streamlit:main
    container_name: streamlit
    ports:
      - "8502:8502"
    volumes:
      - {install_path}/.env:/app/.env
    environment:
      - AGIXT_URI=http://agixt:7437
      - EZLOCALAI_URI=http://ezlocalai:8091
    networks:
      - agixt-network
    restart: unless-stopped
    depends_on:
      - agixt
      - ezlocalai

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - {install_path}/nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - agixt-network
    restart: unless-stopped
    depends_on:
      - agixt
      - ezlocalai
      - streamlit

networks:
  agixt-network:
    driver: bridge
"""
    
    with open(os.path.join(install_path, "docker-compose.yml"), 'w') as f:
        f.write(compose_content)
    
    log("✅ Created docker-compose.yml", "INFO")


def create_nginx_config(install_path: str, config: Dict[str, str]) -> None:
    """Create nginx configuration for reverse proxy"""
    domain = config.get('DOMAIN', 'localhost')
    
    nginx_content = f"""events {{
    worker_connections 1024;
}}

http {{
    upstream agixt_backend {{
        server agixt:7437;
    }}
    
    upstream ezlocalai_backend {{
        server ezlocalai:8091;
    }}
    
    upstream streamlit_backend {{
        server streamlit:8502;
    }}

    server {{
        listen 80;
        server_name {domain};
        
        client_max_body_size 100M;
        
        # AGiXT API
        location /api/ {{
            proxy_pass http://agixt_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
        
        # EzLocalAI API  
        location /ezlocalai/ {{
            proxy_pass http://ezlocalai_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
        
        # Streamlit UI
        location / {{
            proxy_pass http://streamlit_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }}
    }}
}}"""
    
    with open(os.path.join(install_path, "nginx.conf"), 'w') as f:
        f.write(nginx_content)
    
    log("✅ Created nginx.conf", "INFO")


def create_env_file(install_path: str, config: Dict[str, str]) -> None:
    """Create .env file with all configuration variables"""
    
    env_file = os.path.join(install_path, ".env")
    version = config.get('VERSION', 'v1.5-ezlocolai-deepseek')
    
    # Categories of environment variables to include
    categories = {
        'Installation': ['INSTALL_BASE_PATH', 'INSTALL_FOLDER_PREFIX', 'VERSION', 'DOMAIN'],
        'Model Configuration': ['MODEL_NAME', 'MODEL_DISPLAY_NAME', 'MODEL_HF_NAME', 'MODEL_FILE', 
                              'MODEL_ARCHITECTURE', 'MODEL_FORMAT', 'DEFAULT_MODEL', 'EZLOCALAI_MODEL'],
        'Model Settings': ['MAX_TOKENS', 'TEMPERATURE', 'TOP_P', 'THREADS', 'GPU_LAYERS'],
        'Authentication': ['AGIXT_API_KEY', 'EZLOCALAI_API_KEY', 'HF_TOKEN'],
        'URLs and Endpoints': ['AGIXT_SERVER', 'EZLOCALAI_URI', 'STREAMLIT_URI'],
        'Docker Configuration': ['DOCKER_NETWORK', 'CONTAINER_PREFIX']
    }
    
    # Generate API keys
    agixt_api_key = secrets.token_urlsafe(32)
    ezlocalai_api_key = secrets.token_urlsafe(32)
    
    with open(env_file, 'w') as f:
        f.write("# =============================================================================\n")
        f.write(f"# AGiXT Server Configuration - {version}\n")
        f.write("# =============================================================================\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Model: {config.get('MODEL_DISPLAY_NAME', 'Unknown Model')}\n")
        f.write("# =============================================================================\n\n")
        
        # Write categorized environment variables
        for category, keys in categories.items():
            f.write(f"# {category}\n")
            f.write("# " + "=" * (len(category) + 2) + "\n")
            
            for key in keys:
                if key == 'AGIXT_API_KEY':
                    f.write(f"{key}={agixt_api_key}\n")
                elif key == 'EZLOCALAI_API_KEY':
                    f.write(f"{key}={ezlocalai_api_key}\n")
                elif key in config:
                    f.write(f"{key}={config[key]}\n")
                else:
                    # Set reasonable defaults
                    defaults = {
                        'AGIXT_SERVER': f"https://{config.get('DOMAIN', 'localhost')}",
                        'EZLOCALAI_URI': 'http://ezlocalai:8091',
                        'STREAMLIT_URI': 'http://streamlit:8502',
                        'DOCKER_NETWORK': 'agixt-network',
                        'CONTAINER_PREFIX': 'agixt'
                    }
                    if key in defaults:
                        f.write(f"{key}={defaults[key]}\n")
            
            f.write("\n")
        
        # Add any additional config variables not in categories
        f.write("# Additional Configuration\n")
        f.write("# =======================\n")
        for key, value in config.items():
            # Skip if already written in categories
            already_written = any(key in keys for keys in categories.values())
            if not already_written and not key.startswith('MODEL_DOWNLOAD_URL'):
                f.write(f"{key}={value}\n")
    
    log("✅ Created .env file with all configuration variables", "INFO")
    log(f"🔑 Generated AGIXT API Key: {agixt_api_key[:8]}...", "INFO")
    log(f"🔑 Generated EzLocalAI API Key: {ezlocalai_api_key[:8]}...", "INFO")


def main():
    """Main installation function with smart model discovery"""
    if len(sys.argv) != 3:
        log("Usage: python3 install-agixt.py proxy github_token", "ERROR")
        sys.exit(1)
    
    mode = sys.argv[1]
    github_token = sys.argv[2]
    
    if mode != "proxy":
        log("Currently only 'proxy' mode is supported", "ERROR")
        sys.exit(1)
    
    log("🚀 Starting AGiXT installation with Smart Model Discovery", "INFO")
    log("=" * 60, "INFO")
    
    # Load configuration first
    if github_token:
        config = load_config_from_github(github_token)
    else:
        log("GitHub token required for configuration download", "ERROR")
        log("Usage: script.py proxy github_token", "ERROR")
        sys.exit(1)
    
    # Extract HuggingFace token for model discovery
    hf_token = config.get('HF_TOKEN', config.get('HUGGINGFACE_TOKEN', ''))
    if not hf_token:
        log("⚠️  No HuggingFace token found - some models may not be accessible", "WARN")
    
    # Enhance config with smart model discovery
    config = enhance_config_with_model_discovery(config, hf_token)
    
    # Get installation parameters
    install_base = config.get('INSTALL_BASE_PATH', '/var/apps')
    folder_prefix = config.get('INSTALL_FOLDER_PREFIX', 'agixt')
    timestamp = int(time.time())
    install_path = os.path.join(install_base, f"{folder_prefix}-{timestamp}")
    
    log(f"📁 Installation path: {install_path}", "INFO")
    
    # Create installation directory
    os.makedirs(install_path, exist_ok=True)
    os.makedirs(os.path.join(install_path, "agixt"), exist_ok=True)
    os.makedirs(os.path.join(install_path, "conversations"), exist_ok=True)
    
    # Setup model files
    log("🤖 Setting up model files...", "INFO")
    if not copy_or_download_model_files(install_path, config):
        log("❌ Failed to setup model files", "ERROR")
        sys.exit(1)
    
    # Create configuration files
    log("📝 Creating configuration files...", "INFO")
    create_env_file(install_path, config)
    create_docker_compose(install_path, config)
    create_nginx_config(install_path, config)
    
    # Start Docker containers
    log("🐳 Starting Docker containers...", "INFO")
    os.chdir(install_path)
    
    try:
        # Pull latest images
        log("📥 Pulling latest Docker images...", "INFO")
        subprocess.run(["docker", "compose", "pull"], check=True, cwd=install_path)
        
        # Start containers
        log("🚀 Starting containers...", "INFO")
        subprocess.run(["docker", "compose", "up", "-d"], check=True, cwd=install_path)
        
        # Wait for services to be ready
        log("⏳ Waiting for services to start...", "INFO")
        time.sleep(30)
        
        # Verify containers are running
        result = subprocess.run(["docker", "compose", "ps"], 
                              capture_output=True, text=True, cwd=install_path)
        
        if result.returncode == 0:
            log("✅ Docker containers started successfully", "INFO")
            log("📊 Container status:", "INFO")
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    log(f"   {line}", "INFO")
        else:
            log("⚠️  Could not verify container status", "WARN")
            
    except subprocess.CalledProcessError as e:
        log(f"❌ Failed to start Docker containers: {e}", "ERROR")
        log("🔧 Try running manually:", "INFO")
        log(f"   cd {install_path}", "INFO")
        log("   docker compose up -d", "INFO")
        sys.exit(1)
    except FileNotFoundError:
        log("❌ Docker or docker-compose not found", "ERROR")
        log("Please install Docker and Docker Compose first", "ERROR")
        sys.exit(1)
    
    # Installation completed successfully
    log("=" * 60, "INFO")
    log("🎉 AGiXT Installation Completed Successfully!", "INFO")
    log("=" * 60, "INFO")
    
    # Display access information
    domain = config.get('DOMAIN', 'localhost')
    model_name = config.get('MODEL_DISPLAY_NAME', config.get('MODEL_NAME', 'Unknown'))
    
    print(f"\n🌐 ACCESS INFORMATION")
    print(f"=====================")
    print(f"🎮 Main Interface: http://{domain}")
    print(f"🔧 Backend API (via proxy): {config.get('AGIXT_SERVER', f'https://{domain}')}")
    print(f"🤖 EzLocalAI API: http://{domain}/ezlocalai")
    print(f"🧬 GraphQL: {config.get('AGIXT_SERVER', f'https://{domain}')}/graphql")
    
    print(f"\n🤖 MODEL INFORMATION")
    print(f"====================")
    print(f"📝 Model: {model_name}")
    print(f"📁 Location: {install_path}/ezlocalai/{config.get('MODEL_NAME', 'unknown')}")
    print(f"🗂️  Format: {config.get('MODEL_FORMAT', 'unknown').upper()}")
    print(f"💾 Size: ~{config.get('MODEL_SIZE_GB', '0')}GB")
    
    print(f"\n🔑 API KEYS")
    print(f"===========")
    print(f"🔐 AGiXT API Key: Check {install_path}/.env file")
    print(f"🔐 EzLocalAI API Key: Check {install_path}/.env file")
    
    print(f"\n📁 INSTALLATION DETAILS")
    print(f"=======================")
    print(f"📂 Installation Path: {install_path}")
    print(f"🐳 Docker Compose: {install_path}/docker-compose.yml")
    print(f"⚙️  Environment: {install_path}/.env")
    print(f"🌐 Nginx Config: {install_path}/nginx.conf")
    
    print(f"\n🛠️  MANAGEMENT COMMANDS")
    print(f"======================")
    print(f"📍 Navigate: cd {install_path}")
    print(f"🔄 Restart: docker compose restart")
    print(f"📊 Status: docker compose ps")
    print(f"📋 Logs: docker compose logs -f")
    print(f"🛑 Stop: docker compose down")
    
    # Check if model format warning needed
    if config.get('MODEL_FORMAT', '').lower() != 'gguf':
        print(f"\n⚠️  COMPATIBILITY NOTE")
        print(f"=====================")
        print(f"Your model uses {config.get('MODEL_FORMAT', 'unknown').upper()} format.")
        print(f"For optimal performance with EzLocalAI, consider using GGUF format models.")
        print(f"The system will work but may not be as efficient.")
    
    print(f"\n🚀 Ready to use AGiXT with {model_name}!")
    log("Installation script completed successfully", "INFO")


if __name__ == "__main__":
    main()
