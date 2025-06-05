#!/usr/bin/env python3
"""
AGiXT Installer - Models Module (FIXED - Simplified Approach)
============================================================

STRATEGY: Let EzLocalAI handle model downloads and management.
We just map user choices to HuggingFace repo paths and let EzLocalAI do its job.

REMOVED: Manual GGUF downloads, config file creation, complex file management
ADDED: Simple repo path mapping and configuration
"""

import os
from installer_utils import log

def get_model_repo_mapping():
    """Map common model names to working HuggingFace GGUF repositories"""
    return {
        # TinyLlama models
        'tinyllama': 'TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF',
        'tinyllama-1.1b': 'TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF',
        
        # Phi models  
        'phi-2': 'TheBloke/phi-2-dpo-GGUF',
        'phi2': 'TheBloke/phi-2-dpo-GGUF',
        
        # DeepSeek models
        'deepseek': 'TheBloke/deepseek-coder-1.3b-instruct-GGUF',
        'deepseek-coder': 'TheBloke/deepseek-coder-1.3b-instruct-GGUF',
        
        # Llama models
        'llama-2-7b': 'TheBloke/Llama-2-7B-Chat-GGUF',
        'llama2': 'TheBloke/Llama-2-7B-Chat-GGUF',
        
        # Mistral models
        'mistral-7b': 'TheBloke/Mistral-7B-Instruct-v0.1-GGUF',
        'mistral': 'TheBloke/Mistral-7B-Instruct-v0.1-GGUF',
        
        # CodeLlama models
        'codellama': 'TheBloke/CodeLlama-7B-Instruct-GGUF',
        'code-llama': 'TheBloke/CodeLlama-7B-Instruct-GGUF',
    }

def determine_model_repo(model_name):
    """Determine the correct HuggingFace repo path from user's model choice"""
    
    if not model_name or model_name == 'Unknown-Model':
        log("⚠️  No model specified, using default Phi-2", "WARN")
        return 'TheBloke/phi-2-dpo-GGUF'
    
    # Get mapping
    repo_mapping = get_model_repo_mapping()
    model_lower = model_name.lower().strip()
    
    # Direct mapping lookup
    if model_lower in repo_mapping:
        repo_path = repo_mapping[model_lower]
        log(f"✅ Direct mapping: {model_name} -> {repo_path}")
        return repo_path
    
    # Fuzzy matching for common patterns
    for key, repo_path in repo_mapping.items():
        if key in model_lower or model_lower in key:
            log(f"✅ Pattern match: {model_name} -> {repo_path}")
            return repo_path
    
    # If it's already a HuggingFace repo path, use it directly
    if '/' in model_name and not model_name.endswith('.gguf'):
        log(f"✅ Using provided repo path: {model_name}")
        return model_name
    
    # Default fallback
    log(f"⚠️  Unknown model '{model_name}', using default Phi-2", "WARN")
    return 'TheBloke/phi-2-dpo-GGUF'

def get_max_tokens_for_model(repo_path):
    """Get appropriate max tokens based on model type"""
    
    repo_lower = repo_path.lower()
    
    if 'tinyllama' in repo_lower or '1.1b' in repo_lower:
        return '2048'
    elif 'phi-2' in repo_lower or 'phi2' in repo_lower:
        return '2048'  
    elif 'deepseek' in repo_lower and ('1.3b' in repo_lower or 'coder' in repo_lower):
        return '4096'
    elif 'llama-2-7b' in repo_lower or 'llama2' in repo_lower:
        return '4096'
    elif 'mistral' in repo_lower:
        return '4096'
    elif 'codellama' in repo_lower:
        return '4096'
    else:
        return '2048'  # Safe default

def setup_models(install_path, config):
    """
    SIMPLIFIED MODEL SETUP: Let EzLocalAI handle downloads and management
    
    We only:
    1. Create the models directory for volume mapping
    2. Map user's model choice to HuggingFace repo path  
    3. Set configuration for EzLocalAI
    4. Let EzLocalAI do everything else
    """
    
    try:
        log("🤖 Setting up model configuration (Simplified Approach)...")
        
        # Get user's model choice
        model_name = config.get('MODEL_NAME', config.get('DEFAULT_MODEL', 'phi-2'))
        log(f"📝 User requested model: {model_name}")
        
        # Create models directory for Docker volume mapping
        # EzLocalAI expects ./models:/app/models volume mapping
        models_dir = os.path.join(install_path, "models")
        os.makedirs(models_dir, exist_ok=True)
        log(f"📁 Created models directory: {models_dir}")
        
        # Determine correct HuggingFace repo path
        repo_path = determine_model_repo(model_name)
        log(f"🎯 Selected HuggingFace repo: {repo_path}")
        
        # Get appropriate max tokens for this model
        max_tokens = get_max_tokens_for_model(repo_path)
        log(f"🔢 Max tokens for this model: {max_tokens}")
        
        # Set configuration for EzLocalAI
        # EzLocalAI will use DEFAULT_MODEL to download from HuggingFace automatically
        config['DEFAULT_MODEL'] = repo_path
        config['EZLOCALAI_MODEL'] = repo_path
        config['EZLOCALAI_MAX_TOKENS'] = max_tokens
        config['LLM_MAX_TOKENS'] = max_tokens
        
        # Store final model info for logging
        config['FINAL_MODEL_NAME'] = repo_path.split('/')[-1]  # For display purposes
        config['FINAL_MODEL_REPO'] = repo_path
        
        # Log success
        log("✅ Model configuration completed successfully!", "SUCCESS")
        log(f"🎯 EzLocalAI will download: {repo_path}", "SUCCESS")
        log(f"📊 Max tokens configured: {max_tokens}", "SUCCESS")
        log("🔄 EzLocalAI will handle all file management automatically", "INFO")
        
        return True
        
    except Exception as e:
        log(f"❌ Error setting up model configuration: {e}", "ERROR")
        return False

def test_module():
    """Test the simplified model setup"""
    log("🧪 Testing simplified installer_models module...")
    
    # Test model mapping
    test_cases = [
        ('tinyllama', 'TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF'),
        ('phi-2', 'TheBloke/phi-2-dpo-GGUF'),
        ('deepseek', 'TheBloke/deepseek-coder-1.3b-instruct-GGUF'),
        ('Unknown-Model', 'TheBloke/phi-2-dpo-GGUF'),  # Default
    ]
    
    for model_name, expected_repo in test_cases:
        result = determine_model_repo(model_name)
        if result == expected_repo:
            log(f"✓ {model_name} -> {result}", "SUCCESS")
        else:
            log(f"✗ {model_name} -> {result} (expected {expected_repo})", "ERROR")
    
    # Test max tokens
    test_tokens = [
        ('TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF', '2048'),
        ('TheBloke/phi-2-dpo-GGUF', '2048'),
        ('TheBloke/Llama-2-7B-Chat-GGUF', '4096'),
    ]
    
    for repo, expected_tokens in test_tokens:
        result = get_max_tokens_for_model(repo)
        if result == expected_tokens:
            log(f"✓ {repo} -> {result} tokens", "SUCCESS")
        else:
            log(f"✗ {repo} -> {result} tokens (expected {expected_tokens})", "ERROR")
    
    log("✅ Simplified installer_models module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
