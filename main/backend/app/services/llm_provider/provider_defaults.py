import os

from pydantic import BaseModel


class OllamaConfig(BaseModel):
    chat_model: str = "qwen3:8b"
    embedding_model: str = "qwen3-embedding:8b"
    base_url: str = "http://localhost:11434"


class VllmConfig(BaseModel):
    chat_model: str = os.getenv("WORKFORGE_VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    base_url: str = os.getenv("WORKFORGE_VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
    api_key: str = os.getenv("WORKFORGE_VLLM_API_KEY", "")
