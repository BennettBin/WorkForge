from __future__ import annotations

import json


# Called by: main/backend/app/agents/sub_agents/outline_agent.py
# Purpose: Build the LLM prompt for PPT outline generation.
def build_outline_prompt(
    *,
    pages: int,
    requirement: str,
    parsed_text: str,
    no_source_file: bool,
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
) -> str:
    source_hint = (
        "No source file is provided. You must search and organize content."
        if no_source_file
        else "Use source content first."
    )
    outline_json = json.dumps(outline_payload, ensure_ascii=False)
    return (
        "Generate slide content as JSON array with fields: "
        "index, kind, title, bullets, notes, image_placeholders.\n"
        "image_placeholders is an array of {label, source}.\n"
        f"Source strategy: {source_hint}\n"
        f"Outline:\n{outline_json}\n"
        f"Input text summary:\n{parsed_text[:4000]}\n"
        "Output JSON only."
    )
