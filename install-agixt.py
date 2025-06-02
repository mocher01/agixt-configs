#!/usr/bin/env python3
import sys
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def main():
    log("🚀 AGiXT Installer v1.6 - Test Version")
    log("✅ Python syntax is working correctly")
    
    # Parse arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    log(f"📋 Arguments received: {args}")
    
    if len(args) >= 2:
        config_name = args[0]
        github_token = args[1]
        log(f"🔧 Config: {config_name}")
        log(f"🔑 Token: {github_token[:8]}...")
    else:
        log("❌ Missing arguments", "ERROR")
        log("Usage: script.py config_name github_token", "ERROR")
        sys.exit(1)
    
    log("🎉 Test completed successfully - syntax is correct!")

if __name__ == "__main__":
    main()
