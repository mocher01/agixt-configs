#!/usr/bin/env python3
"""
AGiXT Installer - Core Module
=============================

Main installation orchestrator that coordinates all other modules.
This module manages the installation flow and calls appropriate functions
from other modules.
"""

import sys
import os
from installer_utils import log

def run_installation(config_name, github_token, skip_cleanup):
    """Main installation function called by the bootstrapper"""
    
    log("🎯 AGiXT Core Installer v1.6 - Starting Installation Process")
    log("📋 Configuration: " + config_name)
    log("🔑 GitHub token: " + github_token[:8] + "...")
    log("🗑️  Cleanup skipped: " + str(skip_cleanup))
    
    try:
        # Import other modules as needed
        log("📦 Loading installer modules...")
        
        # Test import of utils (should work)
        from installer_utils import check_prerequisites, generate_secure_api_key
        log("✅ installer_utils loaded successfully")
        
        # Try to import other modules (will fail for now)
        try:
            import installer_config
            log("✅ installer_config loaded successfully")
            config_available = True
        except ImportError:
            log("⚠️  installer_config not available yet", "WARN")
            config_available = False
        
        try:
            import installer_models
            log("✅ installer_models loaded successfully")
            models_available = True
        except ImportError:
            log("⚠️  installer_models not available yet", "WARN")
            models_available = False
        
        try:
            import installer_docker
            log("✅ installer_docker loaded successfully")
            docker_available = True
        except ImportError:
            log("⚠️  installer_docker not available yet", "WARN")
            docker_available = False
        
        # Check what we can do with available modules
        log("🔍 Module availability check:")
        log("  - installer_utils: ✅ Available")
        log("  - installer_config: " + ("✅ Available" if config_available else "❌ Missing"))
        log("  - installer_models: " + ("✅ Available" if models_available else "❌ Missing"))
        log("  - installer_docker: " + ("✅ Available" if docker_available else "❌ Missing"))
        
        # Test basic functionality with available modules
        log("🧪 Testing available functionality...")
        
        # Test utilities
        log("Testing API key generation...")
        api_key = generate_secure_api_key()
        log("✅ Generated API key: " + api_key[:8] + "... (length: " + str(len(api_key)) + ")")
        
        log("Testing prerequisites check...")
        if check_prerequisites():
            log("✅ Prerequisites check passed")
        else:
            log("❌ Prerequisites check failed", "ERROR")
            return False
        
        # If we have all modules, run full installation
        if config_available and models_available and docker_available:
            log("🚀 All modules available - running full installation...")
            return run_full_installation(config_name, github_token, skip_cleanup)
        else:
            log("📋 MODULAR INSTALLATION TEST SUCCESSFUL", "SUCCESS")
            log("✅ Core module is working correctly")
            log("✅ Can load and test available modules")
            log("✅ Ready for full installation when all modules are available")
            log("ℹ️  Create the missing modules to enable full installation")
            return True
        
    except Exception as e:
        log("❌ Core installation error: " + str(e), "ERROR")
        return False

def run_full_installation(config_name, github_token, skip_cleanup):
    """Run the full installation when all modules are available"""
    
    log("🚀 FULL INSTALLATION MODE - All modules available")
    
    try:
        # Import all modules
        import installer_config
        import installer_models  
        import installer_docker
        from installer_utils import (
            check_prerequisites, check_docker_network, 
            create_installation_directory, clone_agixt_repository,
            verify_installation, install_graphql_dependencies
        )
        
        # Installation steps
        steps = [
            ("Checking prerequisites", check_prerequisites),
            ("Checking Docker network", check_docker_network),
            ("Loading configuration", lambda: installer_config.load_config_from_github(github_token)),
            ("Creating installation directory", None),  # Special handling
            ("Cloning AGiXT repository", None),         # Special handling  
            ("Setting up models", None),                # Special handling
            ("Creating Docker configuration", None),    # Special handling
            ("Starting services", None),                # Special handling
            ("Installing GraphQL dependencies", None),  # Special handling
            ("Verifying installation", None)            # Special handling
        ]
        
        config = None
        install_path = None
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            log("Step " + str(i) + "/" + str(len(steps)) + ": " + step_name + "...")
            
            if step_func:
                if step_name == "Loading configuration":
                    config = step_func()
                    if not config:
                        log("Configuration loading failed", "ERROR")
                        return False
                    log("✅ Configuration loaded: " + str(len(config)) + " variables")
                else:
                    if not step_func():
                        log("Step failed: " + step_name, "ERROR")
                        return False
            else:
                # Handle special steps that need config/install_path
                if step_name == "Creating installation directory":
                    if not config:
                        log("Config required for this step", "ERROR")
                        return False
                    install_path = create_installation_directory(config)
                    if not install_path:
                        log("Installation directory creation failed", "ERROR")
                        return False
                    
                elif step_name == "Cloning AGiXT repository":
                    if not install_path:
                        log("Install path required for this step", "ERROR") 
                        return False
                    if not clone_agixt_repository(install_path, github_token):
                        log("Repository cloning failed", "ERROR")
                        return False
                        
                elif step_name == "Setting up models":
                    if not install_path or not config:
                        log("Install path and config required for this step", "ERROR")
                        return False
                    if not installer_models.setup_models(install_path, config):
                        log("Model setup failed", "ERROR")
                        return False
                        
                elif step_name == "Creating Docker configuration":
                    if not install_path or not config:
                        log("Install path and config required for this step", "ERROR")
                        return False
                    if not installer_docker.create_configuration(install_path, config):
                        log("Docker configuration failed", "ERROR")
                        return False
                        
                elif step_name == "Starting services":
                    if not install_path or not config:
                        log("Install path and config required for this step", "ERROR")
                        return False
                    if not installer_docker.start_services(install_path, config):
                        log("Service startup failed", "ERROR") 
                        return False
                        
                elif step_name == "Installing GraphQL dependencies":
                    if not install_path:
                        log("Install path required for this step", "ERROR")
                        return False
                    install_graphql_dependencies(install_path)  # Non-critical
                    
                elif step_name == "Verifying installation":
                    if not install_path or not config:
                        log("Install path and config required for this step", "ERROR")
                        return False
                    verify_installation(install_path, config)
        
        # Success
        final_model_name = config.get('FINAL_MODEL_NAME', config.get('MODEL_NAME', 'Unknown-Model'))
        version = config.get('AGIXT_VERSION', 'unknown')
        
        log("🎉 AGiXT " + version + " Installation Complete!", "SUCCESS")
        log("📁 Directory: " + str(install_path))
        log("🤖 Model: " + final_model_name + " (GGUF)")
        log("🌐 Frontend: http://162.55.213.90:3437")
        log("🔧 Backend: http://162.55.213.90:7437") 
        log("🎮 EzLocalAI UI: http://162.55.213.90:8502")
        
        return True
        
    except Exception as e:
        log("❌ Full installation error: " + str(e), "ERROR")
        return False

# Module test function
def test_module():
    """Test this module's functionality"""
    log("🧪 Testing installer_core module...")
    
    # Test with mock parameters
    log("Testing core module loading...")
    
    try:
        # Test function exists
        if callable(run_installation):
            log("run_installation function: ✓", "SUCCESS")
        else:
            log("run_installation function: ✗", "ERROR")
            
        log("✅ installer_core module test completed", "SUCCESS")
        return True
        
    except Exception as e:
        log("❌ installer_core test failed: " + str(e), "ERROR")
        return False

if __name__ == "__main__":
    # Run module test if executed directly
    test_module()
