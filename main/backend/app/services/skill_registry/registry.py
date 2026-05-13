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
        for level1 in self.skill_root.iterdir():
            if not level1.is_dir():
                continue
            # Layout A: skills/<skill_name>/SKILL.md
            direct_skill_file = level1 / "SKILL.md"
            if direct_skill_file.exists() and direct_skill_file.is_file():
                parsed = self._parse_frontmatter(direct_skill_file)
                skill_name = str(parsed.get("name", "")).strip() or level1.name
                domain = str(parsed.get("domain", "")).strip() or "common"
                metas.append(
                    SkillMeta(
                        name=skill_name,
                        domain=domain,
                        path=str(direct_skill_file.resolve()),
                        skill_dir=str(level1.resolve()),
                        runtime_handler=parsed.get("runtime_handler"),
                        trigger_keywords=parsed.get("trigger_keywords"),
                        task_types=parsed.get("task_types"),
                        stages=parsed.get("stages"),
                    )
                )
                continue
            # Layout B: skills/<domain>/<skill_name>/SKILL.md
            for skill_dir in level1.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists() or not skill_file.is_file():
                    continue
                parsed = self._parse_frontmatter(skill_file)
                skill_name = str(parsed.get("name", "")).strip() or skill_dir.name
                domain = str(parsed.get("domain", "")).strip() or level1.name
                metas.append(
                    SkillMeta(
                        name=skill_name,
                        domain=domain,
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
        # Read metadata frontmatter only. Do not load/parse full skill body.
        try:
            with skill_file.open("r", encoding="utf-8") as f:
                lines: list[str] = []
                first = f.readline()
                if not first:
                    return {}
                lines.append(first.rstrip("\n"))
                if lines[0].lstrip("\ufeff").strip() != "---":
                    return {}
                for raw in f:
                    lines.append(raw.rstrip("\n"))
                    if raw.strip() == "---":
                        break
        except Exception:
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
