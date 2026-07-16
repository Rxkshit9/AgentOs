import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env variables into environment for os.getenv compatibility
load_dotenv()

class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "qwen2.5-coder:7b"
    
    # DB Settings
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgrespassword@localhost:5432/agentos"
    
    # Active Project Folder
    ACTIVE_PROJECT_DIR: Optional[str] = None
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    APIS_YAML_PATH: Path = BASE_DIR / "config" / "apis.yaml"
    PROMPTS_DIR: Path = BASE_DIR / "prompts"
    
    # API configuration mapping
    apis: Dict[str, Dict[str, Any]] = {}
    
    class Config:
        env_file = ".env"
        extra = "ignore"

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        self.load_api_registry()

    def load_api_registry(self) -> None:
        """Loads APIs from apis.yaml and retrieves keys from active environment variables."""
        if not self.APIS_YAML_PATH.exists():
            return
        
        try:
            with open(self.APIS_YAML_PATH, "r") as f:
                config_data = yaml.safe_load(f) or {}
                
            self.apis = {}
            for api_name, api_conf in config_data.items():
                provider = api_conf.get("provider")
                key_env = api_conf.get("key_env")
                # Get the value from environment variable dynamically
                api_key = os.getenv(key_env) if key_env else None
                
                self.apis[api_name] = {
                    "provider": provider,
                    "key_env": key_env,
                    "api_key": api_key
                }
        except Exception as e:
            # Fallback or logging could be here, keeping it robust
            print(f"Error loading API registry: {e}")

    def get_api_key(self, api_name: str) -> Optional[str]:
        """Convenience method to retrieve the loaded key for an API."""
        return self.apis.get(api_name, {}).get("api_key")

# Instantiate singleton settings
settings = Settings()
