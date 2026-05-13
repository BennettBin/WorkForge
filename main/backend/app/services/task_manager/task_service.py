from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import UploadFile

from app.agents.coordinator import CoordinatorAgent
from app.agents.task_agents import (
    PPTTaskAgent,
    CodeDocTaskAgent,
    DataAnalysisTaskAgent,
    GenericTaskAgent,
    PaperAssistantTaskAgent,
    ReportTaskAgent,
    TemplateGenerationTaskAgent,
    WechatPostTaskAgent,
)
from app.config import settings
from app.models.entities import AgentRun, FileRecord, OutputFile, SkillCall, Task, TaskEvent, UserSettings
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
from app.services.template_bundle import TEMPLATE_META_FILENAME as BUNDLE_META_FILENAME, TEMPLATE_RULES_FILENAME as BUNDLE_RULES_FILENAME, TEMPLATE_SCHEMA_VERSION, validate_template_bundle
from app.services.text_processing import clean_text_content
from app.services.vector_store import VectorIndexService
from app.utils.ids import new_id


ALLOWED_FILE_TYPES = {"pdf", "docx", "doc", "txt", "ppt", "pptx", "xlsx", "xls"}
TEMPLATE_META_FILENAME = "template.meta.json"
TEMPLATE_PARAMS_FILENAME = "template.params.json"
TEMPLATE_RENDER_SCRIPT_FILENAME = "render_from_template.py"
TEMPLATE_PPT_FILENAME = "template.pptx"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TaskService:
    repos: RepositoryBundle
    storage_root: Path

    RUNNING_STATUSES = {
        "created",
        "file_uploaded",
        "file_parsed",
        "planning",
        "skill_selecting",
        "model_selecting",
        "generating",
        "reviewing",
        "exporting",
        "revision_requested",
        "revision_planning",
        "revision_generating",
        "revision_reviewing",
        "requires_user_completion",
    }
    CAPACITY_COUNT_STATUSES = {
        "planning",
        "skill_selecting",
        "model_selecting",
        "generating",
        "reviewing",
        "exporting",
        "revision_requested",
        "revision_planning",
        "revision_generating",
        "revision_reviewing",
        "requires_user_completion",
    }
    RUNNING_STALE_TIMEOUT_SECONDS = 30 * 60

    def create_task(self, req: CreateTaskRequest) -> Task:
        self._ensure_parallel_capacity(req.user_id)
        task_type = req.task_type
        if task_type == "auto":
            coordinator = CoordinatorAgent(ModelRouter(self.repos))
            task_type = coordinator.infer_task_type(req.user_requirement, user_id=req.user_id)
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
        force_generic_direct: bool = False,
        capability_name: Optional[str] = None,
    ) -> dict:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        self._ensure_parallel_capacity(task.user_id, exclude_task_id=task_id)
        if task.task_type == "template_generation":
            return self._run_template_generation_task(task, rerun=rerun)
        if task.task_type != "ppt":
            return self._run_text_task(
                task=task,
                rerun=rerun,
                require_llm=require_llm,
                llm_timeout_seconds=llm_timeout_seconds,
                force_generic_direct=force_generic_direct,
                capability_name=capability_name,
            )

        if rerun:
            self._add_agent_run(task_id, "TaskAgent", "running", "manual rerun requested")
            self._add_event(task_id, "generating", "manual rerun requested")

        files = self.repos.files.list_by_task(task_id)
        no_source_file = len(files) == 0
        coordinator_for_skill = CoordinatorAgent(ModelRouter(self.repos))
        selected_ppt_skill = coordinator_for_skill.infer_ppt_skill(task.user_requirement)
        self._add_event(task_id, "planning", f"router_selected_skill={selected_ppt_skill}")
        if selected_ppt_skill == "ppt_template_generation":
            if not files:
                raise ValueError("Template extraction requires an uploaded PPT/PPTX file.")
            source_file = Path(files[0].file_path)
            if source_file.suffix.lower() not in {".ppt", ".pptx"}:
                raise ValueError("Template extraction requires a PPT/PPTX source file.")
            self.repos.tasks.update_status(task_id, "generating")
            skill_executor = SkillExecutor.create_default()
            planning_decision = coordinator_for_skill.router.pick(task.user_id, "planning")
            default_cfg = self.repos.providers.get_default_for_user(task.user_id)
            finder_result = skill_executor.execute(
                "find_skill",
                {
                    "task_type": "ppt",
                    "requirement": task.user_requirement,
                    "preferred_skills": ["ppt_template_generation"],
                    "provider_type": planning_decision.provider_type or "",
                    "base_url": planning_decision.base_url or "",
                    "model_name": planning_decision.model_name or "",
                    "api_key": (default_cfg.api_key_encrypted if default_cfg and default_cfg.api_key_encrypted else ""),
                },
            )
            self._add_skill_call(
                task_id,
                "find_skill",
                {"task_type": "ppt", "preferred_skills": ["ppt_template_generation"]},
                finder_result,
                1,
            )
            matched = finder_result.get("matched_skills", []) if isinstance(finder_result, dict) else []
            template_skill_name = matched[0] if matched else "ppt_template_generation"
            templates_root = Path(__file__).resolve().parents[2] / "templates" / "ppt"
            extraction = skill_executor.execute(
                template_skill_name,
                {
                    "source_pptx_path": str(source_file.resolve()),
                    "templates_root": str(templates_root.resolve()),
                    "template_name": self._extract_template_name(task.user_requirement) or source_file.stem,
                    "force_invalid_bundle": str(self._extract_task_setting(task.user_requirement, "ForceInvalidBundle") or "").strip().lower() in {"1", "true", "yes"},
                },
            )
            self._add_skill_call(task_id, template_skill_name, {"source_pptx_path": str(source_file.resolve()), "template_name": extraction.get("template_name", "")}, extraction, 1)
            if str(extraction.get("status", "completed")) == "requires_user_completion":
                recovery_payload = {
                    "task_id": task_id,
                    "template_name": extraction.get("template_name"),
                    "template_dir": extraction.get("template_dir"),
                    "template_file": extraction.get("template_file"),
                    "metadata_file": extraction.get("metadata_file"),
                    "rules_file": extraction.get("rules_file"),
                    "render_script": extraction.get("render_script"),
                    "recovery_file": extraction.get("recovery_file"),
                    "missing_items": extraction.get("missing_items", []),
                    "validation_errors": extraction.get("validation_errors", []),
                    "suggested_values": extraction.get("suggested_values", {}),
                    "resume_token": extraction.get("resume_token", ""),
                }
                self._write_template_recovery_payload(task_id, recovery_payload)
                self.repos.tasks.update_status(task_id, "requires_user_completion")
                self._add_event(task_id, "requires_user_completion", f"template_generation_requires_user_completion:{json.dumps(recovery_payload, ensure_ascii=False)}")
                self._snapshot_excel()
                return {"task_id": task_id, "status": "requires_user_completion", **recovery_payload}
            self._add_agent_run(task_id, "PPTTaskAgent", "completed", f"template_extracted={extraction.get('template_name', '')}")
            self.repos.tasks.update_status(task_id, "completed")
            self._add_event(task_id, "completed", f"template_extracted={extraction.get('template_name', '')}")
            self._snapshot_excel()
            return {
                "task_id": task_id,
                "status": "completed",
                "template_extracted": True,
                "template_name": extraction.get("template_name"),
                "template_dir": extraction.get("template_dir"),
                "template_file": extraction.get("template_file"),
                "metadata_file": extraction.get("metadata_file"),
            }
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
                self._add_event(task_id, "planning", "no_source_file_forced_search_empty;fallback_to_requirement_context")
                parsed_text = clean_text_content(task.user_requirement or "")
            else:
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

        if (task.style or "").strip() or (self._extract_task_setting(task.user_requirement, "TemplateChoice") or "").strip():
            template_ctx = self._load_template_context_for_task(task)
            if template_ctx:
                template_choice = (self._extract_task_setting(task.user_requirement, "TemplateChoice") or "").strip()
                effective_requirement = f"{effective_requirement}\n\n[Template Context]\n{template_ctx}"
                self._add_event(task_id, "planning", f"template_context_loaded style={task.style};template_choice={template_choice or 'none'}")

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
            effective_payload = dict(payload)
            if skill_name == "find_skill":
                effective_payload.setdefault("task_type", "generic_task")
                effective_payload.setdefault("requirement", effective_requirement)
                effective_payload.setdefault("provider_type", generation_decision.provider_type if generation_decision else "")
                effective_payload.setdefault("base_url", generation_decision.base_url if generation_decision else "")
                effective_payload.setdefault("model_name", generation_decision.model_name if generation_decision else "")
                effective_payload.setdefault("api_key", (default_cfg.api_key_encrypted if default_cfg and default_cfg.api_key_encrypted else ""))
            safe_payload = {
                k: ("<callable>" if callable(v) else v)
                for k, v in effective_payload.items()
            }
            started = time.perf_counter()
            try:
                output = skill_executor.execute(skill_name, effective_payload)
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
            template_bundle = self._resolve_selected_template_bundle(task)
            template_path = Path(str(template_bundle["template_file"])) if template_bundle else None
            exported = exporter.export(artifacts.slides, output_path, template_path=template_path, template_bundle=template_bundle)
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
        template_bundle = self._resolve_selected_template_bundle(task)
        template_path = Path(str(template_bundle["template_file"])) if template_bundle else None
        exported = exporter.export(slides, output_path, template_path=template_path, template_bundle=template_bundle)

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
        review_result = skill_executor.execute("ppt_generation", {"slides": slides, "requested_pages": len(slides)})
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
        template_bundle = self._resolve_selected_template_bundle(task)
        template_path = Path(str(template_bundle["template_file"])) if template_bundle else None
        exported = exporter.export(slides, output_path, template_path=template_path, template_bundle=template_bundle)
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
        style_name = (style or "").strip()
        if style_name:
            exact = templates_dir / style_name / TEMPLATE_PPT_FILENAME
            if exact.exists() and exact.is_file():
                return exact
        template_files = [p for p in templates_dir.glob(f"**/{TEMPLATE_PPT_FILENAME}") if p.is_file()]
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

    def _resolve_template_bundle(self, template_name: str) -> dict[str, Any]:
        name = (template_name or "").strip()
        if not name:
            raise ValueError("TemplateChoice is empty.")
        templates_dir = Path(__file__).resolve().parents[2] / "templates" / "ppt"
        bundle_dir = templates_dir / name
        if not bundle_dir.exists() or not bundle_dir.is_dir():
            raise ValueError(f"TemplateChoice points to non-existent template: {name}")
        validation = validate_template_bundle(bundle_dir)
        if not bool(validation.get("ok", False)):
            raise ValueError(
                f"TemplateChoice points to invalid template bundle: {name}; missing_files={validation.get('missing_files', [])}; errors={validation.get('errors', [])}"
            )
        template_file = bundle_dir / TEMPLATE_PPT_FILENAME
        if not template_file.exists():
            raise ValueError(f"TemplateChoice template file missing: {name}/{TEMPLATE_PPT_FILENAME}")
        meta_path = bundle_dir / TEMPLATE_META_FILENAME
        rules_path = bundle_dir / BUNDLE_RULES_FILENAME
        script_path = bundle_dir / TEMPLATE_RENDER_SCRIPT_FILENAME
        return {
            "template_name": name,
            "bundle_dir": bundle_dir,
            "template_file": template_file,
            "meta_path": meta_path,
            "rules_path": rules_path,
            "script_path": script_path,
        }

    def _resolve_selected_template_path(self, task: Task) -> Optional[Path]:
        template_choice = (self._extract_task_setting(task.user_requirement, "TemplateChoice") or "").strip()
        if template_choice:
            bundle = self._resolve_template_bundle(template_choice)
            return Path(bundle["template_file"])
        return self._resolve_template_path(task.style)

    def _resolve_selected_template_bundle(self, task: Task) -> Optional[dict[str, Any]]:
        template_choice = (self._extract_task_setting(task.user_requirement, "TemplateChoice") or "").strip()
        if template_choice:
            return self._resolve_template_bundle(template_choice)
        style_path = self._resolve_template_path(task.style)
        if not style_path:
            return None
        bundle_dir = style_path.parent
        validation = validate_template_bundle(bundle_dir)
        if not bool(validation.get("ok", False)):
            return None
        return {
            "template_name": bundle_dir.name,
            "bundle_dir": bundle_dir,
            "template_file": style_path,
            "meta_path": bundle_dir / TEMPLATE_META_FILENAME,
            "rules_path": bundle_dir / BUNDLE_RULES_FILENAME,
            "script_path": bundle_dir / TEMPLATE_RENDER_SCRIPT_FILENAME,
        }

    def _load_template_context(self, style: str) -> str:
        path = self._resolve_template_path(style)
        if path is None:
            return ""
        parent = path.parent
        meta_path = parent / TEMPLATE_META_FILENAME
        params_path = parent / TEMPLATE_PARAMS_FILENAME
        parts: list[str] = []
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                parts.append("TemplateMeta=" + json.dumps(meta, ensure_ascii=False)[:4000])
            except Exception:
                pass
        if params_path.exists():
            try:
                params = json.loads(params_path.read_text(encoding="utf-8"))
                parts.append("TemplateParams=" + json.dumps(params, ensure_ascii=False)[:1200])
            except Exception:
                pass
        return "\n".join(parts).strip()

    def _load_template_context_for_task(self, task: Task) -> str:
        template_choice = (self._extract_task_setting(task.user_requirement, "TemplateChoice") or "").strip()
        if template_choice:
            bundle = self._resolve_template_bundle(template_choice)
            parts: list[str] = []
            meta_path = Path(bundle["meta_path"])
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    parts.append("TemplateMeta=" + json.dumps(meta, ensure_ascii=False)[:4000])
                except Exception:
                    pass
            rules_path = Path(bundle["rules_path"])
            if rules_path.exists():
                try:
                    rules = json.loads(rules_path.read_text(encoding="utf-8"))
                    parts.append("TemplateRules=" + json.dumps(rules, ensure_ascii=False)[:2000])
                except Exception:
                    pass
            return "\n".join(parts).strip()
        return self._load_template_context(task.style)

    def _normalize_style_key(self, value: str) -> str:
        return "".join((ch.lower() if ch.isalnum() else "_") for ch in (value or "")).strip("_")

    def _is_ppt_template_extract_request(self, requirement: str) -> bool:
        text = (requirement or "").lower()
        signals = [
            "提取模板",
            "模板提取",
            "保存模板",
            "提取ppt模板",
            "extract template",
            "save template",
            "extract ppt template",
        ]
        return any(sig in text for sig in signals)

    def _extract_template_name(self, requirement: str) -> Optional[str]:
        text = (requirement or "").strip()
        markers = ["模板名=", "template_name=", "template="]
        for line in text.splitlines():
            raw = line.strip()
            for marker in markers:
                if raw.lower().startswith(marker.lower()):
                    value = raw[len(marker) :].strip()
                    return value or None
        return None

    def list_ppt_templates(self) -> list[dict[str, Any]]:
        templates_dir = Path(__file__).resolve().parents[2] / "templates" / "ppt"
        if not templates_dir.exists():
            return []
        items: list[dict[str, Any]] = []
        for bundle_dir in templates_dir.iterdir():
            if not bundle_dir.is_dir():
                continue
            validation = validate_template_bundle(bundle_dir)
            if not bool(validation.get("ok", False)):
                continue
            template_name = bundle_dir.name
            pptx = bundle_dir / TEMPLATE_PPT_FILENAME
            meta_path = bundle_dir / TEMPLATE_META_FILENAME
            meta: dict[str, Any] = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            items.append(
                {
                    "name": template_name,
                    "style_value": template_name,
                    "file_path": str(pptx.resolve()),
                    "metadata_file": str(meta_path.resolve()) if meta_path.exists() else None,
                    "metadata": meta,
                    "is_valid": True,
                    "missing_files": [],
                    "schema_version": str(meta.get("schema_version", TEMPLATE_SCHEMA_VERSION)),
                }
            )
        items.sort(key=lambda x: str(x.get("name", "")))
        return items

    def list_templates(self, template_type: str) -> list[dict[str, Any]]:
        normalized = (template_type or "").strip().lower()
        if normalized == "ppt":
            return self.list_ppt_templates()
        templates_dir = Path(__file__).resolve().parents[2] / "templates" / normalized
        if not templates_dir.exists():
            return []
        items: list[dict[str, Any]] = []
        for f in templates_dir.glob("**/*"):
            if not f.is_file() or f.name == TEMPLATE_META_FILENAME:
                continue
            if f.suffix.lower() not in {".md", ".txt", ".docx", ".pptx"}:
                continue
            meta_path = f.parent / TEMPLATE_META_FILENAME
            meta: dict[str, Any] = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            name = str(meta.get("template_name", "")).strip() or f.stem
            items.append(
                {
                    "name": name,
                    "style_value": name,
                    "file_path": str(f.resolve()),
                    "metadata_file": str(meta_path.resolve()) if meta_path.exists() else None,
                    "metadata": meta,
                    "is_valid": True,
                    "missing_files": [],
                    "schema_version": str(meta.get("schema_version", "")),
                }
            )
        items.sort(key=lambda x: str(x.get("name", "")))
        return items

    def _run_text_task(
        self,
        task: Task,
        rerun: bool,
        require_llm: bool,
        llm_timeout_seconds: Optional[int],
        force_generic_direct: bool,
        capability_name: Optional[str],
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
                self._add_event(task_id, "planning", "no_source_file_forced_search_empty;fallback_to_requirement_context")
                parsed_text = clean_text_content(task.user_requirement or "")
            else:
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
            effective_payload = dict(payload)
            if skill_name == "find_skill":
                effective_payload.setdefault("task_type", task.task_type or "generic_task")
                effective_payload.setdefault("requirement", task.user_requirement)
                effective_payload.setdefault("provider_type", generation_decision.provider_type if generation_decision else "")
                effective_payload.setdefault("base_url", generation_decision.base_url if generation_decision else "")
                effective_payload.setdefault("model_name", generation_decision.model_name if generation_decision else "")
                effective_payload.setdefault("api_key", (default_cfg.api_key_encrypted if default_cfg and default_cfg.api_key_encrypted else ""))
            safe_payload = {
                k: ("<callable>" if callable(v) else v)
                for k, v in effective_payload.items()
            }
            started = time.perf_counter()
            try:
                output = skill_executor.execute(skill_name, effective_payload)
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
            "generic_task": GenericTaskAgent,
        }
        agent_cls = task_agent_map.get(task.task_type, GenericTaskAgent)
        task_agent = agent_cls()
        task_agent_name = agent_cls.__name__
        execute_kwargs = {
            "requirement": task.user_requirement,
            "parsed_text": parsed_text,
            "style": task.style,
            "language": task.language,
            "skill_execute_fn": skill_execute,
            "llm_generate_fn": llm_generate if generation_decision is not None else None,
        }
        if isinstance(task_agent, GenericTaskAgent):
            execute_kwargs["force_direct"] = force_generic_direct
            execute_kwargs["selected_capability_name"] = capability_name
        try:
            artifacts = task_agent.execute(**execute_kwargs)
        except Exception as exc:
            recovered = False
            if isinstance(task_agent, GenericTaskAgent) and capability_name:
                repaired = self._auto_repair_generic_capability_runtime(capability_name, str(exc))
                if repaired:
                    self._add_event(task_id, "generating", f"capability_runtime_repaired:{capability_name};retry_once")
                    try:
                        retry_kwargs = dict(execute_kwargs)
                        retry_kwargs["llm_generate_fn"] = llm_generate if generation_decision is not None else None
                        retry_kwargs["force_direct"] = force_generic_direct
                        retry_kwargs["selected_capability_name"] = capability_name
                        artifacts = task_agent.execute(**retry_kwargs)
                        recovered = True
                    except Exception as retry_exc:
                        self._add_event(task_id, "generating", f"capability_runtime_repair_retry_failed:{str(retry_exc)[:160]}")
                        if require_llm:
                            self.repos.tasks.update_status(task_id, "failed_generation")
                            self._add_agent_run(task_id, task_agent_name, "failed", str(retry_exc)[:300])
                            self._snapshot_excel()
                            raise ValueError(f"Generation failed (LLM required): {str(retry_exc)}") from retry_exc
                        self._add_event(task_id, "generating", f"text_task_agent_failed_fallback={str(retry_exc)[:160]}")
                        retry_fallback_kwargs = dict(execute_kwargs)
                        retry_fallback_kwargs["llm_generate_fn"] = None
                        retry_fallback_kwargs["force_direct"] = True
                        retry_fallback_kwargs["selected_capability_name"] = None
                        artifacts = task_agent.execute(**retry_fallback_kwargs)
                        recovered = True
                else:
                    self._add_event(task_id, "generating", f"capability_runtime_repair_unavailable:{capability_name}")
            if recovered:
                pass
            elif require_llm:
                self.repos.tasks.update_status(task_id, "failed_generation")
                self._add_agent_run(task_id, task_agent_name, "failed", str(exc)[:300])
                self._snapshot_excel()
                raise ValueError(f"Generation failed (LLM required): {str(exc)}") from exc
            else:
                self._add_event(task_id, "generating", f"text_task_agent_failed_fallback={str(exc)[:160]}")
                fallback_kwargs = dict(execute_kwargs)
                fallback_kwargs["llm_generate_fn"] = None
                if isinstance(task_agent, GenericTaskAgent):
                    fallback_kwargs["force_direct"] = force_generic_direct
                    fallback_kwargs["selected_capability_name"] = capability_name
                artifacts = task_agent.execute(**fallback_kwargs)

        if isinstance(task_agent, GenericTaskAgent) and artifacts.requires_capability_setup:
            suggested = (artifacts.suggested_capability_name or "new_capability").strip()
            self.repos.tasks.update_status(task_id, "failed_generation")
            self._add_event(task_id, "failed_generation", f"capability_setup_required:{suggested}")
            self._snapshot_excel()
            return {
                "task_id": task_id,
                "status": "capability_setup_required",
                "task_type": task.task_type,
                "requires_capability_setup": True,
                "suggested_capability_name": suggested,
                "setup_url": f"/capabilities/setup?taskId={task_id}&capability={suggested}",
            }

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
                        "data_analysis",
                        {
                            "excel_path": str(source_file.resolve()),
                            "report_docx_path": str(docx_path.resolve()),
                            "chart_png_path": str(chart_path.resolve()),
                            "requirement": task.user_requirement,
                            "llm_markdown": artifacts.markdown,
                            "language": task.language,
                            "target_column": self._extract_task_setting(task.user_requirement, "TargetColumn") or "cate",
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

    def bootstrap_generic_capability(self, task_id: str, capability_name: str, capability_spec: Optional[str] = None) -> dict[str, Any]:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        slug = self._normalize_capability_slug(capability_name)
        if not slug:
            raise ValueError("Invalid capability name.")
        spec_text = (capability_spec or task.user_requirement or "").strip()
        spec_signature = self._capability_signature(spec_text)

        skills_root = Path(__file__).resolve().parents[2] / "skills"
        base_skill_name = f"generic_{slug}_executor"
        base_skill_dir = skills_root / "custom" / base_skill_name
        manifest_name = "capability.meta.json"

        # Policy:
        # 1) same-name + same-content => reuse existing
        # 2) same-name + different-content => create distinguished capability name
        if base_skill_dir.exists():
            manifest_path = base_skill_dir / manifest_name
            if manifest_path.exists():
                try:
                    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            else:
                meta = {}
            existing_sig = str(meta.get("spec_signature", "")).strip()
            if existing_sig and existing_sig == spec_signature:
                self._add_event(task_id, "planning", f"capability_reused:{slug};skill={base_skill_name}")
                self._snapshot_excel()
                return {
                    "task_id": task_id,
                    "capability_name": slug,
                    "skill_name": base_skill_name,
                    "skill_dir": str(base_skill_dir.resolve()),
                    "agent_path": str((Path(__file__).resolve().parents[2] / "agents" / "task_agents" / f"{slug}_task_agent.py").resolve()),
                    "runtime_check_ok": True,
                    "reused_existing": True,
                    "reason": "same_name_same_content",
                }
            short = spec_signature[:8]
            slug = f"{slug}_{short}"

        skill_name = f"generic_{slug}_executor"
        skill_dir = skills_root / "custom" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_md = (
            "---\n"
            f"name: {skill_name}\n"
            "description: Executes a user-bootstrapped generic capability.\n"
            "domain: custom\n"
            "version: 1.0.0\n"
            "owner: backend\n"
            "status: active\n"
            "task_types:\n"
            "  - generic_task\n"
            "stages:\n"
            "  - generating\n"
            "runtime_handler: runtime.py:run\n"
            "trigger_keywords:\n"
            f"  - {slug}\n"
            "---\n\n"
            f"# {skill_name}\n\n"
            "## When to Use This Skill\n"
            "Use this skill when the user asks to execute the custom capability.\n\n"
            "## What This Skill Does\n"
            "Generates structured markdown output for the custom capability task.\n\n"
            "## How to Execute\n"
            "Call via `SkillExecutor.execute` with requirement/context payload.\n\n"
            "## Example\n"
            "Input: requirement/context\n"
            "Output: markdown text\n\n"
            "## Fallback\n"
            "If execution fails, orchestration should fall back to generic direct generation.\n"
        )
        runtime_py = (
            "from __future__ import annotations\n\n"
            "def run(payload: dict) -> dict:\n"
            "    requirement = str(payload.get('requirement', '')).strip()\n"
            "    context = str(payload.get('context', '')).strip()\n"
            f"    title = '{slug.replace('_', ' ').title()}'\n"
            "    body = context if context else requirement\n"
            "    markdown = f\"# {title}\\n\\n## Summary\\n{body[:3500]}\\n\"\n"
            "    return {'passed': True, 'markdown': markdown, 'capability': title}\n"
        )
        skill_md_path = skill_dir / "SKILL.md"
        runtime_py_path = skill_dir / "runtime.py"
        manifest_path = skill_dir / manifest_name
        skill_md_path.write_text(skill_md, encoding="utf-8")
        runtime_py_path.write_text(runtime_py, encoding="utf-8")
        manifest_path.write_text(
            json.dumps(
                {
                    "capability_name": slug,
                    "skill_name": skill_name,
                    "spec_signature": spec_signature,
                    "source_task_id": task_id,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        agent_path = Path(__file__).resolve().parents[2] / "agents" / "task_agents" / f"{slug}_task_agent.py"
        agent_code = (
            "from __future__ import annotations\n\n"
            "from dataclasses import dataclass\n"
            "from typing import Any, Callable, Optional\n\n"
            "@dataclass\n"
            "class CapabilityTaskArtifacts:\n"
            "    markdown: str\n"
            "    review_passed: bool\n"
            "    review_issues: list[str]\n"
            "    plan_summary: str\n"
            "    section_count: int\n\n"
            "class CapabilityTaskAgent:\n"
            "    def execute(\n"
            "        self,\n"
            "        requirement: str,\n"
            "        parsed_text: str,\n"
            "        style: str,\n"
            "        language: str,\n"
            "        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],\n"
            "        llm_generate_fn: Optional[Callable[[str], str]] = None,\n"
            "    ) -> CapabilityTaskArtifacts:\n"
            f"        result = skill_execute_fn('{skill_name}', {{'requirement': requirement, 'context': parsed_text, 'style': style, 'language': language}})\n"
            "        markdown = str(result.get('markdown', '')).strip() + '\\n'\n"
            "        return CapabilityTaskArtifacts(markdown=markdown, review_passed=True, review_issues=[], plan_summary='custom capability task agent', section_count=max(1, markdown.count('\\n## ')))\n"
        )
        agent_path.write_text(agent_code, encoding="utf-8")

        compile(runtime_py, str(runtime_py_path), "exec")
        compile(agent_code, str(agent_path), "exec")

        check = SkillExecutor.create_default().execute(
            skill_name,
            {"requirement": task.user_requirement, "context": task.user_requirement},
        )
        self._add_event(task_id, "planning", f"capability_bootstrapped:{slug};skill={skill_name}")
        self._snapshot_excel()
        return {
            "task_id": task_id,
            "capability_name": slug,
            "skill_name": skill_name,
            "skill_dir": str(skill_dir.resolve()),
            "agent_path": str(agent_path.resolve()),
            "runtime_check_ok": isinstance(check, dict),
            "reused_existing": False,
            "reason": "created_new_or_distinguished",
        }

    def _run_template_generation_task(self, task: Task, rerun: bool = False) -> dict[str, Any]:
        task_id = task.task_id
        if rerun:
            self._add_agent_run(task_id, "TemplateGenerationTaskAgent", "running", "manual rerun requested")
        files = self.repos.files.list_by_task(task_id)
        source_file_path = ""
        parsed_text = ""
        if files:
            file_row = files[0]
            source_file_path = file_row.file_path
            if file_row.parse_status != "success":
                try:
                    file_row = self.parse_task_file(task_id, force=False)
                except Exception:
                    file_row = files[0]
            if file_row.parsed_text_path:
                p = Path(file_row.parsed_text_path)
                if p.exists():
                    parsed_text = clean_text_content(p.read_text(encoding="utf-8"))

        self.repos.tasks.update_status(task_id, "planning")
        self._add_event(task_id, "planning", "start template generation planning")
        self.repos.tasks.update_status(task_id, "generating")

        skill_executor = SkillExecutor.create_default()
        planning_decision = ModelRouter(self.repos).pick(task.user_id, "planning")
        default_cfg = self.repos.providers.get_default_for_user(task.user_id)

        def skill_execute(skill_name: str, payload: dict[str, Any]) -> dict[str, Any]:
            effective_payload = dict(payload)
            if skill_name == "find_skill":
                effective_payload.setdefault("task_type", "template_generation")
                effective_payload.setdefault("requirement", task.user_requirement)
                effective_payload.setdefault("provider_type", planning_decision.provider_type or "")
                effective_payload.setdefault("base_url", planning_decision.base_url or "")
                effective_payload.setdefault("model_name", planning_decision.model_name or "")
                effective_payload.setdefault("api_key", (default_cfg.api_key_encrypted if default_cfg and default_cfg.api_key_encrypted else ""))
            started = time.perf_counter()
            output = skill_executor.execute(skill_name, effective_payload)
            self._add_skill_call(
                task_id,
                skill_name,
                effective_payload,
                output,
                max(1, int((time.perf_counter() - started) * 1000)),
            )
            return output

        templates_root = Path(__file__).resolve().parents[2] / "templates"
        agent = TemplateGenerationTaskAgent()
        result = agent.execute(
            requirement=task.user_requirement,
            parsed_text=parsed_text,
            source_file_path=source_file_path,
            templates_root=str(templates_root.resolve()),
            skill_execute_fn=skill_execute,
        )
        self._add_agent_run(task_id, "TemplateGenerationTaskAgent", "completed", f"type={result.template_type};name={result.template_name}")
        if result.status == "requires_user_completion":
            self.repos.tasks.update_status(task_id, "requires_user_completion")
            recovery_payload = {
                "task_id": task_id,
                "template_type": result.template_type,
                "template_name": result.template_name,
                "template_dir": result.template_dir,
                "template_file": result.template_file,
                "metadata_file": result.metadata_file,
                "params_file": result.params_file,
                "render_script": result.render_script,
                "missing_fields": result.missing_fields,
                "suggested_values": result.suggested_values,
            }
            self._write_template_recovery_payload(task_id, recovery_payload)
            self._add_event(task_id, "requires_user_completion", f"template_generation_requires_user_completion:{json.dumps(recovery_payload, ensure_ascii=False)}")
            self._snapshot_excel()
            return {"task_id": task_id, "status": "requires_user_completion", **recovery_payload}

        self.repos.tasks.update_status(task_id, "exporting")
        output_path = Path(result.template_file)
        suffix = output_path.suffix.lower()
        output_file_type = "md"
        if suffix == ".pptx":
            output_file_type = "pptx"
        elif suffix == ".json":
            output_file_type = "json"
        elif suffix == ".txt":
            output_file_type = "txt"
        elif suffix == ".docx":
            output_file_type = "docx"

        latest = self.repos.outputs.get_latest(task_id)
        next_version = 1 if latest is None else latest.version + 1
        out = OutputFile(
            output_id=new_id("output"),
            task_id=task_id,
            version=next_version,
            file_type=output_file_type,  # type: ignore[arg-type]
            file_path=str(output_path.resolve()),
        )
        self.repos.outputs.create(out)
        self.repos.tasks.update_status(task_id, "completed")
        self._add_event(task_id, "completed", f"template_generated type={result.template_type};name={result.template_name}")
        self._clear_template_recovery_payload(task_id)
        self._snapshot_excel()
        return {
            "task_id": task_id,
            "status": "completed",
            "task_type": task.task_type,
            "template_type": result.template_type,
            "template_name": result.template_name,
            "template_dir": result.template_dir,
            "template_file": result.template_file,
            "metadata_file": result.metadata_file,
            "params_file": result.params_file,
            "render_script": result.render_script,
            "output_version": next_version,
            "output_path": str(output_path.resolve()),
        }

    def get_template_generation_recovery(self, task_id: str) -> dict[str, Any]:
        task = self.repos.tasks.get_by_id(task_id)
        if task is None:
            raise ValueError("Task not found.")
        if task.task_type not in {"template_generation", "ppt"}:
            raise ValueError("Task is not a template generation task.")
        data = self._read_template_recovery_payload(task_id)
        if not data:
            return {"task_id": task_id, "has_recovery": False}
        return {"task_id": task_id, "has_recovery": True, **data}

    def resume_template_generation_recovery(self, task_id: str, resume_token: str, user_filled_fields: dict[str, str]) -> dict[str, Any]:
        recovery = self._read_template_recovery_payload(task_id)
        if not recovery:
            raise ValueError("No recovery payload found for this task.")
        expected_token = str(recovery.get("resume_token", "")).strip()
        if not expected_token or resume_token.strip() != expected_token:
            raise ValueError("Invalid resume token.")
        resume_attempt = int(recovery.get("resume_attempt", 0) or 0) + 1
        recovery["resume_attempt"] = resume_attempt
        template_dir = Path(str(recovery.get("template_dir", "")))
        meta_path = Path(str(recovery.get("metadata_file", ""))) if recovery.get("metadata_file") else (template_dir / BUNDLE_META_FILENAME)
        rules_path = Path(str(recovery.get("rules_file", ""))) if recovery.get("rules_file") else (template_dir / BUNDLE_RULES_FILENAME)
        if not meta_path.exists():
            raise ValueError("Recovery metadata file not found.")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        updates = user_filled_fields or {}
        for key, value in updates.items():
            if not str(value).strip():
                continue
            if str(key).startswith("rules."):
                if not rules_path.exists():
                    rules_path.write_text(json.dumps({"schema_version": "v1", "rules": []}, ensure_ascii=False, indent=2), encoding="utf-8")
                rules = json.loads(rules_path.read_text(encoding="utf-8"))
                rules_key = key[len("rules.") :]
                rules_value: Any = value
                if rules_key == "rules":
                    try:
                        parsed = json.loads(str(value))
                        if isinstance(parsed, list):
                            rules_value = parsed
                    except Exception:
                        rules_value = [{"name": "text_overflow", "action": "shrink"}]
                self._set_nested_key(rules, rules_key, rules_value)
                rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
            else:
                self._set_nested_key(meta, key, value)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        validation = validate_template_bundle(template_dir)
        self._add_event(
            task_id,
            "planning",
            (
                f"template_bundle_validation template_name={recovery.get('template_name', template_dir.name)};"
                f"ok={bool(validation.get('ok', False))};"
                f"missing={len(validation.get('missing_files', []))};"
                f"errors={len(validation.get('errors', []))};"
                f"resume_attempt={resume_attempt}"
            ),
        )
        if not bool(validation.get("ok", False)):
            recovery["missing_items"] = validation.get("missing_files", [])
            recovery["validation_errors"] = validation.get("errors", [])
            self._write_template_recovery_payload(task_id, recovery)
            task = self.repos.tasks.update_status(task_id, "requires_user_completion")
            self._add_event(
                task_id,
                "requires_user_completion",
                (
                    "template_generation_resume_validation_failed;"
                    f"template_name={recovery.get('template_name', template_dir.name)};"
                    f"missing_items={len(recovery.get('missing_items', []))};"
                    f"validation_errors={len(recovery.get('validation_errors', []))};"
                    f"resume_attempt={resume_attempt}"
                ),
            )
            self._snapshot_excel()
            return {
                "task_id": task_id,
                "status": task.status if task else "requires_user_completion",
                "has_recovery": True,
                **recovery,
            }
        rules_count = 0
        if rules_path.exists():
            try:
                rules_payload = json.loads(rules_path.read_text(encoding="utf-8"))
                maybe_rules = rules_payload.get("rules", [])
                if isinstance(maybe_rules, list):
                    rules_count = len(maybe_rules)
            except Exception:
                rules_count = 0
        self._clear_template_recovery_payload(task_id)
        task = self.repos.tasks.update_status(task_id, "completed")
        self._add_event(
            task_id,
            "completed",
            (
                "template_generation_resume_completed;"
                f"template_name={recovery.get('template_name', template_dir.name)};"
                f"resume_attempt={resume_attempt};"
                f"applied_rules={rules_count}"
            ),
        )
        self._snapshot_excel()
        return {"task_id": task_id, "status": task.status if task else "completed"}

    def complete_template_generation_recovery(self, task_id: str, fields: dict[str, str]) -> dict[str, Any]:
        # Backward-compatible alias for previous frontend route.
        recovery = self._read_template_recovery_payload(task_id)
        resume_token = str(recovery.get("resume_token", "")).strip()
        if not resume_token:
            raise ValueError("No recovery resume token found.")
        return self.resume_template_generation_recovery(task_id, resume_token, fields)

    def _template_recovery_file(self, task_id: str) -> Path:
        folder = self.storage_root / "outputs" / task_id
        folder.mkdir(parents=True, exist_ok=True)
        return folder / "template.recovery.json"

    def _write_template_recovery_payload(self, task_id: str, payload: dict[str, Any]) -> None:
        path = self._template_recovery_file(task_id)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_template_recovery_payload(self, task_id: str) -> dict[str, Any]:
        path = self._template_recovery_file(task_id)
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _clear_template_recovery_payload(self, task_id: str) -> None:
        path = self._template_recovery_file(task_id)
        if path.exists():
            path.unlink()

    def _set_nested_key(self, data: dict[str, Any], key: str, value: Any) -> None:
        parts = [p for p in str(key).split(".") if p]
        if not parts:
            return
        curr: Any = data
        for part in parts[:-1]:
            if not isinstance(curr, dict):
                return
            if part not in curr or not isinstance(curr[part], dict):
                curr[part] = {}
            curr = curr[part]
        if isinstance(curr, dict):
            curr[parts[-1]] = value

    def _nested_key_has_value(self, data: dict[str, Any], key: str) -> bool:
        parts = [p for p in str(key).split(".") if p]
        curr: Any = data
        for part in parts:
            if not isinstance(curr, dict) or part not in curr:
                return False
            curr = curr[part]
        if curr is None:
            return False
        if isinstance(curr, str):
            return bool(curr.strip())
        if isinstance(curr, (list, dict)):
            return len(curr) > 0
        return True

    def _normalize_capability_slug(self, value: str) -> str:
        raw = (value or "").strip().lower()
        slug = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
        return slug[:48]

    def _capability_signature(self, content: str) -> str:
        normalized = re.sub(r"\s+", " ", (content or "").strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _auto_repair_generic_capability_runtime(self, capability_name: str, error_message: str) -> bool:
        slug = self._normalize_capability_slug(capability_name)
        if not slug:
            return False
        skill_name = f"generic_{slug}_executor"
        skill_dir = Path(__file__).resolve().parents[2] / "skills" / "custom" / skill_name
        runtime_path = skill_dir / "runtime.py"
        if not runtime_path.exists():
            return False
        safe_error = (error_message or "").replace("\n", " ").replace("\r", " ").strip()[:240]
        repaired_runtime = (
            "from __future__ import annotations\n\n"
            "def run(payload: dict) -> dict:\n"
            "    requirement = str(payload.get('requirement', '')).strip()\n"
            "    context = str(payload.get('context', '')).strip()\n"
            f"    title = '{slug.replace('_', ' ').title()}'\n"
            "    body = context if context else requirement\n"
            "    # auto-repaired runtime fallback for generic capability execution\n"
            "    markdown = (\n"
            "        f\"# {title}\\n\\n\"\n"
            "        f\"## Summary\\n{body[:3000]}\\n\\n\"\n"
            f"        f\"## Runtime Repair Note\\nAuto-repaired from previous error: {safe_error}\\n\"\n"
            "    )\n"
            "    return {'passed': True, 'markdown': markdown, 'capability': title, 'auto_repaired': True}\n"
        )
        try:
            compile(repaired_runtime, str(runtime_path), "exec")
            runtime_path.write_text(repaired_runtime, encoding="utf-8")
        except Exception:
            return False
        return True

    def _force_search_context(
        self,
        *,
        task_id: str,
        requirement: str,
        vector_index_service: VectorIndexService,
        max_results: int = 4,
    ) -> tuple[list[dict[str, Any]], str]:
        skill_executor = SkillExecutor.create_default()
        base_query = requirement.strip()
        if not base_query:
            base_query = "latest information overview"
        query_candidates = [base_query, f"{base_query} latest overview", f"{base_query} background key points"]
        items: list[dict[str, Any]] = []
        for query in query_candidates:
            started = time.perf_counter()
            try:
                result = skill_executor.execute("knowledge_search", {"query": query, "max_results": max_results})
                current = result.get("items", []) if isinstance(result, dict) else []
                self._add_skill_call(
                    task_id,
                    "knowledge_search",
                    {"query": query, "max_results": max_results, "forced": True},
                    {"count": len(current)},
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                if isinstance(current, list) and current:
                    items = current
                    break
            except Exception as exc:
                self._add_skill_call(
                    task_id,
                    "knowledge_search_failed",
                    {"query": query, "max_results": max_results, "forced": True},
                    {"error": str(exc)[:300]},
                    max(1, int((time.perf_counter() - started) * 1000)),
                )
                continue
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
                "user_settings": self.repos.user_settings.store.read_all(),
            }
        )

    def get_user_max_parallel_tasks(self, user_id: str) -> int:
        settings = self.repos.user_settings.get_by_user(user_id)
        if settings is None:
            return 10
        return max(1, min(10, int(settings.max_parallel_tasks)))

    def set_user_max_parallel_tasks(self, user_id: str, max_parallel_tasks: int) -> int:
        value = max(1, min(10, int(max_parallel_tasks)))
        current = self.repos.user_settings.get_by_user(user_id)
        payload = (
            current.model_copy(update={"max_parallel_tasks": value, "updated_at": _utc_now()})
            if current is not None
            else UserSettings(user_id=user_id, max_parallel_tasks=value, updated_at=_utc_now())
        )
        self.repos.user_settings.upsert(payload)
        self._snapshot_excel()
        return value

    def list_running_tasks_by_user(self, user_id: str) -> list[Task]:
        tasks = self.repos.tasks.list_by_user(user_id)
        running: list[Task] = []
        now = _utc_now()
        for t in tasks:
            if t.status not in self.RUNNING_STATUSES:
                continue
            age_seconds = (now - t.updated_at).total_seconds()
            if age_seconds > self.RUNNING_STALE_TIMEOUT_SECONDS:
                self.repos.tasks.update_status(t.task_id, "failed_generation")
                self._add_event(t.task_id, "failed_generation", "stale_running_task_auto_closed")
                continue
            running.append(t)
        if running:
            running.sort(key=lambda x: x.updated_at, reverse=True)
        return running

    def _ensure_parallel_capacity(self, user_id: str, exclude_task_id: Optional[str] = None) -> None:
        limit = self.get_user_max_parallel_tasks(user_id)
        running = [t for t in self.list_running_tasks_by_user(user_id) if t.status in self.CAPACITY_COUNT_STATUSES]
        if exclude_task_id:
            running = [t for t in running if t.task_id != exclude_task_id]
        if len(running) >= limit:
            raise ValueError(f"Running task limit reached ({len(running)}/{limit}).")

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


def recover_interrupted_running_tasks(repos: RepositoryBundle) -> int:
    """
    On backend restart, previously in-flight tasks cannot continue (no resumable worker runtime).
    Convert stale running-like statuses to failed_generation so UI won't keep showing zombie tasks.
    """
    tasks_repo = repos.tasks
    if not hasattr(tasks_repo, "store"):
        return 0

    rows = tasks_repo.store.read_all()
    now = _utc_now().isoformat()
    interrupted_statuses = TaskService.RUNNING_STATUSES
    changed = 0
    affected_task_ids: list[str] = []

    for row in rows:
        status = str(row.get("status", "")).strip()
        if status in interrupted_statuses:
            row["status"] = "failed_generation"
            row["updated_at"] = now
            changed += 1
            task_id = str(row.get("task_id", "")).strip()
            if task_id:
                affected_task_ids.append(task_id)

    if changed == 0:
        return 0

    tasks_repo.store.write_all(rows)
    for task_id in affected_task_ids:
        repos.task_events.create(
            TaskEvent(
                event_id=new_id("evt"),
                task_id=task_id,
                stage="failed_generation",
                message="interrupted_task_auto_closed_on_backend_restart",
            )
        )
    return changed

