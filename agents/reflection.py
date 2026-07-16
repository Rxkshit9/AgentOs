import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.models import get_llm
from prompts.registry import get_prompt
from agents.planner import clean_json_string

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

def reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Reflection Agent node that reviews factual accuracy and creates the final response."""
    llm = get_llm(temperature=0.7)  # Higher temperature for friendly small talk
    system_prompt = get_prompt("reflection")
    
    # Context format
    history = state.get("messages", [])
    
    # Get the last human message as the active query
    human_messages = [msg for msg in history if msg.type == "human"]
    user_query = human_messages[-1].content if human_messages else "No objective set"
    
    current_retries = state.get("retries", 0)
    
    log_entry = {
        "agent": "reflection",
        "action": "Conducted Final Reflection",
        "output": "Greeting or small talk detected. Bypassed strict factual verification checks."
    }
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    if is_simple_greeting(user_query):
        # Conversational bypass: let LLM reply directly to history
        memories = state.get("memories_retrieved", [])
        if memories:
            mem_context = "Recall these facts from long-term memory about the user:\n" + "\n".join([f"- {m}" for m in memories])
            system_prompt_with_mems = f"{system_prompt}\n\n{mem_context}"
            messages = [
                SystemMessage(content=system_prompt_with_mems)
            ] + list(history)
            response = llm.invoke(messages)
        else:
            response = llm.invoke(history)
            
        updated_messages = list(history)
        updated_messages.append(AIMessage(content=response.content, name="reflection"))
        
        return {
            "messages": updated_messages,
            "reflection_passed": True,
            "suggested_retry_agent": None,
            "agent_logs": new_logs,
            "retries": current_retries
        }
        
    # Standard factual query processing:
    # Find the index of the last human message to isolate current turn findings
    last_human_idx = -1
    for i in range(len(history) - 1, -1, -1):
        if history[i].type == "human":
            last_human_idx = i
            break
            
    current_turn_messages = history[last_human_idx + 1:] if last_human_idx != -1 else history
    findings = "\n\n".join([
        f"--- {msg.name or msg.type.upper()}: ---\n{msg.content}"
        for msg in current_turn_messages if msg.type in ("ai", "tool")
    ])
    
    # Format the recent history for the reflection agent (short-term memory context)
    history_context = "\n".join([
        f"{msg.type.upper()}: {msg.content}"
        for msg in history if msg.type in ("human", "ai") and msg.content != user_query
    ])
    if not history_context.strip():
        history_context = "None (This is the start of the conversation)."
    
    memories = state.get("memories_retrieved", [])
    memories_context = "\n".join([f"- {m}" for m in memories]) if memories else "None"
    
    confidence = state.get("confidence_score", 100)
    
    prompt = (
        f"User Query: {user_query}\n\n"
        f"Recent Chat History:\n{history_context}\n\n"
        f"Long-term Memories context:\n{memories_context}\n\n"
        f"Factual Confidence Score (0-100): {confidence}\n\n"
        f"Agent Findings from Execution:\n{findings}\n\n"
        "Review the findings, conversational history, and long-term memories context to draft the final response. Output JSON format."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    content = clean_json_string(response.content)
    
    # Defaults
    reflection_passed = True
    hallucination_detected = False
    feedback = "Direct pass without reflection errors."
    suggested_retry_agent = None
    refined_response = ""
    
    try:
        data = json.loads(content)
        reflection_passed = data.get("reflection_passed", True)
        hallucination_detected = data.get("hallucination_detected", False)
        feedback = data.get("feedback", "")
        suggested_retry_agent = data.get("suggested_retry_agent")
        refined_response = data.get("refined_response", "")
    except Exception as e:
        print(f"Error parsing reflection JSON: {e}. Content: {content}")
        # Default fallback to a basic synthesis
        refined_response = f"Here is what we gathered:\n\n{findings}"
        
    log_entry = {
        "agent": "reflection",
        "action": "Conducted Final Reflection",
        "output": f"Passed: {reflection_passed}\nHallucinations Detected: {hallucination_detected}\nFeedback: {feedback}"
    }
    
    current_logs = state.get("agent_logs") or []
    new_logs = current_logs + [log_entry]
    
    # If passed and we have a refined response, we attach it to the message stack
    updated_messages = list(history)
    if reflection_passed and refined_response:
        updated_messages.append(AIMessage(
            content=refined_response,
            name="reflection"
        ))
        
    current_retries = state.get("retries", 0)
    next_retries = current_retries if reflection_passed else current_retries + 1

    return {
        "messages": updated_messages,
        "reflection_passed": reflection_passed,
        "suggested_retry_agent": suggested_retry_agent,
        "agent_logs": new_logs,
        "retries": next_retries
    }
