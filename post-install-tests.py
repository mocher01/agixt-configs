#!/usr/bin/env python3
"""
AGiXT Enhanced Post-Installation Test Suite
===========================================

Enhanced version that validates token configurations, model settings,
and performs comprehensive debugging to catch installer issues early.

NEW FEATURES:
- Token limit validation (checks for 16K vs 2048 mismatch)
- Agent configuration verification
- Model path validation
- Provider settings check
- Deep debugging of configuration mismatches
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
        "DEBUG": Colors.BLUE,
        "CRITICAL": Colors.RED + Colors.BOLD
    }
    color = color_map.get(level, Colors.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Colors.RESET}")

def load_config_from_env(install_path):
    """Load configuration from .env file"""
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

def load_agent_config(install_path, agent_name="XT"):
    """Load agent configuration from JSON file"""
    agent_path = os.path.join(install_path, "models", "agents", f"{agent_name}.json")
    
    if os.path.exists(agent_path):
        try:
            with open(agent_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            log(f"Could not load agent config: {e}", "WARN")
            return {}
    else:
        log(f"Agent config file not found: {agent_path}", "WARN")
        return {}

def test_token_configuration_comprehensive(install_path):
    """CRITICAL: Test for the token limit mismatch issue"""
    log("🔢 TESTING TOKEN CONFIGURATION (CRITICAL)", "HEADER")
    
    config = load_config_from_env(install_path)
    agent_config = load_agent_config(install_path)
    
    issues = []
    warnings = []
    
    # 1. Check environment variables
    log("📋 Environment Token Configuration:", "TEST")
    
    llm_max_tokens = config.get('LLM_MAX_TOKENS', 'NOT_SET')
    ezlocalai_max_tokens = config.get('EZLOCALAI_MAX_TOKENS', 'NOT_SET')
    default_model = config.get('DEFAULT_MODEL', 'NOT_SET')
    
    log(f"  LLM_MAX_TOKENS: {llm_max_tokens}", "DEBUG")
    log(f"  EZLOCALAI_MAX_TOKENS: {ezlocalai_max_tokens}", "DEBUG")
    log(f"  DEFAULT_MODEL: {default_model}", "DEBUG")
    
    # 2. Check agent configuration
    log("👤 Agent Token Configuration:", "TEST")
    
    agent_provider = "NOT_SET"
    agent_max_tokens = "NOT_SET"
    agent_model = "NOT_SET"
    
    if agent_config and 'settings' in agent_config:
        settings = agent_config['settings']
        agent_provider = settings.get('provider', 'NOT_SET')
        agent_max_tokens = settings.get('MAX_TOKENS', 'NOT_SET')
        agent_model = settings.get('AI_MODEL', 'NOT_SET')
    
    log(f"  Agent Provider: {agent_provider}", "DEBUG")
    log(f"  Agent MAX_TOKENS: {agent_max_tokens}", "DEBUG")
    log(f"  Agent AI_MODEL: {agent_model}", "DEBUG")
    
    # 3. CRITICAL VALIDATIONS
    log("🎯 Critical Token Validation:", "TEST")
    
    # Check for the 16K token limit bug
    if ezlocalai_max_tokens in ['0', 'NOT_SET']:
        issues.append("EZLOCALAI_MAX_TOKENS is 0 or missing - will cause 16K token limit bug!")
        log("❌ CRITICAL: EZLOCALAI_MAX_TOKENS=0 will cause AGiXT to use 16000 token limit", "CRITICAL")
    elif ezlocalai_max_tokens == '2048':
        log("✅ EZLOCALAI_MAX_TOKENS correctly set to 2048", "SUCCESS")
    else:
        warnings.append(f"EZLOCALAI_MAX_TOKENS={ezlocalai_max_tokens} (expected 2048 for Phi-2)")
        log(f"⚠️  EZLOCALAI_MAX_TOKENS={ezlocalai_max_tokens} (expected 2048)", "WARN")
    
    # Check agent token consistency
    if agent_max_tokens == '4096':
        issues.append("Agent MAX_TOKENS=4096 (hardcoded default from installer bug)")
        log("❌ CRITICAL: Agent MAX_TOKENS=4096 suggests installer wasn't fixed", "CRITICAL")
    elif agent_max_tokens == '2048':
        log("✅ Agent MAX_TOKENS correctly set to 2048", "SUCCESS")
    elif agent_max_tokens == 'NOT_SET':
        issues.append("Agent configuration missing or corrupted")
        log("❌ Agent MAX_TOKENS not found in configuration", "ERROR")
    else:
        warnings.append(f"Agent MAX_TOKENS={agent_max_tokens} (unexpected value)")
        log(f"⚠️  Agent MAX_TOKENS={agent_max_tokens} (unusual value)", "WARN")
    
    # Check provider setting
    if agent_provider == 'rotation':
        issues.append("Agent provider=rotation (should be ezlocalai)")
        log("❌ CRITICAL: Agent provider=rotation will cause failures", "CRITICAL")
    elif agent_provider == 'ezlocalai':
        log("✅ Agent provider correctly set to ezlocalai", "SUCCESS")
    else:
        issues.append(f"Agent provider={agent_provider} (unexpected)")
        log(f"❌ Agent provider={agent_provider} (should be ezlocalai)", "ERROR")
    
    # Check model configuration
    if 'phi-2' in default_model.lower():
        log("✅ DEFAULT_MODEL is Phi-2 based", "SUCCESS")
        
        # For Phi-2, validate 2048 token limit
        if ezlocalai_max_tokens != '2048':
            issues.append(f"Phi-2 model requires 2048 tokens, but EZLOCALAI_MAX_TOKENS={ezlocalai_max_tokens}")
    elif 'tinyllama' in default_model.lower():
        log("⚠️  DEFAULT_MODEL is TinyLlama (known to have case sensitivity issues)", "WARN")
        warnings.append("TinyLlama may have filename case sensitivity issues with EzLocalAI")
    elif default_model == 'NOT_SET':
        issues.append("DEFAULT_MODEL not configured")
        log("❌ DEFAULT_MODEL not set", "ERROR")
    else:
        log(f"ℹ️  DEFAULT_MODEL: {default_model}", "INFO")
    
    # 4. Check docker-compose token settings
    log("🐳 Docker Compose Token Settings:", "TEST")
    
    docker_compose_path = os.path.join(install_path, "docker-compose.yml")
    if os.path.exists(docker_compose_path):
        try:
            with open(docker_compose_path, 'r') as f:
                compose_content = f.read()
                
            if 'LLM_MAX_TOKENS:-0}' in compose_content:
                issues.append("Docker compose has LLM_MAX_TOKENS:-0} (unlimited tokens bug)")
                log("❌ CRITICAL: docker-compose.yml has LLM_MAX_TOKENS:-0}", "CRITICAL")
            elif 'LLM_MAX_TOKENS:-2048}' in compose_content:
                log("✅ Docker compose correctly defaults to 2048 tokens", "SUCCESS")
            else:
                log("ℹ️  Docker compose token settings appear custom", "INFO")
                
        except Exception as e:
            log(f"Could not analyze docker-compose.yml: {e}", "WARN")
    
    # 5. Summary and recommendations
    log("📊 Token Configuration Summary:", "HEADER")
    
    if issues:
        log("❌ CRITICAL ISSUES FOUND:", "ERROR")
        for issue in issues:
            log(f"  • {issue}", "ERROR")
        log("", "INFO")
        log("🔧 FIXES NEEDED:", "WARN")
        log("  1. Update installer_docker.py line 179: change '4096' to '2048'", "INFO")
        log("  2. Update installer_docker.py line ~293: change ':-0}' to ':-2048}'", "INFO")
        log("  3. Manually fix current installation with:", "INFO")
        log("     sed -i 's/MAX_TOKENS.*4096/MAX_TOKENS\": \"2048/g' models/agents/XT.json", "INFO")
        log("     echo 'EZLOCALAI_MAX_TOKENS=2048' >> .env", "INFO")
        return False
    
    if warnings:
        log("⚠️  WARNINGS:", "WARN")
        for warning in warnings:
            log(f"  • {warning}", "WARN")
    
    if not issues and not warnings:
        log("🎉 ALL TOKEN CONFIGURATIONS ARE CORRECT!", "SUCCESS")
        return True
    
    return len(issues) == 0

def test_api_with_token_validation(base_url, api_key=None):
    """Test API and check for token limit errors"""
    log("🧪 API Token Limit Testing:", "TEST")
    
    if not api_key:
        log("No API key provided, skipping authenticated tests", "INFO")
        return True
    
    # Test small request (should always work)
    small_test = {
        "model": "TheBloke/phi-2-dpo-GGUF",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10
    }
    
    try:
        # Test EzLocalAI directly
        req = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=json.dumps(small_test).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                
                if 'choices' in data and data['choices']:
                    content = data['choices'][0].get('message', {}).get('content', '')
                    usage = data.get('usage', {})
                    
                    log(f"✅ Small request successful: '{content[:50]}...'", "SUCCESS")
                    log(f"   Token usage: {usage}", "DEBUG")
                    return True
                else:
                    log("⚠️  API responded but with unexpected format", "WARN")
                    return False
            else:
                log(f"❌ API returned HTTP {response.getcode()}", "ERROR")
                return False
                
    except urllib.error.HTTPError as e:
        if e.code == 401:
            log("❌ Authentication failed - check API key", "ERROR")
        else:
            log(f"❌ HTTP {e.code}: {e.reason}", "ERROR")
        return False
    except Exception as e:
        if "Unable to process request" in str(e):
            log("❌ CRITICAL: 'Unable to process request' error detected", "CRITICAL")
            log("   This suggests token limit mismatch (16K vs 2048)", "CRITICAL")
            return False
        else:
            log(f"❌ API test failed: {e}", "ERROR")
            return False

def test_live_token_limits_with_agixt(install_path):
    """Test AGiXT's actual token limit behavior"""
    log("🎯 Live AGiXT Token Limit Testing:", "HEADER")
    
    config = load_config_from_env(install_path)
    agixt_api_key = config.get('AGIXT_API_KEY')
    
    if not agixt_api_key:
        log("No AGiXT API key found, skipping live tests", "WARN")
        return True
    
    # Test AGiXT agent endpoint to see actual provider limits
    try:
        req = urllib.request.Request(
            "http://localhost:7437/v1/agent/XT",
            headers={'Authorization': f'Bearer {agixt_api_key}'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() == 200:
                agent_data = json.loads(response.read().decode())
                log("✅ AGiXT agent endpoint accessible", "SUCCESS")
                
                # Look for provider configuration
                if 'settings' in agent_data:
                    provider = agent_data['settings'].get('provider', 'Unknown')
                    max_tokens = agent_data['settings'].get('MAX_TOKENS', 'Unknown')
                    
                    log(f"   Live Agent Provider: {provider}", "DEBUG")
                    log(f"   Live Agent MAX_TOKENS: {max_tokens}", "DEBUG")
                    
                    if provider != 'ezlocalai':
                        log(f"❌ CRITICAL: Live agent provider is {provider}, not ezlocalai", "CRITICAL")
                        return False
                    
                    if max_tokens not in ['2048', 2048]:
                        log(f"⚠️  Live agent MAX_TOKENS is {max_tokens}, expected 2048", "WARN")
                
                return True
            else:
                log(f"❌ AGiXT agent endpoint returned HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        log(f"❌ Could not test live AGiXT configuration: {e}", "ERROR")
        return False

def test_file_structure_enhanced(install_path):
    """Enhanced file structure test with model validation"""
    log("📁 Enhanced File Structure Testing:", "HEADER")
    
    required_structure = {
        ".env": "file",
        "docker-compose.yml": "file", 
        "models": "directory",
        "models/agents": "directory",
        "models/agents/XT.json": "file",
        "WORKSPACE": "directory",
        "conversations": "directory"
    }
    
    issues = []
    
    for item, item_type in required_structure.items():
        full_path = os.path.join(install_path, item)
        
        if not os.path.exists(full_path):
            issues.append(f"Missing {item_type}: {item}")
            log(f"❌ Missing: {item}", "ERROR")
            continue
        
        if item_type == "directory" and not os.path.isdir(full_path):
            issues.append(f"Type mismatch: {item} (expected directory)")
            log(f"❌ Wrong type: {item} (expected directory)", "ERROR")
            continue
        
        if item_type == "file" and not os.path.isfile(full_path):
            issues.append(f"Type mismatch: {item} (expected file)")
            log(f"❌ Wrong type: {item} (expected file)", "ERROR")
            continue
        
        log(f"✅ Found: {item}", "SUCCESS")
    
    # Special validation for agent config
    agent_config_path = os.path.join(install_path, "models", "agents", "XT.json")
    if os.path.exists(agent_config_path):
        try:
            with open(agent_config_path, 'r') as f:
                agent_data = json.load(f)
                
            if 'settings' not in agent_data:
                issues.append("Agent config missing 'settings' section")
                log("❌ Agent config corrupted - missing settings", "ERROR")
            else:
                log("✅ Agent config structure valid", "SUCCESS")
                
        except json.JSONDecodeError:
            issues.append("Agent config has invalid JSON")
            log("❌ Agent config has invalid JSON", "ERROR")
        except Exception as e:
            issues.append(f"Could not validate agent config: {e}")
            log(f"❌ Agent config validation failed: {e}", "ERROR")
    
    return len(issues) == 0

def run_enhanced_comprehensive_test_suite(install_path):
    """Run enhanced test suite with token validation focus"""
    log("🚀 AGiXT Enhanced Post-Installation Test Suite v2.0", "HEADER")
    log("🎯 Special focus on token configuration validation", "INFO")
    log(f"📁 Testing installation at: {install_path}", "INFO")
    log("=" * 80, "INFO")
    
    # Load configurations
    config = load_config_from_env(install_path)
    log(f"📋 Loaded {len(config)} environment variables", "INFO")
    
    # Critical token configuration test (NEW)
    token_config_ok = test_token_configuration_comprehensive(install_path)
    
    # Enhanced file structure test
    file_structure_ok = test_file_structure_enhanced(install_path)
    
    # Container status
    log("\n🐳 Docker Container Status:", "TEST")
    containers_ok = True
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "table"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            log("Container Status:", "INFO")
            for line in result.stdout.split('\n')[1:]:
                if line.strip():
                    if 'running' in line.lower():
                        log(f"✅ {line.strip()}", "SUCCESS")
                    else:
                        log(f"❌ {line.strip()}", "ERROR")
                        containers_ok = False
        else:
            log("❌ Could not get container status", "ERROR")
            containers_ok = False
            
    except Exception as e:
        log(f"❌ Container check failed: {e}", "ERROR")
        containers_ok = False
    
    # API endpoint tests
    log("\n🌐 API Endpoint Testing:", "TEST")
    endpoints = [
        ("http://localhost:3437", "AGiXT Frontend"),
        ("http://localhost:7437", "AGiXT API"),
        ("http://localhost:8091", "EzLocalAI API"),
        ("http://localhost:8502", "EzLocalAI UI")
    ]
    
    endpoint_results = []
    for url, name in endpoints:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                if 200 <= response.getcode() < 400:
                    log(f"✅ {name}: HTTP {response.getcode()}", "SUCCESS")
                    endpoint_results.append(True)
                else:
                    log(f"⚠️  {name}: HTTP {response.getcode()}", "WARN")
                    endpoint_results.append(False)
        except:
            log(f"❌ {name}: Not accessible", "ERROR")
            endpoint_results.append(False)
    
    # Token-specific API testing
    ezlocalai_api_key = config.get('EZLOCALAI_API_KEY')
    if ezlocalai_api_key and endpoint_results[2]:  # EzLocalAI API accessible
        api_token_ok = test_api_with_token_validation("http://localhost:8091", ezlocalai_api_key)
    else:
        api_token_ok = True  # Skip if not accessible
        log("⚠️  Skipping API token tests (EzLocalAI not accessible)", "WARN")
    
    # Live AGiXT testing
    if endpoint_results[1]:  # AGiXT API accessible
        live_agixt_ok = test_live_token_limits_with_agixt(install_path)
    else:
        live_agixt_ok = True  # Skip if not accessible
        log("⚠️  Skipping live AGiXT tests (API not accessible)", "WARN")
    
    # COMPREHENSIVE SUMMARY
    log("\n" + "=" * 80, "INFO")
    log("🎯 COMPREHENSIVE TEST RESULTS", "HEADER")
    log("=" * 80, "INFO")
    
    tests_results = [
        ("Token Configuration", token_config_ok),
        ("File Structure", file_structure_ok),
        ("Docker Containers", containers_ok),
        ("API Endpoints", sum(endpoint_results) >= 2),
        ("Token API Testing", api_token_ok),
        ("Live AGiXT Config", live_agixt_ok)
    ]
    
    passed_tests = sum(1 for _, result in tests_results if result)
    
    for test_name, result in tests_results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"  {status}: {test_name}", "SUCCESS" if result else "ERROR")
    
    log(f"\n📊 Overall Score: {passed_tests}/{len(tests_results)} tests passed", "INFO")
    
    # CRITICAL ASSESSMENT
    critical_passed = token_config_ok and file_structure_ok
    
    if critical_passed and passed_tests >= 4:
        log("\n🎉 INSTALLATION STATUS: EXCELLENT", "SUCCESS")
        log("✅ All critical configurations are correct", "SUCCESS")
        log("✅ Token limits properly configured", "SUCCESS")
        log("✅ Installation ready for production use", "SUCCESS")
        return True
    elif token_config_ok and passed_tests >= 3:
        log("\n🟡 INSTALLATION STATUS: FUNCTIONAL", "WARN")
        log("✅ Token configuration is correct", "SUCCESS")
        log("⚠️  Some services need attention", "WARN")
        log("ℹ️  Installation usable but may need minor fixes", "INFO")
        return True
    else:
        log("\n❌ INSTALLATION STATUS: NEEDS REPAIR", "ERROR")
        if not token_config_ok:
            log("🎯 PRIORITY: Fix token configuration issues first", "CRITICAL")
            log("   This is the most common cause of 'Unable to process request' errors", "CRITICAL")
        log("🔧 Review test results above for specific issues to fix", "ERROR")
        return False

def main():
    # Auto-detect or use provided installation path
    if len(sys.argv) > 1:
        install_path = sys.argv[1]
    else:
        # Try to find AGiXT installation
        possible_paths = [
            "/var/apps/agixt-v1.7-optimized-universal",
            "/var/apps/agixt-v1.6-ezlocolai-universal",
        ]
        
        install_path = None
        for path in possible_paths:
            if os.path.exists(path):
                install_path = path
                break
        
        if not install_path:
            log("❌ Could not find AGiXT installation", "ERROR")
            log("Usage: python3 post-install-tests.py [installation_path]", "INFO")
            sys.exit(1)
    
    if not os.path.exists(install_path):
        log(f"❌ Installation path does not exist: {install_path}", "ERROR")
        sys.exit(1)
    
    log(f"🎯 Testing AGiXT installation at: {install_path}", "INFO")
    
    success = run_enhanced_comprehensive_test_suite(install_path)
    
    if success:
        log("\n🎉 SUCCESS: Installation passed comprehensive testing!", "SUCCESS")
        sys.exit(0)
    else:
        log("\n❌ FAILED: Installation needs attention", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
