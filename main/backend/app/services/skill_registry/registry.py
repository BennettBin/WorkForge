from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SkillMeta:
    name: str
    domain: str
    path: str
    skill_dir: str
    runtime_handler: Optional[str] = None
    trigger_keywords: Optional[list[str]] = None
    task_types: Optional[list[str]] = None
    stages: Optional[list[str]] = None


class SkillRegistry:
    def __init__(self, skill_root: Path):
        self.skill_root = skill_root

    def list_all(self) -> list[SkillMeta]:
        metas: list[SkillMeta] = []
        if not self.skill_root.exists():
            return metas
        for domain_dir in self.skill_root.iterdir():
            if not domain_dir.is_dir():
                continue
            for skill_dir in domain_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists() or not skill_file.is_file():
                    continue
                parsed = self._parse_frontmatter(skill_file)
                skill_name = str(parsed.get("name", "")).strip() or skill_dir.name
                metas.append(
                    SkillMeta(
                        name=skill_name,
                        domain=domain_dir.name,
                        path=str(skill_file.resolve()),
                        skill_dir=str(skill_dir.resolve()),
                        runtime_handler=parsed.get("runtime_handler"),
                        trigger_keywords=parsed.get("trigger_keywords"),
                        task_types=parsed.get("task_types"),
                        stages=parsed.get("stages"),
                    )
                )
        return metas

    def resolve_for(self, task_type: str, stage: str) -> list[SkillMeta]:
        all_skills = self.list_all()
        # Include common skills and task-specific domain skills.
        domains = {"common"}
        normalized_task_type = (task_type or "").strip().lower()
        if normalized_task_type == "ppt":
            domains.add("ppt")
        elif normalized_task_type in {"report", "wechat_post", "data_analysis", "code_doc", "paper_assistant"}:
            domains.add(normalized_task_type)
        selected: list[SkillMeta] = []
        for skill in all_skills:
            if skill.domain not in domains:
                continue
            skill_task_types = [str(x).strip().lower() for x in (skill.task_types or []) if str(x).strip()]
            if skill_task_types and ("all" not in skill_task_types) and (normalized_task_type not in skill_task_types):
                continue
            selected.append(skill)
        return selected

    def _parse_frontmatter(self, skill_file: Path) -> dict:
        try:
            text = skill_file.read_text(encoding="utf-8")
        except Exception:
            return {}
        lines = text.splitlines()
        if lines:
            lines[0] = lines[0].lstrip("\ufeff")
        if not lines or lines[0].strip() != "---":
            return {}
        i = 1
        data: dict = {}
        current_key = None
        while i < len(lines):
            raw = lines[i].rstrip()
            if raw.strip() == "---":
                break
            if raw.strip().startswith("- ") and current_key:
                data.setdefault(current_key, []).append(raw.strip()[2:].strip())
            elif ":" in raw:
                key, value = raw.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value:
                    data[key] = value
                    current_key = None
                else:
                    data[key] = []
                    current_key = key
            i += 1
        return data
