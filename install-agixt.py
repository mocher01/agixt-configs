#!/usr/bin/env python3
import os
import sys
import urllib.request
import urllib.error
import tempfile
import shutil
import subprocess
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("[" + timestamp + "] " + level + ": " + str(message))

def run_command(command, timeout=60):
    try:
        result = subprocess.run(
            command.split(), 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0
    except:
        return False

def comprehensive_cleanup():
    log("🔍 Scanning for existing AGiXT/EzLocalAI installations...")
    
    # Find containers
    log("🐳 Checking for containers...")
    containers_to_remove = []
    
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            all_containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
            for c in all_containers:
                if 'agixt' in c.lower() or 'ezlocalai' in c.lower():
                    containers_to_remove.append(c)
    except:
        pass
    
    # Find images
    log("📦 Checking for images...")
    images_to_remove = []
    
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            all_images = result.stdout.strip().split('\n') if result.stdout.strip() else []
            for img in all_images:
                if 'agixt' in img.lower() or 'ezlocalai' in img.lower():
                    images_to_remove.append(img)
    except:
        pass
    
    # Find directories
    log("📁 Checking for installation directories...")
    directories_to_remove = []
    
    base_paths = ['/var/apps', '/opt', '/home']
    for base_path in base_paths:
        if os.path.exists(base_path):
            try:
                for item in os.listdir(base_path):
                    if 'agixt' in item.lower():
                        full_path = os.path.join(base_path, item)
                        if os.path.isdir(full_path):
                            directories_to_remove.append(full_path)
            except:
                pass
    
    # Display what will be cleaned
    total_items = len(containers_to_remove) + len(images_to_remove) + len(directories_to_remove)
    
    if total_items == 0:
        log("✅ System is already clean - no AGiXT/EzLocalAI components found", "SUCCESS")
        return True
    
    log("🗑️  COMPREHENSIVE CLEANUP - Found " + str(total_items) + " items to remove:")
    
    if containers_to_remove:
        log("🐳 Containers (" + str(len(containers_to_remove)) + "): " + ", ".join(containers_to_remove))
    
    if images_to_remove:
        log("📦 Images (" + str(len(images_to_remove)) + "): " + ", ".join(images_to_remove))
    
    if directories_to_remove:
        log("📁 Directories (" + str(len(directories_to_remove)) + "): " + ", ".join(directories_to_remove))
    
    # Perform cleanup
    cleanup_success = True
    
    # Stop and remove containers
    if containers_to_remove:
        log("🛑 Stopping containers...")
        for container in containers_to_remove:
            if not run_command("docker stop " + container):
                log("⚠️  Could not stop " + container + " (may already be stopped)", "WARN")
        
        log("🗑️  Removing containers...")
        for container in containers_to_remove:
            if run_command("docker rm " + container):
                log("✅ Removed container: " + container, "SUCCESS")
            else:
                log("❌ Failed to remove container: " + container, "ERROR")
                cleanup_success = False
    
    # Remove images
    if images_to_remove:
        log("🗑️  Removing images...")
        for image in images_to_remove:
            if run_command("docker rmi " + image):
                log("✅ Removed image: " + image, "SUCCESS")
            else:
                log("⚠️  Could not remove image: " + image + " (may be in use)", "WARN")
    
    # Remove directories
    if directories_to_remove:
        log("🗑️  Removing directories...")
        for directory in directories_to_remove:
            try:
                shutil.rmtree(directory, ignore_errors=True)
                if not os.path.exists(directory):
                    log("✅ Removed directory: " + directory, "SUCCESS")
                else:
                    log("⚠️  Could not fully remove: " + directory, "WARN")
            except Exception as e:
                log("❌ Failed to remove directory " + directory + ": " + str(e), "ERROR")
                cleanup_success = False
    
    # Remove network
    log("🌐 Cleaning Docker network...")
    if run_command("docker network rm agixt-network"):
        log("✅ Removed agixt-network", "SUCCESS")
    else:
        log("ℹ️  agixt-network not found or already removed")
    
    # Clean volumes
    log("🗂️  Cleaning unused volumes...")
    run_command("docker volume prune -f")
    
    if cleanup_success:
        log("✅ COMPREHENSIVE CLEANUP COMPLETED - System is clean", "SUCCESS")
    else:
        log("⚠️  Cleanup completed with some warnings", "WARN")
    
    return True

def download_file(url, target_path, github_token=None):
    try:
        req = urllib.request.Request(url)
        if github_token:
            req.add_header('Authorization', 'token ' + github_token)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(target_path, 'wb') as f:
                f.write(response.read())
        
        return True
    except Exception as e:
        log("Failed to download " + url + ": " + str(e), "ERROR")
        return False

def main():
    log("🚀 AGiXT Installer v1.6 - FULL BOOTSTRAPPER WITH CLEANUP")
    log("🔧 Professional installation with comprehensive cleanup")
    log("🆕 This is the NEW version with comprehensive cleanup functionality")
    
    # Parse command line arguments
    config_name = "proxy"
    github_token = None
    skip_cleanup = False
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
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
    
    log("🔍 CLEANUP PHASE STARTING...")
    
    # Perform comprehensive cleanup unless disabled
    if not skip_cleanup:
        log("🗑️  Starting comprehensive cleanup...")
        comprehensive_cleanup()
    else:
        log("⚠️  Skipping cleanup - existing installations may conflict", "WARN")
    
    log("📦 MODULE DOWNLOAD PHASE STARTING...")
    
    # Create temporary directory for modules
    temp_dir = tempfile.mkdtemp(prefix="agixt_installer_")
    log("📁 Created temporary directory: " + temp_dir)
    
    try:
        # Define required modules - START WITH UTILS TO TEST DOWNLOAD
        modules = [
            "installer_utils.py",     # ← Test this first
            "installer_core.py",
            "installer_config.py", 
            "installer_models.py",
            "installer_docker.py"
        ]
        
        base_url = "https://raw.githubusercontent.com/mocher01/agixt-configs/main/modules"
        
        # Download all modules
        log("📦 Downloading installer modules...")
        downloaded_modules = []
        
        for module in modules:
            module_url = base_url + "/" + module
            module_path = os.path.join(temp_dir, module)
            
            log("📥 Downloading " + module + "...")
            if download_file(module_url, module_path, github_token):
                log("✅ Downloaded " + module, "SUCCESS")
                downloaded_modules.append(module)
            else:
                log("❌ Failed to download " + module, "ERROR")
                log("ℹ️  Continuing with available modules...")
        
        log("📋 Downloaded " + str(len(downloaded_modules)) + " of " + str(len(modules)) + " modules")
        
        # Check if we have enough modules to proceed
        if len(downloaded_modules) == 0:
            log("❌ No modules downloaded - cannot proceed", "ERROR")
            sys.exit(1)
        
        if "installer_core.py" not in downloaded_modules:
            log("❌ installer_core.py required but not available", "ERROR")
            sys.exit(1)
        
        if "installer_utils.py" not in downloaded_modules:
            log("❌ installer_utils.py required but not available", "ERROR")
            sys.exit(1)
        
        log("✅ Essential modules available - proceeding with installation")
        
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
            log("❌ Failed to import installer modules: " + str(e), "ERROR")
            sys.exit(1)
        except Exception as e:
            log("❌ Installation error: " + str(e), "ERROR")
            sys.exit(1)
        
        log("✅ Essential modules available - proceeding with installation")
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            log("🧹 Cleaned up temporary files")
        except:
            pass

if __name__ == "__main__":
    main()
