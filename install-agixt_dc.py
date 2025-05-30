#!/usr/bin/env python3
"""
AGiXT Automated Installer - VERSION 1 (Docker-compose override)
===============================================================

Cette version modifie le docker-compose.yml pour passer TOUTES les variables .env
aux containers, résolvant ainsi le problème d'interface management.

Usage:
  curl -H "Authorization: token YOUR_TOKEN" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt_dc.py | python3 - CONFIG_NAME GITHUB_TOKEN

Example:
  curl -H "Authorization: token github_pat_xxx" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt_dc.py | python3 - AGIXT_0530_1239_4 github_pat_xxx

Features:
- ✅ Configuration complète intégrée (pas de téléchargement externe)
- ✅ Modification docker-compose.yml pour passer toutes variables
- ✅ Interface management complète activée
- ✅ Thème doom et fonctionnalités avancées
- ✅ Compatible curl pipe
"""

import os
import sys
import subprocess
import time
import shutil
from datetime import datetime
from typing import Dict, Optional, List
import tempfile
import json


def run_command(command: str, cwd: Optional[str] = None, timeout: int = 300) -> bool:
    """Execute a shell command with proper error handling"""
    try:
        print(f"ℹ️  Running: {command}")
        result = subprocess.run(
            command.split(), 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        
        if result.returncode == 0:
            return True
        else:
            print(f"❌ Command failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        return False


def check_prerequisites() -> bool:
    """Check if all required tools are installed"""
    tools = {
        'git': 'git --version',
        'docker': 'docker --version', 
        'docker-compose': 'docker compose version'
    }
    
    for tool, command in tools.items():
        if run_command(command):
            print(f"✅ {tool.title()} ✓")
        else:
            print(f"❌ {tool.title()} not found or not working")
            return False
    
    return True


def cleanup_previous_installations():
    """Clean up any previous AGiXT installations"""
    base_path = "/var/apps"
    
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
        return
    
    for item in os.listdir(base_path):
        if item.startswith("AGIXT_"):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                print(f"🗑️  Cleaning up {item_path}")
                
                # Stop docker services if they exist
                compose_file = os.path.join(item_path, "docker-compose.yml")
                if os.path.exists(compose_file):
                    subprocess.run(
                        ["docker", "compose", "-f", compose_file, "down"], 
                        cwd=item_path,
                        capture_output=True
                    )
                
                # Remove directory
                shutil.rmtree(item_path, ignore_errors=True)


def create_installation_directory(config_name: str) -> Optional[str]:
    """Create the installation directory with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    install_path = f"/var/apps/{config_name}_{timestamp}"
    
    try:
        os.makedirs(install_path, exist_ok=True)
        print(f"📁 Created installation directory: {install_path}")
        return install_path
    except Exception as e:
        print(f"❌ Failed to create directory {install_path}: {e}")
        return None


def clone_agixt_repository(install_path: str, github_token: Optional[str] = None) -> bool:
    """Clone the AGiXT repository"""
    try:
        if github_token:
            repo_url = f"https://{github_token}@github.com/Josh-XT/AGiXT.git"
        else:
            repo_url = "https://github.com/Josh-XT/AGiXT.git"
        
        result = subprocess.run(
            ["git", "clone", repo_url, "."],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ AGiXT repository cloned successfully")
            return True
        else:
            print(f"❌ Failed to clone repository: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error cloning repository: {e}")
        return False


def get_env_config() -> Dict[str, str]:
    """Get the .env configuration - embedded in script"""
    return {
        # Configuration de base
        'AGIXT_AUTO_UPDATE': 'true',
        'AGIXT_API_KEY': '',
        'UVICORN_WORKERS': '10',
        'WORKING_DIRECTORY': './WORKSPACE',
        'TEXTGEN_URI': 'http://text-generation-webui:5000',
        'AGIXT_URI': 'http://agixt:7437',
        'TZ': 'Europe/Paris',
        'AGIXT_SERVER': 'http://162.55.213.90:7437',
        
        # Interface complète
        'APP_NAME': 'AGiXT Production Server',
        'APP_DESCRIPTION': 'AGiXT Production Server - AI Agent Automation Platform',
        'APP_URI': 'http://162.55.213.90:3437',
        'AUTH_WEB': 'http://162.55.213.90:3437/user',
        'AGIXT_AGENT': 'XT',
        'AGIXT_SHOW_SELECTION': 'agent,conversation',
        'AGIXT_SHOW_AGENT_BAR': 'true',
        'AGIXT_SHOW_APP_BAR': 'true',
        'AGIXT_CONVERSATION_MODE': 'select',
        'THEME_NAME': 'doom',
        'AGIXT_FOOTER_MESSAGE': 'AGiXT Production Server - Powered by AI',
        
        # Fonctionnalités avancées
        'AGIXT_FILE_UPLOAD_ENABLED': 'true',
        'AGIXT_VOICE_INPUT_ENABLED': 'true',
        'AGIXT_RLHF': 'true',
        'AGIXT_ALLOW_MESSAGE_EDITING': 'true',
        'AGIXT_ALLOW_MESSAGE_DELETION': 'true',
        'AGIXT_SHOW_OVERRIDE_SWITCHES': 'tts,websearch,analyze-user-input',
        'INTERACTIVE_MODE': 'chat',
        
        # Création agents automatique
        'CREATE_AGENT_ON_REGISTER': 'true',
        'CREATE_AGIXT_AGENT': 'true',
        'AUTH_PROVIDER': 'magicalauth',
        'ALLOW_EMAIL_SIGN_IN': 'true',
        
        # Système
        'DATABASE_TYPE': 'sqlite',
        'DATABASE_NAME': 'models/agixt',
        'LOG_LEVEL': 'INFO',
        'LOG_FORMAT': '%(asctime)s | %(levelname)s | %(message)s',
        'ALLOWED_DOMAINS': '*',
        'AGIXT_BRANCH': 'stable',
        'AGIXT_REQUIRE_API_KEY': 'false'
    }


def create_env_file(install_path: str, config: Dict[str, str]) -> bool:
    """Create the .env file with all configurations"""
    env_file = os.path.join(install_path, ".env")
    
    try:
        with open(env_file, 'w') as f:
            f.write("# =============================================================================\n")
            f.write("# AGiXT Server Configuration - AUTO GENERATED\n")
            f.write("# =============================================================================\n")
            f.write(f"# Generated on: {datetime.now().isoformat()}\n")
            f.write("# Configuration: Complete with Interface Management\n")
            f.write("# =============================================================================\n\n")
            
            for key, value in config.items():
                f.write(f"{key}={value}\n")
            
            f.write("\n# =============================================================================\n")
            f.write("# END CONFIGURATION\n")
            f.write("# =============================================================================\n")
        
        print(f"✅ Created .env file with {len(config)} variables")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def setup_permissions(install_path: str):
    """Set up proper permissions for the installation"""
    try:
        subprocess.run(["chmod", "-R", "755", install_path], check=True)
        print("✅ Permissions set successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not set permissions: {e}")


def modify_docker_compose(install_path: str, config: Dict[str, str]) -> bool:
    """Modify docker-compose.yml to pass all our environment variables"""
    compose_file = os.path.join(install_path, "docker-compose.yml")
    
    if not os.path.exists(compose_file):
        print(f"❌ docker-compose.yml not found at {compose_file}")
        return False
    
    try:
        # Read original docker-compose.yml
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Backup original
        backup_file = compose_file + ".backup"
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"📋 Backup created: {backup_file}")
        
        # Create environment variables section for our custom variables
        env_vars = []
        for key, value in config.items():
            env_vars.append(f"      {key}: ${{{key}:-{value}}}")
        
        custom_env_section = "\n".join(env_vars)
        
        # Find agixtinteractive service and add our environment variables
        lines = content.split('\n')
        new_lines = []
        in_agixtinteractive = False
        in_environment = False
        environment_added = False
        
        for line in lines:
            if 'agixtinteractive:' in line and not line.strip().startswith('#'):
                in_agixtinteractive = True
                new_lines.append(line)
            elif in_agixtinteractive and line.strip().startswith('environment:'):
                in_environment = True
                new_lines.append(line)
                # Add our custom environment variables right after environment:
                new_lines.append("      # === CUSTOM CONFIGURATION VARIABLES ===")
                new_lines.append(custom_env_section)
                new_lines.append("      # === END CUSTOM VARIABLES ===")
                environment_added = True
            elif in_agixtinteractive and line.strip() and not line.startswith('  ') and not line.startswith('\t'):
                # We've exited the agixtinteractive service
                in_agixtinteractive = False
                in_environment = False
                new_lines.append(line)
            else:
                new_lines.append(line)
        
        # If we couldn't find environment section, add it
        if in_agixtinteractive and not environment_added:
            print("⚠️  No environment section found in agixtinteractive, adding one")
            # Find the agixtinteractive service and add environment section
            lines = new_lines
            new_lines = []
            for i, line in enumerate(lines):
                new_lines.append(line)
                if 'agixtinteractive:' in line and not line.strip().startswith('#'):
                    # Add environment section after service declaration
                    new_lines.append("    environment:")
                    new_lines.append("      # === CUSTOM CONFIGURATION VARIABLES ===")
                    new_lines.append(custom_env_section)
                    new_lines.append("      # === END CUSTOM VARIABLES ===")
        
        # Write modified docker-compose.yml
        modified_content = '\n'.join(new_lines)
        with open(compose_file, 'w') as f:
            f.write(modified_content)
        
        print(f"✅ Modified docker-compose.yml with {len(config)} environment variables")
        return True
        
    except Exception as e:
        print(f"❌ Failed to modify docker-compose.yml: {e}")
        return False


def start_agixt_services(install_path: str) -> bool:
    """Start AGiXT services using docker-compose"""
    try:
        os.chdir(install_path)
        
        # Always use default docker-compose.yml
        compose_file = "docker-compose.yml"
        
        print(f"🚀 Starting AGiXT services...")
        result = subprocess.run(
            ["docker", "compose", "-f", compose_file, "up", "-d"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ AGiXT services started successfully")
            print(f"📝 Output: {result.stdout}")
            
            # Wait for services to be ready
            time.sleep(15)
            
            # Check service status
            ps_result = subprocess.run(
                ["docker", "compose", "ps"], 
                capture_output=True, 
                text=True
            )
            print(f"📊 Service status:\n{ps_result.stdout}")
            
            return True
        else:
            print(f"❌ Failed to start services:")
            print(f"📝 Error: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout starting AGiXT services (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error starting AGiXT services: {e}")
        return False


def verify_installation(install_path: str):
    """Verify the installation is working"""
    print("\n🔍 Verifying installation...")
    
    # Check if containers are running
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "table"],
            cwd=install_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("📊 Container status:")
            print(result.stdout)
        
        # Check if ports are accessible
        import socket
        
        ports_to_check = [3437, 7437]
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                print(f"✅ Port {port} is accessible")
            else:
                print(f"⚠️  Port {port} is not accessible yet")
            sock.close()
            
    except Exception as e:
        print(f"⚠️  Could not verify installation: {e}")


def main():
    """Main installation function"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║            AGiXT Installer - Version 1 (Override)            ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    if len(sys.argv) < 2:
        print("❌ Usage: python3 - CONFIG_NAME [GITHUB_TOKEN]")
        print("📝 Example: curl -sSL script.py | python3 - AGIXT_0530_1239_4 github_token")
        sys.exit(1)
    
    config_name = sys.argv[1]
    github_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"📋 Configuration: {config_name}")
    print(f"🔑 GitHub Token: {'Fourni' if github_token else 'Non fourni'}")
    
    # Check prerequisites
    print("🚀 Checking prerequisites...")
    if not check_prerequisites():
        sys.exit(1)
    
    # Get configuration (embedded in script)
    print(f"\n🔄 Getting configuration...")
    config = get_env_config()
    if not config:
        print("❌ Failed to get configuration")
        sys.exit(1)
    
    # Installation steps
    print("\n🔄 Step 1/6: Cleaning previous installations...")
    cleanup_previous_installations()
    
    install_path = create_installation_directory(config_name)
    if not install_path:
        sys.exit(1)
    
    print(f"\n🔄 Step 2/6: Cloning AGiXT repository...")
    if not clone_agixt_repository(install_path, github_token):
        sys.exit(1)
    
    print(f"\n🔄 Step 3/6: Creating .env file...")
    if not create_env_file(install_path, config):
        sys.exit(1)
    
    print(f"\n🔄 Step 4/6: Setting up permissions...")
    setup_permissions(install_path)
    
    print(f"\n🔄 Step 5/6: Modifying docker-compose.yml...")
    if not modify_docker_compose(install_path, config):
        print("❌ Failed to modify docker-compose.yml")
        sys.exit(1)
    
    print(f"\n🔄 Step 6/6: Starting AGiXT services...")
    if not start_agixt_services(install_path):
        print("❌ Failed to start services")
        sys.exit(1)
    
    print(f"\n✅ Installation completed successfully!")
    print(f"📁 Directory: {install_path}")
    print(f"🌐 AGiXT Interface: http://162.55.213.90:3437")
    print(f"🔧 AGiXT API: http://162.55.213.90:7437")
    print(f"📋 Management: docker compose -C {install_path} ps")
    print(f"📝 Logs: docker compose -C {install_path} logs -f")


if __name__ == "__main__":
    main()
