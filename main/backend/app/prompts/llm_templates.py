from __future__ import annotations

import json
from typing import Any


def _template_constraints_block(template_constraints: dict[str, Any] | None) -> str:
    if not isinstance(template_constraints, dict) or not template_constraints:
        return ""
    compact = json.dumps(template_constraints, ensure_ascii=False)[:5000]
    return (
        "Template constraints:\n"
        f"{compact}\n"
        "Respect the supplied layout_map, slide_contracts, text_slots, text limits, image slot intent, and overflow rules. "
        "When slide_contracts are present, every generated slide must use a compatible kind and provide exactly those slot ids in texts.\n"
    )


# Called by: main/backend/app/agents/sub_agents/outline_agent.py
# Purpose: Build the LLM prompt for PPT outline generation.
def build_outline_prompt(
    *,
    pages: int,
    requirement: str,
    parsed_text: str,
    no_source_file: bool,
    template_constraints: dict[str, Any] | None = None,
) -> str:
    source_hint = (
        "No source file is provided. You must proactively search and organize reliable content."
        if no_source_file
        else "Prioritize source-file content."
    )
    return (
        "Generate a PPT outline as JSON array with fields: "
        "index, kind(cover/content/summary), title, goals.\n"
        f"Total pages: {pages}. First page must be cover. Last page must be summary.\n"
        "Do not change the user topic/entity. Keep every slide tightly aligned with user requirement.\n"
        f"{_template_constraints_block(template_constraints)}"
        f"Source strategy: {source_hint}\n"
        f"User requirement: {requirement}\n"
        f"Input text summary:\n{parsed_text[:4000]}\n"
        "Output JSON only."
    )


# Called by: main/backend/app/agents/sub_agents/content_agent.py
# Purpose: Build the LLM prompt for per-slide content generation.
def build_content_prompt(
    *,
    outline_payload: list[dict],
    parsed_text: str,
    no_source_file: bool,
    template_constraints: dict[str, Any] | None = None,
) -> str:
    source_hint = (
        "No source file is provided. You must search and organize content."
        if no_source_file
        else "Use source content first."
    )
    outline_json = json.dumps(outline_payload, ensure_ascii=False)
    return (
        "Generate slide content as JSON array with fields: "
        "index, kind, title, bullets, texts, notes, image_placeholders.\n"
        "texts must be an object keyed by the exact slot ids from Template constraints.slide_contracts for that slide kind. "
        "Use Template constraints.text_contract/slide_slot_details to decide what each text box should contain "
        "(for example page title, main content, remarks). Do not invent slot ids. Fill every required slot. Keep bullets for legacy compatibility.\n"
        "image_placeholders is an array of {label, source}; for every slide, propose 1-2 concrete images that should be inserted later. "
        "Do not reuse or describe the template's existing decorative images; describe the topic-specific image the user should add.\n"
        "Do not change the user topic/entity. Keep all titles and bullets on the requested topic.\n"
        f"{_template_constraints_block(template_constraints)}"
        f"Source strategy: {source_hint}\n"
        f"Outline:\n{outline_json}\n"
        f"Input text summary:\n{parsed_text[:4000]}\n"
        "Output JSON only."
    )
