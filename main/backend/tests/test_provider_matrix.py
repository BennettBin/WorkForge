from pathlib import Path
from tempfile import TemporaryDirectory
from urllib import error
from urllib import request

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import settings
from app.services.llm_provider.provider_service import ProviderService


def _register_and_login(client: TestClient):
    client.post("/v1/auth/register", json={"username": "provider", "password": "123456"})
    login = client.post("/v1/auth/login", json={"account": "provider", "password": "123456"})
    assert login.status_code == 200
    data = login.json()["data"]
    return data["user_id"], data["token"]


def test_provider_matrix_upsert_and_test_connection():
    auth_checked_urls = []

    class _FakeResponse:
        def __init__(self, body: str):
            self._body = body.encode("utf-8")

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(req, timeout=8):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        headers = {k.lower(): v for k, v in req.header_items()} if hasattr(req, "header_items") else {}
        auth_header = headers.get("authorization")
        api_key_header = headers.get("x-api-key")
        if url.endswith("/api/tags"):
            return _FakeResponse('{"models":[{"name":"qwen3:8b"}]}')
        if url.endswith("/messages"):
            assert api_key_header == "sk-anthropic"
            auth_checked_urls.append(url)
            return _FakeResponse('{"content":[{"type":"text","text":"ok"}]}')
        if url.endswith("/models"):
            if "api.deepseek.com" in url or "api.openai.com" in url or "dashscope.aliyuncs.com" in url:
                assert auth_header and auth_header.startswith("Bearer sk-")
                auth_checked_urls.append(url)
            return _FakeResponse('{"data":[{"id":"deepseek-v4-flash"},{"id":"deepseek-v4-pro"},{"id":"gpt-4.1-mini"},{"id":"qwen-plus"},{"id":"meta-llama/Meta-Llama-3.1-8B-Instruct"},{"id":"local-model"}]}')
        return _FakeResponse("{}")

    original_urlopen = request.urlopen
    request.urlopen = _fake_urlopen
    with TemporaryDirectory() as temp_dir:
        try:
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
                    "model_name": "deepseek-v4-flash",
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
                    {
                        "provider_type": "deepseek_api",
                        "base_url": "https://api.deepseek.com",
                        "model_name": "deepseek-v4-flash",
                        "api_key": "sk-deepseek",
                    },
                    {
                        "provider_type": "openai_api",
                        "base_url": "https://api.openai.com/v1",
                        "model_name": "gpt-4.1-mini",
                        "api_key": "sk-openai",
                    },
                    {
                        "provider_type": "anthropic_api",
                        "base_url": "https://api.anthropic.com/v1",
                        "model_name": "claude-3-7-sonnet-latest",
                        "api_key": "sk-anthropic",
                    },
                    {
                        "provider_type": "qwen_api",
                        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                        "model_name": "qwen-plus",
                        "api_key": "sk-qwen",
                    },
                    {"provider_type": "ollama", "base_url": "http://localhost:11434", "chat_model": "qwen3:8b"},
                    {"provider_type": "huggingface", "base_url": "http://127.0.0.1:8000/v1", "model_name": "meta-llama/Meta-Llama-3.1-8B-Instruct"},
                    {"provider_type": "local_llm", "base_url": "http://127.0.0.1:8001/v1", "model_name": "local-model"},
                ]
                for payload in test_payloads:
                    resp = client.post("/v1/providers/test", json=payload, headers=auth)
                    assert resp.status_code == 200
                    data = resp.json()["data"]
                    assert data["status"] == "ok"
                    assert data["reachable"] is True
                    assert data["model_found"] is True
                assert any("api.deepseek.com" in url for url in auth_checked_urls)
                assert any("api.openai.com" in url for url in auth_checked_urls)
                assert any("dashscope.aliyuncs.com" in url for url in auth_checked_urls)
                assert any("api.anthropic.com" in url for url in auth_checked_urls)
        finally:
            request.urlopen = original_urlopen


def test_deepseek_legacy_alias_matches_current_model_ids():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            _, token = _register_and_login(client)
            auth = {"Authorization": f"Bearer {token}"}
            service = ProviderService(app.state.repositories)
            assert service._model_matches(
                "deepseek-chat",
                ["deepseek-v4-flash", "deepseek-v4-pro"],
                provider_type="deepseek_api",
            )

            resp = client.post(
                "/v1/providers/test",
                json={"provider_type": "deepseek_api", "base_url": "https://api.deepseek.com", "model_name": "deepseek-chat"},
                headers=auth,
            )
            assert resp.status_code == 400


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


def test_provider_test_returns_connection_refused_error_code_for_vllm():
    def _fail_urlopen(req, timeout=8):
        raise error.URLError(ConnectionRefusedError(10061, "No connection could be made because the target machine actively refused it"))

    original_urlopen = request.urlopen
    request.urlopen = _fail_urlopen
    with TemporaryDirectory() as temp_dir:
        try:
            settings.data_dir = Path(temp_dir)
            app = create_app()
            with TestClient(app) as client:
                _, token = _register_and_login(client)
                auth = {"Authorization": f"Bearer {token}"}
                resp = client.post(
                    "/v1/providers/test",
                    json={"provider_type": "vllm", "base_url": "http://127.0.0.1:8000/v1", "model_name": "qwen3.5-9b"},
                    headers=auth,
                )
                assert resp.status_code == 200
                data = resp.json()["data"]
                assert data["status"] == "error"
                assert data["reachable"] is False
                assert data["error_code"] == "CONNECTION_REFUSED"
        finally:
            request.urlopen = original_urlopen


def test_provider_upsert_keeps_existing_api_key_when_blank_and_hides_secret_in_response():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            user_id, token = _register_and_login(client)
            auth = {"Authorization": f"Bearer {token}"}

            create_resp = client.post(
                "/v1/providers",
                json={
                    "user_id": user_id,
                    "provider_type": "deepseek_api",
                    "display_name": "DeepSeek",
                    "base_url": "https://api.deepseek.com",
                    "model_name": "deepseek-v4-flash",
                    "api_key": "sk-initial",
                    "is_default": True,
                },
                headers=auth,
            )
            assert create_resp.status_code == 200
            created = create_resp.json()["data"]
            provider_id = created["provider_id"]
            assert created.get("has_api_key") is True
            assert "api_key_encrypted" not in created

            update_resp = client.post(
                "/v1/providers",
                json={
                    "provider_id": provider_id,
                    "user_id": user_id,
                    "provider_type": "deepseek_api",
                    "display_name": "DeepSeek Updated",
                    "base_url": "https://api.deepseek.com",
                    "model_name": "deepseek-v4-flash",
                    "api_key": "",
                    "is_default": True,
                },
                headers=auth,
            )
            assert update_resp.status_code == 200
            updated = update_resp.json()["data"]
            assert updated.get("has_api_key") is True
            assert "api_key_encrypted" not in updated

            cfg = app.state.repositories.providers.get_by_id(provider_id)
            assert cfg is not None
            assert cfg.api_key_encrypted == "sk-initial"
