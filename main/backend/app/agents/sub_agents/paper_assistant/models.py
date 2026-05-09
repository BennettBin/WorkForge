from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaperPlan:
    summary: str
    sections: list[str]
    review_checks: list[str]


@dataclass
class PaperDraft:
    markdown: str
    section_count: int


@dataclass
class PaperReview:
    passed: bool
    issues: list[str]
    normalized_markdown: str
