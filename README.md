🚀 AGiXT Automated Installation System
Deploy AGiXT on any server with custom configurations - one command installation!
This private repository contains an automated installation system that allows you to deploy AGiXT with different configurations on multiple servers using a single script.
🎯 How It Works

Create custom .env files for each server/environment in this repository
Run the installation script with your chosen configuration name
Script automatically downloads your config and deploys AGiXT with your specific settings

📁 Repository Structure
agixt-configs/
├── install-agixt.py           # Main installation script
├── production-server.env      # Production server config
├── staging-server.env         # Staging server config  
├── development-server.env     # Development server config
├── AGiXT-0528_1531.env       # Your current server config
└── README.md                 # This documentation
🔑 GitHub Token Setup (Required for Private Repository)
Step 1: Create GitHub Personal Access Token

Go to GitHub Settings: https://github.com/settings/tokens
Generate New Token:

Click "Personal access tokens" → "Tokens (classic)" → "Generate new token (classic)"
Note: AGiXT Installation Private Repo
Expiration: 90 days (or No expiration for permanent use)
Scopes: ✅ Check repo (Full control of private repositories)
Click "Generate token"


Copy Token: Save it immediately (you won't see it again!)

Format: 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



Step 2: Test Token Access
bash# Test if your token can access the repository
curl -H "Authorization: token github_pat_YOUR_TOKEN_HERE" \
     https://api.github.com/repos/mocher01/agixt-configs/contents
🚀 Installation Commands
Single Command Installation
Replace YOUR_TOKEN_HERE with your actual GitHub token and CONFIG_NAME with your .env file name (without .env extension):
bashcurl -H "Authorization: token github_pat_YOUR_TOKEN_HERE" \
     -o install-agixt.py \
     https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py

python3 install-agixt.py CONFIG_NAME github_pat_YOUR_TOKEN_HERE
Example: Install AGiXT-0528_1531 Configuration
bash# Step 1: Download installer script
curl -H "Authorization: token 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" \
     -o install-agixt.py \
     https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py

# Step 2: Run installation with your config
python3 install-agixt.py AGiXT-0528_1531 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
Example: Install Production Server Configuration
bash# Step 1: Download installer script  
curl -H "Authorization: token github_pat_YOUR_ACTUAL_TOKEN" \
     -o install-agixt.py \
     https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py

# Step 2: Run installation for production
python3 install-agixt.py production-server github_pat_YOUR_ACTUAL_TOKEN
Example: Install Development Server Configuration
bash# Step 1: Download installer script
curl -H "Authorization: token github_pat_YOUR_ACTUAL_TOKEN" \
     -o install-agixt.py \
     https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py

# Step 2: Run installation for development  
python3 install-agixt.py development-server github_pat_YOUR_ACTUAL_TOKEN
🎯 What The Script Does Automatically

✅ Downloads your specific .env configuration from this private repository
✅ Checks prerequisites (Docker, Git, Python 3.8+)
✅ Installs missing dependencies (Docker, Docker Compose if needed)
✅ Detects server IP and updates network URLs automatically
✅ Creates installation directory (based on INSTALL_FOLDER_NAME in your config)
✅ Clones AGiXT repository (branch based on SERVER_TYPE in your config)
✅ Configures all services according to your .env settings
✅ Starts AGiXT services (production or development mode)
✅ Performs health checks and displays access URLs
✅ Shows next steps for accessing your AGiXT installation

📝 Configuration File Examples
Key Configuration Parameters
Each .env file should contain these essential settings:
bash# Installation Settings (Controls script behavior)
INSTALL_FOLDER_NAME="AGiXT-MyServer"     # Folder name in /var/apps/
SERVER_TYPE="stable"                     # "stable" = production, "dev" = development

# Network URLs (Auto-updated by script with server IP)
AGIXT_URI="http://localhost:7437"        # API endpoint
APP_URI="http://localhost:3437"          # Web interface

# Security
AGIXT_API_KEY=""                        # Auto-generated if empty
AGIXT_REQUIRE_API_KEY="true"            # "true" = secure, "false" = open access

# Email Authentication (Required for login)
SMTP_SERVER="smtp.gmail.com"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# AI Providers (Add your API keys)
OPENAI_API_KEY=""                       # Your OpenAI key
ANTHROPIC_API_KEY=""                    # Your Anthropic key
WITH_EZLOCALAI="true"                   # Enable free local AI models
Production Server Example (production-server.env)
bashINSTALL_FOLDER_NAME="AGiXT-Production"
SERVER_TYPE="stable"
AGIXT_REQUIRE_API_KEY="true"
SMTP_SERVER="smtp.company.com"
SMTP_USER="agixt@company.com"
DATABASE_TYPE="postgresql"
UVICORN_WORKERS="8"
THEME_NAME="default"
Development Server Example (development-server.env)
bashINSTALL_FOLDER_NAME="AGiXT-Development"  
SERVER_TYPE="dev"
AGIXT_REQUIRE_API_KEY="false"
SMTP_SERVER="smtp.gmail.com"
SMTP_USER="dev@gmail.com"
DATABASE_TYPE="sqlite"
UVICORN_WORKERS="4"
THEME_NAME="doom"
WITH_EZLOCALAI="true"
🌐 After Installation Access
The script will show you the exact URLs for your installation. Typically:
ServiceURL PatternPurposeWeb Interfacehttp://YOUR_SERVER_IP:3437Main chat interfaceAPI Documentationhttp://YOUR_SERVER_IP:7437API endpointsManagement Interfacehttp://YOUR_SERVER_IP:8501Agent management
🔐 Login Process

Open the web interface URL (shown after installation)
Enter your email address (configured in SMTP settings)
Check your email for the magic login link
Click the link to authenticate
Start using AGiXT!

⚙️ Server Requirements

OS: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
RAM: 2GB minimum (4GB+ recommended)
CPU: 2 cores minimum (4+ recommended)
Storage: 10GB minimum (50GB+ recommended)
Network: Internet connection for downloads
Ports: 3437, 7437, 8501 (opened automatically)

🛠️ Management Commands
After installation, manage your AGiXT with these commands:
View Logs
bashcd /var/apps/YOUR_INSTALL_FOLDER_NAME
docker compose logs -f
Restart Services
bashcd /var/apps/YOUR_INSTALL_FOLDER_NAME
docker compose restart
Stop Services
bashcd /var/apps/YOUR_INSTALL_FOLDER_NAME
docker compose down
Update AGiXT
bashcd /var/apps/YOUR_INSTALL_FOLDER_NAME
git pull
docker compose pull
docker compose up -d
Check Status
bashcd /var/apps/YOUR_INSTALL_FOLDER_NAME
docker compose ps
🆘 Troubleshooting
Permission Issues
bash# If permission denied, run with sudo:
sudo python3 install-agixt.py CONFIG_NAME github_pat_YOUR_TOKEN
GitHub Token Issues
bash# Error: "Access denied - check your GitHub token"
- Verify token has 'repo' scope checked
- Check token hasn't expired  
- Ensure no extra spaces when copying token
- Try regenerating the token
Configuration Not Found
bash# Error: "Configuration file not found"
- Verify your .env file exists in the repository
- Check the filename exactly matches (case-sensitive)
- Ensure CONFIG_NAME parameter doesn't include .env extension
Services Not Starting
bash# Check what went wrong:
cd /var/apps/YOUR_INSTALL_FOLDER_NAME
docker compose logs

# Common fixes:
sudo ufw allow 3437
sudo ufw allow 7437  
sudo ufw allow 8501
🔧 Adding New Server Configurations
Step 1: Create New Configuration File
Create a new .env file in this repository for your server:
bash# Example: new-server.env
INSTALL_FOLDER_NAME="AGiXT-NewServer"
SERVER_TYPE="stable"
SMTP_USER="admin@newserver.com"
SMTP_PASSWORD="your-smtp-password"
OPENAI_API_KEY="sk-your-openai-key"
# ... other settings
Step 2: Install on New Server
bashcurl -H "Authorization: token github_pat_YOUR_TOKEN" \
     -o install-agixt.py \
     https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py

python3 install-agixt.py new-server github_pat_YOUR_TOKEN
🔄 Updates and Maintenance
The installation system automatically:

✅ Updates AGiXT code from Git
✅ Pulls latest Docker images
✅ Preserves your configuration
✅ Maintains your data and agents

📞 Support

AGiXT Documentation: https://josh-xt.github.io/AGiXT/
AGiXT Repository: https://github.com/Josh-XT/AGiXT
Issues: https://github.com/Josh-XT/AGiXT/issues


🎉 Quick Start Template
Copy, paste, and adapt this command for your installation:
bash# Replace YOUR_TOKEN_HERE with your actual GitHub token
# Replace CONFIG_NAME with your .env filename (without .env)

curl -H "Authorization: token github_pat_YOUR_TOKEN_HERE" \
     -o install-agixt.py \
     https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py && \
python3 install-agixt.py CONFIG_NAME github_pat_YOUR_TOKEN_HERE
Example for AGiXT-0528_1531 configuration:
bashcurl -H "Authorization: token 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" \
     -o install-agixt.py \
     https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py && \
python3 install-agixt.py AGiXT-0528_1531 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
That's it! Your custom AGiXT server will be deployed and ready to use! 🚀RéessayerClaude peut faire des erreurs. Assurez-vous de vérifier ses réponses.
