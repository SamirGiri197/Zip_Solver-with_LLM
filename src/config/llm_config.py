# --- LLM Providers ---
LLM_PROVIDERS = {
    "gemini": {
        "enabled": True,
        "name": "Google Gemini",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-2.0-flash",
    },
    "ollama": {
        "enabled": True,
        "name": "Ollama (Local)",
        "model": "gemma3:latest",
    }
}

# --- Logging ---
ENABLE_WANDB = True
WANDB_PROJECT = "zip-puzzle-llm"
LOG_FILE = "log.txt"
LOG_LEVEL = "INFO"

# --- Retry Logic ---
MAX_LLM_RETRIES = 3
LLM_TIMEOUT = 30