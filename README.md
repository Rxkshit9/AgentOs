# AgentOS

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

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
