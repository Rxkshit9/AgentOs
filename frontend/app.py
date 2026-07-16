import os
import uuid
import json
import requests
import streamlit as st

# Server URL Configuration
BACKEND_URL = os.getenv("AGENTOS_BACKEND_URL", "http://localhost:8000")

# Page Config
st.set_page_config(
    page_title="AgentOS – Multi-Agent AI Platform",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Sleek CSS Styling (Google Font, Dark Mode, Glassmorphism, Gradients)
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Glassmorphism Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #0e1117 0%, #161b22 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Main Gradient Header */
.main-header {
    background: linear-gradient(90deg, #537895 0%, #09203f 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 5px;
}

.subheader {
    color: #8b9bb4;
    font-size: 1.1rem;
    margin-bottom: 25px;
}

/* Card Styling */
.metric-card {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 10px;
}

/* Trace Logs Styling */
.trace-log {
    border-left: 3px solid #38bdf8;
    background-color: rgba(56, 189, 248, 0.03);
    padding: 10px 15px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
}

.trace-agent {
    font-weight: 600;
    color: #38bdf8;
    font-size: 0.9rem;
    text-transform: uppercase;
}

.trace-action {
    color: #e2e8f0;
    font-size: 0.95rem;
    margin: 3px 0;
}

.trace-output {
    color: #94a3b8;
    font-size: 0.85rem;
    white-space: pre-wrap;
    background: rgba(0,0,0,0.2);
    padding: 6px;
    border-radius: 4px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Session state initialization for chat and configurations
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_traces" not in st.session_state:
    st.session_state.agent_traces = []

# Fetch active configurations and model lists
@st.cache_data(ttl=10)
def fetch_system_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return r.json()
    except Exception:
        return {"status": "unhealthy", "database": "disconnected"}

@st.cache_data(ttl=60)
def fetch_models():
    try:
        r = requests.get(f"{BACKEND_URL}/models", timeout=3)
        return r.json()
    except Exception:
        return {"default": "qwen2.5-coder:7b", "available": ["qwen2.5-coder:7b"]}

@st.cache_data(ttl=30)
def fetch_tools():
    try:
        r = requests.get(f"{BACKEND_URL}/tools", timeout=3)
        return r.json().get("tools", [])
    except Exception:
        return []

@st.cache_data(ttl=10)
def fetch_memories():
    try:
        r = requests.get(f"{BACKEND_URL}/memory", timeout=3)
        return r.json().get("memories", [])
    except Exception:
        return []

system_health = fetch_system_health()
models_info = fetch_models()

# SIDEBAR CONTROLS
st.sidebar.markdown("<h2 style='text-align: center; color: #fff;'>🌌 AgentOS Dashboard</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Health indicator
db_status = system_health.get("database", "disconnected")
db_color = "green" if "connected" in db_status.lower() else "red"
st.sidebar.markdown(f"**Database:** <span style='color:{db_color};'>{db_status}</span>", unsafe_allow_html=True)

# Active Conversations (Resume chat)
st.sidebar.markdown("### 💬 Active Conversations")
try:
    threads_res = requests.get(f"{BACKEND_URL}/threads", timeout=2)
    thread_list = threads_res.json().get("threads", [])
except Exception:
    thread_list = []
    
if st.session_state.thread_id not in thread_list:
    thread_list.append(st.session_state.thread_id)

try:
    thread_index = thread_list.index(st.session_state.thread_id)
except ValueError:
    thread_index = 0

selected_thread = st.sidebar.selectbox(
    "Select/Resume Chat History",
    options=thread_list,
    index=thread_index
)

if selected_thread != st.session_state.thread_id:
    st.session_state.thread_id = selected_thread
    try:
        history_res = requests.get(f"{BACKEND_URL}/threads/{selected_thread}/messages", timeout=3)
        st.session_state.chat_history = history_res.json().get("messages", [])
    except Exception:
        st.session_state.chat_history = []
    st.session_state.agent_traces = []
    st.rerun()

if st.sidebar.button("New Session / Reset Thread"):
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.agent_traces = []
    st.rerun()

st.sidebar.markdown("---")

# LLM Selection
selected_model = st.sidebar.selectbox(
    "Active LLM Model",
    options=models_info.get("available", ["qwen2.5-coder:7b"]),
    index=0
)

# Start an Agent Workspace Mode
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Agent Workspace Mode")
agent_mode = st.sidebar.checkbox("Activate Project Builder Agent", value=False)
project_folder = None
if agent_mode:
    project_folder = st.sidebar.text_input(
        "Local Project Folder Path", 
        value=os.path.join(os.path.expanduser("~"), "my-agentos-project"),
        help="The agent will create directory structures and write code files in this folder."
    )

selected_tab = "Workspace Chat"

# MAIN CONTAINER
if selected_tab == "Workspace Chat":
    st.markdown("<h1 class='main-header'>AgentOS Multi-Agent Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subheader'>Orchestrated via LangGraph. Powered by Ollama.</p>", unsafe_allow_html=True)
    
    col_chat, col_traces = st.columns([1.4, 1.0])
    
    # Left side: Chat UI
    with col_chat:
        st.subheader("Interactive Session")
        
        # File uploader for convenient document ingestion without copy-pasting paths
        with st.expander("📁 Upload Document for RAG Ingestion"):
            uploaded_file = st.file_uploader("Upload a text or markdown document to save into local semantic memory", type=["txt", "md"])
            if uploaded_file is not None:
                os.makedirs("temp_uploads", exist_ok=True)
                temp_path = os.path.join("temp_uploads", uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if st.button("Index and Ingest Document"):
                    with st.spinner("Processing embeddings and indexing..."):
                        payload = {
                            "message": f"Index the file {os.path.abspath(temp_path)}",
                            "thread_id": st.session_state.thread_id,
                            "model_name": selected_model,
                            "project_dir": project_folder if agent_mode else None
                        }
                        try:
                            r = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
                            if r.status_code == 200:
                                res_json = r.json()
                                reply = res_json.get("response", "File uploaded and indexed successfully!")
                                st.success(reply)
                            else:
                                st.error(f"Error from server: {r.text}")
                        except Exception as e:
                            st.error(f"Failed to connect to backend: {e}")
                            
        # Display existing messages
        for msg in st.session_state.chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.markdown(msg["content"])
                
        # Handle new user input
        if prompt := st.chat_input("Enter your request here..."):
            # Add to state and display immediately
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            # Stream response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                response_placeholder.markdown("*Invoking AgentOS Planner...*")
                
                # Clear trace lists for the new request execution
                st.session_state.agent_traces = []
                
                payload = {
                    "message": prompt,
                    "thread_id": st.session_state.thread_id,
                    "model_name": selected_model,
                    "project_dir": project_folder if agent_mode else None
                }
                
                try:
                    response = requests.post(f"{BACKEND_URL}/stream", json=payload, stream=True)
                    final_reply = ""
                    confidence = 100
                    plan = {}
                    
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data: "):
                                data = json.loads(decoded[6:])
                                
                                # Trace status updates
                                if data["type"] == "log":
                                    new_logs = data.get("logs", [])
                                    st.session_state.agent_traces.extend(new_logs)
                                    # Trigger instant re-render of trace col
                                    with col_traces:
                                        st.empty() # Simple trigger
                                        
                                # Final synthesis tokens
                                elif data["type"] == "final":
                                    final_reply = data.get("response", "")
                                    confidence = data.get("confidence_score", 100)
                                    plan = data.get("plan", {})
                                    response_placeholder.markdown(final_reply)
                                    
                                # Errors
                                elif data["type"] == "error":
                                    st.error(f"Execution Error: {data.get('detail')}")
                                    
                    if final_reply:
                        st.session_state.chat_history.append({"role": "assistant", "content": final_reply})
                        
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
                    
    # Right side: Live Agent Traces
    with col_traces:
        st.subheader("Agent Execution Steps")
        if not st.session_state.agent_traces:
            st.info("Agent execution steps will appear here in real time.")
        else:
            for log in st.session_state.agent_traces:
                agent = log.get("agent", "unknown").upper()
                action = log.get("action", "")
                output = log.get("output", "")
                
                # Dynamic coloring for agents
                agent_colors = {
                    "PLANNER": "#a855f7",
                    "SUPERVISOR": "#eab308",
                    "RESEARCH": "#3b82f6",
                    "RETRIEVER": "#10b981",
                    "TOOL": "#ec4899",
                    "MEMORY": "#f97316",
                    "VERIFICATION": "#6366f1",
                    "REFLECTION": "#ef4444"
                }
                color = agent_colors.get(agent, "#38bdf8")
                
                html_block = f"""
                <div class="trace-log" style="border-left-color: {color};">
                    <span class="trace-agent" style="color: {color};">{agent}</span>
                    <div class="trace-action">{action}</div>
                    <div class="trace-output">{output}</div>
                </div>
                """
                st.markdown(html_block, unsafe_allow_html=True)
