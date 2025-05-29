#!/usr/bin/env python3
import os
import sys
import subprocess
import urllib.request
import time

GITHUB_REPO_BASE = "https://raw.githubusercontent.com/mocher01/agixt-configs/main"
AGIXT_REPO = "https://github.com/Josh-XT/AGiXT.git"
DEFAULT_BASE_PATH = "/var/apps"

def print_step(msg): print(f"\n🚀 {msg}")
def print_success(msg): print(f"✅ {msg}")
def print_warning(msg): print(f"⚠️  {msg}")
def print_error(msg): print(f"❌ {msg}")
def print_info(msg): print(f"ℹ️  {msg}")

def run_command(command, cwd=None, check=True):
    try:
        print_info(f"Running: {command}")
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, check=check)
        if result.stdout: print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        if e.stderr: print_error(f"Error: {e.stderr}")
        if check: sys.exit(1)
        return e

def download_file(url, filename):
    try:
        print_info(f"Downloading {filename}")
        urllib.request.urlretrieve(url, filename)
        print_success(f"Downloaded {filename}")
        return True
    except Exception as e:
        print_error(f"Failed to download {filename}: {e}")
        return False

def load_env_config(env_file):
    config = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"'')
        print_success(f"Loaded {len(config)} configuration variables")
        return config
    except Exception as e:
        print_error(f"Failed to load {env_file}: {e}")
        sys.exit(1)

def create_installation_directory(config_name):
    install_path = os.path.join(DEFAULT_BASE_PATH, config_name)
    print_step(f"Creating installation directory: {install_path}")
    os.makedirs(install_path, exist_ok=True)
    print_success(f"Created directory: {install_path}")
    return install_path

def clone_repository(install_path, branch="main"):
    print_step(f"Cloning AGiXT repository (branch: {branch})...")
    clone_cmd = f"git clone --branch {branch} --depth 1 {AGIXT_REPO} ."
    result = run_command(clone_cmd, cwd=install_path, check=False)
    if result.returncode != 0:
        print_error(f"Failed to clone {branch} branch")
        return False
    print_success("Repository setup complete")
    return True

def create_env_file(config, install_path):
    env_file = os.path.join(install_path, '.env')
    print_step(f"Creating .env file: {env_file}")
    try:
        with open(env_file, 'w') as f:
            for key, value in sorted(config.items()):
                f.write(f'{key}="{value}"\n')
        os.chmod(env_file, 0o600)
        print_success("Environment file created")
        return env_file
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        sys.exit(1)

def start_services(install_path):
    print_step("Starting AGiXT services...")
    os.chdir(install_path)
    run_command("docker compose down", check=False)
    result = run_command("docker compose up -d")
    return result.returncode == 0

def main():
    print("╔═══════════════════════════════════════════════════╗")
    print("║          AGiXT Minimal Installer (Clean)          ║")
    print("╚═══════════════════════════════════════════════════╝")

    if len(sys.argv) < 2:
        print_error("Missing required argument: CONFIG_NAME")
        print("Usage: python3 install-clean.py <config_name>")
        sys.exit(1)

    config_name = sys.argv[1]
    env_url = f"{GITHUB_REPO_BASE}/{config_name}.env"
    env_file = f"{config_name}.env"

    if not download_file(env_url, env_file): sys.exit(1)

    config = load_env_config(env_file)
    install_path = create_installation_directory(config_name)
    if not clone_repository(install_path, config.get('AGIXT_BRANCH', 'main')): sys.exit(1)
    create_env_file(config, install_path)

    if not start_services(install_path):
        print_error("Failed to start services")
        sys.exit(1)

    print_success("Installation completed. Services are running.")

if __name__ == "__main__":
    main()
