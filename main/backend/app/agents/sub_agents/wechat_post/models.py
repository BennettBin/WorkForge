from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WechatPostPlan:
    title_candidates: list[str]
    summary: str


@dataclass
class WechatPostDraft:
    markdown: str
    section_count: int


@dataclass
class WechatPostReview:
    passed: bool
    issues: list[str]
    normalized_markdown: str
