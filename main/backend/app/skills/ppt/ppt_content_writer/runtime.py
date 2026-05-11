from __future__ import annotations

import json
import re

from app.prompts import CONTENT_NOTES_SOURCE_FILE_TEMPLATE, CONTENT_NOTES_WEB_SEARCH_TEMPLATE, build_content_prompt


def _normalize_placeholders(rows) -> list[dict]:
    result: list[dict] = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label", "")).strip()
        source = str(row.get("source", "")).strip()
        if label:
            result.append({"label": label[:90], "source": source[:180] or "unknown"})
    return result


def _extract_image_candidates(parsed_text: str) -> list[dict]:
    candidates: list[dict] = []
    lines = [ln.strip() for ln in parsed_text.splitlines() if ln.strip()]
    for ln in lines:
        if re.search(r"\b(fig(?:ure)?|image|chart|graph)\b", ln, re.IGNORECASE) or ("图" in ln):
            source = "source_file"
            m = re.search(r"(https?://\S+)", ln)
            if m:
                source = m.group(1)
            candidates.append({"label": ln[:90], "source": source})
        if len(candidates) >= 12:
            break
    return candidates


def run(payload: dict) -> dict:
    outline = payload.get("outline", [])
    parsed_text = str(payload.get("parsed_text", ""))
    retrieve_context_fn = payload.get("retrieve_context_fn")
    external_knowledge_by_slide = payload.get("external_knowledge_by_slide", {})
    llm_generate_fn = payload.get("llm_generate_fn")
    no_source_file = bool(payload.get("no_source_file", False))

    if callable(llm_generate_fn) and isinstance(outline, list):
        prompt = build_content_prompt(outline_payload=outline, parsed_text=parsed_text, no_source_file=no_source_file)
        try:
            raw = llm_generate_fn(prompt)
            text = (raw or "").strip()
            rows = json.loads(text[text.find("[") : text.rfind("]") + 1])
            slides: list[dict] = []
            for i, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    continue
                ref = outline[i - 1] if i - 1 < len(outline) and isinstance(outline[i - 1], dict) else {}
                bullets_raw = row.get("bullets", [])
                bullets = [str(x).strip() for x in bullets_raw if str(x).strip()] if isinstance(bullets_raw, list) else []
                if not bullets:
                    goals = ref.get("goals", []) if isinstance(ref.get("goals"), list) else []
                    bullets = [str(x) for x in goals[:3]] or [str(ref.get("title", f"Slide {i}"))]
                slides.append(
                    {
                        "index": i,
                        "kind": str(row.get("kind", ref.get("kind", "content"))),
                        "title": str(row.get("title", ref.get("title", f"Content {i}"))),
                        "bullets": bullets[:5],
                        "notes": str(row.get("notes", f"Slide {i} notes"))[:600],
                        "image_placeholders": _normalize_placeholders(row.get("image_placeholders", []))[:2],
                    }
                )
            if slides:
                return {"slides": slides}
        except Exception:
            pass

    image_candidates = _extract_image_candidates(parsed_text)
    slides: list[dict] = []
    for item in outline if isinstance(outline, list) else []:
        if not isinstance(item, dict):
            continue
        idx = int(item.get("index", 0) or 0)
        kind = str(item.get("kind", "content"))
        title = str(item.get("title", ""))
        goals = item.get("goals", []) if isinstance(item.get("goals"), list) else []
        bullets = [str(g)[:120] for g in goals if str(g).strip()]
        if callable(retrieve_context_fn):
            for recall in retrieve_context_fn(title, 2):
                cand = str(recall).strip().replace("\n", " ")
                if cand:
                    bullets.append(cand[:120])
        knowledge_rows = external_knowledge_by_slide.get(idx, []) if isinstance(external_knowledge_by_slide, dict) else []
        for row in knowledge_rows if isinstance(knowledge_rows, list) else []:
            if isinstance(row, dict):
                snippet = str(row.get("snippet") or row.get("content") or "").strip()
                if snippet:
                    bullets.append(snippet[:120])
        deduped: list[str] = []
        seen: set[str] = set()
        for b in bullets:
            key = b.lower().strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(b)
        deduped = deduped[:5] or ["TBD content"]
        placeholders: list[dict] = []
        if kind == "content" and image_candidates:
            pick = image_candidates[max(0, (idx - 2) % len(image_candidates))]
            placeholders.append({"label": pick.get("label", "Figure placeholder"), "source": pick.get("source", "source_file")})
        notes_template = CONTENT_NOTES_WEB_SEARCH_TEMPLATE if no_source_file else CONTENT_NOTES_SOURCE_FILE_TEMPLATE
        slides.append(
            {
                "index": idx,
                "kind": kind,
                "title": title,
                "bullets": deduped,
                "notes": notes_template.format(index=idx, title=title),
                "image_placeholders": placeholders[:1],
            }
        )
    return {"slides": slides}

