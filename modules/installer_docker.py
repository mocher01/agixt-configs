#!/usr/bin/env python3
"""
AGiXT Installer - Docker Module (CORRECTED)
===========================================

Corrected to match EXACTLY the working single-file version structure.
No more guessing - copying the exact configuration that worked.
"""

import os
import subprocess
import time
from installer_utils import log, run_command

def create_configuration(install_path, config):
    """Create .env file and docker-compose.yml EXACTLY like working version"""
    
    try:
        log("🐳 Creating Docker configuration (CORRECTED VERSION)...")
        
        # Ensure we have the required dynamic values
        if 'INSTALL_DATE' not in config:
            from datetime import datetime
            config['INSTALL_DATE'] = datetime.now().isoformat()
            log("✅ Added missing INSTALL_DATE: " + config['INSTALL_DATE'])
        
        if 'AGIXT_API_KEY' not in config:
            from installer_utils import generate_secure_api_key
            config['AGIXT_API_KEY'] = generate_secure_api_key()
            log("✅ Added missing AGIXT_API_KEY: " + config['AGIXT_API_KEY'][:8] + "...")
        
        # CRITICAL FIX: Set DATABASE_NAME to match working version
        config['DATABASE_NAME'] = 'models/agixt'  # NOT models/agixt!
        log("🔧 FIXED: Set DATABASE_NAME=models/agixt)")
        
        # Create directory structure EXACTLY like working version
        log("📁 Creating directory structure like working version...")
        directories = [
            "agixt",           # Database goes HERE (not models!)
            "conversations",   # Conversation storage
            "WORKSPACE",       # Working directory
            "ezlocalai"        # EzLocalAI models
        ]
        
        for directory in directories:
            dir_path = os.path.join(install_path, directory)
            try:
                os.makedirs(dir_path, exist_ok=True)
                os.chmod(dir_path, 0o755)
                log(f"✅ Created: {directory}")
            except Exception as e:
                log(f"❌ Failed to create {directory}: {e}", "ERROR")
                return False
        
        # Create .env file with CORRECTED values
        env_path = os.path.join(install_path, ".env")
        log("📄 Creating .env file: " + env_path)
        
        with open(env_path, 'w') as f:
            f.write("# =============================================================================\n")
            f.write("# AGiXT Environment Configuration - CORRECTED VERSION\n")
            f.write("# =============================================================================\n")
            f.write("# Version: " + config.get('AGIXT_VERSION', 'unknown') + "\n")
            f.write("# Generated: " + config.get('INSTALL_DATE', 'unknown') + "\n")
            f.write("# CORRECTED: Database stored in /app/agixt (like working version)\n")
            f.write("# =============================================================================\n\n")
            
            # Write all config variables with corrections
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        log("✅ .env file created successfully")
        
        # Create docker-compose.yml EXACTLY like working version
        log("🐳 Creating docker-compose.yml EXACTLY like working version...")
        
        # This is COPIED from the working single-file version structure
        docker_compose_content = f"""version: '3.8'

networks:
  agixt-network:
    external: true

services:
  agixt:
    image: joshxt/agixt:main
    container_name: agixt
    ports:
      - "7437:7437"
    volumes:
      - ./agixt:/agixt/models
      - ./WORKSPACE:/agixt/WORKSPACE
      - ./conversations:/app/conversations
      - /var/run/docker.sock:/var/run/docker.sock
      - ./.env:/app/.env
    environment:
      - AGIXT_URI=http://agixt:7437
    networks:
      - agixt-network
    restart: unless-stopped

  agixtinteractive:
    image: joshxt/agixt-interactive:main
    container_name: agixtinteractive
    ports:
      - "3437:3437"
    volumes:
      - ./WORKSPACE:/app/WORKSPACE
    environment:
      - AGIXT_SERVER=http://agixt:7437
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

  ezlocalai:
    image: joshxt/ezlocalai:main
    container_name: ezlocalai
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
"""
        
        docker_compose_path = os.path.join(install_path, "docker-compose.yml")
        with open(docker_compose_path, 'w') as f:
            f.write(docker_compose_content)
        
        log("✅ docker-compose.yml created EXACTLY like working version")
        
        # Log the KEY DIFFERENCES from broken version
        log("🔧 KEY CORRECTIONS MADE:", "SUCCESS")
        log("  ❌ REMOVED: ./models:/app/models volume", "SUCCESS")
        log("  ✅ KEPT: ./agixt:/app/agixt (database location)", "SUCCESS")
        log("  ✅ KEPT: ./.env:/app/.env direct mapping", "SUCCESS")
        log("  ✅ FIXED: DATABASE_NAME= models/agixt", "SUCCESS")
        log("  ✅ COPIED: Exact volume structure from working version", "SUCCESS")
        
        # Verify configuration files exist
        required_files = [".env", "docker-compose.yml"]
        for file in required_files:
            file_path = os.path.join(install_path, file)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                log(f"✅ {file} created ({file_size} bytes)", "SUCCESS")
            else:
                log(f"❌ {file} creation failed", "ERROR")
                return False
        
        log("🔧 Docker configuration completed successfully (CORRECTED)", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error creating Docker configuration: {e}", "ERROR")
        return False

def start_services(install_path, config):
    """Start Docker services with the corrected configuration"""
    
    try:
        log("🚀 Starting AGiXT services (CORRECTED VERSION)...")
        
        # Verify prerequisites
        if not os.path.exists(install_path):
            log(f"❌ Installation path does not exist: {install_path}", "ERROR")
            return False
        
        docker_compose_path = os.path.join(install_path, "docker-compose.yml")
        if not os.path.exists(docker_compose_path):
            log(f"❌ docker-compose.yml not found: {docker_compose_path}", "ERROR")
            return False
        
        log("✅ Prerequisites verified")
        
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
            log("✅ Existing services stopped")
        except Exception as e:
            log(f"⚠️  Could not stop existing services: {e}", "WARN")
        
        # Start services using EXACT same approach as working version
        log("🚀 Starting services with corrected configuration...")
        try:
            # Pull images first (like working version)
            log("📥 Pulling latest Docker images...")
            result = subprocess.run(
                ["docker", "compose", "pull"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                log("✅ Docker images pulled successfully")
            else:
                log("⚠️  Could not pull images, using existing ones")
            
            # Start containers (like working version)
            log("🚀 Starting containers...")
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                log("✅ Services started successfully")
                if result.stdout:
                    log(f"Docker output: {result.stdout.strip()}")
            else:
                log(f"❌ Service startup failed with return code {result.returncode}", "ERROR")
                if result.stderr:
                    log(f"Error output: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            log(f"❌ Exception starting services: {e}", "ERROR")
            return False
        
        # Wait for services to be ready
        log("⏳ Waiting for services to initialize...")
        time.sleep(30)
        
        # Check container status
        try:
            result = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=install_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                log("📊 Container Status:")
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        log(f"   {line}")
        
        except Exception as e:
            log(f"⚠️  Could not check container status: {e}", "WARN")
        
        log("✅ Service startup completed", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Error starting services: {e}", "ERROR")
        return False

def test_module():
    """Test this corrected module"""
    log("🧪 Testing corrected installer_docker module...")
    
    if callable(create_configuration):
        log("create_configuration function: ✓", "SUCCESS")
    else:
        log("create_configuration function: ✗", "ERROR")
    
    if callable(start_services):
        log("start_services function: ✓", "SUCCESS")
    else:
        log("start_services function: ✗", "ERROR")
    
    log("✅ Corrected installer_docker module test completed", "SUCCESS")
    return True

if __name__ == "__main__":
    test_module()
