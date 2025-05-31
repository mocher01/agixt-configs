#!/usr/bin/env python3
"""
AGiXT Automated Installer - No Override Version
===============================================

Usage:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - CONFIG_NAME
  python3 install-agixt.py CONFIG_NAME [GITHUB_TOKEN]

Example:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - AGiXT-0528_1531
  python3 install-agixt.py AGiXT-0528_1531 github_pat_xxxxx

This script will:
1. Download the specified .env config from GitHub
2. Create installation folder based on INSTALL_FOLDER_NAME
3. Download and set up AGiXT with all configurations
4. Preserve ALL environment variables as defined in .env file
5. Start the AGiXT server with proper health checks

Author: No Override Version
Version: 2.2.0
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
import socket
import platform
import time
import json
import re
import secrets
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configuration
GITHUB_REPO_BASE = "https://raw.githubusercontent.com/mocher01/agixt-configs/main"
AGIXT_REPO = "https://github.com/Josh-XT/AGiXT.git"
DEFAULT_BASE_PATH = "/var/apps"

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'

def print_step(message: str):
    """Print a step message in blue"""
    print(f"\n{Colors.BLUE}🚀 {message}{Colors.END}")

def print_success(message: str):
    """Print a success message in green"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message: str):
    """Print a warning message in yellow"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message: str):
    """Print an error message in red"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    """Print an info message in cyan"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def run_command(command: str, cwd: Optional[str] = None, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result"""
    try:
        print_info(f"Running: {command}")
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=capture_output, 
            text=True, 
            check=check
        )
        if result.stdout and capture_output:
            print(f"Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(f"Return code: {e.returncode}")
        if e.stderr:
            print_error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def download_file(url: str, filename: str) -> bool:
    """Download a file from URL with optional GitHub token support"""
    try:
        print_info(f"Downloading {filename} from {url}")
        
        # Check if we have a GitHub token for private repos
        github_token = os.environ.get('GITHUB_TOKEN')
        
        if github_token and ('github.com' in url or 'githubusercontent.com' in url):
            # Create request with authorization header
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'token {github_token}')
            req.add_header('User-Agent', 'AGiXT-Installer/2.2')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(filename, 'wb') as f:
                    f.write(response.read())
        else:
            # Standard download for public repos
            urllib.request.urlretrieve(url, filename)
            
        print_success(f"Downloaded {filename}")
        return True
    except urllib.error.HTTPError as e:
        print_error(f"HTTP Error {e.code}: {e.reason}")
        if e.code == 404:
            print_error(f"Configuration file '{filename}' not found in repository")
        elif e.code == 403:
            print_error("Access denied - check your GitHub token")
        return False
    except urllib.error.URLError as e:
        print_error(f"Network error downloading {filename}: {e}")
        return False
    except Exception as e:
        print_error(f"Failed to download {filename}: {e}")
        return False

def check_system_requirements() -> bool:
    """Check system requirements and compatibility"""
    print_step("Checking system requirements...")
    
    # Check OS compatibility
    system = platform.system().lower()
    if system not in ['linux', 'darwin']:
        print_error(f"Unsupported operating system: {system}")
        print_error("This script supports Linux and macOS only")
        return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error(f"Python 3.8+ required, found {sys.version}")
        return False
    print_success(f"Python {sys.version.split()[0]} ✓")
    
    # Check available disk space (minimum 5GB)
    try:
        statvfs = os.statvfs('/')
        free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        if free_space_gb < 5:
            print_warning(f"Low disk space: {free_space_gb:.1f}GB available (5GB recommended)")
        else:
            print_success(f"Disk space: {free_space_gb:.1f}GB available ✓")
    except:
        print_warning("Could not check disk space")
    
    return True

def check_prerequisites() -> bool:
    """Check if required tools are installed"""
    print_step("Checking prerequisites...")
    
    if not check_system_requirements():
        return False
    
    # Check Git
    result = run_command("git --version", check=False)
    if result.returncode != 0:
        print_error("Git is required but not installed")
        print_info("Install with: sudo apt update && sudo apt install git")
        return False
    print_success("Git ✓")
    
    # Check Docker
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print_warning("Docker not found - attempting installation...")
        if not install_docker():
            return False
    else:
        print_success("Docker ✓")
        # Check if Docker daemon is running
        result = run_command("docker ps", check=False)
        if result.returncode != 0:
            print_error("Docker daemon is not running")
            print_info("Start with: sudo systemctl start docker")
            return False
    
    # Check Docker Compose
    result = run_command("docker compose version", check=False)
    if result.returncode != 0:
        print_warning("Docker Compose not found - attempting installation...")
        if not install_docker_compose():
            return False
    else:
        print_success("Docker Compose ✓")
    
    return True

def install_docker() -> bool:
    """Install Docker based on the operating system"""
    system = platform.system().lower()
    
    if system == "linux":
        print_step("Installing Docker on Linux...")
        
        # Check if running as root or with sudo
        if os.geteuid() != 0:
            print_error("Docker installation requires root privileges")
            print_info("Run with: sudo python3 install-agixt.py ...")
            return False
        
        commands = [
            "curl -fsSL https://get.docker.com -o get-docker.sh",
            "sh get-docker.sh",
            "systemctl start docker",
            "systemctl enable docker"
        ]
        
        for cmd in commands:
            result = run_command(cmd, check=False)
            if result.returncode != 0:
                print_error(f"Failed to install Docker: {cmd}")
                return False
        
        # Add current user to docker group if not root
        if 'SUDO_USER' in os.environ:
            user = os.environ['SUDO_USER']
            run_command(f"usermod -aG docker {user}")
            print_warning(f"User {user} added to docker group - logout and login required")
        
        print_success("Docker installed successfully")
        return True
        
    else:
        print_error(f"Please install Docker manually for {system}")
        print_info("Visit: https://docs.docker.com/get-docker/")
        return False

def install_docker_compose() -> bool:
    """Install Docker Compose"""
    system = platform.system().lower()
    
    if system == "linux":
        print_step("Installing Docker Compose...")
        
        # Modern Docker installations include compose as a plugin
        result = run_command("docker compose version", check=False)
        if result.returncode == 0:
            print_success("Docker Compose already available")
            return True
        
        # Install compose plugin
        result = run_command("apt-get update && apt-get install -y docker-compose-plugin", check=False)
        if result.returncode == 0:
            print_success("Docker Compose plugin installed")
            return True
        
        print_warning("Could not install Docker Compose plugin, trying standalone...")
        
        # Fallback to standalone installation
        arch = platform.machine()
        if arch == "x86_64":
            arch = "x86_64"
        elif arch == "aarch64":
            arch = "aarch64"
        else:
            print_error(f"Unsupported architecture: {arch}")
            return False
        
        compose_url = f"https://github.com/docker/compose/releases/latest/download/docker-compose-linux-{arch}"
        cmd = f'curl -L "{compose_url}" -o /usr/local/bin/docker-compose'
        
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            print_error("Failed to download Docker Compose")
            return False
        
        run_command("chmod +x /usr/local/bin/docker-compose")
        print_success("Docker Compose installed")
        return True
    else:
        print_warning("Docker Compose should be included with Docker Desktop")
        return True

def get_server_ip() -> str:
    """Get the server's external IP address"""
    try:
        # Try to get external IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        
        # Check if it's a private IP and try to get public IP
        if local_ip.startswith(('192.168.', '10.', '172.')):
            try:
                import urllib.request
                with urllib.request.urlopen('https://api.ipify.org', timeout=10) as response:
                    public_ip = response.read().decode().strip()
                    print_info(f"Detected public IP: {public_ip}")
                    return public_ip
            except:
                print_warning("Could not determine public IP, using local IP")
        
        return local_ip
    except Exception as e:
        print_warning(f"Could not determine IP address: {e}")
        return "localhost"

def load_env_config(env_file: str) -> Dict[str, str]:
    """Load environment variables from .env file"""
    config = {}
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Handle lines with =
                if '=' not in line:
                    print_warning(f"Invalid line {line_num} in {env_file}: {line}")
                    continue
                
                # Split on first = only
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                config[key] = value
                
        print_success(f"Loaded {len(config)} configuration variables")
        return config
        
    except Exception as e:
        print_error(f"Failed to load {env_file}: {e}")
        sys.exit(1)

def validate_config(config: Dict[str, str]) -> bool:
    """Validate essential configuration parameters"""
    print_step("Validating configuration...")
    
    # INSTALL_FOLDER_NAME is now auto-generated, no longer required in config
    # No required fields to check
    
    # Check for AI provider configuration
    ai_providers = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'WITH_EZLOCALAI']
    has_ai_provider = any(config.get(provider) for provider in ai_providers)
    
    if not has_ai_provider and config.get('WITH_EZLOCALAI', '').lower() != 'true':
        print_warning("No AI provider configured - AGiXT will have limited functionality")
        print_info("Consider setting OPENAI_API_KEY, ANTHROPIC_API_KEY, or enabling WITH_EZLOCALAI")
    
    # Check SMTP configuration for email login
    smtp_fields = ['SMTP_SERVER', 'SMTP_USER', 'SMTP_PASSWORD']
    has_smtp = all(config.get(field) for field in smtp_fields)
    
    if not has_smtp:
        print_warning("SMTP not configured - email login will not work")
        print_info("Configure SMTP_SERVER, SMTP_USER, and SMTP_PASSWORD for email authentication")
    

    if not config.get('AGIXT_API_KEY') or config.get('AGIXT_API_KEY') == 'None':
        print_warning("AGIXT_API_KEY not set - consider generating a secure API key")
    
    # Network accessibility info
    agixt_uri = config.get('AGIXT_URI', '')
    app_uri = config.get('APP_URI', '')
    
    if 'localhost' in agixt_uri or 'localhost' in app_uri:
        print_info("Configuration uses localhost - services will only be accessible from this machine")
        server_ip = get_server_ip()
        if server_ip != "localhost":
            print_info(f"To allow external access, consider updating URLs to use: {server_ip}")
    
    print_success("Configuration validation complete")
    return True

def create_installation_directory(install_folder_name: str) -> str:
    """Create and prepare the installation directory"""
    # Use /var/apps as base path, but fall back to user home if permission denied
    base_paths = [DEFAULT_BASE_PATH, os.path.expanduser("~/agixt-installations")]
    
    for base_path in base_paths:
        try:
            install_path = os.path.join(base_path, install_folder_name)
            print_step(f"Creating installation directory: {install_path}")
            
            # Create base directory if it doesn't exist
            os.makedirs(base_path, exist_ok=True)
            
            if os.path.exists(install_path):
                print_warning(f"Directory {install_path} already exists")
                response = input("Continue? This will update the existing installation (y/N): ").strip().lower()
                if response != 'y':
                    print_info("Installation cancelled by user")
                    sys.exit(0)
            else:
                os.makedirs(install_path, exist_ok=True)
                print_success(f"Created directory: {install_path}")
            
            # Test write permissions
            test_file = os.path.join(install_path, '.test_write')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print_success(f"Write permissions confirmed: {install_path}")
                return install_path
            except Exception as e:
                print_warning(f"No write permission to {install_path}: {e}")
                continue
                
        except PermissionError:
            print_warning(f"Cannot create directory in {base_path} - permission denied")
            continue
        except Exception as e:
            print_warning(f"Failed to create directory in {base_path}: {e}")
            continue
    
    print_error("Could not create installation directory in any location")
    print_info("Try running with sudo or ensure you have write permissions")
    sys.exit(1)

def clone_agixt_repository(install_path: str, config: Dict[str, str]) -> bool:
    """Clone or update the AGiXT repository"""
    print_step("Setting up AGiXT repository...")
    
    # Use branch from config, default to stable
    branch = config.get('AGIXT_BRANCH', 'stable')
    print_info(f"Using branch: {branch}")
    
    git_path = os.path.join(install_path, '.git')
    
    if os.path.exists(git_path):
        print_info("Repository exists, updating...")
        
        # Fetch latest changes
        result = run_command("git fetch origin", cwd=install_path, check=False)
        if result.returncode != 0:
            print_warning("Failed to fetch updates, continuing with existing version")
            return True
        
        # Reset to latest branch
        run_command(f"git checkout {branch}", cwd=install_path, check=False)
        run_command(f"git reset --hard origin/{branch}", cwd=install_path, check=False)
        print_success("Repository updated")
        
    else:
        print_info(f"Cloning AGiXT repository (branch: {branch})...")
        
        # Clone the repository
        clone_cmd = f"git clone --branch {branch} --depth 1 {AGIXT_REPO} ."
        result = run_command(clone_cmd, cwd=install_path, check=False)
        
        if result.returncode != 0:
            print_warning(f"Failed to clone {branch} branch, trying main...")
            clone_cmd = f"git clone --branch main --depth 1 {AGIXT_REPO} ."
            result = run_command(clone_cmd, cwd=install_path)
        
        print_success("Repository cloned successfully")
    
    return True

def create_env_file(config: Dict[str, str], install_path: str) -> str:
    """Create .env file in the installation directory"""
    env_file = os.path.join(install_path, '.env')
    
    print_step(f"Creating .env file: {env_file}")
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# AGiXT Configuration\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Installation: {install_path}\n")
            f.write("# NOTE: All values preserved from original configuration\n\n")
            
            # Group related configurations
            sections = {
                'Core Settings': ['AGIXT_API_KEY', 'AGIXT_BRANCH'],
                'Network & URLs': ['AGIXT_URI', 'APP_URI', 'AUTH_WEB', 'ALLOWED_DOMAINS'],
                'Authentication': ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_USE_TLS', 'FROM_EMAIL'],
                'AI Providers': ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'WITH_EZLOCALAI'],
                'System Settings': ['DATABASE_TYPE', 'DATABASE_NAME', 'UVICORN_WORKERS', 'LOG_LEVEL', 'WORKING_DIRECTORY']
            }
            
            # Write sections
            written_keys = set()
            for section_name, keys in sections.items():
                section_keys = [k for k in keys if k in config and k not in written_keys]
                if section_keys:
                    f.write(f"\n# {section_name}\n")
                    for key in section_keys:
                        f.write(f'{key}="{config[key]}"\n')
                        written_keys.add(key)
            
            # Write remaining keys
            remaining_keys = [k for k in sorted(config.keys()) if k not in written_keys]
            if remaining_keys:
                f.write(f"\n# Additional Settings\n")
                for key in remaining_keys:
                    f.write(f'{key}="{config[key]}"\n')
        
        # Secure the file
        os.chmod(env_file, 0o600)
        print_success("Environment file created and secured")
        return env_file
        
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        sys.exit(1)

def start_agixt_services(install_path: str) -> bool:
    """Start AGiXT services using Docker Compose"""
    print_step("Starting AGiXT services...")
    
    # Change to installation directory
    original_cwd = os.getcwd()
    os.chdir(install_path)
    
    try:
        # Stop any existing containers
        print_info("Stopping existing containers...")
        run_command("docker compose down", check=False, capture_output=False)
        
        # Always use default docker-compose.yml
        compose_file = "docker-compose.yml"
        print_info(f"Using compose file: {compose_file}")
        
        # Pull latest images
        print_info("Pulling Docker images...")
        result = run_command(f"docker compose -f {compose_file} pull", check=False, capture_output=False)
        if result.returncode != 0:
            print_warning("Failed to pull some images, continuing...")
        
        # Start services
        print_info("Starting services...")
        result = run_command(f"docker compose -f {compose_file} up -d", capture_output=False)
        
        if result.returncode == 0:
            print_success("AGiXT services started successfully!")
            return True
        else:
            print_error("Failed to start AGiXT services")
            return False
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def wait_for_services(config: Dict[str, str], timeout: int = 120) -> Tuple[str, str]:
    """Wait for services to be ready and return URLs"""
    print_step("Waiting for services to be ready...")
    
    api_url = config.get('AGIXT_URI', 'http://localhost:7437')
    web_url = config.get('APP_URI', 'http://localhost:3437')
    
    # Health check endpoints
    health_endpoints = [
        (api_url, "API"),
        (web_url, "Web Interface")
    ]
    
    start_time = time.time()
    check_interval = 5
    
    for endpoint_url, service_name in health_endpoints:
        print_info(f"Checking {service_name} at {endpoint_url}")
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect to the service
                import urllib.request
                req = urllib.request.Request(endpoint_url, headers={'User-Agent': 'AGiXT-Health-Check'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status < 400:
                        print_success(f"{service_name} is ready!")
                        break
            except Exception as e:
                elapsed = int(time.time() - start_time)
                remaining = timeout - elapsed
                print(f"⏳ {service_name} not ready yet... ({elapsed}s elapsed, {remaining}s remaining)")
                
                if remaining <= 0:
                    print_warning(f"{service_name} did not become ready within {timeout}s")
                    break
                    
                time.sleep(check_interval)
    
    return api_url, web_url

def show_installation_summary(install_path: str, config: Dict[str, str], api_url: str, web_url: str):
    """Display installation summary and next steps"""
    print("\n" + "="*70)
    print(f"{Colors.GREEN}{Colors.BOLD}🎉 AGiXT Installation Complete!{Colors.END}")
    print("="*70)
    
    print(f"\n📁 {Colors.BOLD}Installation Details:{Colors.END}")
    print(f"   Location: {install_path}")
    print(f"   Branch: {config.get('AGIXT_BRANCH', 'stable')}")
    
    print(f"\n🌐 {Colors.BOLD}Service URLs:{Colors.END}")
    print(f"   Web Interface: {Colors.CYAN}{web_url}{Colors.END}")
    print(f"   API Endpoint:  {Colors.CYAN}{api_url}{Colors.END}")
    
    # Try to show management URL if different port pattern
    management_url = web_url.replace(':3437', ':8501') if ':3437' in web_url else f"{web_url.rsplit(':', 1)[0]}:8501"
    print(f"   Management:    {Colors.CYAN}{management_url}{Colors.END}")
    
    # Authentication info
    smtp_configured = all(config.get(field) for field in ['SMTP_SERVER', 'SMTP_USER', 'SMTP_PASSWORD'])
    if smtp_configured:
        print(f"\n📧 {Colors.BOLD}Email Authentication:{Colors.END}")
        print(f"   SMTP Server: {config.get('SMTP_SERVER')}")
        print(f"   From Email:  {config.get('FROM_EMAIL', config.get('SMTP_USER'))}")
    else:
        print(f"\n📧 {Colors.YELLOW}Email Authentication: Not configured{Colors.END}")
    
    # AI Providers
    providers = []
    if config.get('OPENAI_API_KEY'): providers.append('OpenAI')
    if config.get('ANTHROPIC_API_KEY'): providers.append('Anthropic')
    if config.get('GOOGLE_API_KEY'): providers.append('Google')
    if config.get('WITH_EZLOCALAI', '').lower() == 'true': providers.append('ezLocalAI')
    
    print(f"\n🤖 {Colors.BOLD}AI Providers:{Colors.END}")
    if providers:
        print(f"   Configured: {', '.join(providers)}")
    else:
        print(f"   {Colors.YELLOW}No AI providers configured{Colors.END}")
    
    # Security status
    api_key_set = bool(config.get('AGIXT_API_KEY') and config.get('AGIXT_API_KEY') != 'None')
    print(f"\n🔐 {Colors.BOLD}Security:{Colors.END}")
    print(f"   API Key Set: {Colors.GREEN if api_key_set else Colors.YELLOW}{'Yes' if api_key_set else 'No'}{Colors.END}")
    if api_key_set:
        print(f"   API Key: {config.get('AGIXT_API_KEY', 'Not set')[:16]}...")
    

    
    print(f"\n🚀 {Colors.BOLD}Next Steps:{Colors.END}")
    print("   1. Open the web interface in your browser")
    if smtp_configured:
        print("   2. Login with your email address")
        print("   3. Check your email for the magic link")
        print("   4. Start creating agents and conversations!")
    else:
        print("   2. Configure SMTP settings for email authentication")
        print("   3. Configure at least one AI provider")
        print("   4. Restart services and begin using AGiXT!")
    
    print(f"\n💡 {Colors.BOLD}Useful Commands:{Colors.END}")
    print(f"   View logs:     cd {install_path} && docker compose logs -f")
    print(f"   Restart:       cd {install_path} && docker compose restart")
    print(f"   Stop:          cd {install_path} && docker compose down")
    print(f"   Update:        cd {install_path} && git pull && docker compose up -d")

def cleanup_temp_files(*files):
    """Clean up temporary files"""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print_info(f"Cleaned up: {file}")
        except Exception as e:
            print_warning(f"Could not remove {file}: {e}")

def main():
    """Main installation function"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                  AGiXT Automated Installer                   ║")
    print("║                  No Override Version v2.2                    ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print_error("Missing required argument: CONFIG_NAME")
        print(f"\n{Colors.BOLD}Usage:{Colors.END}")
        print("  python3 install-agixt.py <config_name> [github_token]")
        print(f"\n{Colors.BOLD}Examples:{Colors.END}")
        print("  python3 install-agixt.py AGiXT-0528_1531")
        print("  python3 install-agixt.py AGiXT-0528_1531 github_pat_xxxxx")
        print(f"\n{Colors.BOLD}Remote Installation:{Colors.END}")
        print("  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - AGiXT-0528_1531")
        sys.exit(1)
    
    config_name = sys.argv[1]
    github_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Extract installation folder name from config name
    install_folder_name = config_name.replace('.env', '')
    print_info(f"Installation folder will be: {install_folder_name}")
    
    # Set token in environment for download functions
    if github_token:
        os.environ['GITHUB_TOKEN'] = github_token
        print_success("GitHub token configured for private repository access")
    
    env_url = f"{GITHUB_REPO_BASE}/{config_name}.env"
    env_file = f"{config_name}.env"
    
    print_info(f"Configuration: {config_name}")
    print_info(f"Repository: {GITHUB_REPO_BASE}")
    print_info(f"Target: {env_url}")
    
    try:
        # Step 1: Prerequisites check
        if not check_prerequisites():
            print_error("Prerequisites check failed")
            sys.exit(1)
        
        # Step 2: Download configuration
        print_step(f"Downloading configuration: {config_name}.env")
        if not download_file(env_url, env_file):
            print_error(f"Failed to download configuration: {config_name}.env")
            print_info("Available configurations:")
            print_info(f"  Check: {GITHUB_REPO_BASE}/")
            print_info("  Ensure the .env file exists and is accessible")
            sys.exit(1)
        
        # Step 3: Load and validate configuration
        config = load_env_config(env_file)
        if not validate_config(config):
            print_error("Configuration validation failed")
            sys.exit(1)
        
        print_success("Configuration loaded successfully - NO VALUES MODIFIED")
        
        # Step 4: Create installation directory
        install_path = create_installation_directory(install_folder_name)
        
        # Step 5: Clone/update AGiXT repository
        if not clone_agixt_repository(install_path, config):
            print_error("Failed to setup AGiXT repository")
            sys.exit(1)
        
        # Step 6: Create environment file
        env_file_path = create_env_file(config, install_path)
        
        # Step 7: Start AGiXT services
        if not start_agixt_services(install_path):
            print_error("Failed to start AGiXT services")
            print_info("Check the logs for more information:")
            print_info(f"  cd {install_path} && docker compose logs")
            sys.exit(1)
        
        # Step 8: Wait for services to be ready
        api_url, web_url = wait_for_services(config)
        
        # Step 9: Show installation summary
        show_installation_summary(install_path, config, api_url, web_url)
        
        print(f"\n{Colors.GREEN}✨ Installation completed successfully!{Colors.END}")
        print(f"{Colors.CYAN}📝 All configuration values preserved as specified in .env file{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Installation cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        import traceback
        print_error("Full error details:")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up temporary files
        cleanup_temp_files(env_file)

if __name__ == "__main__":
    main()
