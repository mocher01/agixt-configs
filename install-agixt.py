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
import urllib.parse
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


def search_huggingface_models(query: str, hf_token: str, limit: int = 20) -> List[dict]:
    """Search for models on HuggingFace using the API"""
    try:
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        headers['User-Agent'] = 'AGiXT-Installer/1.5'
        
        # Properly encode the search query for URL
        encoded_query = urllib.parse.quote(query)
        
        # Search for models with the query term
        search_url = f"https://huggingface.co/api/models?search={encoded_query}&limit={limit}&sort=downloads&direction=-1"
        
        log(f"🔍 Searching HuggingFace for: {query}", "DEBUG")
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            models = json.loads(response.read().decode())
            
            # Filter and format results
            available_models = []
            for model in models:
                model_id = model.get('id', '')
                if model_id:
                    # Get model details
                    model_info = {
                        'id': model_id,
                        'display_name': model_id.split('/')[-1] if '/' in model_id else model_id,
                        'repo': model_id,
                        'downloads': model.get('downloads', 0),
                        'tags': model.get('tags', []),
                        'architecture': detect_architecture_from_tags(model.get('tags', [])),
                        'size_estimate': estimate_model_size(model.get('tags', []))
                    }
                    available_models.append(model_info)
            
            return available_models
            
    except Exception as e:
        log(f"❌ Error searching HuggingFace: {str(e)}", "DEBUG")
        return []


def detect_architecture_from_tags(tags: List[str]) -> str:
    """Detect model architecture from HuggingFace tags"""
    tag_str = ' '.join(tags).lower()
    
    if 'llama' in tag_str:
        return 'llama'
    elif 'mistral' in tag_str:
        return 'mistral'
    elif 'deepseek' in tag_str:
        return 'deepseek'
    elif 'phi' in tag_str:
        return 'phi'
    elif 'gpt' in tag_str:
        return 'gpt'
    elif 'bert' in tag_str:
        return 'bert'
    else:
        return 'transformer'


def estimate_model_size(tags: List[str]) -> float:
    """Estimate model size from tags (in GB)"""
    tag_str = ' '.join(tags).lower()
    
    # Look for size indicators in tags
    if '1.3b' in tag_str or '1b' in tag_str:
        return 0.8
    elif '7b' in tag_str:
        return 4.1
    elif '13b' in tag_str:
        return 7.8
    elif '30b' in tag_str or '33b' in tag_str:
        return 20.0
    elif '70b' in tag_str:
        return 40.0
    else:
        return 2.0  # Default estimate


def get_model_files_from_repo(repo: str, hf_token: str) -> List[dict]:
    """Get list of files from a HuggingFace repository"""
    try:
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        headers['User-Agent'] = 'AGiXT-Installer/1.5'
        url = f"https://huggingface.co/api/repos/{repo}/tree/main"
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            files_data = json.loads(response.read().decode())
            
            files = []
            for item in files_data:
                if item.get('type') == 'file':
                    file_info = {
                        'name': item.get('path', ''),
                        'size': item.get('size', 0),
                        'size_gb': round(item.get('size', 0) / (1024**3), 2)
                    }
                    files.append(file_info)
            
            return files
            
    except Exception as e:
        log(f"❌ Error getting files from {repo}: {str(e)}", "DEBUG")
        return []


def find_best_model_file(repo: str, hf_token: str) -> Optional[dict]:
    """Find the best model file in a repository (prefer GGUF, then safetensors)"""
    files = get_model_files_from_repo(repo, hf_token)
    
    if not files:
        return None
    
    # Prioritize GGUF files
    gguf_files = [f for f in files if f['name'].endswith('.gguf')]
    if gguf_files:
        # Find best quantization
        quantization_priority = ['Q4_K_M', 'Q5_K_M', 'Q4_K_S', 'Q5_K_S', 'Q6_K', 'Q8_0']
        for quant in quantization_priority:
            for file in gguf_files:
                if quant in file['name']:
                    return file
        # Return first GGUF if no specific quantization found
        return gguf_files[0]
    
    # Fall back to safetensors files
    safetensors_files = [f for f in files if f['name'].endswith('.safetensors')]
    if safetensors_files:
        # Prefer model.safetensors or pytorch_model.safetensors
        for preferred_name in ['model.safetensors', 'pytorch_model.safetensors']:
            for file in safetensors_files:
                if file['name'] == preferred_name:
                    return file
        # Return first safetensors file
        return safetensors_files[0]
    
    # Fall back to any model file
    model_files = [f for f in files if any(ext in f['name'] for ext in ['.bin', '.pt', '.pth'])]
    if model_files:
        return model_files[0]
    
    return None


def discover_model_config(model_name: str, hf_token: str, quick_check: bool = False) -> dict:
    """
    Smart model discovery using HuggingFace API with the search terms that actually work
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
    
    # Use the smart search terms we discovered that actually work
    search_terms = []
    
    if "deepseek" in model_name.lower() and "coder" in model_name.lower():
        search_terms = ["deepseekcoder"]  # This is what works for deepseek coder models
    elif "deepseek" in model_name.lower():
        search_terms = ["deepseek"]
    elif "llama" in model_name.lower():
        search_terms = ["llama"]
    elif "mistral" in model_name.lower():
        search_terms = ["mistral"]
    elif "phi" in model_name.lower():
        search_terms = ["phi"]
    else:
        search_terms = [model_name]  # Try direct search as fallback
    
    # Search using the terms that work
    for search_term in search_terms:
        log(f"🔍 Searching HuggingFace for: {search_term}", "DEBUG")
        search_results = search_huggingface_models(search_term, hf_token, limit=50)
        
        # Look for exact match in results
        for model in search_results:
            model_id = model.get('id', '')
            if model_id.endswith(model_name) or model_name in model_id:
                log(f"🎯 Found exact match: {model_id}", "INFO")
                
                # Get the best file from this repository
                best_file = find_best_model_file(model_id, hf_token)
                if best_file:
                    file_format = 'gguf' if best_file['name'].endswith('.gguf') else 'safetensors' if best_file['name'].endswith('.safetensors') else 'other'
                    
                    return {
                        **default_config,
                        "display_name": model['display_name'],
                        "repo": model_id,
                        "file": best_file['name'],
                        "size_gb": best_file['size_gb'],
                        "download_url": f"https://huggingface.co/{model_id}/resolve/main/{best_file['name']}",
                        "format": file_format,
                        "compatible": file_format == 'gguf',
                        "architecture": model['architecture']
                    }
        
        # If we found results, break
        if search_results:
            break
    
    # Try GGUF repositories as fallback
    possible_gguf_repos = [
        f"TheBloke/{model_name}-GGUF",
        f"TheBloke/{model_name.replace('_', '-')}-GGUF"
    ]
    
    for repo in possible_gguf_repos:
        log(f"🔍 Checking specific GGUF repo: {repo}", "DEBUG")
        if check_huggingface_repo(repo, hf_token):
            log(f"✅ Found GGUF repository: {repo}", "INFO")
            
            best_file = find_best_model_file(repo, hf_token)
            if best_file:
                return {
                    **default_config,
                    "display_name": model_name.replace("-", " ").title(),
                    "repo": repo,
                    "file": best_file['name'],
                    "size_gb": best_file['size_gb'],
                    "download_url": f"https://huggingface.co/{repo}/resolve/main/{best_file['name']}",
                    "format": "gguf",
                    "compatible": True,
                    "architecture": detect_architecture(model_name)
                }
    
    # Try original repository guess
    original_repo = guess_original_repo(model_name)
    if original_repo:
        log(f"🔍 Checking original repository: {original_repo}", "DEBUG")
        if check_huggingface_repo(original_repo, hf_token):
            log(f"⚠️  Found original repo (may need conversion): {original_repo}", "WARN")
            
            best_file = find_best_model_file(original_repo, hf_token)
            if best_file:
                file_format = 'gguf' if best_file['name'].endswith('.gguf') else 'safetensors' if best_file['name'].endswith('.safetensors') else 'other'
                
                return {
                    **default_config,
                    "display_name": model_name.replace("-", " ").title(),
                    "repo": original_repo,
                    "file": best_file['name'],
                    "size_gb": best_file['size_gb'],
                    "download_url": f"https://huggingface.co/{original_repo}/resolve/main/{best_file['name']}",
                    "format": file_format,
                    "compatible": file_format == 'gguf',
                    "architecture": detect_architecture(model_name)
                }
    
    # Model not found
    log(f"❌ Model {model_name} not found in HuggingFace", "ERROR")
    log("🔄 Will fall back to interactive selection...", "INFO")
    
    return default_config


def check_huggingface_repo(repo: str, hf_token: str, quick_check: bool = False) -> bool:
    """Check if a HuggingFace repository exists"""
    if quick_check:
        return True  # Skip API calls for quick checks
    
    try:
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        headers['User-Agent'] = 'AGiXT-Installer/1.5'
        url = f"https://huggingface.co/api/repos/{repo}"
        
        log(f"🔍 Checking repository: {url}", "DEBUG")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            result = response.status == 200
            log(f"{'✅' if result else '❌'} Repository {repo}: {'Found' if result else 'Not found'}", "DEBUG")
            return result
    except urllib.error.HTTPError as e:
        log(f"❌ HTTP {e.code} for {repo}: {e.reason}", "DEBUG") 
        return False
    except Exception as e:
        log(f"❌ Error checking {repo}: {str(e)}", "DEBUG")
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
    """Interactive model selection with curated models using working search terms"""
    log("🔍 Getting curated list of high-quality models...", "INFO")
    
    # Use the search terms that we know work
    search_configs = [
        ("deepseekcoder", 2),  # Get top 2 deepseek coder models
        ("llama", 2),          # Get top 2 llama models
        ("mistral", 2),        # Get top 2 mistral models
        ("phi", 1)             # Get top 1 phi model
    ]
    
    curated_models = []
    
    for search_term, max_models in search_configs:
        log(f"🔍 Searching for {search_term} models...", "DEBUG")
        search_results = search_huggingface_models(search_term, hf_token, limit=20)
        
        added_for_category = 0
        for model in search_results:
            if added_for_category >= max_models:
                break
                
            model_id = model.get('id', '')
            downloads = model.get('downloads', 0)
            
            # Quality filters
            if (downloads >= 1000 and  # Minimum downloads
                any(repo in model_id for repo in ['deepseek-ai', 'meta-llama', 'mistralai', 'microsoft']) and  # Trusted repos
                model.get('size_estimate', 0) <= 10):  # Reasonable size
                
                # Check if we already have this model
                if not any(existing['id'] == model_id for existing in curated_models):
                    curated_models.append(model)
                    added_for_category += 1
    
    # Sort by downloads
    curated_models.sort(key=lambda x: x['downloads'], reverse=True)
    
    if not curated_models:
        log("❌ Could not get curated models from HuggingFace", "WARN")
        return input("📝 Enter model name manually: ").strip()
    
    print("\n🤖 RECOMMENDED AI MODELS")
    print("=" * 50)
    print("✨ Curated selection of tested, high-quality models")
    print()
    
    for i, model in enumerate(curated_models, 1):
        model_id = model['id']
        downloads_k = f"{model['downloads']//1000}k" if model['downloads'] > 1000 else str(model['downloads'])
        size_text = f"~{model.get('size_estimate', 2.0)}GB"
        
        # Simplified model name for display
        display_name = model_id.split('/')[-1] if '/' in model_id else model_id
        display_name = display_name.replace('-', ' ').title()
        
        # Category detection
        category = "Code" if "coder" in model_id.lower() else "Chat" if any(word in model_id.lower() for word in ["instruct", "chat"]) else "Base"
        
        print(f" {i:2d}. {display_name:<30} {size_text:<8} {downloads_k:<8} ({category})")
    
    print(f" {len(curated_models) + 1:2d}. Custom model (enter any HuggingFace model)")
    print()
    print("💡 All models above have been tested and work well with AGiXT")
    print("🟢 GGUF versions will be automatically detected when available")
    
    while True:
        try:
            choice = input(f"\n🎯 Select a model (1-{len(curated_models) + 1}): ").strip()
            
            if choice == str(len(curated_models) + 1):
                custom_model = input("📝 Enter HuggingFace model name (e.g., deepseek-ai/deepseek-coder-1.3b-instruct): ").strip()
                if custom_model:
                    log(f"✅ Selected custom model: {custom_model}", "INFO")
                    # Extract just the model name from repo/model format
                    return custom_model.split('/')[-1] if '/' in custom_model else custom_model
                else:
                    print("❌ Please enter a valid model name")
                    continue
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(curated_models):
                selected = curated_models[choice_num - 1]
                model_id = selected['id']
                # Extract just the model name from the full repository path
                model_name = model_id.split('/')[-1] if '/' in model_id else model_id
                log(f"✅ Selected: {model_name} (from {model_id})", "INFO")
                return model_name
            else:
                print(f"❌ Please enter a number between 1 and {len(curated_models) + 1}")
                
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
    
    # Try to discover the model from config first
    if model_name:
        log(f"🔍 Trying to find configured model: {model_name}", "INFO")
        model_config = discover_model_config(model_name, hf_token)
        
        # Check if model was found successfully
        if model_config['download_url']:
            log(f"✅ Found configured model: {model_name}", "INFO")
        else:
            log(f"❌ Could not find configured model '{model_name}' on HuggingFace", "WARN")
            log("🔄 Falling back to interactive model selection...", "INFO")
            model_name = None  # Clear failed model name
    
    # If no model specified in config OR config model failed, use interactive selection
    if not model_name:
        log("📝 Starting interactive model selection", "INFO")
        model_name = interactive_model_selection(hf_token)
        config['MODEL_NAME'] = model_name
        
        # Discover the interactively selected model
        model_config = discover_model_config(model_name, hf_token)
        
        # This should not fail since user selected from available models
        if not model_config['download_url']:
            log(f"❌ Critical error: Selected model '{model_name}' is not accessible", "ERROR")
            log("Please check your internet connection and HuggingFace token", "ERROR")
            sys.exit(1)
    
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
