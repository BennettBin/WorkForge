from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReportPlan:
    summary: str
    sections: list[str]


@dataclass
class ReportDraft:
    markdown: str
    section_count: int


@dataclass
class ReportReview:
    passed: bool
    issues: list[str]
    normalized_markdown: str
