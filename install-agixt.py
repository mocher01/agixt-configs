# Fixed section for the installer script - replace the problematic part

def update_docker_compose(install_path: str) -> bool:
    """Update docker-compose.yml for proxy setup and EzLocalAI"""
    compose_file = os.path.join(install_path, "docker-compose.yml")
    
    if not os.path.exists(compose_file):
        log(f"docker-compose.yml not found at {compose_file}", "ERROR")
        return False
    
    try:
        log("Updating docker-compose.yml for v1.1-proxy-fixed...")
        
        # Read original docker-compose.yml
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Backup original
        backup_file = compose_file + f".backup-{VERSION}"
        with open(backup_file, 'w') as f:
            f.write(content)
        log(f"Backup created: {backup_file}")
        
        # Create the enhanced docker-compose.yml
        enhanced_compose = """networks:
  agixt-network:
    external: true

services:
  # EzLocalAI - Manual Model Selection
  ezlocalai:
    image: joshxt/ezlocalai:main
    container_name: ezlocalai
    restart: unless-stopped
    environment:
      - LLM_MAX_TOKENS=${LLM_MAX_TOKENS}
      - THREADS=${THREADS}
      - GPU_LAYERS=${GPU_LAYERS}
      - WHISPER_MODEL=${WHISPER_MODEL}
      - IMG_ENABLED=${IMG_ENABLED}
      - AUTO_UPDATE=${AUTO_UPDATE}
      - EZLOCALAI_API_KEY=${EZLOCALAI_API_KEY}
      - EZLOCALAI_URL=http://ezlocalai:8091
      - DEFAULT_MODEL=${DEFAULT_MODEL}
    ports:
      - "8091:8091"
    volumes:
      - ./ezlocalai:/app/models
      - ./ezlocalai/voices:/app/voices
    networks:
      - agixt-network

  # AGiXT Backend API
  agixt:
    image: joshxt/agixt:main
    container_name: agixt
    restart: unless-stopped
    depends_on:
      - ezlocalai
    environment:
      # Version & Basic Configuration
      - AGIXT_VERSION=${AGIXT_VERSION}
      - INSTALL_DATE=${INSTALL_DATE}
      - AGIXT_AUTO_UPDATE=${AGIXT_AUTO_UPDATE}
      - AGIXT_API_KEY=${AGIXT_API_KEY}
      - UVICORN_WORKERS=${UVICORN_WORKERS}
      - WORKING_DIRECTORY=${WORKING_DIRECTORY}
      - TZ=${TZ}
      # URLs
      - AGIXT_SERVER=${AGIXT_SERVER}
      - AGIXT_URI=${AGIXT_URI}
      # System Configuration
      - DATABASE_TYPE=${DATABASE_TYPE}
      - DATABASE_NAME=${DATABASE_NAME}
      - LOG_LEVEL=${LOG_LEVEL}
      - LOG_FORMAT=${LOG_FORMAT}
      - ALLOWED_DOMAINS=${ALLOWED_DOMAINS}
      - AGIXT_BRANCH=${AGIXT_BRANCH}
      - AGIXT_REQUIRE_API_KEY=${AGIXT_REQUIRE_API_KEY}
      # GraphQL Support
      - GRAPHIQL=${GRAPHIQL}
      - ENABLE_GRAPHQL=${ENABLE_GRAPHQL}
      # EzLocalAI Integration
      - EZLOCALAI_API_URL=${EZLOCALAI_API_URL}
      - EZLOCALAI_API_KEY=${EZLOCALAI_API_KEY}
      - EZLOCALAI_MAX_TOKENS=${EZLOCALAI_MAX_TOKENS}
      - EZLOCALAI_TEMPERATURE=${EZLOCALAI_TEMPERATURE}
      - EZLOCALAI_TOP_P=${EZLOCALAI_TOP_P}
      - EZLOCALAI_VOICE=${EZLOCALAI_VOICE}
      # External Services
      - TEXTGEN_URI=${TEXTGEN_URI}
      - N8N_URI=${N8N_URI}
    ports:
      - "7437:7437"
    volumes:
      - ./models:/agixt/models
      - ./WORKSPACE:/agixt/WORKSPACE
      - ./agixt:/agixt
    networks:
      - agixt-network

  # AGiXT Frontend Interface
  agixtinteractive:
    image: joshxt/agixt-interactive:main
    container_name: agixtinteractive
    restart: unless-stopped
    depends_on:
      - agixt
    environment:
      # Interface Configuration
      - APP_NAME=${APP_NAME}
      - APP_DESCRIPTION=${APP_DESCRIPTION}
      - APP_URI=${APP_URI}
      - AUTH_WEB=${AUTH_WEB}
      - AGIXT_AGENT=${AGIXT_AGENT}
      - AGIXT_SHOW_SELECTION=${AGIXT_SHOW_SELECTION}
      - AGIXT_SHOW_AGENT_BAR=${AGIXT_SHOW_AGENT_BAR}
      - AGIXT_SHOW_APP_BAR=${AGIXT_SHOW_APP_BAR}
      - AGIXT_CONVERSATION_MODE=${AGIXT_CONVERSATION_MODE}
      - INTERACTIVE_MODE=${INTERACTIVE_MODE}
      - THEME_NAME=${THEME_NAME}
      - AGIXT_FOOTER_MESSAGE=${AGIXT_FOOTER_MESSAGE}
      # Authentication
      - AUTH_PROVIDER=${AUTH_PROVIDER}
      - CREATE_AGENT_ON_REGISTER=${CREATE_AGENT_ON_REGISTER}
      - CREATE_AGIXT_AGENT=${CREATE_AGIXT_AGENT}
      - ALLOW_EMAIL_SIGN_IN=${ALLOW_EMAIL_SIGN_IN}
      # Features
      - AGIXT_FILE_UPLOAD_ENABLED=${AGIXT_FILE_UPLOAD_ENABLED}
      - AGIXT_VOICE_INPUT_ENABLED=${AGIXT_VOICE_INPUT_ENABLED}
      - AGIXT_RLHF=${AGIXT_RLHF}
      - AGIXT_ALLOW_MESSAGE_EDITING=${AGIXT_ALLOW_MESSAGE_EDITING}
      - AGIXT_ALLOW_MESSAGE_DELETION=${AGIXT_ALLOW_MESSAGE_DELETION}
      - AGIXT_SHOW_OVERRIDE_SWITCHES=${AGIXT_SHOW_OVERRIDE_SWITCHES}
      # Backend Connection
      - AGIXT_SERVER=${AGIXT_SERVER}
      - AGIXT_URI=http://agixt:7437
      - TZ=${TZ}
    ports:
      - "3437:3437"
    volumes:
      - ./WORKSPACE:/app/WORKSPACE
    networks:
      - agixt-network
"""
        
        # Write the enhanced docker-compose.yml
        with open(compose_file, 'w') as f:
            f.write(enhanced_compose)
        
        log("docker-compose.yml updated for v1.1-proxy-fixed with manual EzLocalAI", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Failed to update docker-compose.yml: {e}", "ERROR")
        return False
