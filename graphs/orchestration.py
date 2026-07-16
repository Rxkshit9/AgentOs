import logging
from typing import Dict, Any, List, Annotated, Tuple, Optional
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver

from memory.postgres_store import PostgresStore
from agents.planner import planner_node
from agents.supervisor import supervisor_node
from agents.research import research_node
from agents.retriever import retriever_node
from agents.tool import tool_node
from agents.memory import memory_node
from agents.verification import verification_node
from agents.reflection import reflection_node

class AgentState(MessagesState):
    """Custom state tracking overall session data, plan status, and agent outputs."""
    plan: Dict[str, Any]
    current_step: int
    next_agent: str
    instructions: str
    memories_retrieved: List[str]
    confidence_score: int
    reflection_passed: bool
    suggested_retry_agent: str
    agent_logs: List[Dict[str, Any]]
    retries: int

def retrieve_memories_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves long-term user memories from PostgreSQL before executing planner."""
    store = PostgresStore()
    
    # Extract the user query from the messages state
    history = state.get("messages", [])
    human_messages = [msg for msg in history if msg.type == "human"]
    user_query = human_messages[-1].content if human_messages else ""

    # Search for user memories semantically using pgvector
    try:
        if user_query:
            items = store.search(namespace_prefix=("default_user", "memories"), query=user_query, limit=5)
        else:
            items = store.search(namespace_prefix=("default_user", "memories"), limit=5)
    except Exception as exc:
        logging.getLogger(__name__).warning("Memory lookup failed, continuing without stored memories: %s", exc)
        items = []
        
    mem_strings = [item.value.get("content", "") for item in items if item.value]
    
    log_entry = {
        "agent": "memory_retriever",
        "action": "Loaded Memories",
        "output": f"Loaded {len(mem_strings)} user memory records."
    }
    
    current_logs = state.get("agent_logs") or []
    return {
        "memories_retrieved": mem_strings,
        "agent_logs": [log_entry],
        "retries": 0,
        "plan": {},
        "current_step": 0,
        "next_agent": "",
        "instructions": "",
        "reflection_passed": None,
        "suggested_retry_agent": None
    }

# Routing logic helper for the Supervisor
def supervisor_router(state: AgentState) -> str:
    """Routes execution based on the supervisor's decision."""
    next_node = state.get("next_agent", "memory")
    # Return matching node name
    if next_node in ("research", "retriever", "tool", "memory"):
        return next_node
    return "memory"

# Routing logic helper for Reflection
def reflection_router(state: AgentState) -> str:
    """Routes back to planner/supervisor if reflection fails, else finishes."""
    passed = state.get("reflection_passed", True)
    retries = state.get("retries", 0)
    
    if passed or retries >= 2:
        return END
        
    retry_target = state.get("suggested_retry_agent", "supervisor")
    if retry_target == "planner":
        return "planner"
    return "supervisor"

# Define the StateGraph workflow
workflow = StateGraph(AgentState)

# Register Nodes
workflow.add_node("retrieve_memories", retrieve_memories_node)
workflow.add_node("planner", planner_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("research", research_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("tool", tool_node)
workflow.add_node("memory", memory_node)
workflow.add_node("verification", verification_node)
workflow.add_node("reflection", reflection_node)

# Connect Nodes
workflow.add_edge(START, "retrieve_memories")
workflow.add_edge("retrieve_memories", "planner")
workflow.add_edge("planner", "supervisor")

# Supervisor conditional routing
workflow.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "research": "research",
        "retriever": "retriever",
        "tool": "tool",
        "memory": "memory"
    }
)

# Return loops back to Supervisor
workflow.add_edge("research", "supervisor")
workflow.add_edge("retriever", "supervisor")
workflow.add_edge("tool", "supervisor")

# Post-execution chain
workflow.add_edge("memory", "verification")
workflow.add_edge("verification", "reflection")

# Reflection conditional routing (retry loop or complete)
workflow.add_conditional_edges(
    "reflection",
    reflection_router,
    {
        "planner": "planner",
        "supervisor": "supervisor",
        END: END
    }
)

def compile_graph(checkpointer: Optional[Any] = None) -> Any:
    """Compiles the compiled graph with an optional checkpointer for thread persistence."""
    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
    elif hasattr(checkpointer, "setup"):
        checkpointer.setup()
    
    return workflow.compile(checkpointer=checkpointer)
