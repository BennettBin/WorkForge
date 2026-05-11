from __future__ import annotations

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from app.services.skill_registry import SkillRegistry


class SkillExecutionError(Exception):
    pass


@dataclass
class SkillExecutor:
    registry: SkillRegistry

    @classmethod
    def create_default(cls) -> "SkillExecutor":
        skills_root = Path(__file__).resolve().parents[2] / "skills"
        return cls(registry=SkillRegistry(skills_root))

    def execute(self, skill_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        name = (skill_name or "").strip().lower()
        meta = next((row for row in self.registry.list_all() if row.name.lower() == name), None)
        if meta is None:
            raise SkillExecutionError(f"Unsupported skill execution: {skill_name}")
        runtime_handler = str(meta.runtime_handler or "").strip()
        if not runtime_handler:
            raise SkillExecutionError(f"Skill runtime handler is missing: {skill_name}")
        return self._execute_runtime(meta.skill_dir, runtime_handler, payload)

    def _execute_runtime(self, skill_dir: str, runtime_handler: str, payload: dict[str, Any]) -> dict[str, Any]:
        if ":" not in runtime_handler:
            raise SkillExecutionError(f"Invalid runtime handler: {runtime_handler}")
        relative_file, callable_name = runtime_handler.split(":", 1)
        file_path = (Path(skill_dir) / relative_file).resolve()
        if not file_path.exists() or not file_path.is_file():
            raise SkillExecutionError(f"Skill runtime file not found: {file_path}")
        spec = spec_from_file_location(f"workforge_skill_{file_path.stem}", file_path)
        if spec is None or spec.loader is None:
            raise SkillExecutionError(f"Cannot load skill runtime module: {file_path}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        func = getattr(module, callable_name.strip(), None)
        if not callable(func):
            raise SkillExecutionError(f"Skill runtime callable not found: {runtime_handler}")
        result = func(payload)
        if not isinstance(result, dict):
            raise SkillExecutionError(f"Skill runtime output must be dict: {runtime_handler}")
        return result
