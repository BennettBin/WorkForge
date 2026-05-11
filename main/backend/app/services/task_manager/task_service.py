from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import UploadFile

from app.agents.coordinator import CoordinatorAgent
from app.agents.task_agents import (
    PPTTaskAgent,
    CodeDocTaskAgent,
    DataAnalysisTaskAgent,
    PaperAssistantTaskAgent,
    ReportTaskAgent,
    WechatPostTaskAgent,
)
from app.config import settings
from app.models.entities import AgentRun, FileRecord, OutputFile, SkillCall, Task, TaskEvent
from app.models.requests import CreateTaskRequest
from app.prompts import NO_SOURCE_FILE_SYSTEM_INSTRUCTION
from app.services.export_engine import PptxExportError, PptxExporter
from app.services.file_parser.parser import ParseError, parse_file
from app.services.llm_runtime import LLMInvokeError, LLMTextGenerator
from app.services.llm_provider.provider_defaults import OllamaConfig
from app.services.model_router import ModelRouter
from app.services.repository_factory import RepositoryBundle
from app.services.skill_runtime import SkillExecutor
from app.services.skill_registry import SkillRegistry
from app.services.text_processing import clean_text_content
from app.services.vector_store import VectorIndexService
from app.utils.ids import new_id


ALLOWED_FILE_TYPES = {"pdf", "docx", "doc", "txt", "ppt", "pptx", "xlsx", "xls"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TaskService:
    repos: RepositoryBundle
    storage_root: Path

    def create_task(self, req: CreateTaskRequest) -> Task:
        task_type = req.task_type
        if task_type == "auto":
            coordinator = CoordinatorAgent(ModelRouter(self.repos))
            task_type = coordinator.infer_task_type(req.user_requirement)
        task = Task(
            task_id=new_id("task"),
            user_id=req.user_id,
            task_type=task_type,
            user_requirement=req.user_requirement,
            status="created",
            requested_pages=req.pages,
            style=req.style,
            language=req.language,
            expires_at=_utc_now() + timedelta(days=7),
        )
        self.repos.tasks.create(task)
        self._add_event(task.task_id, "created", "task created")
        self._snapshot_excel()
        return task

    def upload_file(self, task_id: str, upload: UploadFile) -> FileRecord:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")

        suffix = (Path(upload.filename or "").suffix or "").lower().lstrip(".")
        if suffix not in ALLOWED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {suffix}")

        file_bytes = upload.file.read()
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")
        if len(file_bytes) > settings.max_upload_size_bytes:
            raise ValueError("Uploaded file exceeds 50MB limit.")

        upload_dir = self.storage_root / "uploads" / task_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_id = new_id("file")
        file_path = upload_dir / f"{file_id}.{suffix}"
        file_path.write_bytes(file_bytes)

        record = FileRecord(
            file_id=file_id,
            task_id=task_id,
            file_name=upload.filename or file_path.name,
            file_type=suffix,
            file_path=str(file_path.resolve()),
            file_size_bytes=len(file_bytes),
            parse_status="pending",
            expires_at=_utc_now() + timedelta(days=7),
        )
        self.repos.files.create(record)
        self.repos.tasks.update_status(task_id, "file_uploaded")
        self._add_event(task_id, "file_uploaded", f"file uploaded: {record.file_name}")
        self._snapshot_excel()
        return record

    def parse_task_file(self, task_id: str, force: bool = False) -> FileRecord:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")

        files = self.repos.files.list_by_task(task_id)
        if not files:
            raise ValueError("No source file bound to this task.")
        record = files[0]
        if record.parse_status == "success" and not force:
            return record

        source_path = Path(record.file_path)
        if not source_path.exists():
            raise ValueError("Source file path does not exist.")

        try:
            parse_result = parse_file(source_path, record.file_type)
        except ParseError as exc:
            self.repos.tasks.update_status(task_id, "failed_file_parse")
            updated = record.model_copy(update={"parse_status": "failed", "summary": str(exc)})
            self._replace_file_record(updated)
            self._add_event(task_id, "failed_file_parse", str(exc))
            self._snapshot_excel()
            raise ValueError(str(exc)) from exc

        cleaned_text = clean_text_content(parse_result.text)
        if not cleaned_text:
            self.repos.tasks.update_status(task_id, "failed_file_parse")
            updated = record.model_copy(update={"parse_status": "failed", "summary": "Parsed text is empty after cleaning."})
            self._replace_file_record(updated)
            self._add_event(task_id, "failed_file_parse", "Parsed text is empty after cleaning.")
            self._snapshot_excel()
            raise ValueError("Parsed text is empty after cleaning.")

        parsed_dir = self.storage_root / "parsed" / task_id
        parsed_dir.mkdir(parents=True, exist_ok=True)
        parsed_text_path = parsed_dir / f"{record.file_id}.txt"
        parsed_text_path.write_text(cleaned_text, encoding="utf-8")

        vector_index_service = self._build_vector_index_service(task.user_id)
        try:
            index_info = vector_index_service.build_index(task_id, cleaned_text)
        except Exception as exc:
            self.repos.tasks.update_status(task_id, "failed_file_parse")
            updated = record.model_copy(update={"parse_status": "failed", "summary": f"Vectorization failed: {exc}"})
            self._replace_file_record(updated)
            self._add_event(task_id, "failed_file_parse", f"vectorization_failed={str(exc)[:160]}")
            self._snapshot_excel()
            raise ValueError(f"Vectorization failed: {exc}") from exc

        summary = cleaned_text[:500]
        updated = record.model_copy(
            update={
                "parsed_text_path": str(parsed_text_path.resolve()),
                "parse_status": "success",
                "summary": summary,
            }
        )
        self._replace_file_record(updated)
        self.repos.tasks.update_status(task_id, "file_parsed")
        self._add_event(task_id, "file_parsed", f"parsed_text_path={updated.parsed_text_path}")
        self._add_event(
            task_id,
            "file_parsed",
            (
                f"vector_cache_ready chunks={index_info['chunk_count']};"
                f"type={index_info.get('vectorizer_type')};model={index_info.get('vectorizer_model')}"
            ),
        )
        self._snapshot_excel()
        return updated

    def run_task(
        self,
        task_id: str,
        rerun: bool = False,
        require_llm: bool = False,
        llm_timeout_seconds: Optional[int] = None,
    ) -> dict:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        if task.task_type != "ppt":
            return self._run_text_task(
                task=task,
                rerun=rerun,
                require_llm=require_llm,
                llm_timeout_seconds=llm_timeout_seconds,
            )

        if rerun:
            self._add_agent_run(task_id, "TaskAgent", "running", "manual rerun requested")
            self._add_event(task_id, "generating", "manual rerun requested")

        files = self.repos.files.list_by_task(task_id)
        no_source_file = len(files) == 0
        parsed_text = ""
        effective_requirement = task.user_requirement
        vector_index_service = self._build_vector_index_service(task.user_id)
        if no_source_file:
            effective_requirement = f"{task.user_requirement}\n\n{NO_SOURCE_FILE_SYSTEM_INSTRUCTION}"
            self._add_event(task_id, "planning", "no_source_file_detected; agent should search and organize content")
            self._add_event(task_id, "planning", "no_source_file_system_instruction_applied")
            forced_items, forced_context = self._force_search_context(
                task_id=task_id,
                requirement=task.user_requirement,
                vector_index_service=vector_index_service,
                max_results=4,
            )
            if not forced_items:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_event(task_id, "failed_generation", "no_source_file_forced_search_empty")
                self._snapshot_excel()
                raise ValueError("No source file uploaded and forced search returned no usable results.")
            parsed_text = forced_context
        else:
            if files[0].parse_status != "success":
                self.parse_task_file(task_id, force=False)

            parsed_text_path = files[0].parsed_text_path
            if not parsed_text_path:
                raise ValueError("Parsed text path is missing.")
            parsed_text = Path(parsed_text_path).read_text(encoding="utf-8")
            parsed_text = clean_text_content(parsed_text)
            if not parsed_text:
                self.repos.tasks.update_status(task_id, "failed_file_parse")
                self._add_event(task_id, "failed_file_parse", "parsed text empty during run")
                self._snapshot_excel()
                raise ValueError("Parsed text is empty.")

        if (not no_source_file) and (not vector_index_service.has_index(task_id)):
            index_info = vector_index_service.build_index(task_id, parsed_text)
            self._add_event(
                task_id,
                "planning",
                (
                    f"vector_cache_rebuilt chunks={index_info['chunk_count']};"
                    f"type={index_info.get('vectorizer_type')};model={index_info.get('vectorizer_model')}"
                ),
            )

        self.repos.tasks.update_status(task_id, "planning")
        self._add_event(task_id, "planning", "start planning")
        router = ModelRouter(self.repos)
        coordinator = CoordinatorAgent(router)
        plan = coordinator.plan_for_ppt(task.user_id, effective_requirement)
        self._add_agent_run(
            task_id,
            "CoordinatorAgent",
            "completed",
            f"task_type={plan.task_type}; stages={','.join(plan.stages)}; requirement={plan.requirement_summary}",
        )
        self._add_event(task_id, "planning", f"requirement_understood={plan.requirement_summary}")

        self.repos.tasks.update_status(task_id, "skill_selecting")
        selected_skills = self._select_skills(task_id, "ppt", "generation")
        selected_skill_names = [s["name"] for s in selected_skills]
        self._add_event(task_id, "skill_selecting", f"selected_skills={','.join(selected_skill_names)}")
        self.repos.tasks.update_status(task_id, "model_selecting")
        self._add_event(task_id, "model_selecting", "model decisions resolved")
        self._add_agent_run(
            task_id,
            "ModelRouter",
            "completed",
            "; ".join(
                [
                    f"{d.stage}:{d.provider_type}/{d.model_name}({d.source})"
                    for d in plan.model_decisions
                ]
            ),
        )

        self.repos.tasks.update_status(task_id, "generating")
        self._add_event(task_id, "generating", "start content generation")
        ppt_task_agent = PPTTaskAgent()
        skill_executor = SkillExecutor.create_default()
        llm_runtime = LLMTextGenerator()
        can_use_knowledge_search = no_source_file or (("knowledge_search" in selected_skill_names) and plan.needs_web_search)
        generation_decision = next((d for d in plan.model_decisions if d.stage == "generation"), None)
        default_cfg = self.repos.providers.get_default_for_user(task.user_id)
        effective_timeout_seconds = (
            llm_timeout_seconds
            if llm_timeout_seconds is not None
            else (
                default_cfg.timeout_seconds
                if (default_cfg is not None and default_cfg.timeout_seconds is not None and default_cfg.timeout_seconds > 0)
                else 600  # 设置的LLM调用超过600秒将自动调用占位负继续下面的流程。
            )
        )
        llm_state = {
            "disabled": False,
            "attempted": False,
            "succeeded": False,
            "failure_reason": None,
            "timeout_seconds": effective_timeout_seconds,
        }
        if generation_decision is not None:
            self._add_event(
                task_id,
                "model_selecting",
                (
                    "llm_generation_target="
                    f"{generation_decision.provider_type}/{generation_decision.model_name};"
                    f"timeout={effective_timeout_seconds}s;require_llm={require_llm}"
                ),
            )

        def retrieve_context(query_text: str, top_k: int = 2) -> list[str]:
            return vector_index_service.query(task_id, query_text, top_k=top_k)

        def execute_knowledge_search(query_text: str, max_results: int = 2) -> list[dict]:
            if not can_use_knowledge_search:
                return []
            started = time.perf_counter()
            result = skill_executor.execute(
                "knowledge_search",
                {"query": query_text, "max_results": max_results},
            )
            duration_ms = int((time.perf_counter() - started) * 1000)
            items = result.get("items", [])
            self._add_skill_call(
                task_id,
                "knowledge_search",
                {"query": query_text, "max_results": max_results},
                {"count": len(items)},
                max(duration_ms, 1),
            )
            if items:
                append_info = vector_index_service.append_documents(task_id, items)
                self._add_event(
                    task_id,
                    "generating",
                    (
                        f"vector_cache_appended from_web chunks={append_info['appended_chunk_count']};"
                        f"type={append_info.get('vectorizer_type')};model={append_info.get('vectorizer_model')}"
                    ),
                )
            return items

        def skill_execute(skill_name: str, payload: dict[str, Any]) -> dict[str, Any]:
            safe_payload = {
                k: ("<callable>" if callable(v) else v)
                for k, v in payload.items()
            }
            started = time.perf_counter()
            try:
                output = skill_executor.execute(skill_name, payload)
                self._add_skill_call(
                    task_id,
                    skill_name,
                    safe_payload,
                    output,
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                return output
            except Exception as exc:
                self._add_skill_call(
                    task_id,
                    f"{skill_name}_failed",
                    safe_payload,
                    {"error": str(exc)[:300]},
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                raise

        def llm_generate(prompt: str) -> str:
            if llm_state["disabled"]:
                raise LLMInvokeError("LLM runtime disabled after previous failure.")
            if generation_decision is None:
                raise LLMInvokeError("No generation model decision.")
            llm_state["attempted"] = True
            provider_type = str(generation_decision.provider_type or "").strip()
            model_name = str(generation_decision.model_name or "").strip()
            base_url = generation_decision.base_url.strip() if isinstance(generation_decision.base_url, str) else generation_decision.base_url
            api_key = (default_cfg.api_key_encrypted or "").strip() if default_cfg and default_cfg.api_key_encrypted else None
            if not provider_type:
                raise LLMInvokeError("Provider type is empty in generation decision.")
            if not model_name:
                raise LLMInvokeError("Model name is empty in generation decision.")
            if not (prompt or "").strip():
                raise LLMInvokeError("Prompt is empty.")
            self._add_event(
                task_id,
                "generating",
                f"llm_call_start provider={provider_type};model={model_name};timeout={llm_state['timeout_seconds']}s",
            )
            started = time.perf_counter()
            try:
                text = llm_runtime.generate(
                    provider_type=provider_type,
                    base_url=base_url,
                    model_name=model_name,
                    prompt=prompt,
                    api_key=api_key,
                    timeout_seconds=llm_state["timeout_seconds"],
                )
            except Exception as exc:
                llm_state["disabled"] = True
                llm_state["failure_reason"] = str(exc)
                self._add_event(
                    task_id,
                    "generating",
                    f"llm_call_failed provider={provider_type};model={model_name};reason={str(exc)[:160]}",
                )
                self._add_skill_call(
                    task_id,
                    "llm_text_generation_failed",
                    {
                        "provider_type": provider_type,
                        "model_name": model_name,
                        "prompt_len": len(prompt),
                        "prompt": prompt[:8000],
                    },
                    {"error": str(exc)[:300]},
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                raise
            duration_ms = int((time.perf_counter() - started) * 1000)
            llm_state["succeeded"] = True
            self._add_event(
                task_id,
                "generating",
                f"llm_call_succeeded provider={provider_type};model={model_name};latency_ms={max(1, duration_ms)}",
            )
            self._add_skill_call(
                task_id,
                "llm_text_generation",
                {
                    "provider_type": provider_type,
                    "model_name": model_name,
                    "prompt_len": len(prompt),
                    "prompt": prompt[:8000],
                },
                {"text_len": len(text), "text": text[:12000]},
                max(1, duration_ms),
            )
            return text

        try:
            start_outline = time.perf_counter()
            artifacts = ppt_task_agent.execute(
                parsed_text=parsed_text,
                requested_pages=task.requested_pages,
                requirement=effective_requirement,
                retrieve_context_fn=retrieve_context,
                knowledge_search_fn=execute_knowledge_search if can_use_knowledge_search else None,
                llm_generate_fn=llm_generate,
                no_source_file=no_source_file,
                skill_execute_fn=skill_execute,
            )
            duration_outline = int((time.perf_counter() - start_outline) * 1000)
            self._add_skill_call(task_id, "ppt_generation_bundle", {"requested_pages": task.requested_pages}, {"slides": len(artifacts.slides)}, duration_outline)
            if (plan.needs_web_search or no_source_file) and not can_use_knowledge_search:
                self._add_event(task_id, "generating", "knowledge_search requested but skill not selected")
        except Exception as exc:
            if require_llm:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_agent_run(task_id, "PPTTaskAgent", "failed", f"llm_required_and_failed={str(exc)[:300]}")
                self._add_event(task_id, "failed_generation", f"llm_required_and_failed={str(exc)[:160]}")
                self._snapshot_excel()
                raise ValueError(f"Generation failed (LLM required): {exc}") from exc
            # fallback to deterministic generation when LLM runtime fails
            self._add_event(task_id, "generating", f"llm_generation_failed_fallback={str(exc)[:160]}")
            try:
                artifacts = ppt_task_agent.execute(
                    parsed_text=parsed_text,
                    requested_pages=task.requested_pages,
                    requirement=effective_requirement,
                    retrieve_context_fn=retrieve_context,
                    knowledge_search_fn=execute_knowledge_search if can_use_knowledge_search else None,
                    llm_generate_fn=None,
                    no_source_file=no_source_file,
                    skill_execute_fn=skill_execute,
                )
            except Exception:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_agent_run(task_id, "PPTTaskAgent", "failed", str(exc))
                self._add_event(task_id, "failed_generation", str(exc))
                self._snapshot_excel()
                raise ValueError(f"Generation failed: {exc}") from exc
            duration_outline = 1
            self._add_skill_call(task_id, "ppt_generation_bundle", {"requested_pages": task.requested_pages, "fallback": True}, {"slides": len(artifacts.slides)}, duration_outline)

        self._add_agent_run(
            task_id,
            "OutlineAgent",
            "completed",
            f"outline_pages={len(artifacts.outline)}",
        )
        self._add_agent_run(
            task_id,
            "ContentAgent",
            "completed",
            f"slides_generated={len(artifacts.slides)}",
        )
        if require_llm and (not llm_state["attempted"] or not llm_state["succeeded"]):
            self.repos.tasks.update_status(task_id, "failed_generation")
            reason = llm_state["failure_reason"] or "No successful LLM invocation was recorded."
            self._add_agent_run(task_id, "PPTTaskAgent", "failed", f"llm_required_without_success={reason[:300]}")
            self._add_event(task_id, "failed_generation", f"llm_required_without_success={reason[:160]}")
            self._snapshot_excel()
            raise ValueError(f"Generation failed (LLM required): {reason}")

        self.repos.tasks.update_status(task_id, "reviewing")
        self._add_event(task_id, "reviewing", "quality review started")
        if not artifacts.review_passed:
            self.repos.tasks.update_status(task_id, "failed_review")
            self._add_agent_run(
                task_id,
                "ReviewAgent",
                "failed",
                " | ".join(artifacts.review_issues),
            )
            self._add_event(task_id, "failed_review", " | ".join(artifacts.review_issues))
            self._snapshot_excel()
            raise ValueError("Quality review failed: " + " | ".join(artifacts.review_issues))
        self._add_agent_run(task_id, "ReviewAgent", "completed", "quality review passed")
        self._add_event(task_id, "reviewing", "quality review passed")

        self.repos.tasks.update_status(task_id, "exporting")
        self._add_event(task_id, "exporting", "start pptx export")
        output_dir = self.storage_root / "outputs" / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        latest = self.repos.outputs.get_latest(task_id)
        next_version = 1 if latest is None else latest.version + 1
        output_path = output_dir / f"v{next_version}.pptx"
        outline_path = output_dir / f"v{next_version}.outline.json"
        slides_path = output_dir / f"v{next_version}.slides.json"
        outline_path.write_text(json.dumps(artifacts.outline, ensure_ascii=False, indent=2), encoding="utf-8")
        slides_path.write_text(json.dumps(artifacts.slides, ensure_ascii=False, indent=2), encoding="utf-8")

        try:
            exporter = PptxExporter()
            template_path = self._resolve_template_path(task.style)
            exported = exporter.export(artifacts.slides, output_path, template_path=template_path)
            if not exported.exists():
                raise PptxExportError(f"Export finished but output file missing: {exported}")
        except PptxExportError as exc:
            self.repos.tasks.update_status(task_id, "failed_export")
            self._add_agent_run(task_id, "ExportEngine", "failed", str(exc))
            self._snapshot_excel()
            raise ValueError(str(exc)) from exc

        output = OutputFile(
            output_id=new_id("output"),
            task_id=task_id,
            version=next_version,
            file_type="pptx",
            file_path=str(exported.resolve()),
        )
        self.repos.outputs.create(output)
        self._add_agent_run(task_id, "ExportEngine", "completed", f"exported={exported.name}")
        self.repos.tasks.update_status(task_id, "completed")
        self._add_event(task_id, "completed", f"output_version={next_version}")
        self._snapshot_excel()

        return {
            "task_id": task_id,
            "status": "completed",
            "output_version": next_version,
            "output_path": str(exported.resolve()),
            "outline_path": str(outline_path.resolve()),
            "slides_path": str(slides_path.resolve()),
            "llm_debug": {
                "require_llm": require_llm,
                "attempted": bool(llm_state["attempted"]),
                "succeeded": bool(llm_state["succeeded"]),
                "failed_reason": llm_state["failure_reason"],
                "timeout_seconds": int(llm_state["timeout_seconds"]),
                "provider_type": generation_decision.provider_type if generation_decision else None,
                "model_name": generation_decision.model_name if generation_decision else None,
            },
        }

    def list_versions(self, task_id: str) -> list[dict[str, Any]]:
        versions = self.repos.outputs.list_versions(task_id)
        return [v.model_dump(mode="json") for v in versions]

    def compare_versions(self, task_id: str, from_version: int, to_version: int) -> dict[str, Any]:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        from_out = self._get_output_by_version(task_id, from_version)
        to_out = self._get_output_by_version(task_id, to_version)
        if from_out is None or to_out is None:
            raise ValueError("Version not found.")
        if task.task_type != "ppt":
            from_text = Path(from_out.file_path).read_text(encoding="utf-8") if Path(from_out.file_path).exists() else ""
            to_text = Path(to_out.file_path).read_text(encoding="utf-8") if Path(to_out.file_path).exists() else ""
            return {
                "task_id": task_id,
                "from_version": from_version,
                "to_version": to_version,
                "from_length": len(from_text),
                "to_length": len(to_text),
                "changed": from_text != to_text,
            }

        from_slides_path = Path(from_out.file_path).with_suffix(".slides.json")
        to_slides_path = Path(to_out.file_path).with_suffix(".slides.json")
        from_slides = self._read_json_array(from_slides_path)
        to_slides = self._read_json_array(to_slides_path)
        return {
            "task_id": task_id,
            "from_version": from_version,
            "to_version": to_version,
            "from_pages": len(from_slides),
            "to_pages": len(to_slides),
            "changed_page_count": self._count_changed_pages(from_slides, to_slides),
        }

    def rollback_to_version(self, task_id: str, target_version: int) -> dict[str, Any]:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        target = self._get_output_by_version(task_id, target_version)
        if target is None:
            raise ValueError("Target version not found.")
        if task.task_type != "ppt":
            src_path = Path(target.file_path)
            if not src_path.exists():
                raise ValueError("Target version output artifact missing.")
            latest = self.repos.outputs.get_latest(task_id)
            next_version = 1 if latest is None else latest.version + 1
            output_dir = self.storage_root / "outputs" / task_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"v{next_version}{src_path.suffix}"
            output_path.write_bytes(src_path.read_bytes())
            output = OutputFile(
                output_id=new_id("output"),
                task_id=task_id,
                version=next_version,
                file_type=target.file_type,
                file_path=str(output_path.resolve()),
            )
            self.repos.outputs.create(output)
            self._add_event(task_id, "revision_completed", f"rollback_from={target_version}_to={next_version}")
            self._snapshot_excel()
            return {"task_id": task_id, "new_version": next_version, "source_version": target_version}
        target_slides_path = Path(target.file_path).with_suffix(".slides.json")
        slides = self._read_json_array(target_slides_path)
        if not slides:
            raise ValueError("Target version slides artifact missing.")

        latest = self.repos.outputs.get_latest(task_id)
        next_version = 1 if latest is None else latest.version + 1
        output_dir = self.storage_root / "outputs" / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"v{next_version}.pptx"
        outline_path = output_dir / f"v{next_version}.outline.json"
        slides_path = output_dir / f"v{next_version}.slides.json"
        slides_path.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")
        outline_path.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")

        exporter = PptxExporter()
        template_path = self._resolve_template_path(task.style)
        exported = exporter.export(slides, output_path, template_path=template_path)

        output = OutputFile(
            output_id=new_id("output"),
            task_id=task_id,
            version=next_version,
            file_type="pptx",
            file_path=str(exported.resolve()),
        )
        self.repos.outputs.create(output)
        self._add_event(task_id, "revision_completed", f"rollback_from={target_version}_to={next_version}")
        self._snapshot_excel()
        return {"task_id": task_id, "new_version": next_version, "source_version": target_version}

    def revise_page(self, task_id: str, page_index: Optional[int], instruction: str) -> dict[str, Any]:
        latest = self.repos.outputs.get_latest(task_id)
        if latest is None:
            raise ValueError("No output version found.")
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        if task.task_type != "ppt":
            output_path = Path(latest.file_path)
            if not output_path.exists():
                raise ValueError("Latest output artifact missing.")
            original_text = output_path.read_text(encoding="utf-8")

            self.repos.tasks.update_status(task_id, "revision_requested")
            if page_index is not None:
                self._add_event(task_id, "revision_requested", f"page={page_index};ignored_for_non_ppt")
            else:
                self._add_event(task_id, "revision_requested", "non_ppt_revision_requested")
            self.repos.tasks.update_status(task_id, "revision_planning")

            files = self.repos.files.list_by_task(task_id)
            parsed_text = ""
            if files:
                file_row = files[0]
                if file_row.parse_status != "success":
                    file_row = self.parse_task_file(task_id, force=False)
                if file_row.parsed_text_path:
                    parsed_path = Path(file_row.parsed_text_path)
                    if parsed_path.exists():
                        parsed_text = clean_text_content(parsed_path.read_text(encoding="utf-8"))

            vector_index_service = self._build_vector_index_service(task.user_id)
            context_rows: list[str] = []
            if vector_index_service.has_index(task_id):
                for query in [instruction, task.user_requirement]:
                    rows = vector_index_service.query(task_id, query, top_k=3)
                    context_rows.extend([r.strip() for r in rows if str(r).strip()])
            context_rows = list(dict.fromkeys(context_rows))[:8]

            search_items: list[dict[str, Any]] = []
            search_query = f"{task.user_requirement}\n{instruction}".strip()
            started_search = time.perf_counter()
            try:
                search_result = SkillExecutor.create_default().execute("knowledge_search", {"query": search_query, "max_results": 3})
                search_items = search_result.get("items", []) if isinstance(search_result, dict) else []
                self._add_skill_call(
                    task_id,
                    "knowledge_search",
                    {"query": search_query, "max_results": 3, "stage": "revision", "task_type": task.task_type},
                    {"count": len(search_items)},
                    max(1, int((time.perf_counter() - started_search) * 1000)),
                )
            except Exception as exc:
                self._add_event(task_id, "revision_planning", f"knowledge_search_failed={str(exc)[:120]}")

            self._add_event(task_id, "revision_planning", f"non_ppt_revision task_type={task.task_type}")
            self.repos.tasks.update_status(task_id, "revision_generating")

            default_cfg = self.repos.providers.get_default_for_user(task.user_id)
            if default_cfg is not None:
                provider_type = default_cfg.provider_type
                model_name = default_cfg.model_name
                base_url = default_cfg.base_url
                api_key = default_cfg.api_key_encrypted
                timeout_seconds = default_cfg.timeout_seconds or 90
            else:
                ollama_default = OllamaConfig()
                provider_type = "ollama"
                model_name = ollama_default.chat_model
                base_url = ollama_default.base_url
                api_key = None
                timeout_seconds = 90

            web_refs = [
                {"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("snippet", "")}
                for item in search_items[:3]
                if isinstance(item, dict)
            ]
            llm_prompt = (
                "You are revising a generated task output document.\n"
                "Return revised content only (no markdown code block wrappers, no explanations).\n"
                "Keep style/language consistent with original task and satisfy revision instruction.\n"
                f"Task type: {task.task_type}\n"
                f"Original user requirement:\n{task.user_requirement}\n\n"
                f"Revision instruction:\n{instruction}\n\n"
                f"Current output content:\n{original_text[:20000]}\n\n"
                f"Uploaded-file parsed text excerpt:\n{parsed_text[:3000]}\n\n"
                f"Retrieved vector context:\n{json.dumps(context_rows, ensure_ascii=False)}\n\n"
                f"Web references:\n{json.dumps(web_refs, ensure_ascii=False)}\n"
            )

            llm_runtime = LLMTextGenerator()
            started_llm = time.perf_counter()
            revised_text = ""
            try:
                revised_text = llm_runtime.generate(
                    provider_type=provider_type,
                    base_url=base_url,
                    model_name=model_name,
                    prompt=llm_prompt,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds,
                )
                self._add_skill_call(
                    task_id,
                    "llm_text_generation",
                    {
                        "stage": "revision",
                        "task_type": task.task_type,
                        "provider_type": provider_type,
                        "model_name": model_name,
                        "prompt_len": len(llm_prompt),
                        "prompt": llm_prompt[:8000],
                    },
                    {"text_len": len(revised_text), "text": revised_text[:12000]},
                    max(1, int((time.perf_counter() - started_llm) * 1000)),
                )
            except Exception as exc:
                self._add_event(task_id, "revision_generating", f"llm_revision_failed={str(exc)[:160]};fallback_applied")
                revised_text = (
                    f"{original_text.rstrip()}\n\n"
                    f"## Revision Request\n{instruction.strip()}\n\n"
                    "## Revision Note\nLLM revision failed in this run, appended instruction for manual follow-up.\n"
                )

            if not revised_text.strip():
                revised_text = original_text

            self.repos.tasks.update_status(task_id, "revision_reviewing")
            output_dir = self.storage_root / "outputs" / task_id
            output_dir.mkdir(parents=True, exist_ok=True)
            next_version = latest.version + 1
            suffix = output_path.suffix or ".md"
            new_output_path = output_dir / f"v{next_version}{suffix}"
            new_output_path.write_text(revised_text, encoding="utf-8")
            output = OutputFile(
                output_id=new_id("output"),
                task_id=task_id,
                version=next_version,
                file_type=latest.file_type,
                file_path=str(new_output_path.resolve()),
            )
            self.repos.outputs.create(output)
            self.repos.tasks.update_status(task_id, "revision_completed")
            self.repos.tasks.update_status(task_id, "completed")
            self._add_event(task_id, "revision_completed", f"task_type={task.task_type};version={next_version}")
            self._add_agent_run(task_id, "RevisionAgent", "completed", f"task_type={task.task_type};instruction={instruction[:80]}")
            self._snapshot_excel()
            return {"task_id": task_id, "revised_page": None, "revised_pages": [], "new_version": next_version}

        slides_path = Path(latest.file_path).with_suffix(".slides.json")
        slides = self._read_json_array(slides_path)
        if not slides:
            raise ValueError("No slide content found for revision.")
        if page_index is not None and (page_index < 1 or page_index > len(slides)):
            raise ValueError("Page index out of range.")

        self.repos.tasks.update_status(task_id, "revision_requested")
        self._add_event(task_id, "revision_requested", f"page={page_index if page_index is not None else 'auto'}")
        self.repos.tasks.update_status(task_id, "revision_planning")

        files = self.repos.files.list_by_task(task_id)
        parsed_text = ""
        if files:
            file_row = files[0]
            if file_row.parse_status != "success":
                file_row = self.parse_task_file(task_id, force=False)
            if file_row.parsed_text_path:
                parsed_path = Path(file_row.parsed_text_path)
                if parsed_path.exists():
                    parsed_text = clean_text_content(parsed_path.read_text(encoding="utf-8"))

        vector_index_service = self._build_vector_index_service(task.user_id)

        if page_index is not None:
            target_page_indexes = [page_index]
        else:
            self._add_event(task_id, "revision_planning", "page_not_provided; llm_will_identify_target_slides")
            slides_summary = [
                {"index": i, "kind": str(s.get("kind", "content")), "title": str(s.get("title", "")), "bullets": (s.get("bullets", []) or [])[:2]}
                for i, s in enumerate(slides, start=1)
            ]
            selector_prompt = (
                "Identify which slide indexes should be revised for the instruction. "
                "Return JSON only: {\"page_indexes\":[int,...],\"reason\":\"...\"}. "
                "Indexes must be 1-based and within range.\n"
                f"User requirement:\n{task.user_requirement}\n\n"
                f"Revision instruction:\n{instruction}\n\n"
                f"Slides summary:\n{json.dumps(slides_summary, ensure_ascii=False)}\n"
            )
            default_cfg = self.repos.providers.get_default_for_user(task.user_id)
            if default_cfg is not None:
                provider_type = default_cfg.provider_type
                model_name = default_cfg.model_name
                base_url = default_cfg.base_url
                api_key = default_cfg.api_key_encrypted
                timeout_seconds = default_cfg.timeout_seconds or 90
            else:
                ollama_default = OllamaConfig()
                provider_type = "ollama"
                model_name = ollama_default.chat_model
                base_url = ollama_default.base_url
                api_key = None
                timeout_seconds = 90
            llm_runtime = LLMTextGenerator()
            selector_started = time.perf_counter()
            try:
                selector_raw = llm_runtime.generate(
                    provider_type=provider_type,
                    base_url=base_url,
                    model_name=model_name,
                    prompt=selector_prompt,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds,
                )
                self._add_skill_call(
                    task_id,
                    "llm_text_generation",
                    {"stage": "revision_page_select", "prompt_len": len(selector_prompt), "prompt": selector_prompt[:8000]},
                    {"text_len": len(selector_raw), "text": selector_raw[:12000]},
                    max(1, int((time.perf_counter() - selector_started) * 1000)),
                )
                text = (selector_raw or "").strip()
                start = text.find("{")
                end = text.rfind("}")
                payload = json.loads(text[start : end + 1])
                parsed_indexes = payload.get("page_indexes", []) if isinstance(payload, dict) else []
                target_page_indexes = sorted(
                    {int(x) for x in parsed_indexes if isinstance(x, (int, float, str)) and str(x).isdigit() and 1 <= int(x) <= len(slides)}
                )
            except Exception as exc:
                self._add_event(task_id, "revision_planning", f"auto_page_select_failed={str(exc)[:120]}")
                target_page_indexes = []
            if not target_page_indexes:
                target_page_indexes = [1]

        self._add_event(task_id, "revision_planning", f"target_pages={','.join(str(x) for x in target_page_indexes)}")
        self.repos.tasks.update_status(task_id, "revision_generating")

        default_cfg = self.repos.providers.get_default_for_user(task.user_id)
        if default_cfg is not None:
            provider_type = default_cfg.provider_type
            model_name = default_cfg.model_name
            base_url = default_cfg.base_url
            api_key = default_cfg.api_key_encrypted
            timeout_seconds = default_cfg.timeout_seconds or 90
        else:
            ollama_default = OllamaConfig()
            provider_type = "ollama"
            model_name = ollama_default.chat_model
            base_url = ollama_default.base_url
            api_key = None
            timeout_seconds = 90
        llm_runtime = LLMTextGenerator()
        self._add_event(task_id, "revision_generating", f"llm_call_start provider={provider_type};model={model_name};timeout={timeout_seconds}s")

        revised_pages: list[int] = []
        total_latency_ms = 0
        for target_idx in target_page_indexes:
            target_slide = slides[target_idx - 1]
            context_rows: list[str] = []
            if vector_index_service.has_index(task_id):
                for query in [instruction, str(target_slide.get("title", "")), task.user_requirement]:
                    if not query.strip():
                        continue
                    rows = vector_index_service.query(task_id, query, top_k=2)
                    context_rows.extend([r.strip() for r in rows if str(r).strip()])
            context_rows = list(dict.fromkeys(context_rows))[:6]

            search_items: list[dict[str, Any]] = []
            skill_executor = SkillExecutor.create_default()
            search_query = f"{task.user_requirement}\n{instruction}\n{target_slide.get('title', '')}".strip()
            started_search = time.perf_counter()
            try:
                search_result = skill_executor.execute("knowledge_search", {"query": search_query, "max_results": 3})
                search_items = search_result.get("items", []) if isinstance(search_result, dict) else []
                self._add_skill_call(
                    task_id,
                    "knowledge_search",
                    {"query": search_query, "max_results": 3, "stage": "revision", "page": target_idx},
                    {"count": len(search_items)},
                    max(1, int((time.perf_counter() - started_search) * 1000)),
                )
            except Exception as exc:
                self._add_event(task_id, "revision_planning", f"knowledge_search_failed page={target_idx};{str(exc)[:120]}")

            prev_bullets = target_slide.get("bullets", [])
            if not isinstance(prev_bullets, list):
                prev_bullets = []
            web_refs = [
                {"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("snippet", "")}
                for item in search_items[:3]
                if isinstance(item, dict)
            ]
            llm_prompt = (
                "You are revising one slide in an existing PPT deck.\n"
                "Return JSON only with fields: title (string), bullets (string array 3-6 items), notes (string), image_placeholders (array of {label, source}).\n"
                "Keep this slide index unchanged and stay consistent with deck style.\n"
                f"Original user requirement:\n{task.user_requirement}\n\n"
                f"Revision instruction:\n{instruction}\n\n"
                f"Current slide index: {target_idx}\n"
                f"Current slide JSON:\n{json.dumps(target_slide, ensure_ascii=False)}\n\n"
                f"Retrieved source context:\n{json.dumps(context_rows, ensure_ascii=False)}\n\n"
                f"Uploaded-file parsed text excerpt:\n{parsed_text[:2000]}\n\n"
                f"Web references:\n{json.dumps(web_refs, ensure_ascii=False)}\n"
            )
            started_llm = time.perf_counter()
            try:
                llm_raw = llm_runtime.generate(
                    provider_type=provider_type,
                    base_url=base_url,
                    model_name=model_name,
                    prompt=llm_prompt,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as exc:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_event(task_id, "failed_generation", f"revision_llm_failed page={target_idx};{str(exc)[:160]}")
                self._snapshot_excel()
                raise ValueError(f"Revision failed (LLM): {exc}") from exc
            latency_ms = max(1, int((time.perf_counter() - started_llm) * 1000))
            total_latency_ms += latency_ms
            self._add_skill_call(
                task_id,
                "llm_text_generation",
                {"stage": "revision", "page": target_idx, "provider_type": provider_type, "model_name": model_name, "prompt_len": len(llm_prompt), "prompt": llm_prompt[:8000]},
                {"text_len": len(llm_raw), "text": llm_raw[:12000]},
                latency_ms,
            )

            try:
                raw = (llm_raw or "").strip()
                start = raw.find("{")
                end = raw.rfind("}")
                revised_payload = json.loads(raw[start : end + 1])
            except Exception as exc:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_event(task_id, "failed_generation", f"revision_llm_output_invalid_json page={target_idx}")
                self._snapshot_excel()
                raise ValueError(f"Revision failed: invalid LLM JSON output ({exc})") from exc

            new_title = str(revised_payload.get("title", target_slide.get("title", ""))).strip() or str(target_slide.get("title", ""))
            bullets_raw = revised_payload.get("bullets", prev_bullets)
            if isinstance(bullets_raw, list):
                new_bullets = [str(b).strip() for b in bullets_raw if str(b).strip()][:6]
            else:
                new_bullets = prev_bullets
            if not new_bullets:
                new_bullets = prev_bullets[:5] if prev_bullets else [instruction[:120]]
            notes = str(revised_payload.get("notes", target_slide.get("notes", ""))).strip()[:1000]
            placeholders_raw = revised_payload.get("image_placeholders", [])
            placeholders: list[dict[str, str]] = []
            if isinstance(placeholders_raw, list):
                for item in placeholders_raw[:2]:
                    if not isinstance(item, dict):
                        continue
                    label = str(item.get("label", "")).strip()
                    source = str(item.get("source", "")).strip() or "unknown"
                    if not label:
                        continue
                    placeholders.append({"label": label[:90], "source": source[:180]})

            target_slide["title"] = new_title
            target_slide["bullets"] = new_bullets
            target_slide["notes"] = notes
            target_slide["image_placeholders"] = placeholders
            slides[target_idx - 1] = target_slide
            revised_pages.append(target_idx)

        self.repos.tasks.update_status(task_id, "revision_reviewing")
        skill_executor = SkillExecutor.create_default()
        review_result = skill_executor.execute("ppt_quality_reviewer", {"slides": slides, "requested_pages": len(slides)})
        if not bool(review_result.get("passed", False)):
            self.repos.tasks.update_status(task_id, "failed_review")
            issues = [str(x) for x in review_result.get("issues", [])] if isinstance(review_result.get("issues"), list) else []
            self._add_event(task_id, "failed_review", " | ".join(issues[:4]))
            self._snapshot_excel()
            raise ValueError("Revision review failed: " + " | ".join(issues))

        output_dir = self.storage_root / "outputs" / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        next_version = latest.version + 1
        output_path = output_dir / f"v{next_version}.pptx"
        new_slides_path = output_dir / f"v{next_version}.slides.json"
        new_outline_path = output_dir / f"v{next_version}.outline.json"
        new_slides_path.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")
        new_outline_path.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")

        exporter = PptxExporter()
        template_path = self._resolve_template_path(task.style)
        exported = exporter.export(slides, output_path, template_path=template_path)
        output = OutputFile(
            output_id=new_id("output"),
            task_id=task_id,
            version=next_version,
            file_type="pptx",
            file_path=str(exported.resolve()),
        )
        self.repos.outputs.create(output)
        self.repos.tasks.update_status(task_id, "revision_completed")
        self.repos.tasks.update_status(task_id, "completed")
        self._add_event(task_id, "revision_completed", f"pages={','.join(str(x) for x in revised_pages)};version={next_version};llm_latency_ms={total_latency_ms}")
        self._add_agent_run(task_id, "RevisionAgent", "completed", f"pages={','.join(str(x) for x in revised_pages)};instruction={instruction[:80]}")
        self._snapshot_excel()
        return {"task_id": task_id, "revised_page": revised_pages[0] if len(revised_pages) == 1 else None, "revised_pages": revised_pages, "new_version": next_version}

    def clear_task_cache(self, task_id: str) -> dict[str, Any]:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        vector_index_service = VectorIndexService(self.storage_root)
        clear_result = vector_index_service.clear_index(task_id)
        self._add_event(
            task_id,
            "cache_cleared",
            f"vector_cache_removed={clear_result['removed']};files={clear_result['removed_files']}",
        )
        self._snapshot_excel()
        return clear_result

    def _resolve_template_path(self, style: str) -> Optional[Path]:
        templates_dir = Path(__file__).resolve().parents[2] / "templates" / "ppt"
        if not templates_dir.exists():
            return None
        template_files = [p for p in templates_dir.glob("*.ppt*") if p.is_file()]
        if not template_files:
            return None
        style_key = self._normalize_style_key(style)
        ranked: list[tuple[float, Path]] = []
        for path in template_files:
            name_key = self._normalize_style_key(path.stem)
            score = 0.0
            if style_key and style_key in name_key:
                score = 10.0 + (len(style_key) / max(len(name_key), 1))
            else:
                style_tokens = set(style_key.split("_")) if style_key else set()
                name_tokens = set(name_key.split("_"))
                overlap = len(style_tokens & name_tokens)
                score = float(overlap)
            ranked.append((score, path))
        ranked.sort(key=lambda x: (-x[0], x[1].name))
        best_score, best_path = ranked[0]
        if best_score <= 0:
            return None
        return best_path

    def _normalize_style_key(self, value: str) -> str:
        return "".join((ch.lower() if ch.isalnum() else "_") for ch in (value or "")).strip("_")

    def _run_text_task(
        self,
        task: Task,
        rerun: bool,
        require_llm: bool,
        llm_timeout_seconds: Optional[int],
    ) -> dict[str, Any]:
        task_id = task.task_id
        if rerun:
            self._add_agent_run(task_id, "TaskAgent", "running", "manual rerun requested")
        files = self.repos.files.list_by_task(task_id)
        no_source_file = len(files) == 0
        parsed_text = ""
        vector_index_service = self._build_vector_index_service(task.user_id)
        if files:
            file_row = files[0]
            if file_row.parse_status != "success":
                file_row = self.parse_task_file(task_id, force=False)
            if file_row.parsed_text_path:
                parsed_path = Path(file_row.parsed_text_path)
                if parsed_path.exists():
                    parsed_text = clean_text_content(parsed_path.read_text(encoding="utf-8"))
        else:
            self._add_event(task_id, "planning", "no_source_file_detected; forced knowledge search enabled")
            forced_items, forced_context = self._force_search_context(
                task_id=task_id,
                requirement=task.user_requirement,
                vector_index_service=vector_index_service,
                max_results=4,
            )
            if not forced_items:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_event(task_id, "failed_generation", "no_source_file_forced_search_empty")
                self._snapshot_excel()
                raise ValueError("No source file uploaded and forced search returned no usable results.")
            parsed_text = forced_context

        self.repos.tasks.update_status(task_id, "planning")
        self._add_event(task_id, "planning", f"start {task.task_type} planning")
        router = ModelRouter(self.repos)
        coordinator = CoordinatorAgent(router)
        plan = coordinator.plan_for_task(task.user_id, task.task_type, task.user_requirement)
        selected_skills = self._select_skills(task_id, task.task_type, "generation")
        selected_skill_names = [s["name"] for s in selected_skills]
        self._add_event(task_id, "skill_selecting", f"selected_skills={','.join(selected_skill_names)}")
        self._add_agent_run(
            task_id,
            "CoordinatorAgent",
            "completed",
            f"task_type={task.task_type}; stages={','.join(plan.stages)}; requirement={plan.requirement_summary}",
        )

        self.repos.tasks.update_status(task_id, "generating")
        generation_decision = next((d for d in plan.model_decisions if d.stage == "generation"), None)
        default_cfg = self.repos.providers.get_default_for_user(task.user_id)
        timeout_seconds = (
            llm_timeout_seconds
            if llm_timeout_seconds is not None
            else (default_cfg.timeout_seconds if (default_cfg and default_cfg.timeout_seconds and default_cfg.timeout_seconds > 0) else 180)
        )
        self._add_event(task_id, "generating", f"llm_generation_target={generation_decision.provider_type if generation_decision else 'none'}/{generation_decision.model_name if generation_decision else 'none'};timeout={timeout_seconds}s")

        llm_runtime = LLMTextGenerator()
        llm_succeeded = False
        llm_failed_reason: Optional[str] = None
        skill_executor = SkillExecutor.create_default()

        def skill_execute(skill_name: str, payload: dict[str, Any]) -> dict[str, Any]:
            safe_payload = {
                k: ("<callable>" if callable(v) else v)
                for k, v in payload.items()
            }
            started = time.perf_counter()
            try:
                output = skill_executor.execute(skill_name, payload)
                self._add_skill_call(
                    task_id,
                    skill_name,
                    safe_payload,
                    output,
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                return output
            except Exception as exc:
                self._add_skill_call(
                    task_id,
                    f"{skill_name}_failed",
                    safe_payload,
                    {"error": str(exc)[:300]},
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                raise

        def llm_generate(prompt: str) -> str:
            nonlocal llm_succeeded, llm_failed_reason
            if generation_decision is None:
                raise LLMInvokeError("No generation model decision.")
            started = time.perf_counter()
            try:
                content = llm_runtime.generate(
                    provider_type=generation_decision.provider_type,
                    base_url=generation_decision.base_url,
                    model_name=generation_decision.model_name,
                    prompt=prompt,
                    api_key=(default_cfg.api_key_encrypted if default_cfg and default_cfg.api_key_encrypted else None),
                    timeout_seconds=timeout_seconds,
                )
                llm_succeeded = True
                self._add_skill_call(
                    task_id,
                    "llm_text_generation",
                    {"stage": "generation", "task_type": task.task_type, "prompt_len": len(prompt), "prompt": prompt[:8000]},
                    {"text_len": len(content), "text": content[:12000]},
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                return content
            except Exception as exc:
                llm_failed_reason = str(exc)
                self._add_event(task_id, "generating", f"llm_call_failed reason={llm_failed_reason[:160]}")
                raise

        task_agent_map = {
            "report": ReportTaskAgent,
            "wechat_post": WechatPostTaskAgent,
            "data_analysis": DataAnalysisTaskAgent,
            "code_doc": CodeDocTaskAgent,
            "paper_assistant": PaperAssistantTaskAgent,
        }
        agent_cls = task_agent_map.get(task.task_type)
        if agent_cls is None:
            raise ValueError(f"Unsupported non-ppt task_type: {task.task_type}")
        task_agent = agent_cls()
        task_agent_name = agent_cls.__name__
        try:
            artifacts = task_agent.execute(
                requirement=task.user_requirement,
                parsed_text=parsed_text,
                style=task.style,
                language=task.language,
                skill_execute_fn=skill_execute,
                llm_generate_fn=llm_generate if generation_decision is not None else None,
            )
        except Exception as exc:
            if require_llm:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_agent_run(task_id, task_agent_name, "failed", str(exc)[:300])
                self._snapshot_excel()
                raise ValueError(f"Generation failed (LLM required): {str(exc)}") from exc
            self._add_event(task_id, "generating", f"text_task_agent_failed_fallback={str(exc)[:160]}")
            artifacts = task_agent.execute(
                requirement=task.user_requirement,
                parsed_text=parsed_text,
                style=task.style,
                language=task.language,
                skill_execute_fn=skill_execute,
                llm_generate_fn=None,
            )

        self._add_agent_run(task_id, task_agent_name, "completed", f"plan={artifacts.plan_summary[:180]};sections={artifacts.section_count}")
        planner_name = f"{task_agent_name.replace('TaskAgent', '')}PlannerSubAgent"
        writer_name = f"{task_agent_name.replace('TaskAgent', '')}WriterSubAgent"
        reviewer_name = f"{task_agent_name.replace('TaskAgent', '')}ReviewerSubAgent"
        self._add_agent_run(task_id, planner_name, "completed", artifacts.plan_summary[:300])
        self._add_agent_run(task_id, writer_name, "completed", f"sections={artifacts.section_count}")
        self.repos.tasks.update_status(task_id, "reviewing")
        if not artifacts.review_passed:
            self.repos.tasks.update_status(task_id, "failed_review")
            self._add_agent_run(task_id, reviewer_name, "failed", " | ".join(artifacts.review_issues))
            self._add_event(task_id, "failed_review", " | ".join(artifacts.review_issues))
            self._snapshot_excel()
            raise ValueError("Quality review failed: " + " | ".join(artifacts.review_issues))
        self._add_agent_run(task_id, reviewer_name, "completed", "review passed")

        self.repos.tasks.update_status(task_id, "exporting")
        output_dir = self.storage_root / "outputs" / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        latest = self.repos.outputs.get_latest(task_id)
        next_version = 1 if latest is None else latest.version + 1
        output_path = output_dir / f"v{next_version}.md"
        output_file_type = "md"

        # Data-analysis enhancement: for Excel source files, generate chart + Word report artifact.
        if task.task_type == "data_analysis" and files:
            source_file = Path(files[0].file_path)
            if source_file.suffix.lower() in {".xlsx", ".xls"}:
                try:
                    docx_path = output_dir / f"v{next_version}.docx"
                    chart_path = output_dir / f"v{next_version}.cate_distribution.png"
                    report_info = skill_execute(
                        "data_excel_cate_word_report",
                        {
                            "excel_path": str(source_file.resolve()),
                            "report_docx_path": str(docx_path.resolve()),
                            "chart_png_path": str(chart_path.resolve()),
                            "requirement": task.user_requirement,
                            "llm_markdown": artifacts.markdown,
                            "language": task.language,
                            "target_column": self._extract_task_setting(task.user_requirement, "TargetColumn") or "cate",
                            "stage": "exporting",
                            "task_type": "data_analysis",
                        },
                    )
                    if str(report_info.get("report_path", "")).strip():
                        output_path = docx_path
                        output_file_type = "docx"
                    else:
                        self._add_event(task_id, "exporting", "data_excel_word_report_empty_output;fallback_to_markdown")
                except Exception as exc:
                    self._add_event(task_id, "exporting", f"data_excel_word_report_failed={str(exc)[:160]};fallback_to_markdown")

        if output_file_type == "md":
            output_path.write_text(artifacts.markdown, encoding="utf-8")
        output = OutputFile(
            output_id=new_id("output"),
            task_id=task_id,
            version=next_version,
            file_type=output_file_type,  # type: ignore[arg-type]
            file_path=str(output_path.resolve()),
        )
        self.repos.outputs.create(output)
        self.repos.tasks.update_status(task_id, "completed")
        self._add_event(task_id, "completed", f"output_version={next_version};task_type={task.task_type}")
        self._snapshot_excel()
        return {
            "task_id": task_id,
            "status": "completed",
            "task_type": task.task_type,
            "output_version": next_version,
            "output_path": str(output_path.resolve()),
            "llm_debug": {
                "require_llm": require_llm,
                "attempted": generation_decision is not None,
                "succeeded": llm_succeeded,
                "failed_reason": llm_failed_reason,
                "timeout_seconds": timeout_seconds,
                "provider_type": generation_decision.provider_type if generation_decision else None,
                "model_name": generation_decision.model_name if generation_decision else None,
            },
        }

    def _force_search_context(
        self,
        *,
        task_id: str,
        requirement: str,
        vector_index_service: VectorIndexService,
        max_results: int = 4,
    ) -> tuple[list[dict[str, Any]], str]:
        skill_executor = SkillExecutor.create_default()
        query = requirement.strip()
        if not query:
            query = "latest information overview"
        started = time.perf_counter()
        try:
            result = skill_executor.execute("knowledge_search", {"query": query, "max_results": max_results})
            items = result.get("items", []) if isinstance(result, dict) else []
        except Exception as exc:
            self._add_skill_call(
                task_id,
                "knowledge_search_failed",
                {"query": query, "max_results": max_results, "forced": True},
                {"error": str(exc)[:300]},
                max(1, int((time.perf_counter() - started) * 1000)),
            )
            return [], ""

        self._add_skill_call(
            task_id,
            "knowledge_search",
            {"query": query, "max_results": max_results, "forced": True},
            {"count": len(items)},
            max(1, int((time.perf_counter() - started) * 1000)),
        )
        if items:
            try:
                append_info = vector_index_service.append_documents(task_id, items)
                self._add_event(
                    task_id,
                    "planning",
                    (
                        f"vector_cache_appended forced_search chunks={append_info['appended_chunk_count']};"
                        f"type={append_info.get('vectorizer_type')};model={append_info.get('vectorizer_model')}"
                    ),
                )
            except Exception as exc:
                self._add_event(task_id, "planning", f"forced_search_vector_append_failed={str(exc)[:160]}")

        context_rows: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            content = str(item.get("content", "")).strip()
            row = " | ".join([x for x in [title, snippet or content[:280]] if x])
            if row:
                context_rows.append(row)
        context = "\n".join(context_rows).strip()
        return items, context

    def _add_agent_run(self, task_id: str, agent_name: str, status: str, output: str) -> None:
        run = AgentRun(
            run_id=new_id("run"),
            task_id=task_id,
            agent_name=agent_name,
            status=status,  # type: ignore[arg-type]
            output=output,
        )
        self.repos.agent_runs.create(run)

    def _add_event(self, task_id: str, stage: str, message: str) -> None:
        event = TaskEvent(event_id=new_id("evt"), task_id=task_id, stage=stage, message=message)
        self.repos.task_events.create(event)

    def _add_skill_call(self, task_id: str, skill_name: str, input_payload: dict, output_payload: dict, duration_ms: int) -> None:
        call = SkillCall(
            skill_call_id=new_id("skill"),
            task_id=task_id,
            skill_name=skill_name,
            input=json.dumps(input_payload, ensure_ascii=False),
            output=json.dumps(output_payload, ensure_ascii=False),
            token_usage=max(1, (len(json.dumps(input_payload)) + len(json.dumps(output_payload))) // 4),
            duration_ms=duration_ms,
        )
        self.repos.skill_calls.create(call)

    def _select_skills(self, task_id: str, task_type: str, stage: str) -> list[dict[str, Any]]:
        skills_root = Path(__file__).resolve().parents[2] / "skills"
        registry = SkillRegistry(skills_root)
        skills = registry.resolve_for(task_type, stage)
        selected = [s.__dict__ for s in skills]
        self._add_skill_call(task_id, "skill_registry_resolve", {"task_type": task_type, "stage": stage}, {"count": len(selected)}, 1)
        return selected

    def _build_vector_index_service(self, user_id: str) -> VectorIndexService:
        cfg = self.repos.providers.get_default_for_user(user_id)
        if cfg is not None and str(cfg.provider_type).strip().lower() == "ollama":
            embedding_model = (cfg.embedding_model or cfg.model_name or "").strip()
            if embedding_model:
                return VectorIndexService(
                    self.storage_root,
                    embedding_runtime_config={
                        "provider_type": "ollama",
                        "base_url": (cfg.base_url or "").strip() or "http://localhost:11434",
                        "embedding_model": embedding_model,
                        "api_key": (cfg.api_key_encrypted or "").strip() if cfg.api_key_encrypted else "",
                        "timeout_seconds": cfg.timeout_seconds or 8,
                    },
                )
        default_ollama = OllamaConfig()
        return VectorIndexService(
            self.storage_root,
            embedding_runtime_config={
                "provider_type": "ollama",
                "base_url": default_ollama.base_url,
                "embedding_model": default_ollama.embedding_model,
                "timeout_seconds": 8,
            },
        )

    def _replace_file_record(self, updated: FileRecord) -> None:
        rows = self.repos.files.store.read_all()  # direct store access for MVP replacement
        replaced = False
        for row in rows:
            if row["file_id"] == updated.file_id:
                row.update(updated.model_dump(mode="json"))
                replaced = True
                break
        if not replaced:
            rows.append(updated.model_dump(mode="json"))
        self.repos.files.store.write_all(rows)

    def _snapshot_excel(self) -> None:
        self.repos.excel_mirror.write_snapshot(
            {
                "tasks": self.repos.tasks.store.read_all(),
                "files": self.repos.files.store.read_all(),
                "providers": self.repos.providers.store.read_all(),
                "outputs": self.repos.outputs.store.read_all(),
                "agent_runs": self.repos.agent_runs.store.read_all(),
                "skill_calls": self.repos.skill_calls.store.read_all(),
                "task_events": self.repos.task_events.store.read_all(),
                "users": self.repos.users.store.read_all(),
                "sessions": self.repos.sessions.store.read_all(),
            }
        )

    def _get_output_by_version(self, task_id: str, version: int) -> Optional[OutputFile]:
        for item in self.repos.outputs.list_versions(task_id):
            if item.version == version:
                return item
        return None

    def _read_json_array(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return data
        return []

    def _count_changed_pages(self, a: list[dict[str, Any]], b: list[dict[str, Any]]) -> int:
        max_len = max(len(a), len(b))
        changed = 0
        for i in range(max_len):
            va = a[i] if i < len(a) else None
            vb = b[i] if i < len(b) else None
            if va != vb:
                changed += 1
        return changed

    def _extract_task_setting(self, requirement_text: str, key: str) -> str | None:
        content = requirement_text or ""
        marker = f"{key}="
        for line in content.splitlines():
            raw = line.strip()
            if not raw.startswith(marker):
                continue
            value = raw[len(marker) :].strip()
            if value:
                return value
        return None


def build_task_service(repos: RepositoryBundle) -> TaskService:
    return TaskService(repos=repos, storage_root=settings.data_dir)

