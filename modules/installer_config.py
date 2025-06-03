#!/usr/bin/env python3
"""
AGiXT Installer - Configuration Module (FIXED)
==============================================

Handles loading and parsing configuration from GitHub repository.
This module manages the agixt.config file and validates all settings.

FIXED: File handling bug after downloading config from GitHub
"""

import urllib.request
import urllib.error
from installer_utils import log

def load_config_from_github(github_token):
    """Load configuration from GitHub agixt.config file using Contents API"""
    config = {}
    
    log("📋 Loading configuration from GitHub repository...")
    try:
        config_files = [
            "agixt.config",
            ".env",
            "config.env"
        ]
        
        for config_file in config_files:
            try:
                api_url = "https://api.github.com/repos/mocher01/agixt-configs/contents/" + config_file
                
                req = urllib.request.Request(api_url)
                req.add_header('Authorization', 'token ' + github_token)
                req.add_header('Accept', 'application/vnd.github.v3.raw')
                
                log("📥 Trying to fetch " + config_file + " from GitHub API...")
                
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                    
                    log("✅ Successfully downloaded config from: " + config_file, "SUCCESS")
                    
                    # Parse the config file directly from content (don't save to disk yet)
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
                    
                    # FIXED: Only save to disk AFTER successful parsing
                    try:
                        with open('agixt.config', 'w') as f:
                            f.write(content)
                        log("💾 Configuration saved locally as agixt.config", "SUCCESS")
                    except Exception as save_error:
                        log("⚠️  Could not save config locally: " + str(save_error), "WARN")
                        # Continue anyway since we have the config in memory
                    
                    # Validate required keys (using MODEL_NAME instead of MODEL_HF_NAME)
                    required_keys = [
                        'AGIXT_VERSION', 'MODEL_NAME', 'HUGGINGFACE_TOKEN',
                        'INSTALL_FOLDER_PREFIX', 'INSTALL_BASE_PATH'
                    ]
                    
                    missing_keys = [key for key in required_keys if key not in config]
                    if missing_keys:
                        log("❌ Missing required configuration keys: " + str(missing_keys), "ERROR")
                        return {}
                    
                    log("✅ Configuration loaded successfully: " + str(len(config)) + " variables", "SUCCESS")
                    log("🔧 Version: " + config.get('AGIXT_VERSION', 'Unknown'))
                    log("🤖 Model: " + config.get('MODEL_NAME', 'Unknown'))
                    log("🏗️  Install path: " + config.get('INSTALL_BASE_PATH', 'Unknown'))
                    
                    return config
                    
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    log("ℹ️  " + config_file + " not found in repository")
                    continue  # Try next file
                else:
                    log("⚠️  Error accessing " + config_file + ": HTTP " + str(e.code), "WARN")
            except Exception as e:
                log("⚠️  Error fetching " + config_file + ": " + str(e), "WARN")
        
        log("❌ Could not find configuration file in GitHub repository", "ERROR")
        return {}
        
    except Exception as e:
        log("❌ Error loading config from GitHub: " + str(e), "ERROR")
        return {}

def load_config_fallback():
    """Fallback: try to load config from local files"""
    config = {}
    
    log("📋 Attempting fallback to local configuration files...")
    config_files = ['agixt.config', '.env', 'config.env']
    
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                log("📁 Found local configuration file: " + config_file)
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
            
            if config:
                log("✅ Loaded configuration from " + config_file, "SUCCESS")
                return config
                
        except FileNotFoundError:
            continue
        except Exception as e:
            log("⚠️  Error reading " + config_file + ": " + str(e), "WARN")
    
    log("❌ No local configuration files found", "ERROR")
    return {}

def validate_config(config):
    """Validate configuration values and show summary"""
    if not config:
        log("❌ No configuration to validate", "ERROR")
        return False
    
    log("🔍 Validating configuration...")
    
    # Required keys validation
    required_keys = {
        'AGIXT_VERSION': 'AGiXT version identifier',
        'MODEL_NAME': 'Model to install (auto-detects architecture)',
        'HUGGINGFACE_TOKEN': 'Authentication for model downloads',
        'INSTALL_FOLDER_PREFIX': 'Installation directory prefix',
        'INSTALL_BASE_PATH': 'Base installation path'
    }
    
    missing_keys = []
    for key, description in required_keys.items():
        if key not in config or not config[key]:
            missing_keys.append(key + " (" + description + ")")
    
    if missing_keys:
        log("❌ Missing required configuration:", "ERROR")
        for missing in missing_keys:
            log("  - " + missing, "ERROR")
        return False
    
    # Configuration summary
    log("✅ Configuration validation successful", "SUCCESS")
    log("📋 Configuration Summary:")
    log("  🔧 Version: " + config.get('AGIXT_VERSION', 'Unknown'))
    log("  🤖 Model: " + config.get('MODEL_NAME', 'Unknown'))
    log("  📁 Install Path: " + config.get('INSTALL_BASE_PATH', 'Unknown') + "/" + config.get('INSTALL_FOLDER_PREFIX', 'agixt') + "-" + config.get('AGIXT_VERSION', 'unknown'))
    log("  🔑 HuggingFace Token: " + config.get('HUGGINGFACE_TOKEN', 'NOT SET')[:8] + "...")
    log("  🌐 Frontend URL: " + config.get('APP_URI', 'Not set'))
    log("  🔧 Backend URL: " + config.get('AGIXT_SERVER', 'Not set'))
    
    return True

def enhance_config_with_dynamic_values(config):
    """Add dynamic values that will be set during installation"""
    if not config:
        return config
    
    log("🔧 Enhancing configuration with dynamic values...")
    
    # Add install timestamp
    from datetime import datetime
    config['INSTALL_DATE'] = datetime.now().isoformat()
    
    # Generate API key placeholder (will be replaced during installation)
    from installer_utils import generate_secure_api_key
    config['AGIXT_API_KEY'] = generate_secure_api_key()
    
    log("✅ Added INSTALL_DATE: " + config['INSTALL_DATE'])
    log("✅ Generated AGIXT_API_KEY: " + config['AGIXT_API_KEY'][:8] + "...")
    
    return config

# Module test function
def test_module():
    """Test this module's functionality"""
    log("🧪 Testing installer_config module...")
    
    # Test config validation with mock config
    test_config = {
        'AGIXT_VERSION': 'v1.6-test',
        'MODEL_NAME': 'test-model',
        'HUGGINGFACE_TOKEN': 'test_token',
        'INSTALL_FOLDER_PREFIX': 'agixt',
        'INSTALL_BASE_PATH': '/tmp'
    }
    
    if validate_config(test_config):
        log("Configuration validation: ✓", "SUCCESS")
    else:
        log("Configuration validation: ✗", "ERROR")
    
    # Test config enhancement
    enhanced = enhance_config_with_dynamic_values(test_config)
    if 'INSTALL_DATE' in enhanced and 'AGIXT_API_KEY' in enhanced:
        log("Configuration enhancement: ✓", "SUCCESS")
    else:
        log("Configuration enhancement: ✗", "ERROR")
    
    log("✅ installer_config module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    # Run module test if executed directly
    test_module()
