#!/usr/bin/env python3
"""
AGiXT Automated Installer
=========================

Usage:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - CONFIG_NAME

Example:
  curl -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - test-server

This script will:
1. Download the specified .env config from GitHub
2. Create installation folder based on INSTALL_FOLDER_NAME
3. Download and set up AGiXT with SMTP support
4. Apply all configurations
5. Start the AGiXT server

Author: Your Name
Version: 1.0.0
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
from pathlib import Path

# Configuration
GITHUB_REPO_BASE = "https://raw.githubusercontent.com/YOUR-USERNAME/agixt-configs/main"
AGIXT_REPO = "https://github.com/Josh-XT/AGiXT.git"

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(message):
    """Print a step message in blue"""
    print(f"\n{Colors.BLUE}🚀 {message}{Colors.END}")

def print_success(message):
    """Print a success message in green"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message in yellow"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    """Print an error message in red"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def run_command(command, cwd=None, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def download_file(url, filename):
    """Download a file from URL"""
    try:
        print(f"📥 Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)
        print_success(f"Downloaded {filename}")
        return True
    except urllib.error.URLError as e:
        print_error(f"Failed to download {filename}: {e}")
        return False

def check_prerequisites():
    """Check if required tools are installed"""
    print_step("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ required")
        sys.exit(1)
    print_success(f"Python {sys.version.split()[0]} ✓")
    
    # Check Git
    result = run_command("git --version", check=False)
    if result.returncode != 0:
        print_error("Git is required but not installed")
        sys.exit(1)
    print_success("Git ✓")
    
    # Check Docker
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print_warning("Docker not found - will attempt to install")
        install_docker()
    else:
        print_success("Docker ✓")
    
    # Check Docker Compose
    result = run_command("docker compose version", check=False)
    if result.returncode != 0:
        print_warning("Docker Compose not found - will attempt to install")
        install_docker_compose()
    else:
        print_success("Docker Compose ✓")

def install_docker():
    """Install Docker based on the operating system"""
    system = platform.system().lower()
    
    if system == "linux":
        print_step("Installing Docker on Linux...")
        commands = [
            "curl -fsSL https://get.docker.com -o get-docker.sh",
            "sudo sh get-docker.sh",
            "sudo usermod -aG docker $USER",
            "sudo systemctl start docker",
            "sudo systemctl enable docker"
        ]
        
        for cmd in commands:
            result = run_command(cmd, check=False)
            if result.returncode != 0:
                print_error(f"Failed to install Docker: {cmd}")
                sys.exit(1)
        
        print_success("Docker installed successfully")
        print_warning("Please log out and back in to use Docker without sudo")
        
    else:
        print_error(f"Please install Docker manually for {system}")
        print("Visit: https://docs.docker.com/get-docker/")
        sys.exit(1)

def install_docker_compose():
    """Install Docker Compose"""
    system = platform.system().lower()
    
    if system == "linux":
        print_step("Installing Docker Compose...")
        cmd = 'sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose'
        run_command(cmd)
        run_command("sudo chmod +x /usr/local/bin/docker-compose")
        print_success("Docker Compose installed")
    else:
        print_warning("Docker Compose should be included with Docker Desktop")

def get_server_ip():
    """Get the server's IP address"""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        return ip
    except Exception:
        return "localhost"

def load_env_config(env_file):
    """Load environment variables from .env file"""
    config = {}
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    config[key] = value
        return config
    except Exception as e:
        print_error(f"Failed to load {env_file}: {e}")
        sys.exit(1)

def update_env_config(config):
    """Update configuration with server-specific values"""
    print_step("Updating configuration for this server...")
    
    # Get server IP
    server_ip = get_server_ip()
    print(f"🌐 Detected server IP: {server_ip}")
    
    # Update URLs if they're set to localhost
    if config.get('AGIXT_URI', '').startswith('http://localhost'):
        config['AGIXT_URI'] = f"http://{server_ip}:{config.get('AGIXT_PORT', '7437')}"
    
    if config.get('APP_URI', '').startswith('http://localhost'):
        config['APP_URI'] = f"http://{server_ip}:{config.get('AGIXT_INTERACTIVE_PORT', '3437')}"
    
    # Generate API key if not set
    if not config.get('AGIXT_API_KEY'):
        import secrets
        config['AGIXT_API_KEY'] = secrets.token_hex(32)
        print_success("Generated secure API key")
    
    # Set working directory
    install_folder = config.get('INSTALL_FOLDER_NAME', 'AGiXT-Default')
    config['WORKING_DIRECTORY'] = f"./{install_folder}/WORKSPACE"
    
    return config

def create_env_file(config, folder_path):
    """Create .env file in the installation folder"""
    env_file = os.path.join(folder_path, '.env')
    
    print_step(f"Creating .env file at {env_file}")
    
    with open(env_file, 'w') as f:
        f.write("# AGiXT Configuration\n")
        f.write(f"# Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for key, value in config.items():
            f.write(f'{key}="{value}"\n')
    
    # Secure the file
    os.chmod(env_file, 0o600)
    print_success("Created and secured .env file")

def patch_magical_auth(folder_path):
    """Apply SMTP patches to MagicalAuth.py"""
    print_step("Applying SMTP patches to MagicalAuth.py...")
    
    magical_auth_path = os.path.join(folder_path, 'agixt', 'MagicalAuth.py')
    
    if not os.path.exists(magical_auth_path):
        print_warning("MagicalAuth.py not found - skipping SMTP patch")
        return
    
    # Create backup
    backup_path = f"{magical_auth_path}.backup"
    run_command(f"cp '{magical_auth_path}' '{backup_path}'")
    
    try:
        with open(magical_auth_path, 'r') as f:
            content = f.read()
        
        # Add SMTP imports
        smtp_imports = """import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart"""
        
        if "import smtplib" not in content:
            # Find insertion point after existing imports
            lines = content.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith(('import ', 'from ')) and not line.strip().startswith('#'):
                    insert_index = i + 1
            
            lines.insert(insert_index, smtp_imports)
            content = '\n'.join(lines)
        
        # Add SMTP email method (simplified version)
        smtp_method = '''
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True) -> bool:
        """Send email using SMTP - supports any email provider"""
        try:
            smtp_server = getenv("SMTP_SERVER")
            smtp_port = int(getenv("SMTP_PORT", "587"))
            smtp_user = getenv("SMTP_USER")
            smtp_password = getenv("SMTP_PASSWORD")
            smtp_use_tls = getenv("SMTP_USE_TLS", "true").lower() == "true"
            from_email = getenv("FROM_EMAIL", smtp_user)
            
            if not all([smtp_server, smtp_user, smtp_password]):
                logging.error("SMTP configuration incomplete")
                return False
                
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                if smtp_use_tls:
                    server.starttls()
            
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
            server.quit()
            
            logging.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            return False
'''
        
        # Replace or add send_email method
        if "def send_email(" in content:
            # Replace existing method (simplified regex)
            content = re.sub(
                r'def send_email\(.*?\n(?:.*?\n)*?.*?return.*?\n',
                smtp_method.strip() + '\n',
                content,
                flags=re.MULTILINE | re.DOTALL
            )
        else:
            # Add method to MagicalAuth class
            class_pattern = r'(class MagicalAuth:.*?\n)'
            content = re.sub(class_pattern, r'\1' + smtp_method, content, flags=re.MULTILINE | re.DOTALL)
        
        # Write patched file
        with open(magical_auth_path, 'w') as f:
            f.write(content)
        
        print_success("SMTP patches applied successfully")
        
    except Exception as e:
        print_error(f"Failed to patch MagicalAuth.py: {e}")
        # Restore backup
        if os.path.exists(backup_path):
            run_command(f"cp '{backup_path}' '{magical_auth_path}'")
        print_warning("Restored original file")

def start_agixt(folder_path):
    """Start AGiXT using Docker Compose"""
    print_step("Starting AGiXT containers...")
    
    # Change to installation directory
    os.chdir(folder_path)
    
    # Stop any existing containers
    run_command("docker compose down", check=False)
    
    # Pull latest images and start
    run_command("docker compose pull")
    run_command("docker compose up -d")
    
    print_success("AGiXT containers started successfully!")

def wait_for_services(config):
    """Wait for services to be ready"""
    print_step("Waiting for services to start...")
    
    api_url = config.get('AGIXT_URI', 'http://localhost:7437')
    web_url = config.get('APP_URI', 'http://localhost:3437')
    
    # Wait up to 2 minutes for services
    for i in range(24):  # 24 * 5 seconds = 2 minutes
        try:
            # Check API health
            urllib.request.urlopen(f"{api_url}/health", timeout=5)
            print_success("API service is ready!")
            break
        except:
            if i < 23:
                print(f"⏳ Waiting for services... ({i+1}/24)")
                time.sleep(5)
            else:
                print_warning("Services may still be starting up")
    
    return api_url, web_url

def main():
    """Main installation function"""
    print(f"{Colors.BOLD}🚀 AGiXT Automated Installer{Colors.END}")
    print("=" * 50)
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print_error("Usage: python3 install-agixt.py CONFIG_NAME")
        print("Example: python3 install-agixt.py test-server")
        sys.exit(1)
    
    config_name = sys.argv[1]
    env_url = f"{GITHUB_REPO_BASE}/{config_name}.env"
    env_file = f"{config_name}.env"
    
    print(f"📋 Configuration: {config_name}")
    print(f"🌐 Repository: {GITHUB_REPO_BASE}")
    
    # Step 1: Check prerequisites
    check_prerequisites()
    
    # Step 2: Download environment configuration
    print_step(f"Downloading configuration: {config_name}.env")
    if not download_file(env_url, env_file):
        print_error(f"Failed to download {env_file}")
        print("Available configurations should be at:")
        print(f"  {GITHUB_REPO_BASE}/")
        sys.exit(1)
    
    # Step 3: Load and update configuration
    config = load_env_config(env_file)
    config = update_env_config(config)
    
    install_folder = config.get('INSTALL_FOLDER_NAME', 'AGiXT-Default')
    print(f"📁 Installation folder: {install_folder}")
    
    # Step 4: Create installation directory in /var/apps
    base_path = "/var/apps"
    install_path = os.path.join(base_path, install_folder)

    print_step(f"Creating installation directory: {install_path}")

    # Ensure /var/apps exists with proper permissions
    try:
        os.makedirs(base_path, exist_ok=True)
    except PermissionError:
        print_error("Cannot create /var/apps directory. Run with sudo or create manually:")
        print(f"sudo mkdir -p {base_path}")
        print(f"sudo chown $USER:$USER {base_path}")
        sys.exit(1)

    if os.path.exists(install_path):
        print_warning(f"Directory {install_path} already exists")
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("Installation cancelled")
            sys.exit(0)
    else:
        os.makedirs(install_path, exist_ok=True)
        print_success(f"Created directory: {install_path}")

    # Update install_folder variable for rest of script
    install_folder = install_path
    
    # Step 5: Clone AGiXT repository
    print_step("Downloading AGiXT...")
    if os.path.exists(os.path.join(install_folder, '.git')):
        print("AGiXT already downloaded, updating...")
        run_command("git pull", cwd=install_folder)
    else:
        run_command(f"git clone {AGIXT_REPO} {install_folder}")
    print_success("AGiXT downloaded successfully")
    
    # Step 6: Apply SMTP patches
    patch_magical_auth(install_folder)
    
    # Step 7: Create .env file
    create_env_file(config, install_folder)
    
    # Step 8: Start AGiXT
    start_agixt(install_folder)
    
    # Step 9: Wait for services and show results
    api_url, web_url = wait_for_services(config)
    
    # Step 10: Show final information
    print("\n" + "="*60)
    print(f"{Colors.GREEN}{Colors.BOLD}🎉 AGiXT Installation Complete!{Colors.END}")
    print("="*60)
    print(f"📁 Installation: {os.path.abspath(install_folder)}")
    print(f"🌐 Web Interface: {web_url}")
    print(f"🔗 API Endpoint: {api_url}")
    print(f"📧 Email Login: {config.get('SMTP_USER', 'Not configured')}")
    print("\n🚀 Next Steps:")
    print("1. Open the web interface in your browser")
    print("2. Login with your email address")
    print("3. Check your email for the magic link")
    print("4. Start creating agents and conversations!")
    
    # Clean up
    if os.path.exists(env_file):
        os.remove(env_file)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Installation cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)
