import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from config.models import get_llm
from prompts.registry import get_prompt
from agents.planner import clean_json_string

def supervisor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Supervisor Agent node that manages step execution routing and updates instructions."""
    llm = get_llm(temperature=0.0)
    system_prompt = get_prompt("supervisor")
    
    plan = state.get("plan") or {}
    steps = plan.get("steps") or []
    current_step_idx = state.get("current_step", 0)
    
    # If we have executed all steps, supervisor routes to memory agent
    if current_step_idx >= len(steps):
        log_entry = {
            "agent": "supervisor",
            "action": "Execution Complete",
            "output": "All steps of the plan have been executed. Routing to Memory Agent."
        }
        current_logs = state.get("agent_logs") or []
        return {
            "next_agent": "memory",
            "instructions": "Summarize findings and update memories.",
            "agent_logs": current_logs + [log_entry]
        }
        
    current_step = steps[current_step_idx]
    
    # Format current progress context for the LLM
    progress_context = (
        f"Overall Objective: {plan.get('objective')}\n"
        f"Execution Plan: {json.dumps(steps, indent=2)}\n"
        f"Currently evaluating Step index: {current_step_idx} (Step description: {current_step.get('description')})\n"
        f"Conversation History: {state.get('messages', [])[-3:]}\n"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Assess state and route task:\n{progress_context}")
    ]
    
    response = llm.invoke(messages)
    content = clean_json_string(response.content)
    
    try:
        routing_data = json.loads(content)
        next_agent = routing_data.get("next_agent", current_step.get("required_agent", "research"))
        instructions = routing_data.get("instructions_for_agent", current_step.get("description", ""))
    except Exception as e:
        print(f"Error parsing supervisor routing JSON: {e}. Content: {content}")
        # Fallback to the step definition
        next_agent = current_step.get("required_agent", "research")
        instructions = current_step.get("description", "")
        routing_data = {"reasoning": "Fallback to plan step definition due to parsing error."}
        
    log_entry = {
        "agent": "supervisor",
        "action": f"Routed to {next_agent.upper()}",
        "output": f"Reason: {routing_data.get('reasoning')}\nInstructions: {instructions}"
    }
    
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    return {
        "next_agent": next_agent,
        "instructions": instructions,
        "agent_logs": new_logs
    }
