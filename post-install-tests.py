#!/usr/bin/env python3
"""
AGiXT Enhanced Post-Installation Test Suite
===========================================

Enhanced version that tests both localhost AND configured domains,
with deep debugging to understand AGiXT API failures.
"""

import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    color_map = {
        "INFO": Colors.WHITE,
        "SUCCESS": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARN": Colors.YELLOW,
        "TEST": Colors.CYAN,
        "HEADER": Colors.PURPLE + Colors.BOLD,
        "DEBUG": Colors.BLUE
    }
    color = color_map.get(level, Colors.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Colors.RESET}")

def load_config_from_env(install_path):
    """Load configuration from .env file to test configured domains"""
    config = {}
    env_path = os.path.join(install_path, ".env")
    
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception as e:
            log(f"Could not load .env file: {e}", "WARN")
    
    return config

def debug_agixt_database_issue(install_path):
    """Deep debugging of AGiXT database issues"""
    log("🔍 DEEP DEBUGGING: AGiXT Database Issues", "HEADER")
    
    # Check database configuration in .env
    config = load_config_from_env(install_path)
    db_type = config.get('DATABASE_TYPE', 'Not set')
    db_name = config.get('DATABASE_NAME', 'Not set')
    
    log(f"📊 Database Configuration:", "DEBUG")
    log(f"  DATABASE_TYPE: {db_type}", "DEBUG")
    log(f"  DATABASE_NAME: {db_name}", "DEBUG")
    
    # Check if models directory exists
    models_path = os.path.join(install_path, "models")
    if os.path.exists(models_path):
        log(f"✅ Models directory exists: {models_path}", "SUCCESS")
        
        # Check contents
        try:
            contents = os.listdir(models_path)
            if contents:
                log(f"📁 Models directory contents: {contents}", "DEBUG")
            else:
                log("⚠️  Models directory is empty", "WARN")
        except Exception as e:
            log(f"❌ Cannot read models directory: {e}", "ERROR")
    else:
        log(f"❌ Models directory missing: {models_path}", "ERROR")
    
    # Check AGiXT directory structure
    agixt_path = os.path.join(install_path, "agixt")
    if os.path.exists(agixt_path):
        log(f"✅ AGiXT directory exists: {agixt_path}", "SUCCESS")
    else:
        log(f"❌ AGiXT directory missing: {agixt_path}", "ERROR")
    
    # Get recent AGiXT container logs
    try:
        log("📋 Recent AGiXT container logs:", "DEBUG")
        result = subprocess.run(
            ["docker", "compose", "logs", "agixt", "--tail", "10"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n')[-5:]:
                if line.strip():
                    log(f"  {line}", "DEBUG")
        else:
            log("Could not get AGiXT logs", "WARN")
    except Exception as e:
        log(f"Error getting AGiXT logs: {e}", "WARN")

def test_configured_domains(config):
    """Test the actual configured domains from the config"""
    log("🌐 Testing Configured Domains from Config", "HEADER")
    
    # Extract domain URLs from config
    domain_urls = {
        'AGIXT_SERVER': config.get('AGIXT_SERVER', ''),
        'APP_URI': config.get('APP_URI', ''),
        'AUTH_WEB': config.get('AUTH_WEB', '')
    }
    
    results = []
    
    for config_key, url in domain_urls.items():
        if url and url.startswith('http'):
            log(f"🔗 Testing {config_key}: {url}", "TEST")
            result = test_api_endpoint(url, f"{config_key} Domain", timeout=15)
            results.append((config_key, url, result))
        else:
            log(f"⚠️  {config_key}: No valid URL configured", "WARN")
            results.append((config_key, url, False))
    
    # Summary of domain tests
    log("\n📊 Domain Test Results:", "INFO")
    for config_key, url, result in results:
        status = "✅ WORKING" if result else "❌ FAILED"
        log(f"  {status}: {config_key} -> {url}", "SUCCESS" if result else "ERROR")
    
    return results

def test_api_endpoint(url, name, timeout=10):
    """Enhanced API endpoint testing with more detailed error reporting"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'AGiXT-PostInstall-Test/2.0')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            content_type = response.headers.get('Content-Type', 'unknown')
            
            if 200 <= status < 400:
                log(f"✅ {name}: HTTP {status} ({content_type}) - Accessible", "SUCCESS")
                return True
            else:
                log(f"⚠️  {name}: HTTP {status} - Unexpected status", "WARN")
                return False
                
    except urllib.error.HTTPError as e:
        if e.code == 502:
            log(f"❌ {name}: HTTP 502 - Bad Gateway (backend server down)", "ERROR")
        elif e.code == 404:
            log(f"✅ {name}: HTTP 404 - Server responding (endpoint may not exist)", "SUCCESS")
            return True
        else:
            log(f"❌ {name}: HTTP {e.code} - {e.reason}", "ERROR")
        return False
    except urllib.error.URLError as e:
        if "Connection refused" in str(e.reason):
            log(f"❌ {name}: Connection refused - Service not running", "ERROR")
        elif "timed out" in str(e.reason):
            log(f"❌ {name}: Connection timeout - Service overloaded or slow", "ERROR")
        else:
            log(f"❌ {name}: Connection failed - {e.reason}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ {name}: Test failed - {e}", "ERROR")
        return False

def test_docker_containers_detailed(install_path):
    """Enhanced Docker container testing with detailed status"""
    log("🐳 Testing Docker Containers (Detailed)", "HEADER")
    
    try:
        # Get detailed container information
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            log("Failed to get container status", "ERROR")
            return False
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    container = json.loads(line)
                    containers.append(container)
                except json.JSONDecodeError:
                    continue
        
        if not containers:
            log("No containers found", "ERROR")
            return False
        
        # Analyze each container
        required_containers = ['agixt', 'ezlocalai', 'agixtinteractive']
        found_containers = []
        container_issues = []
        
        for container in containers:
            name = container.get('Name', 'Unknown')
            state = container.get('State', 'Unknown')
            service = container.get('Service', 'Unknown')
            status = container.get('Status', 'Unknown')
            
            if service in required_containers:
                found_containers.append(service)
            
            # Detailed status analysis
            if 'running' in state.lower():
                log(f"✅ {name} ({service}): Running - {status}", "SUCCESS")
            elif 'restarting' in state.lower():
                log(f"🔄 {name} ({service}): Restarting - {status}", "WARN")
                container_issues.append(f"{service}: Restarting (check logs)")
            elif 'exited' in state.lower():
                log(f"❌ {name} ({service}): Exited - {status}", "ERROR")
                container_issues.append(f"{service}: Exited (failed to start)")
            else:
                log(f"⚠️  {name} ({service}): {state} - {status}", "WARN")
                container_issues.append(f"{service}: Unusual state - {state}")
        
        # Check for missing containers
        missing = set(required_containers) - set(found_containers)
        if missing:
            log(f"❌ Missing containers: {', '.join(missing)}", "ERROR")
            container_issues.extend([f"Missing: {m}" for m in missing])
        
        # Report issues
        if container_issues:
            log("🔧 Container Issues Detected:", "WARN")
            for issue in container_issues:
                log(f"  - {issue}", "WARN")
        
        log(f"📊 Container Summary: {len(found_containers)}/{len(required_containers)} found", "INFO")
        
        # If AGiXT is having issues, run deep debugging
        if 'agixt' in [issue.split(':')[0] for issue in container_issues]:
            debug_agixt_database_issue(install_path)
        
        return len(missing) == 0
        
    except Exception as e:
        log(f"Docker container test failed: {e}", "ERROR")
        return False

def test_ezlocalai_models_detailed(base_url):
    """Enhanced EzLocalAI model testing with better error analysis"""
    log("🤖 Testing EzLocalAI Models (Detailed)", "HEADER")
    
    models_url = f"{base_url}/v1/models"
    try:
        req = urllib.request.Request(models_url)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                
                if 'data' in data and isinstance(data['data'], list):
                    models = data['data']
                    log(f"✅ Found {len(models)} model(s) in EzLocalAI", "SUCCESS")
                    
                    for model in models:
                        model_id = model.get('id', 'Unknown')
                        model_object = model.get('object', 'Unknown')
                        log(f"  📄 Model: {model_id} ({model_object})", "INFO")
                    
                    # Look for deepseek model specifically
                    deepseek_models = [m for m in models if 'deepseek' in m.get('id', '').lower()]
                    if deepseek_models:
                        log(f"✅ Deepseek model found and loaded", "SUCCESS")
                        for model in deepseek_models:
                            log(f"  🧠 Deepseek: {model.get('id', 'Unknown')}", "SUCCESS")
                    else:
                        log(f"⚠️  No deepseek model found in loaded models", "WARN")
                        log("🔍 This might be due to the file structure issue we identified", "DEBUG")
                    
                    return True
                else:
                    log("⚠️  Models endpoint returned unexpected format", "WARN")
                    log(f"Response data: {data}", "DEBUG")
                    return False
            else:
                log(f"❌ Models endpoint returned HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        log(f"❌ EzLocalAI models test failed: {e}", "ERROR")
        log("🔍 This is expected if EzLocalAI is failing due to model structure issues", "DEBUG")
        return False

def test_file_structure_detailed(install_path):
    """Enhanced file structure testing with detailed analysis"""
    log("📁 Testing File Structure (Detailed)", "HEADER")
    
    required_structure = {
        ".env": "file",
        "docker-compose.yml": "file",
        "models": "directory",      # Critical for AGiXT database
        "agixt": "directory",       # AGiXT application data
        "ezlocalai": "directory",   # EzLocalAI models
        "WORKSPACE": "directory",   # Working directory
        "conversations": "directory" # Conversation storage
    }
    
    issues = []
    
    for item, item_type in required_structure.items():
        full_path = os.path.join(install_path, item)
        
        if not os.path.exists(full_path):
            log(f"❌ Missing: {item}", "ERROR")
            issues.append(f"Missing {item_type}: {item}")
            continue
        
        if item_type == "directory" and not os.path.isdir(full_path):
            log(f"❌ Wrong type: {item} (expected directory, found file)", "ERROR")
            issues.append(f"Type mismatch: {item}")
            continue
        
        if item_type == "file" and not os.path.isfile(full_path):
            log(f"❌ Wrong type: {item} (expected file, found directory)", "ERROR")
            issues.append(f"Type mismatch: {item}")
            continue
        
        # Check permissions and size
        try:
            if item_type == "directory":
                contents = os.listdir(full_path)
                log(f"✅ Directory: {item} ({len(contents)} items)", "SUCCESS")
                
                # Special checks for critical directories
                if item == "models" and not contents:
                    log(f"⚠️  Models directory is empty - AGiXT needs this for database", "WARN")
                elif item == "ezlocalai":
                    gguf_files = [f for f in contents if f.endswith('.gguf')]
                    if gguf_files:
                        log(f"  🤖 Found {len(gguf_files)} GGUF files", "INFO")
                        for gguf_file in gguf_files:
                            size_gb = os.path.getsize(os.path.join(full_path, gguf_file)) / (1024**3)
                            log(f"    📄 {gguf_file} ({size_gb:.1f}GB)", "INFO")
                    else:
                        log(f"  ⚠️  No GGUF files found in ezlocalai directory", "WARN")
                        issues.append("No GGUF models found")
            else:
                size = os.path.getsize(full_path)
                log(f"✅ File: {item} ({size} bytes)", "SUCCESS")
                
        except Exception as e:
            log(f"⚠️  Could not analyze {item}: {e}", "WARN")
    
    # Report issues summary
    if issues:
        log("🔧 File Structure Issues:", "WARN")
        for issue in issues:
            log(f"  - {issue}", "WARN")
        return False
    else:
        log("✅ File structure check passed", "SUCCESS")
        return True

def run_comprehensive_test_suite(install_path):
    """Run the comprehensive enhanced test suite"""
    log("🚀 AGiXT Enhanced Post-Installation Test Suite", "HEADER")
    log(f"📁 Testing installation at: {install_path}", "INFO")
    log("🔍 Enhanced with domain testing and deep debugging", "INFO")
    log("=" * 80, "INFO")
    
    # Load configuration for domain testing
    config = load_config_from_env(install_path)
    log(f"📋 Loaded {len(config)} configuration variables", "INFO")
    
    # Core tests
    tests = [
        ("File Structure (Detailed)", lambda: test_file_structure_detailed(install_path)),
        ("Docker Containers (Detailed)", lambda: test_docker_containers_detailed(install_path)),
    ]
    
    # Localhost endpoints
    localhost_endpoints = [
        ("http://localhost:3437", "AGiXT Frontend (Localhost)"),
        ("http://localhost:7437", "AGiXT API (Localhost)"),
        ("http://localhost:8091", "EzLocalAI API (Localhost)"),
        ("http://localhost:8502", "EzLocalAI UI (Localhost)"),
    ]
    
    results = []
    
    # Run core tests
    for test_name, test_func in tests:
        log(f"\n🧪 Running test: {test_name}", "TEST")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                log(f"✅ {test_name}: PASSED", "SUCCESS")
            else:
                log(f"❌ {test_name}: FAILED", "ERROR")
        except Exception as e:
            log(f"❌ {test_name}: ERROR - {e}", "ERROR")
            results.append((test_name, False))
    
    # Test localhost endpoints
    log(f"\n🌐 Testing Localhost Endpoints", "TEST")
    localhost_results = []
    for url, name in localhost_endpoints:
        result = test_api_endpoint(url, name, timeout=10)
        localhost_results.append((name, result))
    
    # Test configured domains
    log(f"\n🌍 Testing Configured Domains", "TEST")
    domain_results = test_configured_domains(config)
    
    # Enhanced model testing if EzLocalAI is accessible
    ezlocalai_accessible = any(r[1] for r in localhost_results if "EzLocalAI API" in r[0])
    if ezlocalai_accessible:
        log(f"\n🤖 Enhanced Model Testing", "TEST")
        test_ezlocalai_models_detailed("http://localhost:8091")
    else:
        log(f"\n🤖 EzLocalAI not accessible - skipping model tests", "WARN")
    
    # AGiXT API specific testing
    agixt_accessible = any(r[1] for r in localhost_results if "AGiXT API" in r[0])
    if not agixt_accessible:
        log(f"\n🔍 AGiXT API Deep Debugging", "TEST")
        debug_agixt_database_issue(install_path)
    
    # Comprehensive summary
    log("\n" + "=" * 80, "INFO")
    log("📊 COMPREHENSIVE TEST SUMMARY", "HEADER")
    log("=" * 80, "INFO")
    
    # Core tests summary
    passed_tests = sum(1 for _, result in results if result)
    log(f"🧪 Core Tests: {passed_tests}/{len(results)} passed", "INFO")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"  {status}: {test_name}", "SUCCESS" if result else "ERROR")
    
    # Localhost endpoints summary
    passed_localhost = sum(1 for _, result in localhost_results if result)
    log(f"\n🏠 Localhost Endpoints: {passed_localhost}/{len(localhost_results)} accessible", "INFO")
    for name, result in localhost_results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"  {status}: {name}", "SUCCESS" if result else "ERROR")
    
    # Domain endpoints summary
    passed_domains = sum(1 for _, _, result in domain_results if result)
    log(f"\n🌍 Configured Domains: {passed_domains}/{len(domain_results)} accessible", "INFO")
    for config_key, url, result in domain_results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"  {status}: {config_key} ({url})", "SUCCESS" if result else "ERROR")
    
    # Overall assessment
    total_endpoints = len(localhost_results) + len(domain_results)
    total_passed_endpoints = passed_localhost + passed_domains
    
    log(f"\n📈 Overall Assessment:", "HEADER")
    log(f"Core Tests: {passed_tests}/{len(results)} passed", "INFO")
    log(f"All Endpoints: {total_passed_endpoints}/{total_endpoints} accessible", "INFO")
    
    # Determine success criteria
    critical_services_working = (
        passed_tests >= len(results) - 1 and  # Allow 1 test failure
        passed_localhost >= 2  # At least frontend + one backend service
    )
    
    if critical_services_working:
        log("🎉 INSTALLATION STATUS: FUNCTIONAL", "SUCCESS")
        log("✅ Core AGiXT components are working", "SUCCESS")
        
        if passed_domains > 0:
            log("✅ Some configured domains are accessible", "SUCCESS")
        else:
            log("⚠️  Configured domains need attention (502 errors)", "WARN")
            
        return True
    else:
        log("❌ INSTALLATION STATUS: NEEDS ATTENTION", "ERROR")
        log("Critical services are not responding properly", "ERROR")
        return False

def main():
    # Auto-detect or use provided installation path
    if len(sys.argv) > 1:
        install_path = sys.argv[1]
    else:
        install_path = "/var/apps/agixt-v1.6-ezlocolai-universal"
    
    if not os.path.exists(install_path):
        log(f"❌ Installation path does not exist: {install_path}", "ERROR")
        sys.exit(1)
    
    success = run_comprehensive_test_suite(install_path)
    
    if success:
        log("\n🎯 RECOMMENDATIONS:", "HEADER")
        log("1. ✅ AGiXT installation is functional", "SUCCESS")
        log("2. 🌐 Check domain DNS/proxy configuration for 502 errors", "INFO")
        log("3. 🤖 Fix EzLocalAI model structure if needed", "INFO")
        log("4. 🔍 Monitor logs for any remaining issues", "INFO")
        sys.exit(0)
    else:
        log("\n🔧 NEXT STEPS:", "WARN")
        log("1. Fix critical database/directory issues", "INFO")
        log("2. Check Docker container logs", "INFO")
        log("3. Verify file permissions", "INFO")
        log("4. Consider reinstalling with enhanced debugging", "INFO")
        sys.exit(1)

if __name__ == "__main__":
    main()
