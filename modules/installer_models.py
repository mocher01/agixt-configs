#!/usr/bin/env python3
"""
AGiXT Installer - Models Module
===============================

Handles model discovery, downloading, and architecture setup.
This module implements GGUF model focus with automatic fallbacks
and dynamic architecture detection.
"""

import os
import json
import urllib.request
import urllib.error
import shutil
from datetime import datetime
from installer_utils import log

def get_model_architecture(model_repo, model_name):
    """Get correct architecture values based on model type"""
    
    model_lower = model_name.lower()
    repo_lower = model_repo.lower()
    
    # Deepseek models
    if "deepseek" in model_lower or "deepseek" in repo_lower:
        return {
            "architectures": ["DeepseekForCausalLM"],
            "model_type": "deepseek",
            "hidden_size": 2048,
            "num_attention_heads": 16,
            "num_hidden_layers": 24,
            "num_key_value_heads": 16,
            "vocab_size": 32000,
            "intermediate_size": 5504,
            "bos_token_id": 100000,
            "eos_token_id": 100001,
            "hidden_act": "silu",
            "rms_norm_eps": 1e-06,
            "rope_theta": 10000.0,
            "max_tokens": 8192
        }
    
    # Llama models (including CodeLlama)
    elif "llama" in model_lower or "llama" in repo_lower:
        return {
            "architectures": ["LlamaForCausalLM"],
            "model_type": "llama",
            "hidden_size": 4096,
            "num_attention_heads": 32,
            "num_hidden_layers": 32,
            "num_key_value_heads": 32,
            "vocab_size": 32000,
            "intermediate_size": 11008,
            "bos_token_id": 1,
            "eos_token_id": 2,
            "hidden_act": "silu",
            "rms_norm_eps": 1e-06,
            "rope_theta": 10000.0,
            "max_tokens": 4096
        }
    
    # Mistral models
    elif "mistral" in model_lower or "mistral" in repo_lower:
        return {
            "architectures": ["MistralForCausalLM"],
            "model_type": "mistral",
            "hidden_size": 4096,
            "num_attention_heads": 32,
            "num_hidden_layers": 32,
            "num_key_value_heads": 8,
            "vocab_size": 32000,
            "intermediate_size": 14336,
            "bos_token_id": 1,
            "eos_token_id": 2,
            "hidden_act": "silu",
            "rms_norm_eps": 1e-05,
            "rope_theta": 10000.0,
            "max_tokens": 4096
        }
    
    # Phi models
    elif "phi" in model_lower or "phi" in repo_lower:
        return {
            "architectures": ["PhiForCausalLM"],
            "model_type": "phi",
            "hidden_size": 2560,
            "num_attention_heads": 32,
            "num_hidden_layers": 32,
            "num_key_value_heads": 32,
            "vocab_size": 51200,
            "intermediate_size": 10240,
            "bos_token_id": 1,
            "eos_token_id": 2,
            "hidden_act": "gelu_new",
            "rms_norm_eps": 1e-05,
            "rope_theta": 10000.0,
            "max_tokens": 2048
        }
    
    # Default to Llama if unknown
    else:
        log("⚠️  Unknown model type for " + model_name + ", defaulting to Llama architecture", "WARN")
        return {
            "architectures": ["LlamaForCausalLM"],
            "model_type": "llama",
            "hidden_size": 4096,
            "num_attention_heads": 32,
            "num_hidden_layers": 32,
            "num_key_value_heads": 32,
            "vocab_size": 32000,
            "intermediate_size": 11008,
            "bos_token_id": 1,
            "eos_token_id": 2,
            "hidden_act": "silu",
            "rms_norm_eps": 1e-06,
            "rope_theta": 10000.0,
            "max_tokens": 4096
        }

def get_model_config(model_name, hf_token):
    """Get GGUF model configuration with fallbacks"""
    log("🔍 Looking for GGUF version of " + model_name + "...")
    
    # Priority repositories for GGUF models
    gguf_repos = [
        "TheBloke/" + model_name.replace('/', '-') + "-GGUF",
        "microsoft/" + model_name.split('/')[-1] + "-gguf",
        "bartowski/" + model_name.split('/')[-1] + "-GGUF",
        "TheBloke/" + model_name.split('/')[-1] + "-GGUF"
    ]
    
    # Fallback GGUF models if original not found
    fallback_models = [
        "TheBloke/Llama-2-7B-Chat-GGUF",
        "TheBloke/Mistral-7B-Instruct-v0.1-GGUF", 
        "microsoft/phi-2-gguf",
        "TheBloke/CodeLlama-7B-Instruct-GGUF"
    ]
    
    all_repos = gguf_repos + fallback_models
    
    for repo in all_repos:
        try:
            log("🔍 Checking repository: " + repo)
            
            # Use correct HuggingFace API endpoint
            api_url = "https://huggingface.co/api/models/" + repo
            
            req = urllib.request.Request(api_url)
            req.add_header('Authorization', 'Bearer ' + hf_token)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    repo_info = json.loads(response.read().decode())
                    
                    # Check files in the repo
                    files_url = "https://huggingface.co/api/models/" + repo + "/tree/main"
                    files_req = urllib.request.Request(files_url)
                    files_req.add_header('Authorization', 'Bearer ' + hf_token)
                    
                    with urllib.request.urlopen(files_req, timeout=10) as files_response:
                        files_data = json.loads(files_response.read().decode())
                        
                        # Look for GGUF files
                        gguf_files = [f for f in files_data if f['path'].endswith('.gguf')]
                        
                        if gguf_files:
                            # Prefer Q4_K_M or Q5_K_M for good quality/size balance
                            preferred_file = None
                            for file in gguf_files:
                                if 'q4_k_m' in file['path'].lower():
                                    preferred_file = file
                                    break
                                elif 'q5_k_m' in file['path'].lower():
                                    preferred_file = file
                                    break
                            
                            if not preferred_file:
                                preferred_file = gguf_files[0]  # Take first available
                            
                            config = {
                                'model_repo': repo,
                                'model_file': preferred_file['path'],
                                'model_url': "https://huggingface.co/" + repo + "/resolve/main/" + preferred_file['path'],
                                'model_size_gb': preferred_file.get('size', 0) / (1024**3),
                                'is_fallback': repo in fallback_models
                            }
                            
                            if config['is_fallback']:
                                log("✅ Found fallback GGUF model: " + repo + "/" + preferred_file['path'], "SUCCESS")
                            else:
                                log("✅ Found GGUF version: " + repo + "/" + preferred_file['path'], "SUCCESS")
                            
                            log("📊 Model size: " + str(round(config['model_size_gb'], 1)) + "GB")
                            return repo.split('/')[-1], config
                            
        except Exception as e:
            log("⚠️  Could not access " + repo + ": " + str(e), "WARN")
            continue
    
    log("❌ No GGUF models found", "ERROR")
    return None, {}

def download_with_auth(url, target_path, token):
    """Download file with HuggingFace authentication"""
    try:
        log("📥 Downloading: " + url)
        log("📁 Target: " + target_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Create request with authentication
        req = urllib.request.Request(url)
        req.add_header('Authorization', 'Bearer ' + token)
        
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
                        print("\r[" + datetime.now().strftime('%H:%M:%S') + "] INFO: Download progress: " + str(percent) + "% (" + str(downloaded_mb) + "/" + str(total_mb) + " MB)", end='')
        
        print()  # New line after progress
        
        # Verify download
        if os.path.exists(target_path):
            actual_size_gb = os.path.getsize(target_path) / (1024 * 1024 * 1024)
            log("✅ Download completed: " + str(round(actual_size_gb, 1)) + "GB", "SUCCESS")
            return True
        else:
            log("❌ Download failed - file not found", "ERROR")
            return False
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            log("❌ Authentication failed - check your HuggingFace token", "ERROR")
        else:
            log("❌ HTTP Error " + str(e.code) + ": " + str(e.reason), "ERROR")
        return False
    except Exception as e:
        log("❌ Error downloading file: " + str(e), "ERROR")
        return False

def setup_models(install_path, config):
    """Main model setup function - downloads and configures models"""
    
    # Get model configuration
    model_name = config.get('MODEL_NAME', 'Unknown-Model')
    backup_path = config.get('MODEL_BACKUP_PATH', '')
    hf_token = config.get('HUGGINGFACE_TOKEN', '')
    
    try:
        log("🤖 Setting up " + model_name + " model (GGUF focus)...")
        
        # Get GGUF model configuration
        final_model_name, model_config = get_model_config(model_name, hf_token)
        
        if not model_config:
            log("❌ No suitable GGUF model found - installation cannot continue", "ERROR")
            return False
        
        if model_config.get('is_fallback'):
            log("⚠️  Using fallback model: " + final_model_name, "WARN")
        
        # Get dynamic architecture based on actual model being used
        model_repo = model_config['model_repo']
        architecture = get_model_architecture(model_repo, final_model_name)
        log("🏗️  Using " + architecture['model_type'] + " architecture for " + final_model_name)
        
        # Create model directory
        target_model_dir = os.path.join(install_path, "ezlocalai", final_model_name)
        target_model_path = os.path.join(target_model_dir, model_config['model_file'])
        
        # Create HuggingFace-style directory structure
        os.makedirs(target_model_dir, exist_ok=True)
        log("📁 Created model directory: " + target_model_dir, "SUCCESS")
        
        # Check if backup model exists (original model path)
        if backup_path and os.path.exists(backup_path):
            log("💾 Found backup model at " + backup_path, "SUCCESS")
            
            # Get model size
            model_size = os.path.getsize(backup_path) / (1024 * 1024 * 1024)  # GB
            log("📊 Backup model size: " + str(round(model_size, 1)) + "GB")
            
            # Copy model file
            log("📋 Copying model file from backup...")
            shutil.copy2(backup_path, target_model_path)
            
            # Verify copy
            if os.path.exists(target_model_path):
                target_size = os.path.getsize(target_model_path) / (1024 * 1024 * 1024)  # GB
                log("✅ Model copied successfully: " + str(round(target_size, 1)) + "GB", "SUCCESS")
            else:
                log("❌ Model copy failed", "ERROR")
                return False
        else:
            if backup_path:
                log("⚠️  Backup model not found at " + backup_path, "WARN")
            log("📥 Downloading GGUF model from HuggingFace with authentication...")
            
            # Download GGUF model with authentication
            if not download_with_auth(model_config['model_url'], target_model_path, hf_token):
                log("❌ Failed to download " + model_config['model_file'], "ERROR")
                return False
            log("✅ Downloaded " + model_config['model_file'] + " successfully", "SUCCESS")
        
        # Create HuggingFace config files using DYNAMIC values based on actual model
        log("🔧 Creating/updating HuggingFace config files with dynamic architecture...")
        
        # Create/update config.json with DYNAMIC architecture
        config_json_path = os.path.join(target_model_dir, "config.json")
        if not os.path.exists(config_json_path):
            model_config_json = {
                "architectures": architecture["architectures"],
                "attention_dropout": 0.0,
                "bos_token_id": architecture["bos_token_id"],
                "eos_token_id": architecture["eos_token_id"],
                "hidden_act": architecture["hidden_act"],
                "hidden_size": architecture["hidden_size"],
                "initializer_range": 0.02,
                "intermediate_size": architecture["intermediate_size"],
                "max_position_embeddings": architecture["max_tokens"],
                "model_type": architecture["model_type"],
                "num_attention_heads": architecture["num_attention_heads"],
                "num_hidden_layers": architecture["num_hidden_layers"],
                "num_key_value_heads": architecture["num_key_value_heads"],
                "rms_norm_eps": architecture["rms_norm_eps"],
                "rope_theta": architecture["rope_theta"],
                "tie_word_embeddings": False,
                "torch_dtype": "bfloat16",
                "transformers_version": "4.37.0",
                "use_cache": True,
                "vocab_size": architecture["vocab_size"]
            }
            
            with open(config_json_path, 'w') as f:
                json.dump(model_config_json, f, indent=2)
            log("✅ Created model config.json with " + architecture['model_type'] + " architecture", "SUCCESS")
        
        # Create/update tokenizer_config.json with DYNAMIC values
        tokenizer_config_path = os.path.join(target_model_dir, "tokenizer_config.json")
        if not os.path.exists(tokenizer_config_path):
            # Use dynamic token IDs based on model type
            if architecture["model_type"] == "deepseek":
                tokenizer_config = {
                    "added_tokens_decoder": {
                        "100000": {"content": "<｜begin▁of▁sentence｜>", "lstrip": False, "normalized": False, "rstrip": False, "single_word": False, "special": True},
                        "100001": {"content": "<｜end▁of▁sentence｜>", "lstrip": False, "normalized": False, "rstrip": False, "single_word": False, "special": True}
                    },
                    "bos_token": "<｜begin▁of▁sentence｜>",
                    "eos_token": "<｜end▁of▁sentence｜>",
                    "model_max_length": architecture["max_tokens"],
                    "tokenizer_class": "LlamaTokenizer"
                }
            else:
                # Standard format for Llama/Mistral/Phi
                tokenizer_config = {
                    "bos_token": "<s>",
                    "eos_token": "</s>",
                    "model_max_length": architecture["max_tokens"],
                    "tokenizer_class": "LlamaTokenizer"
                }
            
            with open(tokenizer_config_path, 'w') as f:
                json.dump(tokenizer_config, f, indent=2)
            log("✅ Created tokenizer_config.json for " + architecture['model_type'] + " model", "SUCCESS")
        
        # Set proper permissions
        if os.path.exists(target_model_path):
            os.chmod(target_model_path, 0o644)
            log("🔒 Model permissions set", "SUCCESS")
        
        # Update config with final model info for use by other modules
        config['FINAL_MODEL_NAME'] = final_model_name
        config['FINAL_MODEL_FILE'] = model_config['model_file']
        config['DEFAULT_MODEL'] = final_model_name
        config['EZLOCALAI_MODEL'] = final_model_name
        config['EZLOCALAI_MAX_TOKENS'] = str(architecture["max_tokens"])
        config['LLM_MAX_TOKENS'] = str(architecture["max_tokens"])
        
        # Add dynamic architecture values to config for .env file
        config['MODEL_ARCHITECTURE_TYPE'] = architecture['model_type']
        config['MODEL_HIDDEN_SIZE'] = str(architecture['hidden_size'])
        config['MODEL_NUM_LAYERS'] = str(architecture['num_hidden_layers'])
        config['MODEL_NUM_HEADS'] = str(architecture['num_attention_heads'])
        config['MODEL_NUM_KV_HEADS'] = str(architecture['num_key_value_heads'])
        config['MODEL_VOCAB_SIZE'] = str(architecture['vocab_size'])
        config['MODEL_INTERMEDIATE_SIZE'] = str(architecture['intermediate_size'])
        
        # Final verification
        if os.path.exists(target_model_path) and os.path.isfile(target_model_path):
            final_size = os.path.getsize(target_model_path) / (1024 * 1024 * 1024)
            log("✅ " + final_model_name + " model setup complete: " + str(round(final_size, 1)) + "GB", "SUCCESS")
            log("🏗️  Architecture: " + architecture['model_type'] + " (" + str(architecture['hidden_size']) + "d)", "SUCCESS")
            return True
        else:
            log("❌ " + final_model_name + " model setup failed", "ERROR")
            return False
            
    except Exception as e:
        log("❌ Error setting up model files: " + str(e), "ERROR")
        return False

# Module test function
def test_module():
    """Test this module's functionality"""
    log("🧪 Testing installer_models module...")
    
    # Test architecture detection
    test_models = [
        ("deepseek-coder-1.3b-instruct", "deepseek"),
        ("llama-2-7b-chat", "llama"),
        ("mistral-7b-instruct", "mistral"),
        ("phi-2", "phi")
    ]
    
    for model_name, expected_type in test_models:
        arch = get_model_architecture("test/" + model_name, model_name)
        if arch['model_type'] == expected_type:
            log("Architecture detection for " + model_name + ": ✓", "SUCCESS")
        else:
            log("Architecture detection for " + model_name + ": ✗", "ERROR")
    
    log("✅ installer_models module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    # Run module test if executed directly
    test_module()
