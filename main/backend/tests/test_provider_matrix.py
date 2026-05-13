from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import settings


def _register_and_login(client: TestClient):
    client.post("/v1/auth/register", json={"username": "provider", "password": "123456"})
    login = client.post("/v1/auth/login", json={"account": "provider", "password": "123456"})
    assert login.status_code == 200
    data = login.json()["data"]
    return data["user_id"], data["token"]


def test_provider_matrix_upsert_and_test_connection():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            user_id, token = _register_and_login(client)
            auth = {"Authorization": f"Bearer {token}"}

            provider_payloads = [
                {
                    "provider_type": "deepseek_api",
                    "display_name": "DeepSeek",
                    "base_url": "https://api.deepseek.com",
                    "model_name": "deepseek-chat",
                    "api_key": "sk-deepseek",
                    "is_default": False,
                },
                {
                    "provider_type": "openai_api",
                    "display_name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model_name": "gpt-4.1-mini",
                    "api_key": "sk-openai",
                    "is_default": False,
                },
                {
                    "provider_type": "anthropic_api",
                    "display_name": "Anthropic",
                    "base_url": "https://api.anthropic.com/v1",
                    "model_name": "claude-3-7-sonnet-latest",
                    "api_key": "sk-anthropic",
                    "is_default": False,
                },
                {
                    "provider_type": "qwen_api",
                    "display_name": "Qwen",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model_name": "qwen-plus",
                    "api_key": "sk-qwen",
                    "is_default": False,
                },
                {
                    "provider_type": "ollama",
                    "display_name": "Ollama",
                    "base_url": "http://localhost:11434",
                    "chat_model": "qwen3:8b",
                    "embedding_model": "qwen3-embedding:8b",
                    "is_default": True,
                },
                {
                    "provider_type": "huggingface",
                    "display_name": "HuggingFace",
                    "base_url": "http://127.0.0.1:8000/v1",
                    "model_name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                    "is_default": False,
                },
                {
                    "provider_type": "local_llm",
                    "display_name": "Local LLM",
                    "base_url": "http://127.0.0.1:8001/v1",
                    "model_name": "local-model",
                    "is_default": False,
                },
            ]

            for payload in provider_payloads:
                req = {"user_id": user_id, **payload}
                resp = client.post("/v1/providers", json=req, headers=auth)
                assert resp.status_code == 200

            listed = client.get(f"/v1/providers/{user_id}", headers=auth)
            assert listed.status_code == 200
            assert len(listed.json()["data"]["items"]) == len(provider_payloads)

            default_me = client.get("/v1/providers/default/me", headers=auth)
            assert default_me.status_code == 200
            assert default_me.json()["data"]["item"]["provider_type"] == "ollama"

            test_payloads = [
                {"provider_type": "deepseek_api", "base_url": "https://api.deepseek.com", "model_name": "deepseek-chat"},
                {"provider_type": "openai_api", "base_url": "https://api.openai.com/v1", "model_name": "gpt-4.1-mini"},
                {"provider_type": "anthropic_api", "base_url": "https://api.anthropic.com/v1", "model_name": "claude-3-7-sonnet-latest"},
                {"provider_type": "qwen_api", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen-plus"},
                {"provider_type": "ollama", "base_url": "http://localhost:11434", "chat_model": "qwen3:8b"},
                {"provider_type": "huggingface", "base_url": "http://127.0.0.1:8000/v1", "model_name": "meta-llama/Meta-Llama-3.1-8B-Instruct"},
                {"provider_type": "local_llm", "base_url": "http://127.0.0.1:8001/v1", "model_name": "local-model"},
            ]
            for payload in test_payloads:
                resp = client.post("/v1/providers/test", json=payload, headers=auth)
                assert resp.status_code == 200
                status = resp.json()["data"]["status"]
                if payload["provider_type"] == "ollama":
                    assert status in {"ok", "error"}
                else:
                    assert status == "ok"


def test_provider_endpoints_enforce_user_scope():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            user1, token1 = _register_and_login(client)
            client.post("/v1/auth/register", json={"username": "provider2", "password": "123456"})
            login2 = client.post("/v1/auth/login", json={"account": "provider2", "password": "123456"})
            user2 = login2.json()["data"]["user_id"]

            auth1 = {"Authorization": f"Bearer {token1}"}

            wrong_upsert = client.post(
                "/v1/providers",
                json={
                    "user_id": user2,
                    "provider_type": "vllm",
                    "display_name": "Bad Scope",
                    "base_url": "http://127.0.0.1:8000/v1",
                    "model_name": "Qwen/Qwen2.5-7B-Instruct",
                    "is_default": True,
                },
                headers=auth1,
            )
            assert wrong_upsert.status_code == 400

            wrong_list = client.get(f"/v1/providers/{user2}", headers=auth1)
            assert wrong_list.status_code == 400

            unauthorized = client.get("/v1/providers/default/me")
            assert unauthorized.status_code == 401
