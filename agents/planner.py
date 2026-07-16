import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from config.models import get_llm
from prompts.registry import get_prompt

def clean_json_string(text: str) -> str:
    """Helper to extract JSON block from markdown strings if present."""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def is_simple_greeting(text: str) -> bool:
    clean = text.strip().lower().replace(",", " ").replace(".", " ").replace("!", " ").replace("?", " ")
    words = clean.split()
    if not words:
        return False
        
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "yo", "sup", "howdy", "what's up", "whats up"}
    
    # Check if the entire query is a simple greeting
    if len(words) <= 2 and any(w in greetings for w in words):
        return True
        
    # Check if the text starts with a greeting
    first_word = words[0]
    if first_word in greetings:
        remaining = " ".join(words[1:])
        if not remaining or any(phrase in remaining for phrase in ["my name is", "i am", "i'm", "im", "this is", "how are you", "whats up"]):
            return True
        if len(words) <= 3:
            return True
            
    # Check if the query is a standalone introduction or query about name/identity
    if clean.startswith(("my name is", "i'm ", "im ", "i am ", "who are you", "what is my name", "what is your name")):
        return True
        
    return False

def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Planner Agent node that generates an execution plan for the query."""
    llm = get_llm(temperature=0.1)
    
    # Retrieve system prompt
    system_prompt = get_prompt("planner")
    
    # Gather context including memories
    memories = state.get("memories_retrieved", [])
    memories_context = "\n".join([f"- {m}" for m in memories]) if memories else "None"
    
    user_messages = [msg for msg in state.get("messages", []) if msg.type == "human"]
    user_query = user_messages[-1].content if user_messages else "No objective set"
    
    if is_simple_greeting(user_query):
        plan_data = {
            "objective": "Acknowledge the user's greeting.",
            "steps": []
        }
    else:
        prompt = (
            f"User Query: {user_query}\n\n"
            f"Historical memories of preferences/workflows:\n{memories_context}\n\n"
            "Generate a step-by-step execution plan in JSON format."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        content = clean_json_string(response.content)
        
        try:
            plan_data = json.loads(content)
        except Exception as e:
            # Robust fallback if LLM produces bad JSON
            plan_data = {
                "objective": user_query,
                "steps": [
                    {
                        "step_number": 1,
                        "description": f"Execute general research for: {user_query}",
                        "required_agent": "research",
                        "estimated_tools": ["web_search_tool"]
                    }
                ]
            }
            print(f"Error parsing planner JSON: {e}. Output was: {content}")
        
    # Log execution trace
    log_entry = {
        "agent": "planner",
        "action": "Generated Plan",
        "output": f"Objective: {plan_data.get('objective')}\nSteps: {len(plan_data.get('steps', []))} subtasks identified."
    }
    
    current_logs = state.get("agent_logs", [])
    new_logs = current_logs + [log_entry]
    
    return {
        "plan": plan_data,
        "current_step": 0,
        "agent_logs": new_logs
    }
