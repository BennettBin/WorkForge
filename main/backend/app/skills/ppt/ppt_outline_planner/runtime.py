from __future__ import annotations

import json

from app.prompts import OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS, build_outline_prompt


def _parse_llm_outline(raw: str, pages: int) -> list[dict]:
    text = (raw or "").strip()
    if not text:
        return []
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        rows = json.loads(text[start : end + 1])
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    items: list[dict] = []
    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind", "content")).strip() or "content"
        title = str(row.get("title", f"Content {i}")).strip() or f"Content {i}"
        goals_raw = row.get("goals", [])
        goals = [str(x).strip() for x in goals_raw if str(x).strip()] if isinstance(goals_raw, list) else [title]
        items.append({"index": i, "kind": kind, "title": title, "goals": goals[:5]})
    if len(items) != pages:
        return []
    items[0]["kind"] = "cover"
    items[-1]["kind"] = "summary"
    return items


def run(payload: dict) -> dict:
    parsed_text = str(payload.get("parsed_text", ""))
    requested_pages = int(payload.get("requested_pages", 10) or 10)
    requirement = str(payload.get("requirement", ""))
    retrieve_context_fn = payload.get("retrieve_context_fn")
    llm_generate_fn = payload.get("llm_generate_fn")
    no_source_file = bool(payload.get("no_source_file", False))
    pages = max(3, min(30, requested_pages))

    if callable(llm_generate_fn):
        prompt = build_outline_prompt(pages=pages, requirement=requirement, parsed_text=parsed_text, no_source_file=no_source_file)
        try:
            llm_items = _parse_llm_outline(llm_generate_fn(prompt), pages)
        except Exception:
            llm_items = []
        if llm_items:
            return {"outline": llm_items}

    lines = [line.strip() for line in parsed_text.splitlines() if line.strip()]
    snippets = lines[: max(8, pages * 2)]
    if no_source_file and not snippets:
        snippets = OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS
    items: list[dict] = [{"index": 1, "kind": "cover", "title": "Presentation", "goals": [requirement[:80] if requirement else "Task objective"]}]
    content_pages = pages - 2
    for i in range(content_pages):
        chunk = snippets[i * 2 : i * 2 + 2] or [f"Key point {i + 1}"]
        title = chunk[0][:60] if chunk else f"Content {i + 1}"
        goals = [c[:120] for c in chunk]
        if callable(retrieve_context_fn):
            recalls = retrieve_context_fn(f"{requirement} {title}", 1)
            if recalls:
                goals.append(str(recalls[0])[:120])
        items.append({"index": i + 2, "kind": "content", "title": title or f"Content {i + 1}", "goals": goals})
    items.append({"index": pages, "kind": "summary", "title": "Summary", "goals": ["Key takeaways", "Next steps"]})
    return {"outline": items}

