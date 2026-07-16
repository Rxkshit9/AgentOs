import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.models import get_llm
from prompts.registry import get_prompt
from tools.custom_tools import mcp_execution_tool
from agents.planner import clean_json_string

def tool_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Tool Agent node that identifies, prepares, and executes custom tool APIs or MCP servers."""
    llm = get_llm(temperature=0.0)
    system_prompt = get_prompt("tool")
    
    instructions = state.get("instructions", "Execute tool.")
    history = state.get("messages", [])
    
    # Stage 1: Formulate the tool arguments using LLM
    formulation_prompt = (
        f"Based on instructions: '{instructions}', identify the target server name, tool name, "
        "and arguments (as a JSON string). Provide the payload in a clean JSON format."
        "\nExpected output schema:\n"
        "```json\n"
        "{\n"
        '  "server_name": "example_server",\n'
        '  "tool_name": "example_tool",\n'
        '  "arguments": "{\\"arg1\\": \\"val1\\"}"\n'
        "}\n"
        "```"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=formulation_prompt)
    ]
    
    response = llm.invoke(messages)
    content = clean_json_string(response.content)
    
    try:
        payload = json.loads(content)
        server_name = payload.get("server_name", "default_server")
        tool_name = payload.get("tool_name", "default_tool")
        arguments = payload.get("arguments", "{}")
    except Exception as e:
        print(f"Error parsing tool execution JSON: {e}. Content was: {content}")
        server_name = "default_server"
        tool_name = "default_tool"
        arguments = "{}"
        
    # Stage 2: Call the MCP tool
    result = mcp_execution_tool.invoke({
        "server_name": server_name,
        "tool_name": tool_name,
        "arguments": arguments
    })
    
    new_message = AIMessage(
        content=f"**Tool Agent execution of '{tool_name}' on '{server_name}'**\n\nResult:\n```json\n{result}\n```",
        name="tool"
    )
    
    log_entry = {
        "agent": "tool",
        "action": f"Executed {tool_name} on {server_name}",
        "output": f"Result summary: {result[:150]}"
    }
    
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    current_step = state.get("current_step", 0)
    
    return {
        "messages": history + [new_message],
        "current_step": current_step + 1,
        "agent_logs": new_logs
    }
