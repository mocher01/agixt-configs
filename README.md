# AGiXT Automated Installation Configurations

🚀 **One-command AGiXT installation for any server**

This repository contains pre-configured environment files and an automated installer script that can deploy AGiXT to any server with a single command.

## 🎯 Quick Start

```bash
# Install AGiXT with test configuration
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/agixt-configs/main/install-agixt.py | python3 - test-server
```

## 📁 Available Configurations

| Configuration | Description | Folder Name | Use Case |
|---------------|-------------|-------------|-----------|
| `test-server` | Basic test setup | `AGiXT-TestServer` | Testing and development |

## 🔧 How It Works

1. **Download**: Script downloads your chosen `.env` configuration
2. **Setup**: Creates installation folder based on `INSTALL_FOLDER_NAME`
3. **Install**: Downloads AGiXT, applies SMTP patches, configures everything
4. **Start**: Launches AGiXT with Docker Compose
5. **Ready**: Web interface available immediately

## 📧 Configuration Requirements

### Essential Settings (Update in your .env file):

```bash
# Email Authentication (Required)
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-16-character-app-password"

# AI Provider (At least one required)
OPENAI_API_KEY="sk-your-openai-api-key"
```

### Gmail App Password Setup:
1. Enable 2-Factor Authentication
2. Go to https://myaccount.google.com/apppasswords
3. Generate App Password for "Mail"
4. Use the 16-character password (not your regular password)

## 🌐 Server Access

After installation:
- **Web Interface**: `http://your-server-ip:3437`
- **API Endpoint**: `http://your-server-ip:7437`
- **Login**: Use your email address (magic link authentication)

## 🛠️ Creating Custom Configurations

1. Copy `test-server.env` to `your-config-name.env`
2. Update all settings for your environment
3. Commit to this repository
4. Install with: `curl -sSL ... | python3 - your-config-name`

### Key Variables to Customize:

```bash
INSTALL_FOLDER_NAME="AGiXT-YourName"        # Installation folder
SMTP_USER="your-email@domain.com"          # Your email
SMTP_PASSWORD="your-app-password"          # Email password
OPENAI_API_KEY="sk-your-key"               # AI provider key
AGENT_NAME="YourAgent"                     # Default agent name
APP_NAME="Your AGiXT Server"               # Web interface title
```

## 🔍 Troubleshooting

### Installation Issues:
```bash
# Check Docker status
docker ps

# View logs
docker compose logs -f

# Restart services
docker compose restart
```

### Access Issues:
- Ensure ports 3437 and 7437 are open
- Check your server's firewall settings
- Verify email configuration for login

## 📋 Requirements

- **Python 3.8+**
- **Git**
- **Docker & Docker Compose** (auto-installed on Linux)
- **Email account** with SMTP access
- **AI Provider API key** (OpenAI, Anthropic, Google, etc.)

## 🔐 Security Notes

- `.env` files are created with 600 permissions (secure)
- API keys are auto-generated if not provided
- SMTP passwords should use App Passwords, not regular passwords
- All communication uses TLS encryption

## 🆘 Support

1. Check the [AGiXT Documentation](https://josh-xt.github.io/AGiXT/)
2. Review Docker logs: `docker compose logs`
3. Verify your `.env` configuration
4. Ensure email and AI provider credentials are correct

## 📝 License

This configuration repository is provided as-is for AGiXT deployment automation.
AGiXT itself is licensed under the MIT License.

---

**Made with ❤️ for easy AGiXT deployment**
