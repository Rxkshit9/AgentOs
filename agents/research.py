from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.models import get_llm
from prompts.registry import get_prompt
from tools.custom_tools import web_search_tool

def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Research Agent node that performs web search and summarizes findings with citations."""
    llm = get_llm(temperature=0.0)
    system_prompt = get_prompt("research")
    
    instructions = state.get("instructions", "Perform research.")
    history = state.get("messages", [])
    
    # Stage 1: Formulate search query using LLM
    formulation_prompt = (
        f"Based on these instructions: '{instructions}' and the conversation context, "
        "write a single, optimized search engine query. Output ONLY the query text without quotes."
    )
    query_response = llm.invoke([HumanMessage(content=formulation_prompt)])
    query = query_response.content.strip().strip('"').strip("'")
    
    # Stage 2: Call the search tool
    search_results = web_search_tool.invoke(query)
    
    # Stage 3: Synthesize search results using the agent prompt
    synthesis_prompt = (
        f"Supervisor Instructions: {instructions}\n"
        f"Search Query: {query}\n\n"
        f"Raw Search Results:\n{search_results}\n\n"
        "Synthesize these findings and provide a summary with inline sources."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=synthesis_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # Update messages in state by adding the research findings
    new_message = AIMessage(
        content=f"**Research Agent findings for search query: '{query}'**\n\n{response.content}",
        name="research"
    )
    
    log_entry = {
        "agent": "research",
        "action": f"Searched: '{query}'",
        "output": f"Found results and synthesized findings."
    }
    
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    current_step = state.get("current_step", 0)
    
    return {
        "messages": history + [new_message],
        "current_step": current_step + 1,
        "agent_logs": new_logs
    }
