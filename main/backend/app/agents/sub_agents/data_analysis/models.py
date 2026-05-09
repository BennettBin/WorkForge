from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DataAnalysisPlan:
    summary: str
    clean_steps: list[str]
    chart_plan: list[str]


@dataclass
class DataAnalysisDraft:
    markdown: str
    section_count: int


@dataclass
class DataAnalysisReview:
    passed: bool
    issues: list[str]
    normalized_markdown: str
