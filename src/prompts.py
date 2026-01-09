import os
from jinja2 import Template

PROMPTS_DIR = os.path.join(os.getcwd(), 'config', 'prompts')
DEFAULT_MODE = "default"

# Global state to store the current mode
# in a real app, this might be in DB or redis to persist across restarts
_current_mode = DEFAULT_MODE

def get_current_mode():
    return _current_mode

def set_mode(mode_name):
    """Sets the global bot mode if the prompt file exists."""
    global _current_mode
    path = os.path.join(PROMPTS_DIR, f"{mode_name}.j2")
    if os.path.exists(path):
        _current_mode = mode_name
        return True
    return False

def load_prompt_template(mode_name=None):
    """Loads the Jinja2 template for the given mode (or current mode)."""
    if mode_name is None:
        mode_name = _current_mode

    filename = f"{mode_name}.j2"
    path = os.path.join(PROMPTS_DIR, filename)

    if not os.path.exists(path):
        # Fallback to default if specific mode not found
        path = os.path.join(PROMPTS_DIR, f"{DEFAULT_MODE}.j2")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return Template(f.read())
    except Exception as e:
        print(f"Error loading prompt {path}: {e}")
        # Emergency fallback
        return Template("You are a helpful assistant. {{ services_context }}")

def list_modes():
    """Lists available prompt modes based on files in config/prompts."""
    files = os.listdir(PROMPTS_DIR)
    modes = [f.replace('.j2', '') for f in files if f.endswith('.j2')]
    return modes
