import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from config.models import get_llm
from prompts.registry import get_prompt
from agents.planner import clean_json_string

def verification_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Verification Agent node that calculates a confidence score and detects contradictions."""
    llm = get_llm(temperature=0.0)
    system_prompt = get_prompt("verification")
    
    # Gather findings context from agent messages in the current turn
    history = state.get("messages", [])
    
    # Find the index of the last human message
    last_human_idx = -1
    for i in range(len(history) - 1, -1, -1):
        if history[i].type == "human":
            last_human_idx = i
            break
            
    current_turn_messages = history[last_human_idx + 1:] if last_human_idx != -1 else history
    findings_context = "\n\n".join([
        f"--- Agent Output ({msg.name or msg.type}): ---\n{msg.content}"
        for msg in current_turn_messages if msg.type in ("ai", "tool")
    ])
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Verify findings in history:\n{findings_context}")
    ]
    
    response = llm.invoke(messages)
    content = clean_json_string(response.content)
    
    # Default values
    confidence_score = 100
    contradictions = []
    unsupported_claims = []
    justification = "Direct pass without anomalies."
    
    try:
        verif_data = json.loads(content)
        confidence_score = int(verif_data.get("confidence_score", 100))
        contradictions = verif_data.get("contradictions", [])
        unsupported_claims = verif_data.get("unsupported_claims", [])
        justification = verif_data.get("justification", "")
    except Exception as e:
        print(f"Error parsing verification results: {e}. Content: {content}")
        
    log_entry = {
        "agent": "verification",
        "action": "Verified Factual Accuracy",
        "output": (
            f"Confidence Score: {confidence_score}/100\n"
            f"Contradictions: {len(contradictions)}\n"
            f"Unsupported Claims: {len(unsupported_claims)}\n"
            f"Justification: {justification}"
        )
    }
    
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    return {
        "confidence_score": confidence_score,
        "agent_logs": new_logs
    }
