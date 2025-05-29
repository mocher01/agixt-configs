#!/usr/bin/env python3
"""
AGiXT Fixed Installer - Simple Version
======================================

Fixes applied:
- Uses 'main' branch (AGiXT's actual primary branch)
- Fixes AUTH_PROVIDER configuration 
- Fixes Docker networking issues
- Fixes AUTH_WEB configuration
"""

import os
import sys
import subprocess
import urllib.request
import socket
import time
import secrets

# Configuration
GITHUB_REPO_BASE = "https://raw.githubusercontent.com/mocher01/agixt-configs/main"
AGIXT_REPO = "https://github.com/Josh-XT/AGiXT.git"
DEFAULT_BASE_PATH = "/var/apps"

def print_step(msg):
    print(f"\n🚀 {msg}")

def print_success(msg):
    print(f"✅ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def run_command(command, cwd=None, check=True):
    try:
        print_info(f"Running: {command}")
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, check=check)
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        if e.stderr:
            print_error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def download_file(url, filename):
    try:
        print_info(f"Downloading {filename}")
        github_token = os.environ.get('GITHUB_TOKEN')
        
        if github_token and 'github' in url:
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'token {github_token}')
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(filename, 'wb') as f:
                    f.write(response.read())
        else:
            urllib.request.urlretrieve(url, filename)
        
        print_success(f"Downloaded {filename}")
        return True
    except Exception as e:
        print_error(f"Failed to download {filename}: {e}")
        return False

def get_server_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        
        if local_ip.startswith(('192.168.', '10.', '172.')):
            try:
                with urllib.request.urlopen('https://api.ipify.org', timeout=10) as response:
                    public_ip = response.read().decode().strip()
                    print_info(f"Detected public IP: {public_ip}")
                    return public_ip
            except:
                print_warning("Could not get public IP, using local IP")
        
        return local_ip
    except:
        return "localhost"

def load_env_config(env_file):
    config = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                config[key] = value
        
        print_success(f"Loaded {len(config)} configuration variables")
        return config
    except Exception as e:
        print_error(f"Failed to load {env_file}: {e}")
        sys.exit(1)

def fix_configuration(config, config_name):
    print_step("Applying authentication fixes...")
    
    server_ip = get_server_ip()
    print_info(f"Server IP: {server_ip}")
    
    # CRITICAL FIXES
    
    # 1. Fix AUTH_PROVIDER (single value, not comma-separated)
    auth_provider = config.get('AUTH_PROVIDER', '')
    if ',' in auth_provider:
        print_warning(f"Found comma-separated AUTH_PROVIDER: {auth_provider}")
        config['AUTH_PROVIDER'] = 'magicalauth'
        print_success("Fixed AUTH_PROVIDER to single value: magicalauth")
    elif not auth_provider:
        config['AUTH_PROVIDER'] = 'magicalauth'
        print_success("Set AUTH_PROVIDER to: magicalauth")
    
    # 2. Use MAIN branch (AGiXT's actual primary branch)
    config['AGIXT_BRANCH'] = 'main'
    print_success("Set AGIXT_BRANCH to 'main' (AGiXT's primary branch)")
    
    # 3. Fix Docker networking - AGIXT_SERVER for internal communication
    config['AGIXT_SERVER'] = 'http://agixt:7437'
    print_success("Set AGIXT_SERVER for internal Docker networking")
    
    # 4. Fix external URLs
    config['AGIXT_URI'] = f"http://{server_ip}:7437"
    config['APP_URI'] = f"http://{server_ip}:3437"
    print_success(f"Updated external URLs to use {server_ip}")
    
    # 5. Fix AUTH_WEB to point to user interface
    config['AUTH_WEB'] = f"{config['APP_URI']}/user"
    print_success(f"Fixed AUTH_WEB to: {config['AUTH_WEB']}")
    
    # 6. Enable email authentication
    config['ALLOW_EMAIL_SIGN_IN'] = 'true'
    print_success("Enabled email sign-in")
    
    # 7. Temporarily disable API key requirement for testing
    config['AGIXT_REQUIRE_API_KEY'] = 'false'
    print_warning("Temporarily disabled API key requirement for authentication testing")
    
    # 8. Generate secure API key if needed
    if not config.get('AGIXT_API_KEY') or config.get('AGIXT_API_KEY') == 'None':
        config['AGIXT_API_KEY'] = secrets.token_hex(32)
        print_success("Generated secure API key")
    
    # 9. Set working directory
    config['WORKING_DIRECTORY'] = f"./{config_name}/WORKSPACE"
    
    return config

def create_installation_directory(config_name):
    install_path = os.path.join(DEFAULT_BASE_PATH, config_name)
    print_step(f"Creating installation directory: {install_path}")
    
    if os.path.exists(install_path):
        print_warning(f"Directory {install_path} already exists")
        response = input("Continue? This will update the existing installation (y/N): ").strip().lower()
        if response != 'y':
            print_info("Installation cancelled")
            sys.exit(0)
    
    os.makedirs(install_path, exist_ok=True)
    print_success(f"Created directory: {install_path}")
    return install_path

def clone_repository(install_path, branch="main"):
    print_step(f"Cloning AGiXT repository (branch: {branch})...")
    
    if os.path.exists(os.path.join(install_path, '.git')):
        print_info("Repository exists, updating...")
        run_command("git fetch origin", cwd=install_path, check=False)
        run_command(f"git checkout {branch}", cwd=install_path, check=False)
        run_command(f"git reset --hard origin/{branch}", cwd=install_path, check=False)
    else:
        # Clone directly to main branch (no fallback needed since main exists)
        clone_cmd = f"git clone --branch {branch} --depth 1 {AGIXT_REPO} ."
        result = run_command(clone_cmd, cwd=install_path, check=False)
        if result.returncode != 0:
            print_error(f"Failed to clone {branch} branch")
            return False
    
    print_success("Repository setup complete")
    return True

def create_env_file(config, install_path):
    env_file = os.path.join(install_path, '.env')
    print_step(f"Creating fixed .env file: {env_file}")
    
    try:
        with open(env_file, 'w') as f:
            f.write("# AGiXT Configuration - FIXED VERSION\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# Fixes: Branch logic, AUTH_PROVIDER, Docker networking, AUTH_WEB\n\n")
            
            # Write all configuration variables
            for key, value in sorted(config.items()):
                if not value or value.startswith('"'):
                    f.write(f'{key}={value}\n')
                else:
                    f.write(f'{key}="{value}"\n')
        
        os.chmod(env_file, 0o600)
        print_success("Environment file created with fixes applied")
        return env_file
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        sys.exit(1)

def start_services(install_path):
    print_step("Starting AGiXT services...")
    
    original_cwd = os.getcwd()
    os.chdir(install_path)
    
    try:
        # Stop existing containers
        run_command("docker compose down", check=False)
        
        # Start services
        result = run_command("docker compose up -d")
        if result.returncode == 0:
            print_success("Services started successfully!")
            return True
        else:
            print_error("Failed to start services")
            return False
    finally:
        os.chdir(original_cwd)

def wait_for_services(config):
    print_step("Waiting for services to be ready...")
    
    api_url = config.get('AGIXT_URI', 'http://localhost:7437')
    web_url = config.get('APP_URI', 'http://localhost:3437')
    
    print_info(f"API URL: {api_url}")
    print_info(f"Web URL: {web_url}")
    
    # Wait a bit for services to start
    time.sleep(30)
    
    return api_url, web_url

def show_summary(install_path, config, api_url, web_url):
    print("\n" + "="*70)
    print("🎉 AGiXT Installation Complete - FIXED VERSION!")
    print("="*70)
    
    print(f"\n📁 Installation Details:")
    print(f"   Location: {install_path}")
    print(f"   Branch: {config.get('AGIXT_BRANCH', 'main')} (corrected)")
    
    print(f"\n🔧 Applied Fixes:")
    print(f"   ✅ Branch: Using 'main' (AGiXT's primary branch)")
    print(f"   ✅ AUTH_PROVIDER: Single value 'magicalauth'")
    print(f"   ✅ AUTH_WEB: Points to user interface with /user path")
    print(f"   ✅ AGIXT_SERVER: Internal Docker networking")
    print(f"   ✅ API Key: Temporarily disabled for testing")
    
    print(f"\n🌐 Service URLs:")
    print(f"   Web Interface: {web_url}")
    print(f"   API Endpoint:  {api_url}")
    
    print(f"\n🚀 Next Steps:")
    print("   1. Open the web interface in your browser")
    print("   2. Try logging in with your email address")
    print("   3. Google Authenticator should now work!")
    print("   4. After testing, re-enable API key requirement")
    
    print(f"\n💡 Commands:")
    print(f"   View logs: cd {install_path} && docker compose logs -f")
    print(f"   Restart:   cd {install_path} && docker compose restart")

def main():
    print("╔═══════════════════════════════════════════════════╗")
    print("║           AGiXT Fixed Installer v2.2             ║")
    print("║                                                   ║")
    print("║ Fixes authentication and branch issues            ║")
    print("╚═══════════════════════════════════════════════════╝")
    
    if len(sys.argv) < 2:
        print_error("Missing required argument: CONFIG_NAME")
        print("\nUsage: python3 install-agixt-fixed.py <config_name> [github_token]")
        print("Example: python3 install-agixt-fixed.py AGIXT_0529_1056 github_pat_xxxxx")
        sys.exit(1)
    
    config_name = sys.argv[1]
    github_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    if github_token:
        os.environ['GITHUB_TOKEN'] = github_token
        print_success("GitHub token configured")
    
    env_url = f"{GITHUB_REPO_BASE}/{config_name}.env"
    env_file = f"{config_name}.env"
    
    print_info(f"Configuration: {config_name}")
    
    try:
        # Download configuration
        if not download_file(env_url, env_file):
            sys.exit(1)
        
        # Load and fix configuration
        config = load_env_config(env_file)
        config = fix_configuration(config, config_name)
        
        # Create installation directory
        install_path = create_installation_directory(config_name)
        
        # Clone repository with correct branch
        branch = config.get('AGIXT_BRANCH', 'main')
        if not clone_repository(install_path, branch):
            sys.exit(1)
        
        # Create fixed .env file
        create_env_file(config, install_path)
        
        # Start services
        if not start_services(install_path):
            sys.exit(1)
        
        # Wait for services
        api_url, web_url = wait_for_services(config)
        
        # Show summary
        show_summary(install_path, config, api_url, web_url)
        
        print(f"\n✨ Fixed installation completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\nInstallation cancelled")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)
    finally:
        # Clean up temp files
        if os.path.exists(env_file):
            os.remove(env_file)

if __name__ == "__main__":
    main()
