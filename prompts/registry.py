from pathlib import Path
from typing import Dict
from config.settings import settings

# In-memory cache for loaded prompts
_prompt_cache: Dict[str, str] = {}

def get_prompt(agent_name: str) -> str:
    """Reads a system prompt markdown file from the prompts directory and caches it."""
    if agent_name in _prompt_cache:
        return _prompt_cache[agent_name]
        
    prompt_file = settings.PROMPTS_DIR / f"{agent_name}.md"
    if not prompt_file.exists():
        # Fallback default if file is missing
        return f"You are the {agent_name.capitalize()} Agent in AgentOS."
        
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read()
            _prompt_cache[agent_name] = content
            return content
    except Exception as e:
        print(f"Error loading prompt '{agent_name}': {e}")
        return f"You are the {agent_name.capitalize()} Agent in AgentOS."
