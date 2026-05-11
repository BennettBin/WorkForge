from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from openpyxl import Workbook
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


def test_task_api_extended_task_types_generate_markdown_outputs():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            for task_type in ["report", "wechat_post", "data_analysis", "code_doc", "paper_assistant"]:
                create = client.post(
                    "/v1/tasks",
                    json={
                        "user_id": "u-1",
                        "task_type": task_type,
                        "user_requirement": f"Generate {task_type} content",
                        "pages": 8,
                        "style": "academic_simple",
                        "language": "en-US",
                    },
                )
                assert create.status_code == 200
                task_id = create.json()["data"]["task_id"]

                with patch(
                    "app.services.llm_runtime.text_generator.LLMTextGenerator.generate",
                    return_value=(
                            (
                            "# report\n\n## Summary\nGenerated by llm with detailed context and expanded explanation for reviewers.\n\n## Findings\nPoint A with evidence.\nPoint B with trend.\n\n## Recommendations\nPoint C with action plan.\n"
                            if task_type == "report"
                            else "# wechat_post\n\n## Summary\nGenerated by llm with clear narrative and audience-oriented language.\n\n## Findings\nPoint A for readers.\nPoint B for context.\n\n## Recommendations\nPoint C as next step.\n"
                            if task_type == "wechat_post"
                            else "# data_analysis\n\n## Cleaning\nStep A normalization.\nStep B missing-value strategy.\n\n## Findings\nPoint B distribution.\nPoint C correlation.\n\n## Recommendations\nPoint D chart plan.\n"
                            if task_type == "data_analysis"
                            else "# code_doc\n\n## Quick Start\nStep A install dependencies.\nStep B run service.\n\n## API\nEndpoint B request schema.\nEndpoint C response example.\n\n## Recommendations\nPoint D maintenance.\n"
                            if task_type == "code_doc"
                            else "# paper_assistant\n\n## Abstract\nDraft A with motivation and method overview.\n\n## Revision\nSuggestion B for clarity.\nSuggestion C for evidence linkage.\n\n## Findings\nPoint D contribution scope.\n"
                        )
                    ),
                ), patch(
                    "app.services.knowledge_search.search_service.KnowledgeSearchService.search_and_extract",
                    return_value=[{"title": "t", "url": "https://example.com", "snippet": "s", "content": "c"}],
                ):
                    run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False})
                    assert run.status_code == 200
                    assert run.json()["data"]["status"] == "completed"
                    assert run.json()["data"]["task_type"] == task_type
                    output_path = Path(run.json()["data"]["output_path"])
                    assert output_path.exists()
                    assert output_path.suffix == ".md"
                detail = client.get(f"/v1/tasks/{task_id}")
                assert detail.status_code == 200
                skill_names = [row["skill_name"] for row in detail.json()["data"]["skill_calls"]]
                assert "skill_registry_resolve" in skill_names
                assert any(name in skill_names for name in {
                    "report_planner",
                    "wechat_post_planner",
                    "data_analysis_planner",
                    "code_doc_planner",
                    "paper_assistant_planner",
                })


def test_non_ppt_revision_uses_markdown_pipeline_instead_of_slide_json():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "task_type": "wechat_post",
                    "user_requirement": "Write a WeChat post about AI agents",
                    "pages": 10,
                    "style": "academic_simple",
                    "language": "zh-CN",
                },
            )
            assert create.status_code == 200
            task_id = create.json()["data"]["task_id"]

            with patch(
                "app.services.llm_runtime.text_generator.LLMTextGenerator.generate",
                side_effect=[
                    "# Wechat Post\n\n## Title Options\n- AI Agents in Practice\n- AI Agents for Teams\n\n## Abstract\nThis post explains practical value, risks, and adoption steps.\n\n## Body\nPoint A: real scenarios.\nPoint B: implementation checklist.\nPoint C: common pitfalls.\n\n## Closing CTA\nFollow and share your experience.",
                    "# Wechat Post\n\n## Title Options\n- AI Agents in Practice (Revised)\n- AI Agents for Teams (Revised)\n\n## Abstract\nThis revised version is more concise and emphasizes action.\n\n## Body\nPoint A: practical scenario in one sentence.\nPoint B: checklist with clear priority.\nPoint C: concise risk reminder.\n\n## Closing CTA\nComment your use case and follow for templates.",
                ],
            ):
                run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False})
                assert run.status_code == 200
                assert run.json()["data"]["status"] == "completed"
                rev = client.post(
                    f"/v1/tasks/{task_id}/revisions",
                    json={"instruction": "Make it more concise and stronger CTA"},
                )
                assert rev.status_code == 200
                assert rev.json()["data"]["new_version"] == 2

            versions = client.get(f"/v1/tasks/{task_id}/versions")
            assert versions.status_code == 200
            items = versions.json()["data"]["items"]
            assert len(items) == 2
            latest_path = Path(items[-1]["file_path"])
            assert latest_path.exists()
            assert latest_path.suffix == ".md"


def test_data_analysis_task_accepts_xlsx_and_exports_docx_report():
    with TemporaryDirectory() as temp_dir:
        settings.data_dir = Path(temp_dir)
        app = create_app()
        with TestClient(app) as client:
            create = client.post(
                "/v1/tasks",
                json={
                    "user_id": "u-1",
                    "task_type": "data_analysis",
                    "user_requirement": "Analyze cate distribution and return a Word report with chart.",
                    "pages": 10,
                    "style": "academic_simple",
                    "language": "en-US",
                },
            )
            assert create.status_code == 200
            task_id = create.json()["data"]["task_id"]

            wb = Workbook()
            ws = wb.active
            ws.append(["company", "cate", "revenue"])
            ws.append(["A", "Manufacturing", 100])
            ws.append(["B", "Manufacturing", 120])
            ws.append(["C", "Service", 80])
            ws.append(["D", "Tech", 140])
            stream = BytesIO()
            wb.save(stream)
            stream.seek(0)

            upload = client.post(
                f"/v1/tasks/{task_id}/upload",
                files={"upload": ("sample.xlsx", stream, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            assert upload.status_code == 200

            parse = client.post(f"/v1/tasks/{task_id}/parse", json={"force": False})
            assert parse.status_code == 200

            with patch(
                "app.services.llm_runtime.text_generator.LLMTextGenerator.generate",
                return_value=(
                    "# Data Analysis\n\n## Cleaning\nMissing values checked.\nType normalized.\n\n"
                    "## Findings\nManufacturing dominates cate.\nService and Tech are smaller.\n\n"
                    "## Recommendations\nUse balanced sampling in next-stage modeling.\n"
                ),
            ):
                run = client.post(f"/v1/tasks/{task_id}/run", json={"rerun": False})
                assert run.status_code == 200
                out = Path(run.json()["data"]["output_path"])
                assert out.exists()
                assert out.suffix == ".docx"
