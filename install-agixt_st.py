#!/usr/bin/env python3
"""
AGiXT Automated Installer - VERSION 2 (start.py officiel)
==========================================================

Cette version utilise le start.py officiel d'AGiXT avec toutes nos options
comme arguments de ligne de commande. C'est la méthode recommandée.

Usage:
  curl -H "Authorization: token YOUR_TOKEN" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt_st.py | python3 - CONFIG_NAME GITHUB_TOKEN

Example:
  curl -H "Authorization: token github_pat_xxx" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt_st.py | python3 - AGIXT_0530_1239_4 github_pat_xxx

Features:
- ✅ Utilise le système officiel start.py d'AGiXT
- ✅ Configuration complète intégrée (pas de téléchargement externe)
- ✅ Toutes options passées comme arguments start.py
- ✅ Interface management complète activée
- ✅ Thème doom et fonctionnalités avancées
- ✅ Compatible curl pipe
- ✅ Méthode recommandée par la documentation AGiXT
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
        'docker-compose': 'docker compose version',
        'python3': 'python3 --version'
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
        'APP_NAME': 'AGiXT Production Server v2',
        'APP_DESCRIPTION': 'AGiXT Production Server v2 - AI Agent Automation Platform',
        'APP_URI': 'http://162.55.213.90:3437',
        'AUTH_WEB': 'http://162.55.213.90:3437/user',
        'AGIXT_AGENT': 'XT',
        'AGIXT_SHOW_SELECTION': 'agent,conversation',
        'AGIXT_SHOW_AGENT_BAR': 'true',
        'AGIXT_SHOW_APP_BAR': 'true',
        'AGIXT_CONVERSATION_MODE': 'select',
        'THEME_NAME': 'doom',
        'AGIXT_FOOTER_MESSAGE': 'AGiXT Production Server v2 - Powered by AI',
        
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
            f.write("# AGiXT Server Configuration - AUTO GENERATED (start.py method)\n")
            f.write("# =============================================================================\n")
            f.write(f"# Generated on: {datetime.now().isoformat()}\n")
            f.write("# Configuration: Complete with start.py official method\n")
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


def start_agixt_services(install_path: str, config: Dict[str, str]) -> bool:
    """Start AGiXT services using the official start.py with all our options"""
    try:
        os.chdir(install_path)
        
        # Construire la commande start.py avec toutes nos options
        cmd = ["python3", "start.py"]
        
        # Ajouter toutes nos variables comme options start.py
        if config.get('THEME_NAME'):
            cmd.extend(["--theme-name", config['THEME_NAME']])
        if config.get('AGIXT_SHOW_SELECTION'):
            cmd.extend(["--agixt-show-selection", config['AGIXT_SHOW_SELECTION']])
        if config.get('INTERACTIVE_MODE'):
            cmd.extend(["--interactive-mode", config['INTERACTIVE_MODE']])
        if config.get('APP_NAME'):
            cmd.extend(["--app-name", config['APP_NAME']])
        if config.get('APP_DESCRIPTION'):
            cmd.extend(["--app-description", config['APP_DESCRIPTION']])
        if config.get('APP_URI'):
            cmd.extend(["--app-uri", config['APP_URI']])
        if config.get('AGIXT_AGENT'):
            cmd.extend(["--agixt-agent", config['AGIXT_AGENT']])
        if config.get('AGIXT_SHOW_AGENT_BAR') == 'true':
            cmd.extend(["--agixt-show-agent-bar", "true"])
        if config.get('AGIXT_SHOW_APP_BAR') == 'true':
            cmd.extend(["--agixt-show-app-bar", "true"])
        if config.get('AGIXT_CONVERSATION_MODE'):
            cmd.extend(["--agixt-conversation-mode", config['AGIXT_CONVERSATION_MODE']])
        if config.get('AGIXT_FILE_UPLOAD_ENABLED') == 'true':
            cmd.extend(["--agixt-file-upload-enabled", "true"])
        if config.get('AGIXT_VOICE_INPUT_ENABLED') == 'true':
            cmd.extend(["--agixt-voice-input-enabled", "true"])
        if config.get('AGIXT_RLHF') == 'true':
            cmd.extend(["--agixt-rlhf", "true"])
        if config.get('AGIXT_FOOTER_MESSAGE'):
            cmd.extend(["--agixt-footer-message", config['AGIXT_FOOTER_MESSAGE']])
        if config.get('ALLOW_EMAIL_SIGN_IN') == 'true':
            cmd.extend(["--allow-email-sign-in", "true"])
        if config.get('DATABASE_TYPE'):
            cmd.extend(["--database-type", config['DATABASE_TYPE']])
        if config.get('DATABASE_NAME'):
            cmd.extend(["--database-name", config['DATABASE_NAME']])
        if config.get('LOG_LEVEL'):
            cmd.extend(["--log-level", config['LOG_LEVEL']])
        if config.get('UVICORN_WORKERS'):
            cmd.extend(["--uvicorn-workers", config['UVICORN_WORKERS']])
        if config.get('WORKING_DIRECTORY'):
            cmd.extend(["--working-directory", config['WORKING_DIRECTORY']])
        if config.get('TZ'):
            cmd.extend(["--tz", config['TZ']])
        if config.get('ALLOWED_DOMAINS'):
            cmd.extend(["--allowed-domains", config['ALLOWED_DOMAINS']])
        if config.get('AGIXT_AUTO_UPDATE') == 'true':
            cmd.extend(["--agixt-auto-update", "true"])
        if config.get('AGIXT_REQUIRE_API_KEY') == 'false':
            cmd.extend(["--agixt-require-api-key", "false"])
        
        print(f"🚀 Démarrage AGiXT avec la commande officielle start.py...")
        print(f"📝 Commande: {' '.join(cmd)}")
        print(f"⏰ Cela peut prendre plusieurs minutes...")
        
        # CORRECTION: Utiliser subprocess.Popen pour lancer en arrière-plan
        # au lieu de nohup + shell=True qui cause des problèmes
        with open('start.log', 'w') as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=install_path
            )
        
        print("✅ AGiXT start.py lancé en arrière-plan avec Popen")
        print("⏳ Attente du démarrage des services (90 secondes)...")
        time.sleep(90)
        
        # Vérifier les services via Docker
        ps_result = subprocess.run(["docker", "compose", "ps"], 
                                 capture_output=True, text=True, cwd=install_path)
        if ps_result.returncode == 0:
            print(f"📊 État des containers Docker:\n{ps_result.stdout}")
        
        # Vérifier le fichier de log
        log_file = os.path.join(install_path, "start.log")
        if os.path.exists(log_file):
            print("📝 Dernières lignes du log start.py:")
            tail_result = subprocess.run(["tail", "-10", log_file], 
                                       capture_output=True, text=True)
            if tail_result.returncode == 0:
                print(tail_result.stdout)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage d'AGiXT: {e}")
        return False


def verify_installation(install_path: str):
    """Verify the installation is working"""
    print("\n🔍 Verifying installation...")
    
    # Check if containers are running
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("📊 Container status:")
            print(result.stdout)
        
        # Check AGiXT specific containers
        agixt_containers = subprocess.run(
            ["docker", "ps", "--filter", "name=agixt", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if agixt_containers.stdout.strip():
            print(f"✅ AGiXT containers detected: {agixt_containers.stdout.strip()}")
        else:
            print("⚠️  No AGiXT containers found yet")
        
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
                print(f"⚠️  Port {port} is not accessible yet (services may still be starting)")
            sock.close()
            
        # Check start.py log for errors
        log_file = os.path.join(install_path, "start.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
                if "error" in log_content.lower() or "failed" in log_content.lower():
                    print("⚠️  Potential errors detected in start.log")
                    print("📝 Check the log file for details:")
                    print(f"   tail -f {log_file}")
                else:
                    print("✅ No obvious errors in start.log")
            
    except Exception as e:
        print(f"⚠️  Could not verify installation: {e}")


def main():
    """Main installation function"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║            AGiXT Installer - Version 2 (start.py)            ║")
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
    
    print(f"\n🔄 Step 5/6: Starting AGiXT services via start.py official...")
    if not start_agixt_services(install_path, config):
        print("❌ Failed to start services via start.py")
        sys.exit(1)
    
    print(f"\n🔄 Step 6/6: Verification...")
    verify_installation(install_path)
    
    print(f"\n✅ Installation completed successfully!")
    print(f"📁 Directory: {install_path}")
    print(f"🌐 AGiXT Interface: http://162.55.213.90:3437")
    print(f"🔧 AGiXT API: http://162.55.213.90:7437")
    print(f"📝 Start.py Log: {install_path}/start.log")
    print(f"📋 Container Status: docker ps")
    print(f"🔍 View Logs: tail -f {install_path}/start.log")
    print(f"\n⚠️  Note: Services may take 1-2 minutes to be fully ready")


if __name__ == "__main__":
    main()
