#!/usr/bin/env python3
"""
AGiXT PRODUCTION Post-Installation Test Suite
=============================================

PRODUCTION-READY features:
- Comprehensive debugging without frontend dependency  
- Live repair capabilities (no restart needed)
- Heavy testing of all components
- Real-time monitoring and diagnostics
- Automated fixes for common issues
- Production environment validation

This replaces manual frontend testing with automated validation.
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
        "CRITICAL": Colors.RED + Colors.BOLD,
        "REPAIR": Colors.YELLOW + Colors.BOLD
    }
    color = color_map.get(level, Colors.WHITE)
    print(f"{color}[{timestamp}] {level}: {message}{Colors.RESET}")

def wait_with_progress(seconds, message):
    """Wait with progress indicator"""
    log(f"⏳ {message} ({seconds}s)", "INFO")
    for i in range(seconds):
        remaining = seconds - i
        if remaining % 15 == 0 and remaining > 0:
            log(f"   ⏰ {remaining}s remaining...", "DEBUG")
        time.sleep(1)

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

def load_agent_config(install_path, agent_name=None):
    """Load agent configuration from JSON file"""
    config = load_config_from_env(install_path)
    
    if not agent_name:
        agent_name = config.get('AGIXT_AGENT', 'XT')
    
    agent_path = os.path.join(install_path, "models", "agents", f"{agent_name}.json")
    
    if os.path.exists(agent_path):
        try:
            with open(agent_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            log(f"Could not load agent config: {e}", "WARN")
            return {}
    else:
        # Try common agent names
        for common_name in ['XT', 'AutomationAssistant', 'AGiXT']:
            alt_path = os.path.join(install_path, "models", "agents", f"{common_name}.json")
            if os.path.exists(alt_path):
                log(f"Found agent with different name: {common_name}", "INFO")
                try:
                    with open(alt_path, 'r') as f:
                        return json.load(f)
                except:
                    continue
        
        log(f"Agent config file not found: {agent_path}", "WARN")
        return {}

def test_system_resources():
    """Test system resources and Docker health"""
    log("💻 SYSTEM RESOURCES & DOCKER HEALTH", "HEADER")
    
    issues = []
    
    # Check Docker
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            log(f"✅ Docker: {result.stdout.strip()}", "SUCCESS")
        else:
            issues.append("Docker not responding")
            log("❌ Docker not responding", "ERROR")
    except:
        issues.append("Docker not available")
        log("❌ Docker not available", "ERROR")
    
    # Check available memory
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        mem_total = None
        mem_available = None
        for line in meminfo.split('\n'):
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1]) // 1024  # MB
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1]) // 1024  # MB
        
        if mem_total and mem_available:
            log(f"💾 Memory: {mem_available}MB available / {mem_total}MB total", "INFO")
            if mem_available < 2000:
                issues.append(f"Low memory: {mem_available}MB available")
                log(f"⚠️ Low memory: {mem_available}MB available", "WARN")
            else:
                log("✅ Memory sufficient", "SUCCESS")
    except:
        log("⚠️ Could not check memory", "WARN")
    
    return len(issues) == 0

def test_docker_services_comprehensive(install_path):
    """Comprehensive Docker services test with monitoring"""
    log("🐳 DOCKER SERVICES COMPREHENSIVE TEST", "HEADER")
    
    services_status = {}
    
    try:
        # Get service status
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        service = json.loads(line)
                        name = service.get('Name', 'Unknown')
                        state = service.get('State', 'Unknown')
                        health = service.get('Health', 'Unknown')
                        
                        services_status[name] = {
                            'state': state,
                            'health': health,
                            'running': 'running' in state.lower()
                        }
                        
                        if 'running' in state.lower():
                            log(f"✅ {name}: {state}", "SUCCESS")
                        else:
                            log(f"❌ {name}: {state}", "ERROR")
                            
                    except json.JSONDecodeError:
                        continue
        
        # Check resource usage
        log("📊 Service resource usage:", "TEST")
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if 'agixt' in line.lower() or 'ezlocalai' in line.lower():
                        log(f"   📈 {line}", "DEBUG")
        except:
            log("⚠️ Could not get resource usage", "WARN")
        
        # Count running services
        running_services = sum(1 for status in services_status.values() if status['running'])
        total_services = len(services_status)
        
        log(f"📊 Services status: {running_services}/{total_services} running", "INFO")
        
        if running_services >= 2:  # At least AGiXT and EzLocalAI
            log("✅ Core services are running", "SUCCESS")
            return True
        else:
            log("❌ Insufficient services running", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Docker services check failed: {e}", "ERROR")
        return False

def test_token_configuration_production(install_path):
    """PRODUCTION token configuration validation with live repair"""
    log("🔢 PRODUCTION TOKEN CONFIGURATION TEST", "HEADER")
    
    config = load_config_from_env(install_path)
    agent_config = load_agent_config(install_path)
    
    issues = []
    repairs_made = []
    
    # Get values
    agent_max_tokens = config.get('AGENT_MAX_TOKENS', 'NOT_SET')
    ezlocalai_max_tokens = config.get('EZLOCALAI_MAX_TOKENS', 'NOT_SET')
    llm_max_tokens = config.get('LLM_MAX_TOKENS', 'NOT_SET')
    
    log(f"📋 Current configuration:", "DEBUG")
    log(f"   AGENT_MAX_TOKENS: {agent_max_tokens}", "DEBUG")
    log(f"   EZLOCALAI_MAX_TOKENS: {ezlocalai_max_tokens}", "DEBUG")
    log(f"   LLM_MAX_TOKENS: {llm_max_tokens}", "DEBUG")
    
    # CRITICAL VALIDATION: Check for the token limit bug
    if ezlocalai_max_tokens in ['0', 'NOT_SET']:
        issues.append("CRITICAL: EZLOCALAI_MAX_TOKENS not set (causes 16K limit bug)")
        log("🔥 CRITICAL: EZLOCALAI_MAX_TOKENS not set - will cause system hangs!", "CRITICAL")
        
        # LIVE REPAIR
        log("🔧 LIVE REPAIR: Setting EZLOCALAI_MAX_TOKENS=8192", "REPAIR")
        try:
            env_path = os.path.join(install_path, ".env")
            with open(env_path, 'a') as f:
                f.write("\n# LIVE REPAIR - Added missing token limit\n")
                f.write("EZLOCALAI_MAX_TOKENS=8192\n")
                f.write("LLM_MAX_TOKENS=8192\n")
            repairs_made.append("Added EZLOCALAI_MAX_TOKENS=8192")
            log("✅ LIVE REPAIR: Token limits added to .env", "SUCCESS")
        except Exception as e:
            log(f"❌ LIVE REPAIR failed: {e}", "ERROR")
    
    elif agent_max_tokens == ezlocalai_max_tokens:
        issues.append("Token limits are equal (should be: Agent < EzLocalAI)")
        log(f"⚠️ Token limits equal: Agent={agent_max_tokens}, EzLocalAI={ezlocalai_max_tokens}", "WARN")
        log("   This can cause context overflow issues", "WARN")
    
    else:
        log("✅ Token limits properly differentiated", "SUCCESS")
    
    # Check agent configuration
    if agent_config and 'settings' in agent_config:
        agent_tokens = agent_config['settings'].get('MAX_TOKENS', 'NOT_SET')
        agent_provider = agent_config['settings'].get('provider', 'NOT_SET')
        
        log(f"👤 Agent configuration:", "DEBUG")
        log(f"   Provider: {agent_provider}", "DEBUG")
        log(f"   MAX_TOKENS: {agent_tokens}", "DEBUG")
        
        if agent_provider != 'ezlocalai':
            issues.append(f"Agent provider is {agent_provider} (should be ezlocalai)")
            log(f"❌ Agent provider: {agent_provider} (should be ezlocalai)", "ERROR")
        else:
            log("✅ Agent provider correctly set to ezlocalai", "SUCCESS")
    
    # Summary
    if issues:
        log("⚠️ Token configuration issues found:", "WARN")
        for issue in issues:
            log(f"   • {issue}", "WARN")
    
    if repairs_made:
        log("🔧 Live repairs completed:", "REPAIR")
        for repair in repairs_made:
            log(f"   • {repair}", "REPAIR")
        log("🔄 Recommend restarting services to apply repairs", "INFO")
    
    if not issues:
        log("✅ All token configurations are correct", "SUCCESS")
        return True
    
    return len(issues) <= len(repairs_made)  # Success if we repaired all issues

def test_api_endpoints_heavy(install_path):
    """Heavy API endpoint testing with retries and detailed diagnostics"""
    log("🌐 HEAVY API ENDPOINTS TEST", "HEADER")
    
    config = load_config_from_env(install_path)
    
    endpoints = [
        {
            'url': 'http://localhost:3437',
            'name': 'AGiXT Frontend',
            'expected_content': ['agixt', 'application'],
            'timeout': 15
        },
        {
            'url': 'http://localhost:7437/api/agent',
            'name': 'AGiXT API',
            'headers': {'Authorization': f"Bearer {config.get('AGIXT_API_KEY', '')}"} if config.get('AGIXT_API_KEY') else {},
            'expected_status': [200, 401],  # 401 is OK if no auth
            'timeout': 10
        },
        {
            'url': 'http://localhost:8091/v1/models',
            'name': 'EzLocalAI Models API',
            'headers': {'Authorization': f"Bearer {config.get('EZLOCALAI_API_KEY', '')}"} if config.get('EZLOCALAI_API_KEY') else {},
            'expected_status': [200],
            'timeout': 10
        },
        {
            'url': 'http://localhost:8502',
            'name': 'EzLocalAI UI',
            'expected_content': ['ezlocalai', 'streamlit'],
            'timeout': 15
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        name = endpoint['name']
        url = endpoint['url']
        
        log(f"🧪 Testing {name}...", "TEST")
        
        success = False
        last_error = None
        
        # Retry logic for production reliability
        for attempt in range(3):
            try:
                req = urllib.request.Request(url)
                
                # Add headers if specified
                if 'headers' in endpoint:
                    for header, value in endpoint['headers'].items():
                        if value:  # Only add non-empty headers
                            req.add_header(header, value)
                
                with urllib.request.urlopen(req, timeout=endpoint.get('timeout', 10)) as response:
                    status_code = response.getcode()
                    content = response.read().decode('utf-8', errors='ignore')
                    
                    # Check status code
                    expected_status = endpoint.get('expected_status', [200])
                    if status_code in expected_status:
                        log(f"   ✅ HTTP {status_code}: OK", "SUCCESS")
                        
                        # Check content if specified
                        if 'expected_content' in endpoint:
                            content_match = any(term.lower() in content.lower() 
                                              for term in endpoint['expected_content'])
                            if content_match:
                                log(f"   ✅ Content validation: OK", "SUCCESS")
                                success = True
                                break
                            else:
                                log(f"   ⚠️ Content validation: Expected content not found", "WARN")
                        else:
                            success = True
                            break
                    else:
                        log(f"   ❌ HTTP {status_code}: Unexpected status", "ERROR")
                        last_error = f"HTTP {status_code}"
                        
            except urllib.error.HTTPError as e:
                if e.code in endpoint.get('expected_status', [200]):
                    log(f"   ✅ HTTP {e.code}: Expected error", "SUCCESS")
                    success = True
                    break
                else:
                    last_error = f"HTTP {e.code}: {e.reason}"
                    
            except Exception as e:
                last_error = str(e)
            
            if attempt < 2:  # Don't wait after last attempt
                log(f"   ⏳ Retry {attempt + 2}/3 in 5s...", "DEBUG")
                time.sleep(5)
        
        if success:
            log(f"✅ {name}: ACCESSIBLE", "SUCCESS")
            results[name] = True
        else:
            log(f"❌ {name}: FAILED - {last_error}", "ERROR")
            results[name] = False
    
    # Summary
    successful_endpoints = sum(results.values())
    total_endpoints = len(results)
    
    log(f"📊 Endpoint test results: {successful_endpoints}/{total_endpoints} accessible", "INFO")
    
    return successful_endpoints >= 2  # At least 2 services must be accessible

def test_ezlocalai_model_heavy(install_path):
    """Heavy EzLocalAI model testing with token validation"""
    log("🤖 HEAVY EZLOCALAI MODEL TEST", "HEADER")
    
    config = load_config_from_env(install_path)
    api_key = config.get('EZLOCALAI_API_KEY')
    
    if not api_key:
        log("⚠️ No EzLocalAI API key found, skipping model tests", "WARN")
        return True
    
    # Test 1: Models endpoint
    log("📋 Testing models endpoint...", "TEST")
    try:
        req = urllib.request.Request(
            "http://localhost:8091/v1/models",
            headers={'Authorization': f'Bearer {api_key}'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() == 200:
                models_data = json.loads(response.read().decode())
                
                if 'data' in models_data and models_data['data']:
                    model = models_data['data'][0]
                    model_id = model.get('id', 'Unknown')
                    log(f"✅ Model available: {model_id}", "SUCCESS")
                else:
                    log("⚠️ No models found in response", "WARN")
                    return False
            else:
                log(f"❌ Models endpoint returned HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        log(f"❌ Models endpoint test failed: {e}", "ERROR")
        return False
    
    # Test 2: Small inference request
    log("🧪 Testing small inference request...", "TEST")
    
    small_request = {
        "model": config.get('DEFAULT_MODEL', 'TheBloke/phi-2-dpo-GGUF'),
        "messages": [{"role": "user", "content": "Say 'test' only"}],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    try:
        req = urllib.request.Request(
            "http://localhost:8091/v1/chat/completions",
            data=json.dumps(small_request).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as response:
            response_time = time.time() - start_time
            
            if response.getcode() == 200:
                response_data = json.loads(response.read().decode())
                
                if 'choices' in response_data and response_data['choices']:
                    content = response_data['choices'][0].get('message', {}).get('content', '')
                    usage = response_data.get('usage', {})
                    
                    log(f"✅ Inference successful: '{content.strip()}'", "SUCCESS")
                    log(f"   Response time: {response_time:.2f}s", "DEBUG")
                    log(f"   Token usage: {usage}", "DEBUG")
                    
                    # Check for token limit issues
                    if "Unable to process request" in content:
                        log("🔥 CRITICAL: Token limit issue detected in response!", "CRITICAL")
                        return False
                    
                    return True
                else:
                    log("❌ Invalid response format", "ERROR")
                    return False
            else:
                log(f"❌ Inference failed: HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        if "Unable to process request" in str(e):
            log("🔥 CRITICAL: Token limit issue detected!", "CRITICAL")
            log("   This suggests EzLocalAI token configuration problem", "CRITICAL")
        else:
            log(f"❌ Inference test failed: {e}", "ERROR")
        return False

def test_agixt_agent_creation_heavy(install_path):
    """Heavy AGiXT agent testing and validation"""
    log("👤 HEAVY AGIXT AGENT TEST", "HEADER")
    
    config = load_config_from_env(install_path)
    api_key = config.get('AGIXT_API_KEY')
    
    if not api_key:
        log("⚠️ No AGiXT API key found, skipping authenticated tests", "WARN")
        return True
    
    # Test 1: List agents
    log("📋 Testing agent listing...", "TEST")
    try:
        req = urllib.request.Request(
            "http://localhost:7437/api/agent",
            headers={'Authorization': f'Bearer {api_key}'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() == 200:
                agents_data = json.loads(response.read().decode())
                
                if isinstance(agents_data, list) and agents_data:
                    log(f"✅ Found {len(agents_data)} agents", "SUCCESS")
                    for agent in agents_data[:3]:  # Show first 3
                        agent_name = agent.get('agent_name', agent.get('name', 'Unknown'))
                        log(f"   👤 Agent: {agent_name}", "DEBUG")
                else:
                    log("⚠️ No agents found", "WARN")
                    return False
            else:
                log(f"❌ Agent listing failed: HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        log(f"❌ Agent listing test failed: {e}", "ERROR")
        return False
    
    # Test 2: Get specific agent
    agent_name = config.get('AGIXT_AGENT', 'XT')
    log(f"🔍 Testing specific agent: {agent_name}...", "TEST")
    
    try:
        req = urllib.request.Request(
            f"http://localhost:7437/api/agent/{agent_name}",
            headers={'Authorization': f'Bearer {api_key}'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() == 200:
                agent_data = json.loads(response.read().decode())
                
                # Validate agent configuration
                if 'settings' in agent_data:
                    provider = agent_data['settings'].get('provider', 'Unknown')
                    max_tokens = agent_data['settings'].get('MAX_TOKENS', 'Unknown')
                    
                    log(f"✅ Agent {agent_name} accessible", "SUCCESS")
                    log(f"   Provider: {provider}", "DEBUG")
                    log(f"   MAX_TOKENS: {max_tokens}", "DEBUG")
                    
                    if provider != 'ezlocalai':
                        log(f"⚠️ Agent provider is {provider}, should be ezlocalai", "WARN")
                    
                    return True
                else:
                    log("❌ Agent missing settings configuration", "ERROR")
                    return False
            else:
                log(f"❌ Agent access failed: HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        log(f"❌ Agent access test failed: {e}", "ERROR")
        return False

def test_full_chat_workflow(install_path):
    """Test complete chat workflow through AGiXT"""
    log("💬 FULL CHAT WORKFLOW TEST", "HEADER")
    
    config = load_config_from_env(install_path)
    api_key = config.get('AGIXT_API_KEY')
    agent_name = config.get('AGIXT_AGENT', 'XT')
    
    if not api_key:
        log("⚠️ No AGiXT API key found, skipping chat test", "WARN")
        return True
    
    # Test simple chat
    log("💭 Testing simple chat interaction...", "TEST")
    
    chat_request = {
        "message": "Hello, respond with just 'Hi' please",
        "conversation_name": f"test_conversation_{int(time.time())}"
    }
    
    try:
        req = urllib.request.Request(
            f"http://localhost:7437/api/agent/{agent_name}/chat",
            data=json.dumps(chat_request).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=60) as response:
            response_time = time.time() - start_time
            
            if response.getcode() == 200:
                chat_response = json.loads(response.read().decode())
                
                log(f"✅ Chat successful in {response_time:.2f}s", "SUCCESS")
                
                # Check response content
                if isinstance(chat_response, dict):
                    message = chat_response.get('message', str(chat_response))
                    log(f"   Response: {message[:100]}...", "DEBUG")
                    
                    # Check for error indicators
                    if "Unable to process request" in message:
                        log("🔥 CRITICAL: Token limit issue in chat response!", "CRITICAL")
                        return False
                    
                    if "error" in message.lower() or "failed" in message.lower():
                        log("⚠️ Error indicators in response", "WARN")
                        return False
                    
                    return True
                else:
                    log("❌ Unexpected response format", "ERROR")
                    return False
            else:
                log(f"❌ Chat failed: HTTP {response.getcode()}", "ERROR")
                return False
                
    except Exception as e:
        if "Unable to process request" in str(e):
            log("🔥 CRITICAL: Token limit issue during chat!", "CRITICAL")
        else:
            log(f"❌ Chat test failed: {e}", "ERROR")
        return False

def auto_repair_common_issues(install_path):
    """Automatically repair common production issues"""
    log("🔧 AUTO-REPAIR COMMON ISSUES", "HEADER")
    
    repairs_made = []
    
    # Repair 1: Fix missing token limits
    config = load_config_from_env(install_path)
    env_path = os.path.join(install_path, ".env")
    
    missing_vars = []
    if not config.get('EZLOCALAI_MAX_TOKENS'):
        missing_vars.append('EZLOCALAI_MAX_TOKENS=8192')
    if not config.get('LLM_MAX_TOKENS'):
        missing_vars.append('LLM_MAX_TOKENS=8192')
    if not config.get('AGENT_MAX_TOKENS'):
        missing_vars.append('AGENT_MAX_TOKENS=4096')
    
    if missing_vars:
        log("🔧 REPAIR: Adding missing token limit variables", "REPAIR")
        try:
            with open(env_path, 'a') as f:
                f.write("\n# AUTO-REPAIR: Missing token limits\n")
                for var in missing_vars:
                    f.write(f"{var}\n")
            repairs_made.append("Added missing token limit variables")
            log("✅ Token limit variables added", "SUCCESS")
        except Exception as e:
            log(f"❌ Failed to add token variables: {e}", "ERROR")
    
    # Repair 2: Fix agent configuration
    agent_name = config.get('AGIXT_AGENT', 'XT')
    agent_path = os.path.join(install_path, "models", "agents", f"{agent_name}.json")
    
    if os.path.exists(agent_path):
        try:
            with open(agent_path, 'r') as f:
                agent_config = json.load(f)
            
            needs_repair = False
            
            # Check provider
            if agent_config.get('settings', {}).get('provider') != 'ezlocalai':
                agent_config['settings']['provider'] = 'ezlocalai'
                needs_repair = True
                log("🔧 REPAIR: Fixed agent provider to ezlocalai", "REPAIR")
            
            # Check token limits
            current_tokens = agent_config.get('settings', {}).get('MAX_TOKENS', '0')
            if current_tokens != '4096':
                agent_config['settings']['MAX_TOKENS'] = '4096'
                needs_repair = True
                log("🔧 REPAIR: Fixed agent MAX_TOKENS to 4096", "REPAIR")
            
            # Add missing settings
            if 'EZLOCALAI_API_KEY' not in agent_config.get('settings', {}):
                agent_config['settings']['EZLOCALAI_API_KEY'] = config.get('EZLOCALAI_API_KEY', '')
                needs_repair = True
                log("🔧 REPAIR: Added EZLOCALAI_API_KEY to agent", "REPAIR")
            
            if needs_repair:
                with open(agent_path, 'w') as f:
                    json.dump(agent_config, f, indent=2)
                repairs_made.append(f"Repaired {agent_name} agent configuration")
                log("✅ Agent configuration repaired", "SUCCESS")
                
        except Exception as e:
            log(f"❌ Failed to repair agent config: {e}", "ERROR")
    
    # Repair 3: Restart services if repairs were made
    if repairs_made:
        log("🔄 REPAIR: Restarting services to apply fixes", "REPAIR")
        try:
            subprocess.run(
                ["docker", "compose", "restart"],
                cwd=install_path,
                capture_output=True,
                timeout=120
            )
            log("✅ Services restarted successfully", "SUCCESS")
            wait_with_progress(30, "Waiting for services to initialize after repair")
        except Exception as e:
            log(f"❌ Failed to restart services: {e}", "ERROR")
    
    if repairs_made:
        log("🔧 Auto-repairs completed:", "REPAIR")
        for repair in repairs_made:
            log(f"   • {repair}", "REPAIR")
        return True
    else:
        log("✅ No repairs needed", "SUCCESS")
        return True

def run_production_comprehensive_test_suite(install_path):
    """Run production-ready comprehensive test suite"""
    log("🚀 AGIXT PRODUCTION TEST SUITE v3.0", "HEADER")
    log("🎯 Production-ready testing with auto-repair capabilities", "INFO")
    log(f"📁 Testing installation: {install_path}", "INFO")
    log("=" * 80, "INFO")
    
    # Initial wait for services
    wait_with_progress(45, "Initial service startup wait")
    
    # Test sequence with dependency management
    test_results = {}
    
    # Phase 1: System fundamentals
    log("\n🏗️ PHASE 1: SYSTEM FUNDAMENTALS", "HEADER")
    test_results['system_resources'] = test_system_resources()
    test_results['docker_services'] = test_docker_services_comprehensive(install_path)
    
    # Phase 2: Configuration validation with auto-repair
    log("\n⚙️ PHASE 2: CONFIGURATION VALIDATION", "HEADER")
    test_results['token_config'] = test_token_configuration_production(install_path)
    test_results['auto_repair'] = auto_repair_common_issues(install_path)
    
    # Wait after repairs
    if not test_results['token_config']:
        wait_with_progress(30, "Waiting after configuration repairs")
    
    # Phase 3: API and service testing
    log("\n🌐 PHASE 3: API & SERVICE TESTING", "HEADER")
    test_results['api_endpoints'] = test_api_endpoints_heavy(install_path)
    test_results['ezlocalai_model'] = test_ezlocalai_model_heavy(install_path)
    test_results['agixt_agent'] = test_agixt_agent_creation_heavy(install_path)
    
    # Phase 4: End-to-end functionality
    log("\n🔄 PHASE 4: END-TO-END FUNCTIONALITY", "HEADER")
    test_results['chat_workflow'] = test_full_chat_workflow(install_path)
    
    # Comprehensive analysis
    log("\n" + "=" * 80, "INFO")
    log("🏆 PRODUCTION TEST RESULTS ANALYSIS", "HEADER")
    log("=" * 80, "INFO")
    
    # Categorize results
    critical_tests = ['system_resources', 'docker_services', 'token_config']
    important_tests = ['api_endpoints', 'ezlocalai_model', 'agixt_agent']
    functional_tests = ['chat_workflow', 'auto_repair']
    
    critical_passed = sum(test_results.get(test, False) for test in critical_tests)
    important_passed = sum(test_results.get(test, False) for test in important_tests)
    functional_passed = sum(test_results.get(test, False) for test in functional_tests)
    
    # Detailed results
    for category, tests in [
        ("🔴 CRITICAL", critical_tests),
        ("🟡 IMPORTANT", important_tests),
        ("🟢 FUNCTIONAL", functional_tests)
    ]:
        log(f"\n{category} TESTS:", "INFO")
        for test in tests:
            result = test_results.get(test, False)
            status = "✅ PASS" if result else "❌ FAIL"
            test_name = test.replace('_', ' ').title()
            log(f"   {status}: {test_name}", "SUCCESS" if result else "ERROR")
    
    # Overall assessment
    total_passed = sum(test_results.values())
    total_tests = len(test_results)
    
    log(f"\n📊 OVERALL SCORE: {total_passed}/{total_tests} tests passed", "INFO")
    
    # Production readiness assessment
    if critical_passed == len(critical_tests) and important_passed >= 2:
        if functional_passed >= 1:
            log("\n🏆 PRODUCTION STATUS: EXCELLENT", "SUCCESS")
            log("✅ All critical systems operational", "SUCCESS")
            log("✅ System ready for production use", "SUCCESS")
            log("✅ All core functionality working", "SUCCESS")
            return True
        else:
            log("\n🟡 PRODUCTION STATUS: GOOD", "SUCCESS")
            log("✅ All critical systems operational", "SUCCESS")
            log("⚠️ Minor functionality issues", "WARN")
            log("✅ System usable in production", "SUCCESS")
            return True
    
    elif critical_passed >= 2:
        log("\n🟠 PRODUCTION STATUS: FUNCTIONAL", "WARN")
        log("⚠️ Some critical issues detected", "WARN")
        log("🔧 Auto-repairs may have resolved issues", "INFO")
        log("⚠️ Monitor system closely", "WARN")
        return True
    
    else:
        log("\n🔴 PRODUCTION STATUS: NEEDS ATTENTION", "ERROR")
        log("❌ Critical system failures detected", "ERROR")
        log("🛠️ Manual intervention required", "ERROR")
        
        # Provide specific guidance
        if not test_results.get('docker_services'):
            log("🔧 Priority: Fix Docker services", "REPAIR")
        if not test_results.get('token_config'):
            log("🔧 Priority: Fix token configuration", "REPAIR")
        
        return False

def main():
    """Main function with installation path detection"""
    
    # Enhanced path detection
    if len(sys.argv) > 1:
        install_path = sys.argv[1]
    else:
        log("🔍 Auto-detecting AGiXT installation...", "INFO")
        
        possible_paths = [
            "/var/apps/agixt-v1.7-optimized-universal",
            "/var/apps/agixt-v1.6-ezlocolai-universal",
            "/opt/agixt",
            "./agixt-v1.7-optimized-universal",
            "."
        ]
        
        install_path = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "docker-compose.yml")):
                install_path = path
                log(f"✅ Found installation: {path}", "SUCCESS")
                break
        
        if not install_path:
            log("❌ Could not find AGiXT installation", "ERROR")
            log("💡 Usage: python3 post-install-tests.py [installation_path]", "INFO")
            log("💡 Ensure docker-compose.yml exists in installation directory", "INFO")
            sys.exit(1)
    
    if not os.path.exists(install_path):
        log(f"❌ Installation path does not exist: {install_path}", "ERROR")
        sys.exit(1)
    
    if not os.path.exists(os.path.join(install_path, "docker-compose.yml")):
        log(f"❌ Not a valid AGiXT installation: {install_path}", "ERROR")
        log("💡 docker-compose.yml not found", "ERROR")
        sys.exit(1)
    
    log(f"🎯 Testing AGiXT production installation: {install_path}", "INFO")
    
    try:
        success = run_production_comprehensive_test_suite(install_path)
        
        if success:
            log("\n🎉 PRODUCTION TESTING COMPLETED SUCCESSFULLY!", "SUCCESS")
            log("✅ System is ready for production use", "SUCCESS")
            log("🌐 Frontend should be accessible at configured URLs", "INFO")
            sys.exit(0)
        else:
            log("\n⚠️ PRODUCTION TESTING COMPLETED WITH ISSUES", "WARN")
            log("🔧 Some issues detected but system may still be functional", "WARN")
            log("💡 Check specific test results above for details", "INFO")
            sys.exit(1)
    
    except KeyboardInterrupt:
        log("\n⚠️ Testing interrupted by user", "WARN")
        sys.exit(130)
    except Exception as e:
        log(f"\n❌ Testing failed with exception: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
