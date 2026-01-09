import os
import yaml
from jinja2 import Template

CONFIG_DIR = os.path.join(os.getcwd(), 'config')

def load_yaml(filename):
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_template(filename):
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return Template(f.read())

# Load configs once at module level
try:
    LLM_CONFIG = load_yaml('llm_config.yaml')
    BOT_CONFIG = load_yaml('bot_config.yaml')
    SYSTEM_PROMPT_TEMPLATE = load_template('system_prompt.j2')
except Exception as e:
    print(f"Error loading config: {e}")
    # Fallbacks/Defaults
    LLM_CONFIG = {
        "provider": {"base_url": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant"},
        "parameters": {"temperature": 0.6, "max_tokens": 1024, "top_p": 1.0}
    }
    BOT_CONFIG = {"rate_limit": {"limit": 2, "window": 3}}
    # Minimal fallback template
    SYSTEM_PROMPT_TEMPLATE = Template("You are a helpful assistant. Context: {{ services_context }}")
