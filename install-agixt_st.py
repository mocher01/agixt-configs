def start_agixt_services(install_path: str, config: Dict[str, str]) -> bool:
    """Start AGiXT services using the official start.py with all our options"""
    try:
        os.chdir(install_path)
        
        # Construire la commande start.py avec toutes nos options
        cmd = ["python", "start.py"]
        
        # Ajouter toutes nos variables comme options start.py
        if config.get('THEME_NAME'):
            cmd.extend(["--theme-name", config['THEME_NAME']])
        if config.get('AGIXT_SHOW_SELECTION'):
            cmd.extend(["--agixt-show-selection", config['AGIXT_SHOW_SELECTION']])
        if config.get('AUTH_PROVIDER'):
            cmd.extend(["--auth-provider", config['AUTH_PROVIDER']])
        if config.get('INTERACTIVE_MODE'):
            cmd.extend(["--interactive-mode", config['INTERACTIVE_MODE']])
        if config.get('APP_NAME'):
            cmd.extend(["--app-name", config['APP_NAME']])
        if config.get('APP_DESCRIPTION'):
            cmd.extend(["--app-description", config['APP_DESCRIPTION']])
        if config.get('APP_URI'):
            cmd.extend(["--app-uri", config['APP_URI']])
        if config.get('AUTH_WEB'):
            cmd.extend(["--auth-web", config['AUTH_WEB']])
        if config.get('AGIXT_AGENT'):
            cmd.extend(["--agixt-agent", config['AGIXT_AGENT']])
        if config.get('AGIXT_SHOW_AGENT_BAR') == 'true':
            cmd.extend(["--agixt-show-agent-bar", "true"])
        if config.get('AGIXT_SHOW_APP_BAR') == 'true':
            cmd.extend(["--agixt-show-app-bar", "true"])
        if config.get('AGIXT_CONVERSATION_MODE'):
            cmd.extend(["--agixt-conversation-mode", config['AGIXT_CONVERSATION_MODE']])
        if config.get('AGIXT_FILE_UPLOAD_ENABLED') == 'true':
            cmd.extend(["--agixt-file-upload-enabled", "true"])
        if config.get('AGIXT_VOICE_INPUT_ENABLED') == 'true':
            cmd.extend(["--agixt-voice-input-enabled", "true"])
        if config.get('AGIXT_RLHF') == 'true':
            cmd.extend(["--agixt-rlhf", "true"])
        if config.get('AGIXT_FOOTER_MESSAGE'):
            cmd.extend(["--agixt-footer-message", config['AGIXT_FOOTER_MESSAGE']])
        if config.get('ALLOW_EMAIL_SIGN_IN') == 'true':
            cmd.extend(["--allow-email-sign-in", "true"])
        if config.get('DATABASE_TYPE'):
            cmd.extend(["--database-type", config['DATABASE_TYPE']])
        if config.get('DATABASE_NAME'):
            cmd.extend(["--database-name", config['DATABASE_NAME']])
        if config.get('LOG_LEVEL'):
            cmd.extend(["--log-level", config['LOG_LEVEL']])
        if config.get('UVICORN_WORKERS'):
            cmd.extend(["--uvicorn-workers", config['UVICORN_WORKERS']])
        if config.get('WORKING_DIRECTORY'):
            cmd.extend(["--working-directory", config['WORKING_DIRECTORY']])
        if config.get('TZ'):
            cmd.extend(["--tz", config['TZ']])
        if config.get('ALLOWED_DOMAINS'):
            cmd.extend(["--allowed-domains", config['ALLOWED_DOMAINS']])
        if config.get('AGIXT_AUTO_UPDATE') == 'true':
            cmd.extend(["--agixt-auto-update", "true"])
        
        print(f"🚀 Démarrage AGiXT avec la commande officielle start.py...")
        print(f"📝 Commande: {' '.join(cmd)}")
        
        # Exécuter start.py avec toutes nos options
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ AGiXT démarré avec succès via start.py")
            print(f"📝 Output: {result.stdout}")
            
            # Attendre que les services soient prêts
            time.sleep(10)
            
            # Vérifier les services
            ps_result = subprocess.run(["docker", "compose", "ps"], 
                                     capture_output=True, text=True)
            print(f"📊 État des services:\n{ps_result.stdout}")
            
            return True
        else:
            print(f"❌ Erreur lors du démarrage via start.py:")
            print(f"📝 Error: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout lors du démarrage d'AGiXT (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du démarrage d'AGiXT: {e}")
        return False
