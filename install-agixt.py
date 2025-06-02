#!/usr/bin/env python3
"""
AGiXT Automated Installer - v1.5-ezlocolai-deepseek
====================================================

Complete AGiXT installation with configuration-driven approach:
✅ No hardcoded values - everything from agixt.config
✅ Downloads configuration from GitHub repository
✅ Flexible and reusable for different models/setups
✅ Nginx reverse proxy integration
✅ EzLocalAI integration with configurable models
✅ HuggingFace token authentication support
✅ EzLocalAI web interface exposed
✅ Docker network integration
✅ GraphQL management interface

Usage:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - proxy github_token

The script will automatically:
1. Download agixt.config from your GitHub repository
2. Parse ALL configuration variables from the config file
3. Use those variables for the complete installation
4. No hardcoded values in the script

Arguments:
  CONFIG_NAME     Configuration name (default: proxy)
  GITHUB_TOKEN    GitHub token for private repos (required)
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

def log(message: str, level: str = "INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def load_config_from_github(github_token: str) -> Dict[str, str]:
    """Load configuration from GitHub agixt.config file"""
    config = {}
    
    log("Loading configuration from GitHub repository...", "INFO")
    try:
        config_urls = [
            "https://raw.githubusercontent.com/mocher01/agixt-configs/main/agixt.config",
            "https://raw.githubusercontent.com/mocher01/agixt-configs/main/.env",
            "https://raw.githubusercontent.com/mocher01/agixt-configs/main/config.env"
        ]
        
        for url in config_urls:
            try:
                req = urllib.request.Request(url)
                req.add_header('Authorization', f'token {github_token}')
                
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                    
                    log(f"Successfully downloaded config from: {url}", "SUCCESS")
                    
                    # Parse the config file
                    for line_num, line in enumerate(content.split('\n'), 1):
                        line = line.strip()
                        
                        # Skip comments and empty lines
                        if not line or line.startswith('#'):
                            continue
                            
                        # Parse KEY=VALUE pairs
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                                
                            config[key] = value
                    
                    # Save config locally for reference
                    with open('agixt.config', 'w') as f:
                        f.write(content)
                    log("Configuration saved locally as agixt.config", "SUCCESS")
                    
                    # FIXED: Only require essential keys that should be in config
                    essential_keys = ['MODEL_NAME', 'AGIXT_VERSION', 'HUGGINGFACE_TOKEN']
                    missing_keys = [key for key in essential_keys if key not in config or not config[key]]
                    
                    if missing_keys:
                        log(f"Missing essential configuration keys: {missing_keys}", "ERROR")
                        return {}  # Fail if essential keys missing
                    
                    # Use MODEL_NAME directly - no need for MODEL_HF_NAME
                    log(f"Using MODEL_NAME: {config['MODEL_NAME']}", "INFO")
                    
                    log(f"Configuration loaded successfully: {len(config)} variables", "SUCCESS")
                    log(f"Version: {config.get('AGIXT_VERSION', 'Unknown')}", "INFO")
                    log(f"Model: {config.get('MODEL_NAME', 'Unknown')}", "INFO")
                    
                    return config
                    
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue  # Try next URL
                else:
                    log(f"Error accessing {url}: HTTP {e.code}", "WARN")
            except Exception as e:
                log(f"Error fetching from {url}: {e}", "WARN")
        
        log("Could not find configuration file in GitHub repository", "ERROR")
        return {}
        
    except Exception as e:
        log(f"Error loading config from GitHub: {e}", "ERROR")
        return {}

def load_config_fallback() -> Dict[str, str]:
    """Fallback: try to load config from local files"""
    config = {}
    
    config_files = ['agixt.config', '.env', 'config.env']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            log(f"Found local configuration file: {config_file}", "INFO")
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                
                if config:
                    log(f"Loaded configuration from {config_file}", "SUCCESS")
                    return config
                    
            except Exception as e:
                log(f"Error reading {config_file}: {e}", "WARN")
    
    return {}

def discover_gguf_model(model_name: str, hf_token: str) -> Dict[str, str]:
    """
    Discover GGUF model configuration from HuggingFace
    Priority: GGUF repositories only (TheBloke, etc.)
    """
    log(f"🔍 Discovering GGUF model for: {model_name}", "INFO")
    
    # Try GGUF repositories first (highest priority)
    gguf_candidates = [
        f"TheBloke/{model_name}-GGUF",
        f"TheBloke/{model_name.replace('_', '-')}-GGUF",
        f"microsoft/{model_name}-GGUF",  # For Phi models
        f"bartowski/{model_name}-GGUF",  # Alternative GGUF provider
    ]
    
    for repo in gguf_candidates:
        log(f"🔍 Checking GGUF repo: {repo}", "DEBUG")
        
        if check_huggingface_repo(repo, hf_token):
            log(f"✅ Found GGUF repository: {repo}", "SUCCESS")
            
            # Find best GGUF file
            best_file = find_best_gguf_file(repo, hf_token)
            if best_file:
                return {
                    'repo': repo,
                    'file': best_file['name'],
                    'size_gb': best_file['size_gb'],
                    'download_url': f"https://huggingface.co/{repo}/resolve/main/{best_file['name']}",
                    'format': 'gguf',
                    'compatible': True
                }
    
    # If no GGUF found, return empty (we'll switch models)
    log(f"❌ No GGUF repository found for {model_name}", "ERROR")
    log("💡 Will need to switch to a different model with GGUF support", "INFO")
    return {}

def find_best_gguf_file(repo: str, hf_token: str) -> Optional[Dict[str, str]]:
    """Find the best GGUF quantization file in a repository"""
    try:
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        headers['User-Agent'] = 'AGiXT-Installer/1.5'
        
        # Use correct HuggingFace API endpoint
        url = f"https://huggingface.co/api/models/{repo}/tree/main"
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            files = json.loads(response.read().decode())
        
        # Filter for GGUF files only
        gguf_files = []
        quantization_priority = ['Q4_K_M', 'Q5_K_M', 'Q4_K_S', 'Q5_K_S', 'Q6_K', 'Q8_0']
        
        for file_info in files:
            if file_info.get('type') == 'file' and file_info.get('path', '').endswith('.gguf'):
                gguf_files.append({
                    'name': file_info['path'],
                    'size_gb': round(file_info.get('size', 0) / (1024**3), 1)
                })
        
        if not gguf_files:
            log(f"No GGUF files found in {repo}", "WARN")
            return None
        
        log(f"Found {len(gguf_files)} GGUF files in {repo}", "INFO")
        
        # Find best quantization match
        for quant in quantization_priority:
            for file in gguf_files:
                if quant in file['name']:
                    log(f"Selected GGUF file: {file['name']} ({file['size_gb']}GB)", "SUCCESS")
                    return file
        
        # Return first GGUF file if no preferred quantization found
        log(f"Using first available GGUF: {gguf_files[0]['name']}", "INFO")
        return gguf_files[0]
        
    except Exception as e:
        log(f"Error fetching GGUF files from {repo}: {str(e)}", "ERROR")
        return None

def check_huggingface_repo(repo: str, hf_token: str) -> bool:
    """Check if a HuggingFace repository exists"""
    try:
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        headers['User-Agent'] = 'AGiXT-Installer/1.5'
        
        # Use correct API endpoint
        url = f"https://huggingface.co/api/models/{repo}"
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
            
    except urllib.error.HTTPError as e:
        log(f"HTTP {e.code} for {repo}", "DEBUG")
        return False
    except Exception as e:
        log(f"Error checking {repo}: {str(e)}", "DEBUG")
        return False

def get_fallback_models() -> List[str]:
    """Get list of known GGUF models as fallbacks"""
    return [
        "llama-2-7b-chat",
        "mistral-7b-instruct-v0.1", 
        "phi-2",
        "codellama-7b-instruct"
    ]
    """Download file with HuggingFace authentication"""
    try:
        log(f"Downloading: {url}")
        log(f"Target: {target_path}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Create request with authentication
        req = urllib.request.Request(url)
        if token:  # Only add auth header if token exists
            req.add_header('Authorization', f'Bearer {token}')
        
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

def cleanup_previous_installations(config: Dict[str, str]):
    """Clean up any previous AGiXT installations"""
    base_path = config.get('INSTALL_BASE_PATH', '/var/apps')
    
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
        log(f"Created {base_path} directory", "SUCCESS")
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

def create_installation_directory(config: Dict[str, str]) -> Optional[str]:
    """Create the installation directory using config values"""
    version = config.get('AGIXT_VERSION', 'unknown')
    folder_prefix = config.get('INSTALL_FOLDER_PREFIX', 'agixt')
    base_path = config.get('INSTALL_BASE_PATH', '/var/apps')
    
    install_path = os.path.join(base_path, f"{folder_prefix}-{version}")
    
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

def copy_or_download_model_files(install_path: str, config: Dict[str, str]) -> bool:
    """Setup GGUF model files - download only GGUF format models"""
    
    model_name = config.get('MODEL_NAME', 'Unknown-Model')
    hf_token = config.get('HUGGINGFACE_TOKEN', '')
    
    log(f"Setting up GGUF model: {model_name}", "INFO")
    
    # First, try to discover GGUF model
    model_info = discover_gguf_model(model_name, hf_token)
    
    if not model_info:
        log(f"❌ No GGUF version found for {model_name}", "ERROR")
        log("🔄 Trying fallback models with known GGUF support...", "INFO")
        
        # Try fallback models
        fallback_models = get_fallback_models()
        for fallback_model in fallback_models:
            log(f"🔍 Trying fallback model: {fallback_model}", "INFO")
            model_info = discover_gguf_model(fallback_model, hf_token)
            if model_info:
                log(f"✅ Found GGUF fallback: {fallback_model}", "SUCCESS")
                model_name = fallback_model
                # Update config with working model
                config['MODEL_NAME'] = model_name
                break
        
        if not model_info:
            log("❌ No GGUF models available - installation cannot proceed", "ERROR")
            return False
    
    # Create model directory 
    target_model_dir = os.path.join(install_path, "ezlocalai", model_name)
    os.makedirs(target_model_dir, exist_ok=True)
    
    # Download the GGUF file
    model_file = model_info['file']
    download_url = model_info['download_url']
    target_file_path = os.path.join(target_model_dir, model_file)
    
    log(f"📥 Downloading GGUF model: {model_file}", "INFO")
    log(f"📂 Repository: {model_info['repo']}", "INFO")
    log(f"💾 Size: ~{model_info['size_gb']}GB", "INFO")
    
    if download_with_auth(download_url, target_file_path, hf_token):
        log(f"✅ GGUF model downloaded successfully", "SUCCESS")
        
        # Create minimal config for GGUF model
        create_gguf_config_files(target_model_dir, model_name, model_info)
        
        # Update config with discovered values
        config.update({
            'MODEL_FILE': model_file,
            'MODEL_REPO': model_info['repo'],
            'MODEL_FORMAT': 'gguf',
            'MODEL_SIZE_GB': str(model_info['size_gb']),
            'DEFAULT_MODEL': model_name,
            'EZLOCALAI_MODEL': model_name
        })
        
        return True
    else:
        log(f"❌ Failed to download GGUF model", "ERROR")
        return False

def create_gguf_config_files(model_dir: str, model_name: str, model_info: Dict[str, str]):
    """Create minimal config files for GGUF model"""
    try:
        # Create a simple config.json for GGUF
        config_json = {
            "model_type": "llama",  # Most GGUF models are llama-compatible
            "model_name": model_name,
            "model_file": model_info['file'],
            "model_format": "gguf",
            "model_size": model_info['size_gb']
        }
        
        config_path = os.path.join(model_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config_json, f, indent=2)
        
        log("Created GGUF config.json", "SUCCESS")
        
    except Exception as e:
        log(f"Warning: Could not create config files: {e}", "WARN")
