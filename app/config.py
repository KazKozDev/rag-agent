from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM / embeddings
    openai_api_key: str = Field(default="")
    llm_model: str = "gpt-5-mini"
    embedding_model: str = "text-embedding-3-small"

    # Storage paths
    data_dir: str = "./data"
    docs_dir: str = "./data/docs"
    chroma_path: str = "./data/chroma"
    bm25_path: str = "./data/bm25"
    feedback_db_path: str = "./data/feedback.db"

    # Retrieval
    top_k: int = 5
    rrf_k: int = 60

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_url: str = "http://api:8000"

    def ensure_dirs(self) -> None:
        for p in (self.data_dir, self.docs_dir, self.chroma_path, self.bm25_path):
            os.makedirs(p, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
