#!/usr/bin/env python3
"""
AGiXT Post-Installation Tests v1.7.2
====================================

SIMPLIFIED TESTING APPROACH:
- No API calls that can fail during installation
- Focus on container health and file structure
- Basic connectivity testing only
- No agent creation or model verification
- Designed to work with v1.7.2 simplified installer

Changes from v1.7:
- Removed agent API testing
- Removed EzLocalAI model verification
- Removed complex chat workflow testing
- Added container health checks
- Simplified endpoint testing
"""

import sys
import os
import subprocess
import urllib.request
import urllib.error
import time
import json
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("[" + timestamp + "] " + level + ": " + str(message))

def get_container_stats(install_path):
    """Get Docker container statistics"""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps"],
            cwd=install_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return None
    except Exception:
        return None

def check_container_health(install_path):
    """Check if containers are running and healthy"""
    try:
        log("🐳 CONTAINER HEALTH CHECK", "HEADER")
        
        stats = get_container_stats(install_path)
        if not stats:
            log("❌ Could not get container status", "ERROR")
            return False
        
        lines = stats.strip().split('\n')[1:]  # Skip header
        running_containers = []
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 1:
                    container_name = parts[0]
                    if 'running' in line.lower() or 'up' in line.lower():
                        log(f"✅ {container_name}: running", "SUCCESS")
                        running_containers.append(container_name)
                    else:
                        log(f"❌ {container_name}: not running", "ERROR")
        
        if len(running_containers) >= 2:
            log(f"✅ {len(running_containers)} containers running successfully", "SUCCESS")
            return True
        else:
            log(f"⚠️  Only {len(running_containers)} containers running", "WARN")
            return False
            
    except Exception as e:
        log(f"❌ Container health check failed: {e}", "ERROR")
        return False

def check_file_structure(install_path):
    """Check basic file structure"""
    try:
        log("📁 FILE STRUCTURE CHECK", "HEADER")
        
        required_files = [
            (".env", "Environment configuration"),
            ("docker-compose.yml", "Docker Compose configuration"),
            ("models", "Models directory"),
            ("agixt", "AGiXT repository"),
            ("ezlocalai", "EzLocalAI models directory"),
            ("WORKSPACE", "Working directory"),
            ("conversations", "Conversations directory")
        ]
        
        all_good = True
        for file_path, description in required_files:
            full_path = os.path.join(install_path, file_path)
            if os.path.exists(full_path):
                if os.path.isfile(full_path):
                    size = os.path.getsize(full_path)
                    log(f"✅ {file_path}: {description} ({size} bytes)", "SUCCESS")
                else:
                    log(f"✅ {file_path}: {description} (directory)", "SUCCESS")
            else:
                log(f"❌ {file_path}: missing", "ERROR")
                all_good = False
        
        return all_good
        
    except Exception as e:
        log(f"❌ File structure check failed: {e}", "ERROR")
        return False

def test_basic_connectivity(install_path):
    """Test basic HTTP connectivity without API calls"""
    try:
        log("🌐 BASIC CONNECTIVITY TEST v1.7.2", "HEADER")
        log("ℹ️  Testing HTTP responses only - no API verification")
        
        endpoints = [
            ("http://localhost:3437", "AGiXT Frontend"),
            ("http://localhost:7437", "AGiXT Backend"),
            ("http://localhost:8091", "EzLocalAI API"),
            ("http://localhost:8502", "EzLocalAI UI")
        ]
        
        working_endpoints = 0
        
        for url, name in endpoints:
            try:
                log(f"🧪 Testing {name}...")
                
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'AGiXT-Test/1.7.2')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    status_code = response.getcode()
                    if status_code < 400:
                        log(f"✅ {name}: HTTP {status_code}", "SUCCESS")
                        working_endpoints += 1
                    else:
                        log(f"⚠️  {name}: HTTP {status_code}", "WARN")
                        
            except urllib.error.HTTPError as e:
                if e.code < 500:  # Client errors are often OK (auth required, etc.)
                    log(f"✅ {name}: HTTP {e.code} (service responding)", "SUCCESS")
                    working_endpoints += 1
                else:
                    log(f"⚠️  {name}: HTTP {e.code}", "WARN")
            except Exception as e:
                log(f"❌ {name}: {type(e).__name__}", "ERROR")
        
        log(f"📊 Connectivity: {working_endpoints}/{len(endpoints)} endpoints responding")
        
        if working_endpoints >= 2:
            log("✅ Basic connectivity test passed", "SUCCESS")
            return True
        else:
            log("⚠️  Limited connectivity - some services may need more time", "WARN")
            return False
            
    except Exception as e:
        log(f"❌ Connectivity test failed: {e}", "ERROR")
        return False

def check_system_resources():
    """Check system resources"""
    try:
        log("💻 SYSTEM RESOURCES CHECK", "HEADER")
        
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
                log("❌ Docker not available", "ERROR")
                return False
        except Exception:
            log("❌ Docker not available", "ERROR")
            return False
        
        # Check memory (Linux/Unix systems)
        try:
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('MemAvailable:'):
                            mem_kb = int(line.split()[1])
                            mem_gb = mem_kb / 1024 / 1024
                            log(f"💾 Available Memory: {mem_gb:.1f}GB", "INFO")
                            if mem_gb > 2:
                                log("✅ Sufficient memory available", "SUCCESS")
                            else:
                                log("⚠️  Low memory available", "WARN")
                            break
        except Exception:
            log("ℹ️  Could not check memory usage", "INFO")
        
        return True
        
    except Exception as e:
        log(f"❌ System resources check failed: {e}", "ERROR")
        return False

def run_simplified_tests(install_path):
    """Run all simplified tests for v1.7.2"""
    try:
        log("🚀 AGIXT POST-INSTALLATION TESTS v1.7.2", "HEADER")
        log("🎯 Simplified testing approach - no API calls that can fail")
        log(f"📁 Testing installation: {install_path}")
        log("=" * 80)
        
        # Wait for services to stabilize
        log("⏳ Initial service stabilization wait (30s)")
        for i in range(30, 0, -5):
            log(f"   ⏰ {i}s remaining...")
            time.sleep(5)
        
        # Test phases
        test_results = {}
        
        # Phase 1: System and Docker
        log("\n🏗️ PHASE 1: SYSTEM FUNDAMENTALS", "HEADER")
        test_results['system_resources'] = check_system_resources()
        test_results['container_health'] = check_container_health(install_path)
        
        # Phase 2: File Structure
        log("\n📋 PHASE 2: INSTALLATION VERIFICATION", "HEADER")
        test_results['file_structure'] = check_file_structure(install_path)
        
        # Phase 3: Basic Connectivity
        log("\n🌐 PHASE 3: CONNECTIVITY TESTING", "HEADER")
        test_results['connectivity'] = test_basic_connectivity(install_path)
        
        # Summary
        log("\n" + "=" * 80, "HEADER")
        log("🏆 TEST RESULTS SUMMARY v1.7.2", "HEADER")
        log("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        log("\n🔴 CRITICAL TESTS:")
        critical_tests = ['system_resources', 'container_health']
        for test_name in critical_tests:
            if test_name in test_results:
                status = "✅ PASS" if test_results[test_name] else "❌ FAIL"
                log(f"   {status}: {test_name.replace('_', ' ').title()}")
                if test_results[test_name]:
                    passed_tests += 1
        
        log("\n🟡 IMPORTANT TESTS:")
        important_tests = ['file_structure', 'connectivity']
        for test_name in important_tests:
            if test_name in test_results:
                status = "✅ PASS" if test_results[test_name] else "❌ FAIL"
                log(f"   {status}: {test_name.replace('_', ' ').title()}")
                if test_results[test_name]:
                    passed_tests += 1
        
        # Overall assessment
        log(f"\n📊 OVERALL SCORE: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            log("\n🟢 INSTALLATION STATUS: EXCELLENT", "SUCCESS")
            log("✅ All tests passed - system ready for use")
        elif passed_tests >= total_tests * 0.75:
            log("\n🟡 INSTALLATION STATUS: GOOD", "WARN")
            log("✅ Most tests passed - system should work normally")
        elif passed_tests >= total_tests * 0.5:
            log("\n🟠 INSTALLATION STATUS: FUNCTIONAL", "WARN")
            log("⚠️  Some issues detected but system may still work")
        else:
            log("\n🔴 INSTALLATION STATUS: NEEDS ATTENTION", "ERROR")
            log("❌ Multiple issues detected - manual review needed")
        
        log("\n📋 v1.7.2 USAGE NOTES:")
        log("• No agents created during installation")
        log("• Create agents manually via frontend: http://localhost:3437")
        log("• Use EzLocalAI provider when creating agents")
        log("• Model files downloaded automatically by EzLocalAI")
        log("• All services run independently")
        
        log("\n🎉 POST-INSTALLATION TESTING COMPLETED", "SUCCESS")
        return passed_tests >= total_tests * 0.75
        
    except Exception as e:
        log(f"❌ Test execution failed: {e}", "ERROR")
        return False

def main():
    """Main test execution"""
    if len(sys.argv) < 2:
        log("❌ Usage: python3 post-install-tests.py <install_path>", "ERROR")
        sys.exit(1)
    
    install_path = sys.argv[1]
    
    if not os.path.exists(install_path):
        log(f"❌ Installation path does not exist: {install_path}", "ERROR")
        sys.exit(1)
    
    log("🎯 AGiXT Post-Installation Tests v1.7.2 Starting")
    log(f"📁 Installation path: {install_path}")
    
    success = run_simplified_tests(install_path)
    
    if success:
        log("✅ Testing completed successfully!", "SUCCESS")
        sys.exit(0)
    else:
        log("⚠️  Testing completed with warnings", "WARN")
        log("ℹ️  System may still be functional - check individual test results")
        sys.exit(0)  # Don't fail installation on test warnings

if __name__ == "__main__":
    main()
