import pytest
from config.settings import settings
from config.models import get_llm
from prompts.registry import get_prompt
from tools.registry import get_tools

def test_settings_load():
    """Verify that configuration settings parse and load correctly."""
    assert settings.LLM_PROVIDER == "ollama"
    assert settings.DATABASE_URL is not None
    assert settings.APIS_YAML_PATH.exists()

def test_prompt_registry():
    """Verify that system prompts are successfully loaded from file assets."""
    planner_prompt = get_prompt("planner")
    assert "Planner" in planner_prompt
    
    fallback_prompt = get_prompt("non_existent_agent")
    assert "Non_existent_agent" in fallback_prompt

def test_tool_registry():
    """Verify that active tools are registered and available."""
    tools = get_tools()
    assert len(tools) >= 1
    tool_names = [t.name for t in tools]
    assert "semantic_kb_search_tool" in tool_names
