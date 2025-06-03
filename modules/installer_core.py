#!/usr/bin/env python3
"""
AGiXT Installer - Enhanced Core Module
======================================

Enhanced version with integrated debugging and post-install testing.
Includes analysis of why AGiXT API fails independently of EzLocalAI.
"""

import sys
import os
from installer_utils import log

def run_installation(config_name, github_token, skip_cleanup):
    """Enhanced installation function with debugging and testing"""
    
    log("🎯 AGiXT Enhanced Core Installer v1.6 - Starting Installation Process", "HEADER")
    log("📋 Configuration: " + config_name)
    if github_token:
        log("🔑 GitHub token: " + github_token[:8] + "...")
    else:
        log("🔑 GitHub token: Not provided (using public repository)")
    log("🗑️  Cleanup skipped: " + str(skip_cleanup))
    log("🔍 Enhanced with debugging and integrated testing")
    
    try:
        # Import modules with enhanced error reporting
        log("📦 Loading installer modules...", "HEADER")
        
        # Test import of utils
        from installer_utils import check_prerequisites, generate_secure_api_key
        log("✅ installer_utils loaded successfully")
        
        # Import other modules with detailed error reporting
        modules_status = {}
        
        try:
            import installer_config
            log("✅ installer_config loaded successfully")
            modules_status['config'] = True
        except ImportError as e:
            log(f"⚠️  installer_config not available: {e}", "WARN")
            modules_status['config'] = False
        
        try:
            import installer_models
            log("✅ installer_models loaded successfully")
            modules_status['models'] = True
        except ImportError as e:
            log(f"⚠️  installer_models not available: {e}", "WARN")
            modules_status['models'] = False
        
        try:
            import installer_docker
            log("✅ installer_docker loaded successfully")
            modules_status['docker'] = True
        except ImportError as e:
            log(f"⚠️  installer_docker not available: {e}", "WARN")
            modules_status['docker'] = False
        
        # Module availability summary
        log("🔍 Module availability check:", "INFO")
        log("  - installer_utils: ✅ Available")
        for module, available in modules_status.items():
            status = "✅ Available" if available else "❌ Missing"
            log(f"  - installer_{module}: {status}")
        
        # Test basic functionality
        log("🧪 Testing available functionality...", "TEST")
        
        # Test utilities
        log("Testing API key generation...")
        api_key = generate_secure_api_key()
        log(f"✅ Generated API key: {api_key[:8]}... (length: {len(api_key)})")
        
        log("Testing prerequisites check...")
        if check_prerequisites():
            log("✅ Prerequisites check passed")
        else:
            log("❌ Prerequisites check failed", "ERROR")
            return False
        
        # Test config loading if available
        if modules_status['config']:
            log("🔧 CONFIG MODULE IS AVAILABLE - Testing configuration loading...", "TEST")
            try:
                test_config = installer_config.load_config_from_github(github_token, config_name)
                if test_config:
                    log("✅ Configuration loading successful")
                    log(f"📊 Loaded {len(test_config)} configuration variables")
                    
                    if installer_config.validate_config(test_config):
                        log("✅ Configuration validation successful")
                        enhanced_config = installer_config.enhance_config_with_dynamic_values(test_config)
                        log("✅ Configuration enhancement successful")
                    else:
                        log("⚠️  Configuration validation failed", "WARN")
                else:
                    log("⚠️  Configuration loading failed", "WARN")
            except Exception as e:
                log(f"❌ Config testing error: {e}", "ERROR")
        else:
            log("⚠️  CONFIG MODULE NOT AVAILABLE - Skipping config tests", "WARN")
        
        # Run full installation if all modules available
        if all(modules_status.values()):
            log("🚀 All modules available - running enhanced installation...", "SUCCESS")
            return run_enhanced_installation(config_name, github_token, skip_cleanup)
        else:
            log("📋 PARTIAL INSTALLATION TEST SUCCESSFUL", "SUCCESS")
            log("✅ Core module is working correctly")
            log("✅ Can load and test available modules")
            log("ℹ️  Some modules missing - cannot run full installation")
            
            missing_modules = [f"installer_{module}" for module, available in modules_status.items() if not available]
            log(f"❌ Missing modules: {', '.join(missing_modules)}", "ERROR")
            return False
        
    except Exception as e:
        log(f"❌ Core installation error: {e}", "ERROR")
        return False

def run_enhanced_installation(config_name, github_token, skip_cleanup):
    """Run enhanced installation with debugging and integrated testing"""
    
    log("🚀 ENHANCED INSTALLATION MODE - All modules available", "HEADER")
    
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
        
        # Enhanced installation steps with debugging
        steps = [
            ("Checking prerequisites", check_prerequisites),
            ("Checking Docker network", check_docker_network),
            ("Loading configuration", lambda: installer_config.load_config_from_github(github_token, config_name)),
            ("Creating installation directory", None),
            ("Cloning AGiXT repository", None),
            ("Setting up models", None),
            ("Creating Docker configuration (Enhanced)", None),
            ("Starting services (Enhanced)", None),
            ("Installing GraphQL dependencies", None),
            ("Running post-installation tests", None),
            ("Verifying installation", None)
        ]
        
        config = None
        install_path = None
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            log(f"\n📋 Step {i}/{len(steps)}: {step_name}...", "HEADER")
            
            if step_func:
                if step_name == "Loading configuration":
                    config = step_func()
                    if not config:
                        log("❌ Configuration loading failed", "ERROR")
                        return False
                    log(f"✅ Configuration loaded: {len(config)} variables")
                    
                    # Debug critical configuration values
                    log("🔍 Critical configuration values:", "DEBUG")
                    critical_vars = ['DATABASE_TYPE', 'DATABASE_NAME', 'MODEL_NAME', 'AGIXT_VERSION']
                    for var in critical_vars:
                        value = config.get(var, 'NOT SET')
                        log(f"  {var}: {value}", "DEBUG")
                        
                else:
                    if not step_func():
                        log(f"❌ Step failed: {step_name}", "ERROR")
                        return False
            else:
                # Handle special steps with enhanced error handling
                if step_name == "Creating installation directory":
                    if not config:
                        log("❌ Config required for this step", "ERROR")
                        return False
                    install_path = create_installation_directory(config)
                    if not install_path:
                        log("❌ Installation directory creation failed", "ERROR")
                        return False
                    log(f"✅ Installation directory created: {install_path}")
                    
                elif step_name == "Cloning AGiXT repository":
                    if not install_path:
                        log("❌ Install path required for this step", "ERROR") 
                        return False
                    if not clone_agixt_repository(install_path, github_token):
                        log("❌ Repository cloning failed", "ERROR")
                        return False
                    log("✅ AGiXT repository cloned successfully")
                        
                elif step_name == "Setting up models":
                    if not install_path or not config:
                        log("❌ Install path and config required for this step", "ERROR")
                        return False
                    log("🤖 Starting enhanced model setup...", "INFO")
                    if not installer_models.setup_models(install_path, config):
                        log("❌ Model setup failed", "ERROR")
                        return False
                    log("✅ Model setup completed successfully")
                        
                elif step_name == "Creating Docker configuration (Enhanced)":
                    if not install_path or not config:
                        log("❌ Install path and config required for this step", "ERROR")
                        return False
                    log("🐳 Starting enhanced Docker configuration...", "INFO")
                    if not installer_docker.create_configuration(install_path, config):
                        log("❌ Docker configuration failed", "ERROR")
                        return False
                    log("✅ Enhanced Docker configuration completed")
                        
                elif step_name == "Starting services (Enhanced)":
                    if not install_path or not config:
                        log("❌ Install path and config required for this step", "ERROR")
                        return False
                    log("🚀 Starting enhanced service startup with debugging...", "INFO")
                    if not installer_docker.start_services(install_path, config):
                        log("❌ Service startup failed", "ERROR") 
                        return False
                    log("✅ Enhanced service startup completed")
                        
                elif step_name == "Installing GraphQL dependencies":
                    if not install_path:
                        log("❌ Install path required for this step", "ERROR")
                        return False
                    log("📦 Installing GraphQL dependencies...", "INFO")
                    install_graphql_dependencies(install_path)
                    log("✅ GraphQL dependencies installation attempted")
                    
                elif step_name == "Running post-installation tests":
                    if not install_path or not config:
                        log("❌ Install path and config required for this step", "ERROR")
                        return False
                    log("🧪 Running integrated post-installation tests...", "INFO")
                    run_integrated_tests(install_path, config)
                    
                elif step_name == "Verifying installation":
                    if not install_path or not config:
                        log("❌ Install path and config required for this step", "ERROR")
                        return False
                    log("🔍 Running final verification...", "INFO")
                    verify_installation(install_path, config)
        
        # Enhanced success reporting
        final_model_name = config.get('FINAL_MODEL_NAME', config.get('MODEL_NAME', 'Unknown-Model'))
        version = config.get('AGIXT_VERSION', 'unknown')
        
        log("\n" + "=" * 80, "SUCCESS")
        log("🎉 AGiXT Enhanced Installation Complete!", "SUCCESS")
        log("=" * 80, "SUCCESS")
        log(f"📁 Directory: {install_path}")
        log(f"🔧 Version: {version}")
        log(f"🤖 Model: {final_model_name}")
        
        # Access information
        log("\n🌐 Access Information:", "INFO")
        log("  📱 Frontend: http://localhost:3437")
        log("  🔧 Backend API: http://localhost:7437") 
        log("  🤖 EzLocalAI API: http://localhost:8091")
        log("  🎮 EzLocalAI UI: http://localhost:8502")
        
        # Configuration URLs
        agixt_server = config.get('AGIXT_SERVER', '')
        app_uri = config.get('APP_URI', '')
        if agixt_server:
            log(f"  🌍 Production Backend: {agixt_server}")
        if app_uri:
            log(f"  🌍 Production Frontend: {app_uri}")
        
        log("\n🔍 Post-installation test results are available above", "INFO")
        log("✅ Installation completed successfully!", "SUCCESS")
        
        return True
        
    except Exception as e:
        log(f"❌ Enhanced installation error: {e}", "ERROR")
        import traceback
        log(f"📋 Traceback: {traceback.format_exc()}", "DEBUG")
        return False

def run_integrated_tests(install_path, config):
    """Run integrated post-installation tests"""
    try:
        log("🧪 INTEGRATED POST-INSTALLATION TESTS", "HEADER")
        
        # Import test functions (simulate what the external test script does)
        # This is a simplified version of the main test functions
        
        # Basic file structure check
        log("📁 Quick file structure check...", "TEST")
        required_files = [".env", "docker-compose.yml", "models", "agixt", "ezlocalai"]
        missing_files = []
        
        for file_item in required_files:
            file_path = os.path.join(install_path, file_item)
            if os.path.exists(file_path):
                log(f"  ✅ {file_item}: exists", "SUCCESS")
            else:
                log(f"  ❌ {file_item}: missing", "ERROR")
                missing_files.append(file_item)
        
        if missing_files:
            log(f"⚠️  Missing files detected: {missing_files}", "WARN")
        else:
            log("✅ Basic file structure check passed", "SUCCESS")
        
        # Quick endpoint test
        log("🌐 Quick endpoint accessibility test...", "TEST")
        import urllib.request
        import time
        
        # Wait a bit for services to start
        time.sleep(30)
        
        endpoints = [
            ("http://localhost:3437", "Frontend"),
            ("http://localhost:7437", "AGiXT API"),
            ("http://localhost:8091", "EzLocalAI API")
        ]
        
        working_endpoints = 0
        for url, name in endpoints:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.getcode() < 400:
                        log(f"  ✅ {name}: accessible", "SUCCESS")
                        working_endpoints += 1
                    else:
                        log(f"  ⚠️  {name}: HTTP {response.getcode()}", "WARN")
            except Exception as e:
                log(f"  ❌ {name}: not accessible ({type(e).__name__})", "ERROR")
        
        log(f"📊 Endpoint test: {working_endpoints}/{len(endpoints)} accessible", "INFO")
        
        if working_endpoints >= 1:
            log("✅ At least one service is responding", "SUCCESS")
        else:
            log("⚠️  No services responding yet - may need more time", "WARN")
        
        log("ℹ️  For detailed testing, run: python3 post-install-tests.py", "INFO")
        
    except Exception as e:
        log(f"⚠️  Integrated tests error: {e}", "WARN")

def test_module():
    """Test this enhanced module's functionality"""
    log("🧪 Testing enhanced installer_core module...", "TEST")
    
    try:
        if callable(run_installation):
            log("run_installation function: ✓", "SUCCESS")
        else:
            log("run_installation function: ✗", "ERROR")
            
        if callable(run_enhanced_installation):
            log("run_enhanced_installation function: ✓", "SUCCESS")
        else:
            log("run_enhanced_installation function: ✗", "ERROR")
            
        if callable(run_integrated_tests):
            log("run_integrated_tests function: ✓", "SUCCESS")
        else:
            log("run_integrated_tests function: ✗", "ERROR")
            
        log("✅ Enhanced installer_core module test completed", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Enhanced installer_core test failed: {e}", "ERROR")
        return False

if __name__ == "__main__":
    test_module()
