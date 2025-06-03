#!/usr/bin/env python3
"""
AGiXT Installer - Docker Module (Enhanced with Deep Debugging)
==============================================================

Handles Docker configuration and service management.
Enhanced version with comprehensive debugging to understand
why AGiXT API fails independently of EzLocalAI issues.
"""

import os
import subprocess
import time
from installer_utils import log, run_command

def debug_environment_config(config):
    """Debug environment configuration to identify issues"""
    log("🔍 DEBUGGING ENVIRONMENT CONFIGURATION", "HEADER")
    
    critical_vars = [
        'DATABASE_TYPE', 'DATABASE_NAME', 'LOG_LEVEL', 'AGIXT_BRANCH',
        'AGIXT_VERSION', 'INSTALL_BASE_PATH', 'WORKING_DIRECTORY'
    ]
    
    for var in critical_vars:
        value = config.get(var, 'NOT SET')
        log(f"🔧 {var}: {value}", "INFO")
    
    # Check database configuration specifically
    db_type = config.get('DATABASE_TYPE', 'sqlite')
    db_name = config.get('DATABASE_NAME', 'models/agixt')
    
    log(f"📊 Database Analysis:", "INFO")
    log(f"  Type: {db_type}", "INFO")
    log(f"  Name/Path: {db_name}", "INFO")
    
    if db_type == 'sqlite':
        log("🔍 SQLite database detected - checking path requirements", "WARN")
        if not db_name.startswith('/'):
            log("  ⚠️  Relative database path detected", "WARN")
            log(f"  Expected location inside container: /app/{db_name}", "INFO")
    
    return True

def create_debug_docker_compose(install_path, config):
    """Create docker-compose.yml with debugging features"""
    log("🐳 Creating DEBUG docker-compose.yml based on working version analysis...", "INFO")
    
    # Analyze what the working version might have used
    working_directory = config.get('WORKING_DIRECTORY', './WORKSPACE')
    db_name = config.get('DATABASE_NAME', 'models/agixt')
    
    log(f"📁 Working directory: {working_directory}", "INFO")
    log(f"💾 Database path: {db_name}", "INFO")
    
    # Create a simplified version closer to the working single-file script
    docker_compose_content = f"""# AGiXT Docker Compose - Debug Version
# Based on analysis of working single-file installation
version: '3.8'

networks:
  agixt-network:
    external: true

services:
  # AGiXT Main Service - Focus on getting this working first
  agixt:
    image: joshxt/agixt:main
    container_name: agixt
    hostname: agixt
    ports:
      - "7437:7437"
    volumes:
      # Key volume mappings based on working version analysis
      - ./agixt:/app/agixt
      - ./models:/app/models          # For database
      - ./WORKSPACE:/app/WORKSPACE    # Working directory
      - ./conversations:/app/conversations
      - ./.env:/app/.env             # Environment configuration
    environment:
      # Critical environment variables for debugging
      - DATABASE_TYPE=${{DATABASE_TYPE}}
      - DATABASE_NAME=${{DATABASE_NAME}}
      - LOG_LEVEL=DEBUG              # Force debug logging
      - AGIXT_BRANCH=${{AGIXT_BRANCH}}
      - WORKING_DIRECTORY=${{WORKING_DIRECTORY}}
    networks:
      - agixt-network
    restart: unless-stopped
    # Remove health checks initially to focus on basic startup
    # healthcheck:
    #   test: ["CMD-SHELL", "curl -f http://localhost:7437/api/status || exit 1"]

  # AGiXT Interactive Frontend
  agixtinteractive:
    image: joshxt/agixt-interactive:main
    container_name: agixtinteractive
    hostname: agixtinteractive
    ports:
      - "3437:3437"
    volumes:
      - ./WORKSPACE:/app/WORKSPACE
    environment:
      - AGIXT_SERVER=${{AGIXT_URI}}
      - APP_NAME=${{APP_NAME}}
      - APP_DESCRIPTION=${{APP_DESCRIPTION}}
      - AGIXT_AGENT=${{AGIXT_AGENT}}
      - INTERACTIVE_MODE=${{INTERACTIVE_MODE}}
      - THEME_NAME=${{THEME_NAME}}
    networks:
      - agixt-network
    depends_on:
      - agixt
    restart: unless-stopped

  # EzLocalAI - Separate and optional for now
  ezlocalai:
    image: joshxt/ezlocalai:main
    container_name: ezlocalai
    hostname: ezlocalai
    ports:
      - "8091:8091"
      - "8502:8502"
    volumes:
      - ./ezlocalai:/app/models
      - ./WORKSPACE:/app/WORKSPACE
    environment:
      - DEFAULT_MODEL=${{DEFAULT_MODEL}}
      - LLM_MAX_TOKENS=${{LLM_MAX_TOKENS}}
      - THREADS=${{THREADS}}
      - GPU_LAYERS=${{GPU_LAYERS}}
      - AUTO_UPDATE=${{AUTO_UPDATE}}
    networks:
      - agixt-network
    restart: unless-stopped
    # Make this optional - don't let it block AGiXT
    # depends_on:
    #   - agixt
"""
    
    docker_compose_path = os.path.join(install_path, "docker-compose.yml")
    with open(docker_compose_path, 'w') as f:
        f.write(docker_compose_content)
    
    log("✅ Debug docker-compose.yml created", "SUCCESS")
    log("🔍 Key changes from original:", "INFO")
    log("  - Simplified structure", "INFO")
    log("  - DEBUG logging enabled", "INFO")
    log("  - Removed health checks initially", "INFO")
    log("  - Made EzLocalAI independent", "INFO")
    log("  - Direct .env mapping", "INFO")
    
    return True

def create_debug_directories(install_path, config):
    """Create all required directories with proper structure"""
    log("📁 Creating directory structure for debugging...", "INFO")
    
    directories = [
        "models",           # Critical for AGiXT database
        "agixt",           # AGiXT application data
        "conversations",   # Conversation storage
        "WORKSPACE",       # Working directory
        "ezlocalai"        # EzLocalAI models (separate)
    ]
    
    for directory in directories:
        dir_path = os.path.join(install_path, directory)
        try:
            os.makedirs(dir_path, exist_ok=True)
            # Set proper permissions
            os.chmod(dir_path, 0o755)
            log(f"✅ Created: {directory}", "SUCCESS")
        except Exception as e:
            log(f"❌ Failed to create {directory}: {e}", "ERROR")
            return False
    
    # Verify directory structure
    log("🔍 Verifying directory structure:", "INFO")
    for directory in directories:
        dir_path = os.path.join(install_path, directory)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            log(f"  ✅ {directory}: exists", "SUCCESS")
        else:
            log(f"  ❌ {directory}: missing", "ERROR")
    
    return True

def create_configuration(install_path, config):
    """Create .env file and docker-compose.yml with debugging"""
    
    try:
        log("🐳 Creating Docker configuration with enhanced debugging...", "HEADER")
        
        # Debug the configuration first
        debug_environment_config(config)
        
        # Ensure we have the required dynamic values
        if 'INSTALL_DATE' not in config:
            from datetime import datetime
            config['INSTALL_DATE'] = datetime.now().isoformat()
            log("✅ Added missing INSTALL_DATE: " + config['INSTALL_DATE'])
        
        if 'AGIXT_API_KEY' not in config:
            from installer_utils import generate_secure_api_key
            config['AGIXT_API_KEY'] = generate_secure_api_key()
            log("✅ Added missing AGIXT_API_KEY: " + config['AGIXT_API_KEY'][:8] + "...")
        
        # Create directory structure first
        if not create_debug_directories(install_path, config):
            log("❌ Failed to create directory structure", "ERROR")
            return False
        
        # Create enhanced .env file
        env_path = os.path.join(install_path, ".env")
        log("📄 Creating enhanced .env file: " + env_path)
        
        with open(env_path, 'w') as f:
            f.write("# =============================================================================\n")
            f.write("# AGiXT Environment Configuration - DEBUG VERSION\n")
            f.write("# =============================================================================\n")
            f.write("# Version: " + config.get('AGIXT_VERSION', 'unknown') + "\n")
            f.write("# Generated: " + config.get('INSTALL_DATE', 'unknown') + "\n")
            f.write("# DEBUG MODE: Enhanced logging and debugging enabled\n")
            f.write("# =============================================================================\n\n")
            
            # Force debug settings
            debug_overrides = {
                'LOG_LEVEL': 'DEBUG',
                'LOG_FORMAT': '%(asctime)s | %(levelname)s | %(message)s',
                'DATABASE_TYPE': 'sqlite',
                'DATABASE_NAME': 'models/agixt'
            }
            
            # Write all config variables
            for key, value in config.items():
                # Apply debug overrides
                if key in debug_overrides:
                    actual_value = debug_overrides[key]
                    f.write(f"{key}={actual_value}\n")
                    if str(value) != actual_value:
                        f.write(f"# Original {key} was: {value}\n")
                else:
                    f.write(f"{key}={value}\n")
            
            # Add debug-specific variables
            f.write("\n# DEBUG VARIABLES\n")
            f.write("AGIXT_DEBUG=true\n")
            f.write("PYTHONUNBUFFERED=1\n")
        
        log("✅ Enhanced .env file created successfully", "SUCCESS")
        
        # Create debug docker-compose.yml
        if not create_debug_docker_compose(install_path, config):
            log("❌ Failed to create docker-compose.yml", "ERROR")
            return False
        
        # Verify configuration files
        required_files = [".env", "docker-compose.yml"]
        for file in required_files:
            file_path = os.path.join(install_path, file)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                log(f"✅ {file} created ({file_size} bytes)", "SUCCESS")
            else:
                log(f"❌ {file} creation failed", "ERROR")
                return False
        
        log("🔧 Docker configuration completed successfully", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error creating Docker configuration: {e}", "ERROR")
        return False

def start_services_with_debugging(install_path, config):
    """Start Docker services with enhanced debugging and monitoring"""
    
    try:
        log("🚀 Starting AGiXT services with enhanced debugging...", "HEADER")
        
        # Verify prerequisites
        if not os.path.exists(install_path):
            log(f"❌ Installation path does not exist: {install_path}", "ERROR")
            return False
        
        docker_compose_path = os.path.join(install_path, "docker-compose.yml")
        if not os.path.exists(docker_compose_path):
            log(f"❌ docker-compose.yml not found: {docker_compose_path}", "ERROR")
            return False
        
        log("✅ Prerequisites verified", "SUCCESS")
        
        # Stop any existing services
        log("🛑 Stopping any existing services...")
        try:
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            log("✅ Existing services stopped", "SUCCESS")
        except Exception as e:
            log(f"⚠️  Could not stop existing services: {e}", "WARN")
        
        # Start services with debugging
        log("🚀 Starting services in debug mode...")
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                log("✅ Services started successfully", "SUCCESS")
                if result.stdout:
                    log(f"Docker output: {result.stdout.strip()}", "INFO")
            else:
                log(f"❌ Service startup failed with return code {result.returncode}", "ERROR")
                if result.stderr:
                    log(f"Error output: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            log(f"❌ Exception starting services: {e}", "ERROR")
            return False
        
        # Enhanced monitoring of service startup
        log("🔍 Monitoring service startup with detailed logging...", "INFO")
        
        # Wait and monitor each service
        services = ['agixt', 'agixtinteractive', 'ezlocalai']
        
        for i in range(12):  # 2 minutes of monitoring
            time.sleep(10)
            log(f"⏳ Monitoring round {i+1}/12 (after {(i+1)*10} seconds)...", "INFO")
            
            # Check container status
            try:
                result = subprocess.run(
                    ["docker", "compose", "ps", "--format", "table"],
                    cwd=install_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    log("📊 Container Status:", "INFO")
                    for line in result.stdout.split('\n'):
                        if line.strip() and 'NAME' not in line:
                            log(f"  {line}", "INFO")
                
            except Exception as e:
                log(f"⚠️  Could not check container status: {e}", "WARN")
            
            # Check AGiXT logs specifically
            try:
                agixt_result = subprocess.run(
                    ["docker", "compose", "logs", "agixt", "--tail", "5"],
                    cwd=install_path,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if agixt_result.returncode == 0 and agixt_result.stdout:
                    log("📋 Recent AGiXT logs:", "INFO")
                    for line in agixt_result.stdout.split('\n')[-3:]:
                        if line.strip():
                            log(f"  {line}", "INFO")
                
            except Exception as e:
                log(f"⚠️  Could not get AGiXT logs: {e}", "WARN")
            
            # Test AGiXT API
            try:
                import urllib.request
                req = urllib.request.Request("http://localhost:7437/api/status")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.getcode() == 200:
                        log("🎉 AGiXT API is responding!", "SUCCESS")
                        break
            except Exception:
                log(f"⏳ AGiXT API not ready yet...", "INFO")
        
        log("🔍 Final service verification...", "INFO")
        
        # Final container status
        try:
            result = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=install_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log("📊 Final Container Status:", "SUCCESS")
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        log(f"  {line}", "INFO")
        
        except Exception as e:
            log(f"⚠️  Final verification failed: {e}", "WARN")
        
        log("✅ Service startup monitoring completed", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error in service startup: {e}", "ERROR")
        return False

# Alias for compatibility
start_services = start_services_with_debugging

def test_module():
    """Test this module's functionality"""
    log("🧪 Testing enhanced installer_docker module...", "TEST")
    
    if callable(create_configuration):
        log("create_configuration function: ✓", "SUCCESS")
    else:
        log("create_configuration function: ✗", "ERROR")
    
    if callable(start_services_with_debugging):
        log("start_services_with_debugging function: ✓", "SUCCESS")
    else:
        log("start_services_with_debugging function: ✗", "ERROR")
    
    log("✅ Enhanced installer_docker module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
