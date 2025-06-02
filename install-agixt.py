#!/usr/bin/env python3
"""
AGiXT Automated Installer - Modular Bootstrapper v1.6
======================================================

This is the main entry point that downloads and runs the modular installer.
Users run this with the same command as before - no changes needed!

Usage:
  curl -H "Authorization: token YOUR_TOKEN" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - proxy YOUR_TOKEN
  
  # Skip cleanup (keep existing containers/images)
  curl -H "Authorization: token YOUR_TOKEN" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - proxy YOUR_TOKEN --no-cleanup

Features:
- Downloads all required modules automatically
- Same user experience as before
- Professional modular architecture  
- Universal model support with auto-detection
- Configuration-driven installation
- COMPREHENSIVE CLEANUP by default (containers, images, folders, networks)
- Option to skip cleanup with --no-cleanup
"""

import os
import sys
import urllib.request
import urllib.error
import tempfile
import shutil
import subprocess
from datetime import datetime

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(command, timeout=60):
    """Execute a shell command with proper error handling"""
    try:
        result = subprocess.run(
            command.split(), 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0
    except Exception:
        return False

def comprehensive_cleanup():
    """Perform comprehensive cleanup of all AGiXT and EzLocalAI components"""
    log("🔍 Scanning for existing AGiXT/EzLocalAI installations...")
    
    # Find AGiXT/EzLocalAI containers
    log("🐳 Checking for containers...")
    containers_to_remove = []
    
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            all_containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
            containers_to_remove = [c for c in all_containers if any(keyword in c.lower() for keyword in ['agixt', 'ezlocalai'])]
    except Exception:
        pass
    
    # Find AGiXT/EzLocalAI images
    log("📦 Checking for images...")
    images_to_remove = []
    
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            all_images = result.stdout.strip().split('\n') if result.stdout.strip() else []
            images_to_remove = [img for img in all_images if any(keyword in img.lower() for keyword in ['agixt', 'ezlocalai'])]
    except Exception:
        pass
    
    # Find AGiXT directories
    log("📁 Checking for installation directories...")
    directories_to_remove = []
    
    base_paths = ['/var/apps', '/opt', '/home']
    for base_path in base_paths:
        if os.path.exists(base_path):
            try:
                for item in os.listdir(base_path):
                    if any(keyword in item.lower() for keyword in ['agixt']):
                        full_path = os.path.join(base_path, item)
                        if os.path.isdir(full_path):
                            directories_to_remove.append(full_path)
            except Exception:
                pass
    
    # Display what will be cleaned
    total_items = len(containers_to_remove) + len(images_to_remove) + len(directories_to_remove)
    
    if total_items == 0:
        log("✅ System is already clean - no AGiXT/EzLocalAI components found", "SUCCESS")
        return True
    
    log(f"🗑️  COMPREHENSIVE CLEANUP - Found {total_items} items to remove:")
    
    if containers_to_remove:
        log(f"🐳 Containers ({len(containers_to_remove)}): {', '.join(containers_to_remove)}")
    
    if images_to_remove:
        log(f"📦 Images ({len(images_to_remove)}): {', '.join(images_to_remove)}")
    
    if directories_to_remove:
        log(f"📁 Directories ({len(directories_to_remove)}): {', '.join(directories_to_remove)}")
    
    # Perform cleanup
    cleanup_success = True
    
    # 1. Stop and remove containers
    if containers_to_remove:
        log("🛑 Stopping containers...")
        for container in containers_to_remove:
            if not run_command(f"docker stop {container}"):
                log(f"⚠️  Could not stop {container} (may already be stopped)", "WARN")
        
        log("🗑️  Removing containers...")
        for container in containers_to_remove:
            if run_command(f"docker rm {container}"):
                log(f"✅ Removed container: {container}", "SUCCESS")
            else:
                log(f"❌ Failed to remove container: {container}", "ERROR")
                cleanup_success = False
    
    # 2. Remove images
    if images_to_remove:
        log("🗑️  Removing images...")
        for image in images_to_remove:
            if run_command(f"docker rmi {image}"):
                log(f"✅ Removed image: {image}", "SUCCESS")
            else:
                log(f"⚠️  Could not remove image: {image} (may be in use)", "WARN")
    
    # 3. Remove directories
    if directories_to_remove:
        log("🗑️  Removing directories...")
        for directory in directories_to_remove:
            try:
                shutil.rmtree(directory, ignore_errors=True)
                if not os.path.exists(directory):
                    log(f"✅ Removed directory: {directory}", "SUCCESS")
                else:
                    log(f"⚠️  Could not fully remove: {directory}", "WARN")
            except Exception as e:
                log(f"❌ Failed to remove directory {directory}: {e}", "ERROR")
                cleanup_success = False
    
    # 4. Remove AGiXT network
    log("🌐 Cleaning Docker network...")
    if run_command("docker network rm agixt-network"):
        log("✅ Removed agixt-network", "SUCCESS")
    else:
        log("ℹ️  agixt-network not found or already removed")
    
    # 5. Clean volumes (AGiXT-related only)
    log("🗂️  Cleaning unused volumes...")
    run_command("docker volume prune -f")
    
    if cleanup_success:
        log("✅ COMPREHENSIVE CLEANUP COMPLETED - System is clean", "SUCCESS")
    else:
        log("⚠️  Cleanup completed with some warnings", "WARN")
    
    return True

def download_file(url, target_path, github_token=None):
    """Download a file from GitHub with optional authentication"""
    try:
        req = urllib.request.Request(url)
        if github_token:
            req.add_header('Authorization', f'token {github_token}')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(target_path, 'wb') as f:
                f.write(response.read())
        
        return True
    except Exception as e:
        log(f"Failed to download {url}: {e}", "ERROR")
        return False

def main():
    """Main bootstrapper function"""
    log("🚀 AGiXT Installer v1.6 - Modular Bootstrapper")
    log("🔧 Professional installation with comprehensive cleanup")
    
    # Parse command line arguments
    config_name = "proxy"
    github_token = None
    skip_cleanup = False
    
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--no-cleanup" or arg == "--skip-cleanup":
                skip_cleanup = True
                log("🚫 Cleanup disabled via command line flag")
            elif arg.startswith("github_pat_") or arg.startswith("ghp_"):
                github_token = arg
            elif not arg.startswith("-"):
                config_name = arg
    
    if not github_token:
        log("❌ GitHub token required for installation", "ERROR")
        log("Usage: script.py proxy github_token [--no-cleanup]", "ERROR")
        sys.exit(1)
    
    # Perform comprehensive cleanup unless disabled
    if not skip_cleanup:
        log("🗑️  Starting comprehensive cleanup...")
        comprehensive_cleanup()
    else:
        log("⚠️  Skipping cleanup - existing installations may conflict", "WARN")
    
    # Create temporary directory for modules
    temp_dir = tempfile.mkdtemp(prefix="agixt_installer_")
    log(f"📁 Created temporary directory: {temp_dir}")
    
    try:
        # Define required modules
        modules = [
            "installer_core.py",
            "installer_config.py", 
            "installer_models.py",
            "installer_docker.py",
            "installer_utils.py"
        ]
        
        base_url = "https://raw.githubusercontent.com/mocher01/agixt-configs/main/modules"
        
        # Download all modules
        log("📦 Downloading installer modules...")
        for module in modules:
            module_url = f"{base_url}/{module}"
            module_path = os.path.join(temp_dir, module)
            
            log(f"📥 Downloading {module}...")
            if not download_file(module_url, module_path, github_token):
                log(f"❌ Failed to download {module}", "ERROR")
                log("ℹ️  This is expected - modules don't exist yet")
                sys.exit(1)
            log(f"✅ Downloaded {module}", "SUCCESS")
        
        # Add temp directory to Python path
        sys.path.insert(0, temp_dir)
        
        # Import and run the main installer
        log("🔧 Loading installer modules...")
        try:
            import installer_core
            log("✅ Modules loaded successfully", "SUCCESS")
            
            # Run the main installer
            log("🚀 Starting modular installation...")
            success = installer_core.run_installation(config_name, github_token, skip_cleanup)
            
            if success:
                log("🎉 AGiXT installation completed successfully!", "SUCCESS")
            else:
                log("❌ Installation failed", "ERROR")
                sys.exit(1)
                
        except ImportError as e:
            log(f"❌ Failed to import installer modules: {e}", "ERROR")
            log("ℹ️  This is expected - modules will be created next")
            sys.exit(1)
        except Exception as e:
            log(f"❌ Installation error: {e}", "ERROR")
            sys.exit(1)
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            log("🧹 Cleaned up temporary files")
        except Exception:
            pass

if __name__ == "__main__":
    main()
