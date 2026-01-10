import os
import random
from jinja2 import Template, Environment, FileSystemLoader

PROMPTS_DIR = os.path.join(os.getcwd(), 'config', 'prompts')
DEFAULT_MODE = "default"

# Setup Jinja2 Environment for modular loading
jinja_env = Environment(loader=FileSystemLoader(PROMPTS_DIR))

# Global state to store the current mode (Legacy/Base mode)
_current_mode = DEFAULT_MODE

# In-memory storage for user persona seeds
# Format: {user_id: {"mood": "...", "style": "...", "thought": "..."}}
_user_personas = {}

def get_current_mode():
    return _current_mode

def set_mode(mode_name):
    """Sets the global bot mode if the prompt file exists (Legacy support)."""
    global _current_mode
    path = os.path.join(PROMPTS_DIR, f"{mode_name}.j2")
    if os.path.exists(path):
        _current_mode = mode_name
        return True
    return False

def _get_random_template_content(category):
    """Reads a random .j2 file from a subdirectory (e.g., 'mood')."""
    category_dir = os.path.join(PROMPTS_DIR, category)
    if not os.path.exists(category_dir):
        return ""

    files = [f for f in os.listdir(category_dir) if f.endswith('.j2')]
    if not files:
        return ""

    chosen = random.choice(files)
    path = os.path.join(category_dir, chosen)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading template {path}: {e}")
        return ""

def _get_or_create_user_persona(user_id):
    """Gets existing persona for user or creates a new random one."""
    if user_id not in _user_personas:
        # Determine options dynamically from directories
        moods = [f.replace('.j2','') for f in os.listdir(os.path.join(PROMPTS_DIR, 'mood')) if f.endswith('.j2')]
        styles = [f.replace('.j2','') for f in os.listdir(os.path.join(PROMPTS_DIR, 'style')) if f.endswith('.j2')]
        thoughts = [f.replace('.j2','') for f in os.listdir(os.path.join(PROMPTS_DIR, 'thought')) if f.endswith('.j2')]

        _user_personas[user_id] = {
            "mood": random.choice(moods) if moods else "professional",
            "style": random.choice(styles) if styles else "concise",
            "thought": random.choice(thoughts) if thoughts else "analytical"
        }
    return _user_personas[user_id]

def load_prompt_template(user_id=None):
    """
    Constructs a dynamic 'Consciousness Web' prompt for the user.
    Combines Core + Mood + Style + Thought.
    """
    try:
        # 1. Load Base Core (Secretary)
        core_template = jinja_env.get_template("core/secretary.j2")
        base_prompt = core_template.render()

        # 2. Get User Persona (Randomized but consistent per session)
        if user_id:
            persona = _get_or_create_user_persona(user_id)
            mood_file = f"mood/{persona['mood']}.j2"
            style_file = f"style/{persona['style']}.j2"
            thought_file = f"thought/{persona['thought']}.j2"
        else:
            # Fallback for generic calls
            mood_file = "mood/professional.j2"
            style_file = "style/concise.j2"
            thought_file = "thought/analytical.j2"

        # 3. Load Components
        try:
            mood_text = jinja_env.get_template(mood_file).render()
        except: mood_text = ""

        try:
            style_text = jinja_env.get_template(style_file).render()
        except: style_text = ""

        try:
            thought_text = jinja_env.get_template(thought_file).render()
        except: thought_text = ""

        # 4. Weave together
        # We manually concatenate them because the 'system prompt' is the sum of these instructions.
        # In a more advanced version, we could use a master .j2 that includes them.

        full_prompt_str = (
            f"{base_prompt}\n\n"
            f"--- PERSONALITY MODULES ---\n"
            f"{mood_text}\n\n"
            f"{style_text}\n\n"
            f"{thought_text}\n\n"
            f"--- CONTEXT ---\n"
            "{{ services_context }}"
        )

        return Template(full_prompt_str)

    except Exception as e:
        print(f"Error constructing dynamic prompt: {e}")
        return Template("You are a helpful assistant. {{ services_context }}")

def list_modes():
    """Lists available prompt modes based on files in config/prompts."""
    # This is legacy /modes command. We can list the top-level files.
    files = os.listdir(PROMPTS_DIR)
    modes = [f.replace('.j2', '') for f in files if f.endswith('.j2')]
    return modes
