from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.models import get_llm
from prompts.registry import get_prompt
from tools.custom_tools import semantic_kb_search_tool

def retriever_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retriever Agent node that executes semantic KB document retrieval."""
    llm = get_llm(temperature=0.0)
    system_prompt = get_prompt("retriever")
    
    instructions = state.get("instructions", "Retrieve documentation.")
    history = state.get("messages", [])
    
    # Stage 1: Formulate search keyword/phrase using LLM
    formulation_prompt = (
        f"Based on instructions: '{instructions}', write a single search phrase "
        "to retrieve matching documentation. Output ONLY the phrase without quotes."
    )
    query_response = llm.invoke([HumanMessage(content=formulation_prompt)])
    query = query_response.content.strip().strip('"').strip("'")
    
    # Stage 2: Call the semantic KB search tool
    kb_results = semantic_kb_search_tool.invoke(query)
    
    # Stage 3: Synthesize retrieval content using the agent prompt
    synthesis_prompt = (
        f"Supervisor Instructions: {instructions}\n"
        f"Semantic Search Phrase: {query}\n\n"
        f"Retrieved Document Snippets:\n{kb_results}\n\n"
        "Please extract the relevant details and summarize the retrieved knowledge."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=synthesis_prompt)
    ]
    
    response = llm.invoke(messages)
    
    new_message = AIMessage(
        content=f"**Retriever Agent findings for query: '{query}'**\n\n{response.content}",
        name="retriever"
    )
    
    log_entry = {
        "agent": "retriever",
        "action": f"Retrieved: '{query}'",
        "output": f"Loaded documentation match: {response.content[:150]}..."
    }
    
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    current_step = state.get("current_step", 0)
    
    return {
        "messages": history + [new_message],
        "current_step": current_step + 1,
        "agent_logs": new_logs
    }
