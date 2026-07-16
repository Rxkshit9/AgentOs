import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from config.models import get_llm
from prompts.registry import get_prompt
from memory.postgres_store import PostgresStore
from agents.planner import clean_json_string

def memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Memory Agent node that extracts facts and stores them in PostgreSQL long-term memory."""
    llm = get_llm(temperature=0.0)
    system_prompt = get_prompt("memory")
    
    # Format message history context
    history = state.get("messages", [])
    history_text = "\n".join([f"{msg.type.upper()}: {msg.content}" for msg in history[-10:]])
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Examine the conversation history for facts to store:\n{history_text}")
    ]
    
    response = llm.invoke(messages)
    content = clean_json_string(response.content)
    
    upserted_keys = []
    try:
        data = json.loads(content)
        memories = data.get("memories_to_upsert", [])
        
        # Instantiate memory store
        store = PostgresStore()
        
        for mem in memories:
            key = mem.get("key")
            value = mem.get("value")
            if key and value:
                # Save to PostgreSQL BaseStore
                store.put(
                    namespace=("default_user", "memories"),
                    key=key,
                    value={"content": value}
                )
                upserted_keys.append(key)
    except Exception as e:
        print(f"Error parsing memory updates: {e}. Output was: {content}")
        
    upsert_summary = f"Saved {len(upserted_keys)} memories: {', '.join(upserted_keys)}" if upserted_keys else "No new memories worth saving detected."
    
    log_entry = {
        "agent": "memory",
        "action": "Updated Long-term Memory",
        "output": upsert_summary
    }
    
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    return {
        "agent_logs": new_logs
    }
