from dataclasses import dataclass
import json

from app.prompts import OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS, build_outline_prompt


@dataclass
class SlideOutlineItem:
    index: int
    kind: str
    title: str
    goals: list[str]


class OutlineAgent:
    def generate(
        self,
        parsed_text: str,
        requested_pages: int,
        requirement: str,
        retrieve_context_fn=None,
        llm_generate_fn=None,
        no_source_file: bool = False,
    ) -> list[SlideOutlineItem]:
        pages = max(3, min(30, requested_pages))
        if callable(llm_generate_fn):
            llm_items = self._generate_by_llm(
                parsed_text,
                pages,
                requirement,
                llm_generate_fn,
                no_source_file=no_source_file,
            )
            if llm_items:
                return llm_items

        lines = [line.strip() for line in parsed_text.splitlines() if line.strip()]
        snippets = lines[: max(8, pages * 2)]

        if no_source_file and not snippets:
            snippets = OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS

        items: list[SlideOutlineItem] = []
        items.append(
            SlideOutlineItem(
                index=1,
                kind="cover",
                title="Presentation",
                goals=[requirement[:80] if requirement else "Task objective"],
            )
        )

        content_pages = pages - 2
        for i in range(content_pages):
            start = i * 2
            chunk = snippets[start : start + 2] or [f"Key point {i + 1}"]
            title = chunk[0][:60] if chunk else f"Content {i + 1}"
            goals = [c[:120] for c in chunk]
            if callable(retrieve_context_fn):
                recalls = retrieve_context_fn(f"{requirement} {title}", 1)
                if recalls:
                    goals.append(recalls[0][:120])
            items.append(
                SlideOutlineItem(
                    index=i + 2,
                    kind="content",
                    title=title or f"Content {i + 1}",
                    goals=goals,
                )
            )

        items.append(
            SlideOutlineItem(
                index=pages,
                kind="summary",
                title="Summary",
                goals=["Key takeaways", "Next steps"],
            )
        )
        return items

    def _generate_by_llm(
        self,
        parsed_text: str,
        pages: int,
        requirement: str,
        llm_generate_fn,
        no_source_file: bool = False,
    ) -> list[SlideOutlineItem]:
        prompt = build_outline_prompt(
            pages=pages,
            requirement=requirement,
            parsed_text=parsed_text,
            no_source_file=no_source_file,
        )
        try:
            raw = llm_generate_fn(prompt)
        except Exception:
            return []
        return self._parse_llm_outline(raw, pages)

    def _parse_llm_outline(self, raw: str, pages: int) -> list[SlideOutlineItem]:
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
        items: list[SlideOutlineItem] = []
        for i, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            kind = str(row.get("kind", "content")).strip() or "content"
            title = str(row.get("title", f"Content {i}")).strip() or f"Content {i}"
            goals_raw = row.get("goals", [])
            goals = []
            if isinstance(goals_raw, list):
                goals = [str(x).strip() for x in goals_raw if str(x).strip()]
            if not goals:
                goals = [title]
            items.append(SlideOutlineItem(index=i, kind=kind, title=title, goals=goals[:5]))
        if len(items) != pages:
            return []
        if items[0].kind != "cover":
            items[0].kind = "cover"
        if items[-1].kind != "summary":
            items[-1].kind = "summary"
        return items
