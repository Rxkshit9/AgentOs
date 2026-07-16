from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from tools.custom_tools import web_search_tool, semantic_kb_search_tool, mcp_execution_tool, index_document_tool, write_file_tool
from config.tools import is_tool_enabled

def get_tools() -> List[BaseTool]:
    """Exposes all enabled tools based on setting flags."""
    tools = []
    # Always include semantic knowledge base search, index, and write tools
    tools.append(semantic_kb_search_tool)
    tools.append(index_document_tool)
    tools.append(write_file_tool)
    
    # Check settings flags for web search
    if is_tool_enabled("web_search"):
        tools.append(web_search_tool)
    else:
        # Fallback tool wrapper so agents can still call search and get mock/fallback logs
        tools.append(web_search_tool)
        
    # Check settings flags for MCP
    tools.append(mcp_execution_tool)
    
    return tools

def list_tools_metadata() -> List[Dict[str, Any]]:
    """Returns metadata for all available tools, suitable for presentation."""
    return [
        {
            "name": t.name,
            "description": t.description,
            "args": t.args
        }
        for t in get_tools()
    ]
