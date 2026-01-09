import os
import yaml

CONFIG_DIR = os.path.join(os.getcwd(), 'config')

def load_yaml(filename):
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_text(filename):
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r') as f:
        return f.read()

# Load configs once at module level (or lazy load if preferred, but eager is fine here)
try:
    LLM_CONFIG = load_yaml('llm_config.yaml')
    BOT_CONFIG = load_yaml('bot_config.yaml')
    SYSTEM_PROMPT_TEMPLATE = load_text('system_prompt.txt')
except Exception as e:
    print(f"Error loading config: {e}")
    # Fallbacks/Defaults
    LLM_CONFIG = {
        "provider": {"base_url": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant"},
        "parameters": {"temperature": 0.6, "max_tokens": 1024, "top_p": 1.0}
    }
    BOT_CONFIG = {"rate_limit": {"limit": 2, "window": 3}}
    SYSTEM_PROMPT_TEMPLATE = "Error loading prompt."
