from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CodeDocPlan:
    summary: str
    readme_sections: list[str]
    api_sections: list[str]


@dataclass
class CodeDocDraft:
    markdown: str
    section_count: int


@dataclass
class CodeDocReview:
    passed: bool
    issues: list[str]
    normalized_markdown: str
