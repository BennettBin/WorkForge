from __future__ import annotations

from dataclasses import dataclass
import json
import re

from app.agents.sub_agents.ppt.outline_sub_agent import SlideOutlineItem
from app.prompts import (
    CONTENT_NOTES_SOURCE_FILE_TEMPLATE,
    CONTENT_NOTES_WEB_SEARCH_TEMPLATE,
    build_content_prompt,
)


@dataclass
class SlideContentItem:
    index: int
    kind: str
    title: str
    bullets: list[str]
    notes: str
    image_placeholders: list[dict]


class ContentAgent:
    def generate(
        self,
        outline: list[SlideOutlineItem],
        parsed_text: str,
        retrieve_context_fn=None,
        external_knowledge_by_slide: dict[int, list[dict]] | None = None,
        llm_generate_fn=None,
        no_source_file: bool = False,
    ) -> list[SlideContentItem]:
        if callable(llm_generate_fn):
            llm_content = self._generate_by_llm(
                outline,
                parsed_text,
                llm_generate_fn,
                no_source_file=no_source_file,
            )
            if llm_content:
                return llm_content

        image_candidates = self._extract_image_candidates(parsed_text)
        result: list[SlideContentItem] = []

        for item in outline:
            bullets = [g[:120] for g in item.goals if g.strip()]
            if callable(retrieve_context_fn):
                recalls = retrieve_context_fn(item.title, 2)
                for recall in recalls:
                    candidate = recall.strip().replace("\n", " ")
                    if candidate:
                        bullets.append(candidate[:120])

            knowledge_rows = external_knowledge_by_slide.get(item.index, []) if external_knowledge_by_slide else []
            for knowledge in knowledge_rows:
                snippet = (knowledge.get("snippet") or knowledge.get("content") or "").strip()
                if snippet:
                    bullets.append(snippet[:120])

            bullets = self._dedupe(bullets)[:5] or ["TBD content"]

            placeholders = self._pick_image_placeholders(
                item=item,
                image_candidates=image_candidates,
                knowledge_rows=knowledge_rows,
            )

            notes_template = CONTENT_NOTES_WEB_SEARCH_TEMPLATE if no_source_file else CONTENT_NOTES_SOURCE_FILE_TEMPLATE
            notes = notes_template.format(index=item.index, title=item.title)

            result.append(
                SlideContentItem(
                    index=item.index,
                    kind=item.kind,
                    title=item.title,
                    bullets=bullets,
                    notes=notes,
                    image_placeholders=placeholders,
                )
            )
        return result

    def _generate_by_llm(
        self,
        outline: list[SlideOutlineItem],
        parsed_text: str,
        llm_generate_fn,
        no_source_file: bool = False,
    ) -> list[SlideContentItem]:
        prompt = build_content_prompt(
            outline_payload=[{"index": i.index, "kind": i.kind, "title": i.title, "goals": i.goals} for i in outline],
            parsed_text=parsed_text,
            no_source_file=no_source_file,
        )
        raw = llm_generate_fn(prompt)
        text = (raw or "").strip()
        start = text.find("[")
        end = text.rfind("]")
        rows = json.loads(text[start : end + 1])

        result: list[SlideContentItem] = []
        for i, row in enumerate(rows, start=1):
            kind = str(row.get("kind", outline[i - 1].kind)).strip() or outline[i - 1].kind
            title = str(row.get("title", outline[i - 1].title)).strip() or outline[i - 1].title
            bullets_raw = row.get("bullets", [])
            bullets = [str(x).strip() for x in bullets_raw if str(x).strip()] if isinstance(bullets_raw, list) else []
            if not bullets:
                bullets = outline[i - 1].goals[:3] or [title]
            notes = str(row.get("notes", f"Slide {i} notes: {title}")).strip()
            placeholder_rows = row.get("image_placeholders", [])
            placeholders = self._normalize_placeholders(placeholder_rows)
            result.append(
                SlideContentItem(
                    index=i,
                    kind=kind,
                    title=title,
                    bullets=bullets[:5],
                    notes=notes[:600],
                    image_placeholders=placeholders[:2],
                )
            )
        return result

    def _extract_image_candidates(self, parsed_text: str) -> list[dict]:
        candidates: list[dict] = []
        lines = [ln.strip() for ln in parsed_text.splitlines() if ln.strip()]
        for ln in lines:
            if re.search(r"\b(fig(?:ure)?|image|chart|graph)\b", ln, re.IGNORECASE) or ("图" in ln):
                label = ln[:90]
                source = "source_file"
                m = re.search(r"(https?://\S+)", ln)
                if m:
                    source = m.group(1)
                candidates.append({"label": label, "source": source})
            if len(candidates) >= 12:
                break
        return candidates

    def _pick_image_placeholders(self, item: SlideOutlineItem, image_candidates: list[dict], knowledge_rows: list[dict]) -> list[dict]:
        if item.kind != "content":
            return []

        placeholders: list[dict] = []
        if image_candidates:
            idx = max(0, (item.index - 2) % len(image_candidates))
            pick = image_candidates[idx]
            placeholders.append({"label": pick.get("label", "Figure placeholder"), "source": pick.get("source", "source_file")})

        if not placeholders and knowledge_rows:
            row = knowledge_rows[0]
            label = row.get("title") or row.get("snippet") or "External reference figure"
            source = row.get("url") or "web_search"
            placeholders.append({"label": str(label)[:90], "source": str(source)[:180]})

        return placeholders[:1]

    def _normalize_placeholders(self, rows) -> list[dict]:
        result = []
        if not isinstance(rows, list):
            return result
        for row in rows:
            if not isinstance(row, dict):
                continue
            label = str(row.get("label", "")).strip()
            source = str(row.get("source", "")).strip()
            if not label:
                continue
            result.append({"label": label[:90], "source": source[:180] or "unknown"})
        return result

    def _dedupe(self, rows: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for row in rows:
            key = row.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(row)
        return out
