#!/bin/bash
# =============================================================================
# Fix EzLocalAI Model Configuration - Keep Existing Installation
# =============================================================================
# Only updates model configuration, keeps everything else intact
# =============================================================================

set -e

echo "🎯 EzLocalAI Model Fix - Targeted Update"
echo "========================================"

# Configuration
INSTALL_DIR="/var/apps/agixt-v1.2-ezlocolai model"
BACKUP_MODEL="/var/backups/ezlocalai-models-20250601/Qwen2.5-Coder-7B-Instruct/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
TARGET_MODEL_DIR="$INSTALL_DIR/ezlocalai/Qwen2.5-Coder-7B-Instruct"
TARGET_MODEL_FILE="$TARGET_MODEL_DIR/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
MODEL_PATH_FOR_ENV="Qwen2.5-Coder-7B-Instruct/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"

echo "📁 Installation directory: $INSTALL_DIR"
echo "📦 Source model: $BACKUP_MODEL"
echo "🎯 Target location: $TARGET_MODEL_FILE"

# Step 1: Verify existing installation
echo ""
echo "🔍 Step 1: Verify Existing Installation"
echo "---------------------------------------"

if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "❌ AGiXT installation not found at $INSTALL_DIR"
    exit 1
fi

if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    echo "❌ .env file not found at $INSTALL_DIR/.env"
    exit 1
fi

if [[ ! -f "$INSTALL_DIR/docker-compose.yml" ]]; then
    echo "❌ docker-compose.yml not found at $INSTALL_DIR/docker-compose.yml"
    exit 1
fi

echo "✅ AGiXT installation found"
echo "✅ .env file found"
echo "✅ docker-compose.yml found"

# Step 2: Verify backup model
echo ""
echo "🔍 Step 2: Verify Backup Model"
echo "------------------------------"

if [[ ! -f "$BACKUP_MODEL" ]]; then
    echo "❌ Backup model not found at $BACKUP_MODEL"
    exit 1
fi

MODEL_SIZE=$(du -h "$BACKUP_MODEL" | cut -f1)
echo "✅ Backup model found"
echo "📦 Model size: $MODEL_SIZE"

# Step 3: Stop containers (keep data)
echo ""
echo "🛑 Step 3: Stop Containers (Preserve Data)"
echo "------------------------------------------"

cd "$INSTALL_DIR"
echo "Stopping containers..."
docker compose down
echo "✅ Containers stopped"

# Step 4: Copy model to correct location
echo ""
echo "📋 Step 4: Copy Model to AGiXT Location"
echo "---------------------------------------"

# Create model directory
echo "Creating model directory..."
mkdir -p "$TARGET_MODEL_DIR"

# Copy model file
echo "Copying model file..."
echo "From: $BACKUP_MODEL"
echo "To: $TARGET_MODEL_FILE"

cp "$BACKUP_MODEL" "$TARGET_MODEL_FILE"

if [[ -f "$TARGET_MODEL_FILE" ]]; then
    TARGET_SIZE=$(du -h "$TARGET_MODEL_FILE" | cut -f1)
    echo "✅ Model copied successfully"
    echo "📦 Target size: $TARGET_SIZE"
else
    echo "❌ Model copy failed"
    exit 1
fi

# Set proper permissions
chown -R 1000:1000 "$INSTALL_DIR/ezlocalai" 2>/dev/null || true
chmod -R 755 "$INSTALL_DIR/ezlocalai"
echo "✅ Permissions set"

# Step 5: Update .env file (only model variables)
echo ""
echo "🔧 Step 5: Update Model Configuration in .env"
echo "----------------------------------------------"

ENV_FILE="$INSTALL_DIR/.env"
ENV_BACKUP="$ENV_FILE.backup-$(date +%Y%m%d-%H%M%S)"

# Backup .env file
cp "$ENV_FILE" "$ENV_BACKUP"
echo "📋 .env backed up to: $ENV_BACKUP"

# Update specific model variables
echo "Updating model variables..."

# Update DEFAULT_MODEL
if grep -q "^DEFAULT_MODEL=" "$ENV_FILE"; then
    sed -i "s|^DEFAULT_MODEL=.*|DEFAULT_MODEL=$MODEL_PATH_FOR_ENV|" "$ENV_FILE"
    echo "✅ Updated DEFAULT_MODEL"
else
    echo "DEFAULT_MODEL=$MODEL_PATH_FOR_ENV" >> "$ENV_FILE"
    echo "✅ Added DEFAULT_MODEL"
fi

# Update EZLOCALAI_MODEL if it exists
if grep -q "^EZLOCALAI_MODEL=" "$ENV_FILE"; then
    sed -i "s|^EZLOCALAI_MODEL=.*|EZLOCALAI_MODEL=$MODEL_PATH_FOR_ENV|" "$ENV_FILE"
    echo "✅ Updated EZLOCALAI_MODEL"
fi

echo "✅ Model configuration updated in .env"

# Step 6: Update docker-compose.yml (only model environment)
echo ""
echo "🔧 Step 6: Update Docker Compose Model Environment"
echo "---------------------------------------------------"

COMPOSE_FILE="$INSTALL_DIR/docker-compose.yml"
COMPOSE_BACKUP="$COMPOSE_FILE.backup-$(date +%Y%m%d-%H%M%S)"

# Backup docker-compose.yml
cp "$COMPOSE_FILE" "$COMPOSE_BACKUP"
echo "📋 docker-compose.yml backed up to: $COMPOSE_BACKUP"

# Update DEFAULT_MODEL in ezlocalai service environment
if grep -A 20 "ezlocalai:" "$COMPOSE_FILE" | grep -q "DEFAULT_MODEL"; then
    # Replace existing DEFAULT_MODEL line
    sed -i "/ezlocalai:/,/^[[:space:]]*[a-zA-Z]/ s|DEFAULT_MODEL=.*|DEFAULT_MODEL=$MODEL_PATH_FOR_ENV|" "$COMPOSE_FILE"
    echo "✅ Updated DEFAULT_MODEL in docker-compose.yml"
else
    # Add DEFAULT_MODEL to ezlocalai environment section
    sed -i "/ezlocalai:/,/^[[:space:]]*[a-zA-Z]/ {
        /environment:/a\
      - DEFAULT_MODEL=$MODEL_PATH_FOR_ENV
    }" "$COMPOSE_FILE"
    echo "✅ Added DEFAULT_MODEL to docker-compose.yml"
fi

echo "✅ Docker compose configuration updated"

# Step 7: Start containers
echo ""
echo "🚀 Step 7: Start Containers"
echo "---------------------------"

echo "Starting containers..."
docker compose up -d

echo "⏱️ Waiting for services to initialize..."
sleep 30

echo "✅ Containers started"

# Step 8: Validation and Control Checks
echo ""
echo "🔍 Step 8: Validation and Control Checks"
echo "========================================="

echo ""
echo "📋 Configuration Validation:"
echo "----------------------------"

# Check .env variables
echo "🔍 Checking .env variables:"
if grep -q "^DEFAULT_MODEL=$MODEL_PATH_FOR_ENV" "$ENV_FILE"; then
    echo "  ✅ DEFAULT_MODEL correctly set to: $MODEL_PATH_FOR_ENV"
else
    echo "  ❌ DEFAULT_MODEL not set correctly"
fi

# Check model file exists
echo ""
echo "🔍 Checking model file:"
if [[ -f "$TARGET_MODEL_FILE" ]]; then
    FILE_SIZE=$(du -h "$TARGET_MODEL_FILE" | cut -f1)
    echo "  ✅ Model file exists: $TARGET_MODEL_FILE"
    echo "  📦 Size: $FILE_SIZE"
else
    echo "  ❌ Model file missing: $TARGET_MODEL_FILE"
fi

# Check container status
echo ""
echo "🔍 Checking container status:"
CONTAINERS=$(docker compose ps --format "table {{.Name}}\t{{.Status}}")
echo "$CONTAINERS"

# Check if ezlocalai is running
if docker compose ps | grep -q "ezlocalai.*Up"; then
    echo "  ✅ EzLocalAI container is running"
else
    echo "  ❌ EzLocalAI container is not running"
fi

# Check ezlocalai logs for model loading
echo ""
echo "🔍 Checking EzLocalAI logs for model loading:"
echo "----------------------------------------------"
sleep 10  # Wait a bit more for logs
LOGS=$(docker compose logs ezlocalai --tail 20 2>/dev/null || echo "Could not fetch logs")
echo "$LOGS"

if echo "$LOGS" | grep -q "Qwen2.5-Coder"; then
    echo "  ✅ Model appears to be loading in logs"
else
    echo "  ⚠️  Model loading not clearly visible in logs yet"
fi

# Check API endpoints
echo ""
echo "🔍 Checking API endpoints:"
echo "-------------------------"

# Check EzLocalAI API
if curl -s http://localhost:8091/health >/dev/null 2>&1; then
    echo "  ✅ EzLocalAI API responding on port 8091"
else
    echo "  ⚠️  EzLocalAI API not responding yet on port 8091"
fi

# Check AGiXT API
if curl -s http://localhost:7437 >/dev/null 2>&1; then
    echo "  ✅ AGiXT API responding on port 7437"
else
    echo "  ⚠️  AGiXT API not responding yet on port 7437"
fi

# Final summary
echo ""
echo "📊 FINAL SUMMARY"
echo "================"
echo "🎯 Model Integration Status:"
echo "  📦 Model file: $TARGET_MODEL_FILE"
echo "  🔧 Configuration: $MODEL_PATH_FOR_ENV"
echo "  📁 Installation: $INSTALL_DIR"
echo ""
echo "🔧 Next Steps:"
echo "  1. Wait 2-3 minutes for full startup"
echo "  2. Check EzLocalAI interface: http://162.55.213.90:8091"
echo "  3. Verify model is loaded and selectable"
echo "  4. Test chat functionality in AGiXT"
echo ""
echo "📋 Troubleshooting Commands:"
echo "  cd $INSTALL_DIR"
echo "  docker compose logs ezlocalai -f    # Watch EzLocalAI logs"
echo "  docker compose logs agixt -f        # Watch AGiXT logs"
echo "  docker compose restart ezlocalai    # Restart EzLocalAI only"
echo ""
echo "✅ Model integration completed!"
