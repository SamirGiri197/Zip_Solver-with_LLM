# --- Enhanced LLM Providers with ChatGPT and Claude ---
LLM_PROVIDERS = {
    "gemini": {
        "enabled": True,
        "name": "Google Gemini",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-2.0-flash",
        "description": "Google's latest multimodal AI model"
    },
    "openai": {
        "enabled": True,
        "name": "OpenAI ChatGPT",
        "api_key_env": "OPENAI_API_KEY", 
        "model": "gpt-5-nano",
        "description": "OpenAI's flagship reasoning model"
    },
    "claude": {
        "enabled": True,
        "name": "Claude",
        "api_key_env": "CLAUDE_API_KEY",
        "model": "claude-sonnet-4-5",
        "description": "Anthropic's advanced reasoning AI"
    },
    "ollama": {
        "enabled": True,
        "name": "Ollama (Local)",
        "model": "llama3.1:8b",
        "description": "Local LLM via Ollama"
    }
}

# --- Logging ---
ENABLE_WANDB = True
WANDB_PROJECT = "zip-puzzle-llm"
LOG_FILE = "llm_detailed_logs.txt"
LOG_LEVEL = "INFO"

# --- API Configuration ---
MAX_LLM_RETRIES = 2
LLM_TIMEOUT = 45

# --- Evaluation Settings ---
ENABLE_THINKING_LOGS = True
THINKING_LOG_FILE = "llm_thinking_process.log"