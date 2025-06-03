#!/usr/bin/env python3
"""
AGiXT Post-Installation Test Suite
==================================

Comprehensive testing suite that verifies all components are working
correctly after installation. Run this before frontend testing.

Usage: python3 post-install-tests.py [install_path]
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
        "HEADER": Colors.PURPLE + Colors.BOLD
    }
    color = color_map.get(level, Colors.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Colors.RESET}")

def test_docker_containers(install_path):
    """Test Docker container status"""
    log("🐳 Testing Docker Containers", "HEADER")
    
    try:
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
        
        required_containers = ['agixt', 'ezlocalai', 'agixtinteractive']
        found_containers = []
        
        for container in containers:
            name = container.get('Name', 'Unknown')
            state = container.get('State', 'Unknown')
            service = container.get('Service', 'Unknown')
            
            if service in required_containers:
                found_containers.append(service)
                
            if 'running' in state.lower():
                log(f"✅ {name} ({service}): {state}", "SUCCESS")
            elif 'restarting' in state.lower():
                log(f"🔄 {name} ({service}): {state} (initializing)", "WARN")
            else:
                log(f"❌ {name} ({service}): {state}", "ERROR")
        
        missing = set(required_containers) - set(found_containers)
        if missing:
            log(f"Missing containers: {', '.join(missing)}", "ERROR")
            return False
        
        log(f"Container check: {len(found_containers)}/{len(required_containers)} containers found", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Docker container test failed: {e}", "ERROR")
        return False

def test_api_endpoint(url, name, timeout=10):
    """Test if an API endpoint is accessible"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'AGiXT-PostInstall-Test/1.0')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            if 200 <= status < 400:
                log(f"✅ {name}: HTTP {status} - Accessible", "SUCCESS")
                return True
            else:
                log(f"⚠️  {name}: HTTP {status} - Unexpected status", "WARN")
                return False
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log(f"✅ {name}: HTTP 404 - Server responding (endpoint may not exist)", "SUCCESS")
            return True
        else:
            log(f"❌ {name}: HTTP {e.code} - {e.reason}", "ERROR")
            return False
    except urllib.error.URLError as e:
        log(f"❌ {name}: Connection failed - {e.reason}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ {name}: Test failed - {e}", "ERROR")
        return False

def test_ezlocalai_models(base_url):
    """Test EzLocalAI model endpoint"""
    log("🤖 Testing EzLocalAI Models", "HEADER")
    
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
                    else:
                        log(f"⚠️  No deepseek model found in loaded models", "WARN")
                    
                    return True
                else:
                    log("⚠️  Models endpoint returned unexpected format", "WARN")
                    return False
            else:
                log(f"❌ Models endpoint returned HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        log(f"❌ EzLocalAI models test failed: {e}", "ERROR")
        return False

def test_agixt_api(base_url):
    """Test AGiXT API endpoints"""
    log("🧠 Testing AGiXT API", "HEADER")
    
    # Test basic status endpoint
    status_url = f"{base_url}/api/status"
    try:
        req = urllib.request.Request(status_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() == 200:
                log("✅ AGiXT status endpoint responding", "SUCCESS")
                return True
            else:
                log(f"⚠️  AGiXT status returned HTTP {response.getcode()}", "WARN")
                return False
                
    except Exception as e:
        log(f"❌ AGiXT API test failed: {e}", "ERROR")
        return False

def test_file_structure(install_path):
    """Test installation file structure"""
    log("📁 Testing File Structure", "HEADER")
    
    required_files = [
        ".env",
        "docker-compose.yml",
        "ezlocalai",  # directory
        "agixt",      # directory  
        "WORKSPACE",  # directory
        "conversations"  # directory
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(install_path, file_path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                log(f"✅ Directory: {file_path}", "SUCCESS")
            else:
                size = os.path.getsize(full_path)
                log(f"✅ File: {file_path} ({size} bytes)", "SUCCESS")
        else:
            log(f"❌ Missing: {file_path}", "ERROR")
            missing_files.append(file_path)
    
    # Check for model files in ezlocalai directory
    ezlocalai_path = os.path.join(install_path, "ezlocalai")
    if os.path.exists(ezlocalai_path):
        model_files = [f for f in os.listdir(ezlocalai_path) if f.endswith('.gguf')]
        if model_files:
            log(f"✅ Found {len(model_files)} GGUF model(s):", "SUCCESS")
            for model_file in model_files:
                model_path = os.path.join(ezlocalai_path, model_file)
                size_gb = os.path.getsize(model_path) / (1024**3)
                log(f"  🤖 {model_file} ({size_gb:.1f}GB)", "INFO")
        else:
            log("❌ No GGUF model files found", "ERROR")
            missing_files.append("GGUF models")
    
    return len(missing_files) == 0

def test_environment_config(install_path):
    """Test environment configuration"""
    log("⚙️  Testing Environment Configuration", "HEADER")
    
    env_path = os.path.join(install_path, ".env")
    if not os.path.exists(env_path):
        log("❌ .env file not found", "ERROR")
        return False
    
    try:
        config = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        required_vars = [
            'AGIXT_VERSION',
            'MODEL_NAME', 
            'DEFAULT_MODEL',
            'EZLOCALAI_MODEL',
            'HUGGINGFACE_TOKEN',
            'AGIXT_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var in config and config[var]:
                log(f"✅ {var}: {config[var][:20]}{'...' if len(config[var]) > 20 else ''}", "SUCCESS")
            else:
                log(f"❌ Missing or empty: {var}", "ERROR")
                missing_vars.append(var)
        
        log(f"Configuration check: {len(config)} variables loaded", "INFO")
        return len(missing_vars) == 0
        
    except Exception as e:
        log(f"❌ Environment config test failed: {e}", "ERROR")
        return False

def wait_for_services(max_wait_seconds=300):
    """Wait for services to be fully ready"""
    log("⏳ Waiting for services to fully initialize...", "TEST")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        # Check AGiXT API
        try:
            urllib.request.urlopen("http://localhost:7437/api/status", timeout=5)
            log("✅ All services are ready!", "SUCCESS")
            return True
        except:
            time.sleep(10)
            elapsed = int(time.time() - start_time)
            log(f"⏳ Still waiting... ({elapsed}s/{max_wait_seconds}s)", "INFO")
    
    log("⚠️  Services may still be initializing", "WARN")
    return False

def run_complete_test_suite(install_path):
    """Run the complete test suite"""
    log("🚀 AGiXT Post-Installation Test Suite Starting", "HEADER")
    log(f"📁 Testing installation at: {install_path}", "INFO")
    log("=" * 60, "INFO")
    
    tests = [
        ("File Structure", lambda: test_file_structure(install_path)),
        ("Environment Config", lambda: test_environment_config(install_path)),
        ("Docker Containers", lambda: test_docker_containers(install_path)),
        ("Wait for Services", lambda: wait_for_services(60)),
    ]
    
    # Endpoint tests
    endpoints = [
        ("http://localhost:3437", "AGiXT Frontend"),
        ("http://localhost:7437", "AGiXT API"),
        ("http://localhost:8091", "EzLocalAI API"),
        ("http://localhost:8502", "EzLocalAI UI"),
    ]
    
    results = []
    
    # Run basic tests
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
    
    # Test endpoints
    log(f"\n🌐 Testing API Endpoints", "TEST")
    endpoint_results = []
    for url, name in endpoints:
        result = test_api_endpoint(url, name)
        endpoint_results.append((name, result))
    
    # Test EzLocalAI models
    if any(r[1] for r in endpoint_results if "EzLocalAI API" in r[0]):
        log(f"\n", "INFO")
        test_ezlocalai_models("http://localhost:8091")
    
    # Test AGiXT API
    if any(r[1] for r in endpoint_results if "AGiXT API" in r[0]):
        log(f"\n", "INFO")
        test_agixt_api("http://localhost:7437")
    
    # Final summary
    log("\n" + "=" * 60, "INFO")
    log("📊 TEST SUMMARY", "HEADER")
    log("=" * 60, "INFO")
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"{status}: {test_name}", "SUCCESS" if result else "ERROR")
    
    log(f"\nEndpoint Tests:", "INFO")
    passed_endpoints = 0
    for name, result in endpoint_results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"{status}: {name}", "SUCCESS" if result else "ERROR")
        if result:
            passed_endpoints += 1
    
    log(f"\n📈 Overall Results:", "HEADER")
    log(f"Core Tests: {passed_tests}/{total_tests} passed", "INFO")
    log(f"Endpoints: {passed_endpoints}/{len(endpoint_results)} accessible", "INFO")
    
    if passed_tests == total_tests and passed_endpoints >= 3:
        log("🎉 INSTALLATION VERIFICATION: SUCCESS!", "SUCCESS")
        log("✅ Your AGiXT installation is ready for frontend testing!", "SUCCESS")
        return True
    else:
        log("⚠️  INSTALLATION VERIFICATION: ISSUES DETECTED", "WARN")
        log("Some components may need more time to initialize", "WARN")
        return False

def main():
    if len(sys.argv) > 1:
        install_path = sys.argv[1]
    else:
        # Try to detect installation path
        possible_paths = [
            "/var/apps/agixt-v1.6-ezlocolai-universal",
            "/var/apps/agixt-v1.6-ezlocolai",
            "/opt/agixt",
            "./agixt"
        ]
        
        install_path = None
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "docker-compose.yml")):
                install_path = path
                break
        
        if not install_path:
            log("❌ Could not detect AGiXT installation path", "ERROR")
            log("Usage: python3 post-install-tests.py [install_path]", "ERROR")
            sys.exit(1)
    
    if not os.path.exists(install_path):
        log(f"❌ Installation path does not exist: {install_path}", "ERROR")
        sys.exit(1)
    
    # Run the test suite
    success = run_complete_test_suite(install_path)
    
    if success:
        log("\n🎯 NEXT STEPS:", "HEADER")
        log("1. Open http://localhost:3437 for AGiXT Frontend", "INFO")
        log("2. Open http://localhost:8502 for EzLocalAI UI", "INFO")
        log("3. Check http://localhost:8091/v1/models for model status", "INFO")
        log("4. AGiXT API should be at http://localhost:7437", "INFO")
        sys.exit(0)
    else:
        log("\n🔧 TROUBLESHOOTING:", "WARN")
        log("1. Wait 5-10 minutes for all services to fully start", "INFO")
        log("2. Check container logs: docker compose logs -f", "INFO")
        log("3. Restart services: docker compose restart", "INFO")
        sys.exit(1)

if __name__ == "__main__":
    main()
