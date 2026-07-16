from typing import Optional
from langchain_ollama import ChatOllama
from config.settings import settings

def get_llm(model_name: Optional[str] = None, temperature: float = 0.0) -> ChatOllama:
    """Returns a ChatOllama model instance configured with settings."""
    selected_model = model_name or settings.DEFAULT_MODEL
    
    # We construct the ChatOllama model. If deepseek/llama are passed and running, it'll attempt to run them.
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=selected_model,
        temperature=temperature
    )
