import hashlib
import numpy as np
from typing import List
from langchain_core.embeddings import Embeddings
from config.settings import settings

# Database connection URL
DATABASE_URL = settings.DATABASE_URL

# Vector embeddings configuration
EMBEDDING_DIM = 1536  # Default dimension for our deterministic embeddings

class DeterministicEmbeddings(Embeddings):
    """A deterministic, client-side embedding generator.
    
    Generates a unit-length vector of fixed dimensions from a text's SHA-256 hash.
    Enables vector similarity search (pgvector) without server support.
    """
    def __init__(self, dimension: int = EMBEDDING_DIM):
        self.dimension = dimension

    def _embed(self, text: str) -> List[float]:
        # Generate deterministic vector using SHA-256 seed
        hasher = hashlib.sha256(text.encode("utf-8"))
        seed = int(hasher.hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        vec = rng.normal(size=self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

def get_embeddings():
    """Attempts to load OllamaEmbeddings, falling back to DeterministicEmbeddings on error."""
    try:
        from langchain_ollama import OllamaEmbeddings
        embeddings = OllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.DEFAULT_MODEL
        )
        # Test if it actually works
        embeddings.embed_query("test")
        return embeddings
    except Exception as e:
        # Fallback to local deterministic generator
        print(f"Ollama embeddings not available ({e}). Using client-side DeterministicEmbeddings.")
        return DeterministicEmbeddings()
