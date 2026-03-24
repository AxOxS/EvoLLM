"""Application configuration – reads from .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/evollm"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    chromadb_path: str = "./chroma_data"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_hours: int = 24
    tavily_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
