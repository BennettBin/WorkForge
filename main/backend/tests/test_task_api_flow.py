from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from pptx import Presentation

from app.api.app import create_app
from app.config import settings
from app.models.entities import LLMProviderConfig


def test_task_api_create_upload_parse_run_flow():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "Create 10-page slides from source file",
                    "pages": 10,
                    "style": "academic_simple",
                    "language": "zh-CN",
                },
            )
            assert create.status_code == 200
            task_id = create.json()["data"]["task_id"]

            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.txt", BytesIO(b"hello workforge"), "text/plain")},
            )
            assert upload.status_code == 200
            assert upload.json()["data"]["file_type"] == "txt"

            parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
            assert parse.status_code == 200
            assert parse.json()["data"]["parse_status"] == "success"
            vector_index_path = Path(temp_dir) / "vectors" / task_id / "index.json"
            assert vector_index_path.exists()
            payload = json.loads(vector_index_path.read_text(encoding="utf-8"))
            assert payload["chunk_count"] > 0

            run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False})
            assert run.status_code == 200
            assert run.json()["data"]["status"] == "completed"
            pptx_path = Path(run.json()["data"]["output_path"])
            assert pptx_path.exists()
            prs = Presentation(str(pptx_path))
            assert len(prs.slides) == 10

            get_task = client.get(f"/v1/tasks/{task_id}")
            assert get_task.status_code == 200
            assert get_task.json()["data"]["task"]["status"] == "completed"

            download = client.get(f"/v1/tasks/{task_id}/download/latest")
            assert download.status_code == 200
            assert download.json()["data"]["exists"] is True


def test_task_api_reject_empty_upload():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "Create slides",
                    "pages": 10,
                    "style": "academic_simple",
                    "language": "zh-CN",
                },
            )
            task_id = create.json()["data"]["task_id"]

            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("empty.txt", BytesIO(b""), "text/plain")},
            )
            assert upload.status_code == 400
            assert upload.json()["error"]["code"] == "BAD_REQUEST"


def test_task_api_triggers_knowledge_search_skill_when_requested():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "请搜索最新研究并补充到PPT",
                    "pages": 8,
                    "style": "academic_simple",
                    "language": "zh-CN",
                },
            )
            assert create.status_code == 200
            task_id = create.json()["data"]["task_id"]

            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.txt", BytesIO(b"oncology biomarker research baseline"), "text/plain")},
            )
            assert upload.status_code == 200

            parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
            assert parse.status_code == 200

            with patch(
                "app.services.skill_runtime.executor.SkillExecutor.execute",
                return_value={"items": [{"title": "t", "url": "https://example.com/a", "snippet": "s", "content": "external web content for vector cache"}]},
            ):
                run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False})
                assert run.status_code == 200

            detail = client.get(f"/v1/tasks/{task_id}")
            assert detail.status_code == 200
            skill_calls = detail.json()["data"]["skill_calls"]
            assert any(call["skill_name"] == "knowledge_search" for call in skill_calls)
            vector_index_path = Path(temp_dir) / "vectors" / task_id / "index.json"
            payload = json.loads(vector_index_path.read_text(encoding="utf-8"))
            assert payload["chunk_count"] > 0
            assert any(str(chunk.get("source", "")).startswith("https://example.com") for chunk in payload.get("chunks", []))


def test_task_api_can_clear_vector_cache_manually():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "Create slides",
                    "pages": 8,
                    "style": "academic_simple",
                    "language": "zh-CN",
                },
            )
            task_id = create.json()["data"]["task_id"]

            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.txt", BytesIO(b"cache clear test input"), "text/plain")},
            )
            assert upload.status_code == 200
            parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
            assert parse.status_code == 200

            vector_index_path = Path(temp_dir) / "vectors" / task_id / "index.json"
            assert vector_index_path.exists()

            clear = client.post(f"/v1/tasks/{task_id}/cache/clear", json={})
            assert clear.status_code == 200
            assert clear.json()["data"]["removed"] is True
            assert not vector_index_path.exists()


def test_task_api_no_source_file_can_still_generate_by_search():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "Create PPT about AI trends without source file",
                    "pages": 8,
                    "style": "academic_simple",
                    "language": "en-US",
                },
            )
            assert create.status_code == 200
            task_id = create.json()["data"]["task_id"]

            with patch(
                "app.services.skill_runtime.executor.SkillExecutor.execute",
                return_value={"items": [{"title": "AI trend", "url": "https://example.com/trend", "snippet": "trend snippet", "content": "trend content"}]},
            ):
                run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False})
                assert run.status_code == 200
                assert run.json()["data"]["status"] == "completed"
                pptx_path = Path(run.json()["data"]["output_path"])
                assert pptx_path.exists()

            detail = client.get(f"/v1/tasks/{task_id}")
            assert detail.status_code == 200
            events = detail.json()["data"]["events"]
            assert any("no_source_file_detected" in e["message"] for e in events)


def test_task_api_exports_image_placeholder_metadata():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "Make a research presentation with figure slots",
                    "pages": 8,
                    "style": "academic_simple",
                    "language": "en-US",
                },
            )
            task_id = create.json()["data"]["task_id"]
            file_bytes = (
                b"Figure 1: pipeline architecture from source_file\n"
                b"Methods and results\n"
                b"Figure 2: ablation chart from source_file\n"
            )
            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.txt", BytesIO(file_bytes), "text/plain")},
            )
            assert upload.status_code == 200
            parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
            assert parse.status_code == 200

            run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False})
            assert run.status_code == 200
            slides_path = Path(run.json()["data"]["slides_path"])
            slides = json.loads(slides_path.read_text(encoding="utf-8"))
            assert any(len(s.get("image_placeholders", [])) > 0 for s in slides if s.get("kind") == "content")


def test_task_parse_uses_ollama_embedding_config_when_default_provider_is_ollama():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            # seed default provider for same user
            app.state.repositories.providers.upsert(
                LLMProviderConfig(
                    provider_id="p-ollama",
                    user_id="u-1",
                    provider_type="ollama",
                    display_name="Ollama",
                    base_url="http://localhost:11434",
                    model_name="qwen3:8b",
                    embedding_model="qwen3-embedding:8b",
                    is_default=True,
                )
            )

            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "embedding config test",
                    "pages": 8,
                    "style": "academic_simple",
                    "language": "en-US",
                },
            )
            assert create.status_code == 200
            task_id = create.json()["data"]["task_id"]
            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.txt", BytesIO(b"embedding test content"), "text/plain")},
            )
            assert upload.status_code == 200

            with patch(
                "app.services.vector_store.index_service.VectorIndexService._vectorize_ollama",
                return_value={"0": 1.0},
            ) as mocked:
                parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
                assert parse.status_code == 200
                assert mocked.called

            vector_index_path = Path(temp_dir) / "vectors" / task_id / "index.json"
            payload = json.loads(vector_index_path.read_text(encoding="utf-8"))
            assert payload.get("vectorizer", {}).get("type") == "ollama"
            assert payload.get("vectorizer", {}).get("model") == "qwen3-embedding:8b"


def test_task_api_llm_failure_falls_back_when_not_required():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "Create slides with llm",
                    "pages": 8,
                    "style": "academic_simple",
                    "language": "en-US",
                },
            )
            task_id = create.json()["data"]["task_id"]
            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.txt", BytesIO(b"llm fallback source"), "text/plain")},
            )
            assert upload.status_code == 200
            parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
            assert parse.status_code == 200

            with patch(
                "app.services.llm_runtime.text_generator.LLMTextGenerator.generate",
                side_effect=RuntimeError("forced llm failure for test"),
            ):
                run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False, "require_llm": False})
                assert run.status_code == 200
                assert run.json()["data"]["status"] == "completed"
                llm_debug = run.json()["data"]["llm_debug"]
                assert llm_debug["attempted"] is True
                assert llm_debug["succeeded"] is False
                assert llm_debug["failed_reason"] is not None


def test_task_api_llm_failure_blocks_when_required():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "user_requirement": "Create slides with llm required",
                    "pages": 8,
                    "style": "academic_simple",
                    "language": "en-US",
                },
            )
            task_id = create.json()["data"]["task_id"]
            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.txt", BytesIO(b"llm required source"), "text/plain")},
            )
            assert upload.status_code == 200
            parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
            assert parse.status_code == 200

            with patch(
                "app.services.llm_runtime.text_generator.LLMTextGenerator.generate",
                side_effect=RuntimeError("forced llm failure for test"),
            ):
                run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False, "require_llm": True})
                assert run.status_code == 400
                body = run.json()
                assert body["error"]["code"] == "BAD_REQUEST"
                assert "LLM required" in body["error"]["message"]
