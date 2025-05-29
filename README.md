# AGiXT Automated Installation System

🚀 **One-command AGiXT installation for any server with private repository support**

This repository contains pre-configured environment files and an automated installer script that can deploy AGiXT to any server with a single command, including support for private GitHub repositories.

## 🎯 Quick Start

```bash
# Install AGiXT with your configuration (requires GitHub token for private repo)
curl -H "Authorization: token YOUR_GITHUB_TOKEN" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - XXXX YOUR_GITHUB_TOKEN
```

Replace:
- `YOUR_GITHUB_TOKEN` with your GitHub personal access token
- `XXXX` with your configuration name (without .env extension)

## 📁 Configuration System

### How It Works
1. **Create Configuration**: Name your config file `XXXX.env` (e.g., `AGIXT_0529_1056.env`)
2. **Auto-Generated Folder**: Installation folder will be `XXXX` (same as config name)
3. **One Command Install**: `python3 install-agixt.py XXXX YOUR_GITHUB_TOKEN`

### Example Configuration File Structure
```
Repository:
├── AGIXT_0529_1056.env     # Your configuration
├── PROD_SERVER_01.env      # Production server config  
├── DEV_SETUP_TEST.env      # Development setup
└── install-agixt.py        # Installation script
```

## 🔐 GitHub Token Setup (Required)

Since this repository is private, you need a GitHub personal access token:

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Select scopes: `repo` (Full control of private repositories)
4. Copy the token (starts with `github_pat_`)

## 🛠️ Installation Methods

### Method 1: Remote Installation (Recommended)
```bash
curl -H "Authorization: token github_pat_YOUR_TOKEN" -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | python3 - XXXX github_pat_YOUR_TOKEN
```

### Method 2: Local Installation
```bash
# Download script first
curl -H "Authorization: token github_pat_YOUR_TOKEN" -o install-agixt.py https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py

# Run installation
python3 install-agixt.py XXXX github_pat_YOUR_TOKEN
```

## 📧 Configuration Requirements

### Essential Settings (Update in your .env file)

```bash
# Email Authentication (Required for login)
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-16-character-app-password"

# AI Provider (At least one required for functionality)
OPENAI_API_KEY="sk-your-openai-api-key"
# OR
ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
# OR enable local AI
WITH_EZLOCALAI="true"
```

### Gmail App Password Setup
1. **Enable 2-Factor Authentication** on your Gmail account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate App Password for "Mail"
4. Use the 16-character password (not your regular Gmail password)

## 🌐 Server Access

After successful installation:

- **Web Interface**: `http://your-server-ip:3437`
- **API Endpoint**: `http://your-server-ip:7437`
- **Management**: `http://your-server-ip:8501`

### Login Process
1. Open web interface in browser
2. Enter your email address
3. Check email for magic link
4. Click link to authenticate
5. Start using AGiXT!

## 🔧 Creating Custom Configurations

1. **Copy existing config**: `cp XXXX.env YOUR_CONFIG.env`
2. **Customize settings**:
   ```bash
   # Server type (stable/dev)
   SERVER_TYPE="stable"
   
   # Your email for authentication
   SMTP_USER="your-email@domain.com"
   SMTP_PASSWORD="your-app-password"
   
   # AI provider keys
   OPENAI_API_KEY="sk-your-key-here"
   
   # Customize UI
   APP_NAME="Your AGiXT Server"
   THEME_NAME="doom"
   ```
3. **Commit to repository**
4. **Install**: `python3 install-agixt.py YOUR_CONFIG github_pat_YOUR_TOKEN`

## 🔍 Troubleshooting

### Installation Issues
```bash
# Check Docker status
docker ps

# View detailed logs
cd /var/apps/YOUR_CONFIG && docker compose logs -f

# Restart services
cd /var/apps/YOUR_CONFIG && docker compose restart
```

### Access Issues
- **Ports**: Ensure ports 3437, 7437, and 8501 are open
- **Firewall**: Check server firewall settings
- **Email**: Verify SMTP configuration for login
- **API Keys**: Ensure at least one AI provider is configured

### Common Solutions
```bash
# Restart AGiXT services
cd /var/apps/YOUR_CONFIG
docker compose down
docker compose up -d

# Update to latest version
cd /var/apps/YOUR_CONFIG
git pull
docker compose up -d --build

# Check service health
curl http://your-server-ip:7437/health
curl http://your-server-ip:3437
```

## 📋 System Requirements

- **OS**: Linux or macOS
- **Python**: 3.8+
- **Memory**: 4GB+ RAM recommended
- **Storage**: 5GB+ free space
- **Network**: Internet connection for Docker images
- **Ports**: 3437, 7437, 8501 available

### Auto-Installed Dependencies
- Git
- Docker & Docker Compose
- Required Python packages

## 🔐 Security Features

- ✅ **Private repository support** with GitHub tokens
- ✅ **API key authentication** required
- ✅ **SMTP TLS encryption** for email
- ✅ **Secure .env files** (600 permissions)
- ✅ **Auto-generated API keys** if not provided

## 🆘 Support & Documentation

- **AGiXT Documentation**: [Official AGiXT Docs](https://github.com/Josh-XT/AGiXT)
- **Docker Logs**: `docker compose logs -f`
- **Configuration**: Review your `.env` file settings
- **Email/AI Setup**: Verify credentials are correct

## 📝 Example Complete Installation

```bash
# 1. Get your GitHub token (github_pat_xxxxx)

# 2. Install with your config
curl -H "Authorization: token github_pat_11ABCDEFGH0123456789_abcdefghijklmnopqrstuvwxyz1234567890ABCD" \
  -sSL https://raw.githubusercontent.com/mocher01/agixt-configs/main/install-agixt.py | \
  python3 - AGIXT_0529_1056 github_pat_11ABCDEFGH0123456789_abcdefghijklmnopqrstuvwxyz1234567890ABCD

# 3. Open http://your-server-ip:3437 in browser
# 4. Login with your email
# 5. Check email for magic link
# 6. Start using AGiXT!
```

## ⚡ Advanced Features

- **Multiple Environments**: Production, Development, Staging configs
- **Auto-IP Detection**: Automatically configures server URLs
- **Health Checks**: Waits for services to be ready
- **Automatic Updates**: Pull latest AGiXT version
- **Local AI Support**: ezLocalAI integration for offline models
- **Custom Themes**: Multiple UI themes available

---

**Made with ❤️ for easy AGiXT deployment**

*This automated installer handles all the complexity of AGiXT deployment, from Docker setup to service configuration, making it possible to deploy a complete AI agent system with a single command.*
