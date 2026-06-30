from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SkillMeta:
    name: str
    path: str
    skill_dir: str
    runtime_handler: Optional[str] = None


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
                metas.append(
                    SkillMeta(
                        name=skill_name,
                        path=str(direct_skill_file.resolve()),
                        skill_dir=str(level1.resolve()),
                        runtime_handler=parsed.get("runtime_handler"),
                    )
                )
                continue
            # Legacy nested layout: skills/<group>/<skill_name>/SKILL.md.
            # Groups are not access-control domains; all skills are public.
            for skill_dir in level1.iterdir():
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
                        path=str(skill_file.resolve()),
                        skill_dir=str(skill_dir.resolve()),
                        runtime_handler=parsed.get("runtime_handler"),
                    )
                )
        return metas

    def resolve_for(self, task_type: str, stage: str) -> list[SkillMeta]:
        return self.list_all()

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
