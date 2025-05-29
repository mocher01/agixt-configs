AGiXT Automated Installation Configurations
🚀 One-command AGiXT installation for any server

This repository contains pre-configured environment files and an automated installer script that can deploy AGiXT to any server with a single command.

🎯 Quick Start
# Install AGiXT with test configuration
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/agixt-configs/main/install-agixt.py | python3 - test-server
📁 Available Configurations
Configuration	Description	Folder Name	Use Case
test-server	Basic test setup	AGiXT-TestServer	Testing and development
🔧 How It Works
Download: Script downloads your chosen .env configuration
Setup: Creates installation folder based on INSTALL_FOLDER_NAME
Install: Downloads AGiXT, applies SMTP patches, configures everything
Start: Launches AGiXT with Docker Compose
Ready: Web interface available immediately
📧 Configuration Requirements
Essential Settings (Update in your .env file):
# Email Authentication (Required)
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-16-character-app-password"

# AI Provider (At least one required)
OPENAI_API_KEY="sk-your-openai-api-key"
Gmail App Password Setup:
Enable 2-Factor Authentication
Go to https://myaccount.google.com/apppasswords
Generate App Password for "Mail"
Use the 16-character password (not your regular password)
🌐 Server Access
After installation:

Web Interface: http://your-server-ip:3437
API Endpoint: http://your-server-ip:7437
Login: Use your email address (magic link authentication)
🛠️ Creating Custom Configurations
Copy test-server.env to your-config-name.env
Update all settings for your environment
Commit to this repository
Install with: curl -sSL ... | python3 - your-config-name
Key Variables to Customize:
INSTALL_FOLDER_NAME="AGiXT-YourName"        # Installation folder
SMTP_USER="your-email@domain.com"          # Your email
SMTP_PASSWORD="your-app-password"          # Email password
OPENAI_API_KEY="sk-your-key"               # AI provider key
AGENT_NAME="YourAgent"                     # Default agent name
APP_NAME="Your AGiXT Server"               # Web interface title
🔍 Troubleshooting
Installation Issues:
# Check Docker status
docker ps

# View logs
docker compose logs -f

# Restart services
docker compose restart
Access Issues:
Ensure ports 3437 and 7437 are open
Check your server's firewall settings
Verify email configuration for login
📋 Requirements
Python 3.8+
Git
Docker & Docker Compose (auto-installed on Linux)
Email account with SMTP access
AI Provider API key (OpenAI, Anthropic, Google, etc.)
🔐 Security Notes
.env files are created with 600 permissions (secure)
API keys are auto-generated if not provided
SMTP passwords should use App Passwords, not regular passwords
All communication uses TLS encryption
🆘 Support
Check the AGiXT Documentation
Review Docker logs: docker compose logs
Verify your .env configuration
Ensure email and AI provider credentials are correct
📝 License
This configuration repository is provided as-is for AGiXT deployment automation. AGiXT itself is licensed under the MIT License.

Made with ❤️ for easy AGiXT deployment
