from config.settings import settings

def is_tool_enabled(tool_name: str) -> bool:
    """Checks if a tool is enabled based on its key in Settings."""
    if tool_name == "web_search":
        return settings.get_api_key("search") is not None
    elif tool_name == "github":
        return settings.get_api_key("github") is not None
    elif tool_name == "mcp_server":
        return settings.get_api_key("mcp_server") is not None
    # Retriever and local database searches are always enabled by default
    return True
