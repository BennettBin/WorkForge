from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import json
import re
from urllib.parse import quote
from urllib.request import urlopen


@dataclass
class KnowledgeItem:
    title: str
    url: str
    snippet: str
    content: str


class KnowledgeSearchService:
    def search_and_extract(self, query: str, max_results: int = 2) -> list[dict]:
        seeds = self._search_seed(query, max_results=max_results)
        enriched: list[dict] = []
        for seed in seeds:
            content = self.extract_web_text(seed["url"], max_chars=800)
            enriched.append(
                {
                    "title": seed["title"],
                    "url": seed["url"],
                    "snippet": seed["snippet"],
                    "content": content,
                }
            )
        return enriched

    def _search_seed(self, query: str, max_results: int) -> list[dict]:
        # Public endpoint without API key for MVP; network failures gracefully degrade.
        endpoint = (
            "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json"
            f"&srlimit={max_results}&srsearch={quote(query)}"
        )
        try:
            with urlopen(endpoint, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception:
            return []

        items = []
        for row in data.get("query", {}).get("search", []):
            title = row.get("title", "").strip()
            if not title:
                continue
            snippet = unescape(re.sub(r"<[^>]+>", "", row.get("snippet", ""))).strip()
            url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
            items.append({"title": title, "url": url, "snippet": snippet})
        return items[:max_results]

    def extract_web_text(self, url: str, max_chars: int = 1200) -> str:
        try:
            with urlopen(url, timeout=2) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""
        text = unescape(re.sub(r"<[^>]+>", " ", html))
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
