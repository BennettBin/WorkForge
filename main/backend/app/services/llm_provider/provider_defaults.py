from pydantic import BaseModel


class OllamaConfig(BaseModel):
    chat_model: str = "qwen3:8b"
    embedding_model: str = "qwen3-embedding:8b"
    base_url: str = "http://localhost:11434"
