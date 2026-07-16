# AgentOS

AgentOS is a local multi-agent AI platform built with FastAPI, Streamlit, LangGraph, and Ollama. It combines planning, research, memory, tool use, and verification into a single interactive workspace for building and exploring agent-driven workflows.

## Features

- Multi-agent orchestration using LangGraph
- Chat and streaming API endpoints via FastAPI
- Streamlit-based web interface for interactive use
- Optional long-term memory with PostgreSQL and pgvector
- Tool registry for search, file operations, and agent tasks
- Local LLM support through Ollama

## Project Structure

- backend/ - FastAPI backend API server
- frontend/ - Streamlit frontend UI
- agents/ - Individual agent implementations
- graphs/ - LangGraph workflow orchestration
- config/ - LLM, API, and settings configuration
- tools/ - Tool definitions and registry
- memory/ - Memory persistence helpers
- tests/ - Automated tests

## Prerequisites

Before running the project, make sure you have:

- Python 3.11+ installed
- Ollama installed and running locally
- An Ollama model available, such as qwen2.5-coder:7b
- Optional: Docker Desktop if you want PostgreSQL support via docker-compose

## Installation

1. Clone the repository
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Pull an Ollama model if needed:

```bash
ollama pull qwen2.5-coder:7b
```

4. Optional: start PostgreSQL for persistent memory:

```bash
docker compose up -d postgres
```

## Running the Application

Start the backend:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, start the frontend:

```bash
streamlit run frontend/app.py
```

Then open:

- Backend health check: http://127.0.0.1:8000/health
- Streamlit UI: http://127.0.0.1:8501

## Environment Variables

You can configure the app using a .env file. Common variables include:

- OLLAMA_BASE_URL
- DEFAULT_MODEL
- DATABASE_URL
- AGENTOS_BACKEND_URL
- TAVILY_API_KEY (if using Tavily-based search)

## Notes

- The app will run in a fallback in-memory mode if PostgreSQL is not available.
- Some features such as persistent memory and semantic retrieval work best when PostgreSQL is running.

## License

This project does not currently include a license file. If you plan to publish it publicly on GitHub, add an appropriate license before release.
