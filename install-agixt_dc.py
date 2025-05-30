#!/usr/bin/env python3
"""
AGiXT Automated Installer - VERSION 1 (Docker-compose override) + GraphQL Support
==================================================================================

Cette version modifie le docker-compose.yml pour passer TOUTES les variables .env
aux containers ET inclut les fixes GraphQL nécessaires.

Usage:
  curl -H "Authorization: token YOUR_TOKEN" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt_dc.py | python3 - CONFIG_NAME GITHUB_TOKEN

Example:
  curl -H "Authorization: token github_pat_xxx" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt_dc.py | python3 - AGIXT_0530_1239_5 github_pat_xxx

Features:
- ✅ Configuration complète intégrée (pas de téléchargement externe)
- ✅ Modification docker-compose.yml pour passer toutes variables
- ✅ Interface management complète activée
- ✅ Support GraphQL avec dependencies automatiques
- ✅ Thème doom et fonctionnalités avancées
- ✅ Compatible curl pipe
- ✅ Fixes automatiques pour GraphQL endpoint
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
        'AGIXT_REQUIRE_API_KEY': 'false',
        
        # GraphQL Support - NOUVEAU
        'GRAPHIQL': 'true',
        'ENABLE_GRAPHQL': 'true'
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
            f.write("# Configuration: Complete with Interface Management + GraphQL\n")
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


def get_missing_variables() -> Dict[str, str]:
    """Get only the variables that are NOT in the official docker-compose.yml"""
    return {
        # Variables manquantes critiques pour l'interface
        'AGIXT_SHOW_SELECTION': 'agent,conversation',
        'AGIXT_SHOW_AGENT_BAR': 'true',
        'AGIXT_SHOW_APP_BAR': 'true',
        'THEME_NAME': 'doom',
        'AUTH_PROVIDER': 'magicalauth',
        'AUTH_WEB': 'http://162.55.213.90:3437/user',
        
        # Variables agents automatiques
        'CREATE_AGENT_ON_REGISTER': 'true',
        'CREATE_AGIXT_AGENT': 'true',
        
        # Variables système
        'AGIXT_AUTO_UPDATE': 'true',
        'AGIXT_BRANCH': 'stable',
        'AGIXT_REQUIRE_API_KEY': 'false',
        
        # Variables base (pour service agixt)
        'AGIXT_API_KEY': '',
        'UVICORN_WORKERS': '10',
        'WORKING_DIRECTORY': './WORKSPACE',
        'TEXTGEN_URI': 'http://text-generation-webui:5000',
        'AGIXT_URI': 'http://agixt:7437',
        'DATABASE_TYPE': 'sqlite',
        'DATABASE_NAME': 'models/agixt',
        'LOG_LEVEL': 'INFO',
        'LOG_FORMAT': '%(asctime)s | %(levelname)s | %(message)s',
        'ALLOWED_DOMAINS': '*',
        
        # GraphQL Support - NOUVEAU
        'GRAPHIQL': 'true',
        'ENABLE_GRAPHQL': 'true'
    }


def add_missing_variables_to_compose(install_path: str) -> bool:
    """Add ONLY the missing variables to docker-compose.yml"""
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
        
        # Get only missing variables
        missing_vars = get_missing_variables()
        
        # Create environment variables section for missing variables
        env_vars = []
        for key, value in missing_vars.items():
            env_vars.append(f"      {key}: ${{{key}:-{value}}}")
        
        missing_env_section = "\n".join(env_vars)
        
        # Find agixtinteractive service and add missing variables at the END
        lines = content.split('\n')
        new_lines = []
        in_agixtinteractive = False
        added_vars = False
        
        for i, line in enumerate(lines):
            if 'agixtinteractive:' in line and not line.strip().startswith('#'):
                in_agixtinteractive = True
                new_lines.append(line)
            elif in_agixtinteractive and line.strip().startswith('TZ:'):
                # Add our missing variables BEFORE the last TZ line
                new_lines.append("      # === MISSING VARIABLES ADDED ===")
                new_lines.append(missing_env_section)
                new_lines.append("      # === END MISSING VARIABLES ===")
                new_lines.append(line)  # Add the TZ line
                added_vars = True
            elif in_agixtinteractive and line.strip() and not line.startswith('  ') and not line.startswith('\t'):
                # We've exited the agixtinteractive service
                if not added_vars:
                    # Add variables before exiting if we haven't added them yet
                    new_lines.append("      # === MISSING VARIABLES ADDED ===")
                    new_lines.append(missing_env_section)
                    new_lines.append("      # === END MISSING VARIABLES ===")
                in_agixtinteractive = False
                new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Write modified docker-compose.yml
        modified_content = '\n'.join(new_lines)
        with open(compose_file, 'w') as f:
            f.write(modified_content)
        
        print(f"✅ Added {len(missing_vars)} missing variables to docker-compose.yml")
        return True
        
    except Exception as e:
        print(f"❌ Failed to add missing variables: {e}")
        return False


def add_graphql_volume_mount(install_path: str) -> bool:
    """Add volume mount for agixt directory to ensure latest code is used"""
    compose_file = os.path.join(install_path, "docker-compose.yml")
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Check if volume mount already exists
        if './agixt:/agixt' in content:
            print("ℹ️  AGiXT volume mount already exists")
            return True
        
        # Find agixt service volumes section
        lines = content.split('\n')
        new_lines = []
        in_agixt_service = False
        volumes_section_found = False
        
        for line in lines:
            new_lines.append(line)
            
            # Detect agixt service
            if line.strip().startswith('agixt:') and not line.strip().startswith('#'):
                in_agixt_service = True
            elif in_agixt_service and line.strip().startswith('volumes:'):
                volumes_section_found = True
            elif in_agixt_service and volumes_section_found and line.strip().startswith('- ./models:/agixt/models'):
                # Add our volume mount after the models mount
                new_lines.append("      - ./agixt:/agixt  # Mount latest agixt code for GraphQL support")
            elif in_agixt_service and line.strip() and not line.startswith('  ') and not line.startswith('\t') and not line.strip().startswith('-'):
                # We've exited the agixt service
                in_agixt_service = False
                volumes_section_found = False
        
        # Write modified content
        modified_content = '\n'.join(new_lines)
        with open(compose_file, 'w') as f:
            f.write(modified_content)
        
        print("✅ Added AGiXT volume mount for latest code")
        return True
        
    except Exception as e:
        print(f"❌ Failed to add volume mount: {e}")
        return False


def install_graphql_dependencies(install_path: str) -> bool:
    """Install GraphQL dependencies in the AGiXT container after startup"""
    print("🔧 Installing GraphQL dependencies...")
    
    try:
        # Wait for container to be fully ready
        time.sleep(30)
        
        # Get container name
        result = subprocess.run(
            ["docker", "compose", "ps", "-q", "agixt"],
            cwd=install_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("⚠️  Could not find agixt container")
            return False
        
        container_id = result.stdout.strip()
        if not container_id:
            print("⚠️  AGiXT container not running")
            return False
        
        # Install strawberry-graphql
        print("📦 Installing strawberry-graphql...")
        result = subprocess.run(
            ["docker", "exec", container_id, "pip", "install", "strawberry-graphql"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Strawberry GraphQL installed")
        else:
            print(f"⚠️  Warning: Could not install strawberry-graphql: {result.stderr}")
        
        # Install broadcaster
        print("📦 Installing broadcaster...")
        result = subprocess.run(
            ["docker", "exec", container_id, "pip", "install", "broadcaster"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Broadcaster installed")
        else:
            print(f"⚠️  Warning: Could not install broadcaster: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Could not install GraphQL dependencies: {e}")
        return False


def start_agixt_services(install_path: str) -> bool:
    """Start AGiXT services using docker-compose"""
    try:
        os.chdir(install_path)
        
        print(f"🚀 Starting AGiXT services with enhanced configuration...")
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ AGiXT services started successfully")
            print(f"📝 Output: {result.stdout}")
            
            # Install GraphQL dependencies
            print("\n🔧 Installing GraphQL dependencies...")
            install_graphql_dependencies(install_path)
            
            # Wait for services to be ready
            print("⏳ Waiting for services to be ready...")
            time.sleep(45)
            
            # Restart agixt service to load GraphQL dependencies
            print("🔄 Restarting AGiXT service to load GraphQL...")
            restart_result = subprocess.run(
                ["docker", "compose", "restart", "agixt"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if restart_result.returncode == 0:
                print("✅ AGiXT service restarted with GraphQL support")
            else:
                print(f"⚠️  Warning: Could not restart AGiXT service: {restart_result.stderr}")
            
            # Final wait
            time.sleep(30)
            
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
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                print(f"✅ Port {port} is accessible")
            else:
                print(f"⚠️  Port {port} is not accessible yet (services may still be starting)")
            sock.close()
        
        # Test GraphQL endpoint
        print("\n🧪 Testing GraphQL endpoint...")
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request('http://localhost:7437/graphql')
            try:
                response = urllib.request.urlopen(req, timeout=5)
                print("✅ GraphQL endpoint is accessible")
            except urllib.error.HTTPError as e:
                if e.code == 405:  # Method Not Allowed for GET request is expected
                    print("✅ GraphQL endpoint is accessible (GET method not allowed - normal)")
                else:
                    print(f"⚠️  GraphQL endpoint returned HTTP {e.code}")
            except Exception as e:
                print(f"⚠️  GraphQL endpoint not accessible: {e}")
        except ImportError:
            print("⚠️  Could not test GraphQL endpoint (urllib not available)")
            
    except Exception as e:
        print(f"⚠️  Could not verify installation: {e}")


def main():
    """Main installation function"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║          AGiXT Installer - Version 1 (GraphQL Enhanced)      ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    if len(sys.argv) < 2:
        print("❌ Usage: python3 - CONFIG_NAME [GITHUB_TOKEN]")
        print("📝 Example: curl -sSL script.py | python3 - AGIXT_0530_1239_5 github_token")
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
    print("\n🔄 Step 1/8: Cleaning previous installations...")
    cleanup_previous_installations()
    
    install_path = create_installation_directory(config_name)
    if not install_path:
        sys.exit(1)
    
    print(f"\n🔄 Step 2/8: Cloning AGiXT repository...")
    if not clone_agixt_repository(install_path, github_token):
        sys.exit(1)
    
    print(f"\n🔄 Step 3/8: Creating .env file...")
    if not create_env_file(install_path, config):
        sys.exit(1)
    
    print(f"\n🔄 Step 4/8: Setting up permissions...")
    setup_permissions(install_path)
    
    print(f"\n🔄 Step 5/8: Adding missing variables to docker-compose.yml...")
    if not add_missing_variables_to_compose(install_path):
        print("❌ Failed to add missing variables to docker-compose.yml")
        sys.exit(1)
    
    print(f"\n🔄 Step 6/8: Adding GraphQL volume mount...")
    if not add_graphql_volume_mount(install_path):
        print("⚠️  Warning: Could not add GraphQL volume mount")
    
    print(f"\n🔄 Step 7/8: Starting AGiXT services...")
    if not start_agixt_services(install_path):
        print("❌ Failed to start services")
        sys.exit(1)
    
    print(f"\n🔄 Step 8/8: Verifying installation...")
    verify_installation(install_path)
    
    print(f"\n✅ Installation completed successfully!")
    print(f"📁 Directory: {install_path}")
    print(f"🌐 AGiXT Interface: http://162.55.213.90:3437")
    print(f"🔧 AGiXT API: http://162.55.213.90:7437")
    print(f"🧬 GraphQL Endpoint: http://162.55.213.90:7437/graphql")
    print(f"📋 Management: docker compose -C {install_path} ps")
    print(f"📝 Logs: docker compose -C {install_path} logs -f agixt")
    print(f"⚠️  Note: Services may take 1-2 minutes to be fully ready")


if __name__ == "__main__":
    main()
