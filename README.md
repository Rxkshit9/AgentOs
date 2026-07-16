# AgentOS

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0-lightgrey)](https://github.com/langgraph)
[![LangChain](https://img.shields.io/badge/LangChain-0.2.0-lightgrey)](https://github.com/langchain-ai)
[![Docker Compose](https://img.shields.io/badge/Docker--Compose-%20-blue)](https://docs.docker.com/compose/)
[![Memory: Postgres+pgvector](https://img.shields.io/badge/Memory-Postgres%2Fpgvector-lightgrey)](https://github.com/pgvector/pgvector)

AgentOS is a local multi-agent AI platform built with FastAPI, Streamlit, LangGraph, and Ollama. It combines planning, research, memory, tool use, and verification into a single interactive workspace for building and exploring agent-driven workflows.

## Overview

This project is designed to run a multi-agent system locally with:

- a FastAPI backend for chat and streaming endpoints
- a Streamlit frontend for interactive use
- LangGraph-based orchestration for planner, research, tool, and verification agents
- optional PostgreSQL + pgvector support for persistent memory
- local model execution through Ollama

## Features

- Multi-agent orchestration using LangGraph
- Chat and streaming API endpoints via FastAPI
- Streamlit web UI for conversations and workspace tasks
- Optional long-term memory with PostgreSQL and pgvector
- Tool registry for search, file operations, and agent tasks
- Local LLM support through Ollama

## Dependencies

Key runtime dependencies used by this project:

- `langgraph` (graph-based multi-agent orchestration)
- `langchain` (LLM tooling and agents)
- `langchain-ollama` (Ollama integrations)
- `psycopg[binary]`, `pgvector` (Postgres + vector store for memory)
- `fastapi`, `uvicorn`, `streamlit`
- `docker` / `docker-compose` (optional; used to bring up Postgres with pgvector)

These packages are listed in `requirements.txt` and may be installed via:

```bash
pip install -r requirements.txt
```

Notes:
- If you plan to use persistent memory, run the provided `docker-compose.yml` to start Postgres with pgvector.
- Ollama is used for local model hosting; ensure your desired model is available locally.

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

Before running the project, ensure you have:

- Python 3.11+ installed
- Ollama installed and running locally
- An Ollama model available, such as qwen2.5-coder:7b
- Optional: Docker Desktop if you want PostgreSQL support via docker-compose

## Quick Start

1. Clone the repository
2. Install dependencies:

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

5. Start the backend:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

6. In a second terminal, start the frontend:

```bash
streamlit run frontend/app.py
```

7. Open the app:

- Backend health check: http://127.0.0.1:8000/health
- Streamlit UI: http://127.0.0.1:8501

## Environment Variables

You can configure the app using a .env file. Common variables include:

- OLLAMA_BASE_URL
- DEFAULT_MODEL
- DATABASE_URL
- AGENTOS_BACKEND_URL
- TAVILY_API_KEY (if using Tavily-based search)

## Demo / Screenshots

A typical workflow looks like this:

1. Open the Streamlit UI at http://127.0.0.1:8501
2. Enter a prompt such as "Build a FastAPI service for user authentication"
3. The request is routed through the LangGraph workflow
4. The planner, research, tool, and verification agents collaborate to produce a structured response
5. The app can also ingest uploaded documents for RAG-style memory support

### Example User Flow

- Launch the frontend and backend locally
- Enter a task in the chat interface
- Review the agent traces and final reply
- Use workspace mode to create or modify project files

### Screenshot Placeholder

You can add images to this repository under the assets/ folder and link them here later.

## Architecture

```text
User
  -> Streamlit UI
  -> FastAPI Backend
  -> LangGraph Orchestrator
       -> Planner Agent
       -> Research Agent
       -> Retriever / Tool Agent
       -> Verification Agent
       -> Memory Layer (Postgres or in-memory fallback)
       -> Ollama LLM
```

This architecture allows the system to break a request into steps, gather relevant context, use tools when needed, and validate the output before returning it to the user.

## How It Works

The system uses a graph-based workflow where each agent is responsible for a different stage of the task:

- Planner: creates a plan or structure for the request
- Research: gathers context or external information
- Retriever/Tool: uses available tools or knowledge sources
- Verification: checks consistency and quality
- Memory: stores or retrieves information across sessions

### Sample Prompts

- "Explain how this project is structured"
- "Create a Python script that reads a CSV file and summarizes it"
- "Build a simple FastAPI endpoint with authentication"
- "Index this uploaded document and summarize its contents"

## Notes

- The app runs in a fallback in-memory mode if PostgreSQL is not available.
- Persistent memory and semantic retrieval work best when PostgreSQL is running.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## GitHub Setup

To publish this repository on GitHub, run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```
