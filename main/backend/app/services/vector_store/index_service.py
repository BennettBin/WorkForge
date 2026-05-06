from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import shutil
from typing import Any
from urllib import error, request


@dataclass
class VectorChunk:
    chunk_id: str
    text: str
    vector: dict[str, float]
    source: str = "task_file"
    metadata: dict[str, Any] | None = None


class VectorIndexService:
    def __init__(self, storage_root: Path, embedding_runtime_config: dict[str, Any] | None = None):
        self.storage_root = storage_root
        self.embedding_runtime_config = embedding_runtime_config or {}
        self._ollama_unavailable = False

    def build_index(self, task_id: str, text: str, chunk_chars: int = 500, overlap_chars: int = 120) -> dict:
        chunks = self._chunk_text(text, chunk_chars, overlap_chars)
        vectorizer_meta = self._resolve_vectorizer_metadata(None)
        vector_chunks: list[VectorChunk] = []
        for idx, chunk_text in enumerate(chunks, start=1):
            vector_chunks.append(
                VectorChunk(
                    chunk_id=f"c{idx}",
                    text=chunk_text,
                    vector=self._vectorize(chunk_text, vectorizer_meta),
                    source="task_file",
                )
            )
        if vectorizer_meta.get("type") == "ollama" and self._ollama_unavailable:
            vectorizer_meta = {
                "type": "lexical",
                "fallback_from": "ollama",
                "fallback_model": vectorizer_meta.get("model"),
            }

        payload = {
            "task_id": task_id,
            "chunk_count": len(vector_chunks),
            "vectorizer": vectorizer_meta,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "text": c.text,
                    "vector": c.vector,
                    "source": c.source,
                    "metadata": c.metadata or {},
                }
                for c in vector_chunks
            ],
        }
        index_path = self._index_path(task_id)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return {
            "task_id": task_id,
            "chunk_count": len(vector_chunks),
            "index_path": str(index_path.resolve()),
            "vectorizer_type": vectorizer_meta.get("type"),
            "vectorizer_model": vectorizer_meta.get("model"),
        }

    def append_documents(
        self,
        task_id: str,
        documents: list[dict[str, Any]],
        chunk_chars: int = 420,
        overlap_chars: int = 80,
    ) -> dict[str, Any]:
        payload = self._load_index(task_id) or {"task_id": task_id, "chunk_count": 0, "chunks": []}
        vectorizer_meta = payload.get("vectorizer") if isinstance(payload, dict) else None
        if not vectorizer_meta:
            vectorizer_meta = self._resolve_vectorizer_metadata(None)
            payload["vectorizer"] = vectorizer_meta
        chunks = payload.get("chunks", [])
        existing_keys = {self._dedupe_key(str(row.get("text", ""))) for row in chunks}
        next_index = len(chunks) + 1
        appended = 0

        for doc in documents:
            raw_text = str(doc.get("content") or doc.get("text") or doc.get("snippet") or "").strip()
            if not raw_text:
                continue
            source_url = str(doc.get("url") or "").strip()
            source_title = str(doc.get("title") or "").strip()
            source_label = source_url or "web_document"
            doc_chunks = self._chunk_text(raw_text, chunk_chars, overlap_chars)
            for chunk_text in doc_chunks:
                key = self._dedupe_key(chunk_text)
                if key in existing_keys:
                    continue
                vector = self._vectorize(chunk_text, vectorizer_meta)
                if not vector:
                    continue
                chunks.append(
                    {
                        "chunk_id": f"c{next_index}",
                        "text": chunk_text,
                        "vector": vector,
                        "source": source_label,
                        "metadata": {"title": source_title, "url": source_url},
                    }
                )
                existing_keys.add(key)
                next_index += 1
                appended += 1

        if isinstance(vectorizer_meta, dict) and vectorizer_meta.get("type") == "ollama" and self._ollama_unavailable:
            payload["vectorizer"] = {
                "type": "lexical",
                "fallback_from": "ollama",
                "fallback_model": vectorizer_meta.get("model"),
            }

        payload["chunks"] = chunks
        payload["chunk_count"] = len(chunks)
        index_path = self._index_path(task_id)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return {
            "task_id": task_id,
            "chunk_count": len(chunks),
            "appended_chunk_count": appended,
            "index_path": str(index_path.resolve()),
            "vectorizer_type": vectorizer_meta.get("type"),
            "vectorizer_model": vectorizer_meta.get("model"),
        }

    def has_index(self, task_id: str) -> bool:
        path = self._index_path(task_id)
        return path.exists()

    def clear_index(self, task_id: str) -> dict[str, Any]:
        task_dir = self.storage_root / "vectors" / task_id
        if not task_dir.exists():
            return {"task_id": task_id, "removed": False, "removed_files": 0}
        removed_files = sum(1 for p in task_dir.rglob("*") if p.is_file())
        shutil.rmtree(task_dir, ignore_errors=True)
        return {"task_id": task_id, "removed": True, "removed_files": removed_files}

    def query(self, task_id: str, query_text: str, top_k: int = 3) -> list[str]:
        if not query_text.strip():
            return []
        payload = self._load_index(task_id)
        if payload is None:
            return []
        vectorizer_meta = payload.get("vectorizer") if isinstance(payload, dict) else None
        query_vector = self._vectorize(query_text, vectorizer_meta)
        scored: list[tuple[float, str]] = []
        for chunk in payload.get("chunks", []):
            score = self._cosine_similarity(query_vector, chunk.get("vector", {}))
            if score > 0:
                scored.append((score, chunk.get("text", "")))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:top_k] if text]

    def _index_path(self, task_id: str) -> Path:
        return self.storage_root / "vectors" / task_id / "index.json"

    def _load_index(self, task_id: str) -> dict | None:
        path = self._index_path(task_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _chunk_text(self, text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
        content = text.strip()
        if not content:
            return []
        if len(content) <= chunk_chars:
            return [content]
        result: list[str] = []
        start = 0
        step = max(1, chunk_chars - overlap_chars)
        while start < len(content):
            result.append(content[start : start + chunk_chars].strip())
            start += step
        return [x for x in result if x]

    def _vectorize(self, text: str, vectorizer_hint: dict[str, Any] | None = None) -> dict[str, float]:
        meta = self._resolve_vectorizer_metadata(vectorizer_hint)
        if meta.get("type") == "ollama":
            if self._ollama_unavailable:
                return self._vectorize_lexical(text)
            try:
                return self._vectorize_ollama(text, meta)
            except Exception:
                self._ollama_unavailable = True
                # Keep MVP stability: fallback to lexical vectorization if remote embedding is unavailable.
                return self._vectorize_lexical(text)
        return self._vectorize_lexical(text)

    def _vectorize_lexical(self, text: str) -> dict[str, float]:
        tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", text.lower())
        if not tokens:
            return {}
        freq: dict[str, float] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0.0) + 1.0
        norm = math.sqrt(sum(v * v for v in freq.values()))
        if norm <= 0:
            return {}
        # Keep the vector small for persistence and lookup.
        top_items = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:200]
        return {k: v / norm for k, v in top_items}

    def _vectorize_ollama(self, text: str, meta: dict[str, Any]) -> dict[str, float]:
        payload = {
            "model": str(meta.get("model", "")).strip(),
            "input": text,
        }
        if not payload["model"]:
            return {}
        base_url = str(meta.get("base_url", "http://localhost:11434")).strip().rstrip("/")
        timeout_seconds = int(meta.get("timeout_seconds", 30) or 30)
        api_key = str(meta.get("api_key", "")).strip()
        url = f"{base_url}/api/embed"
        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        try:
            with request.urlopen(req, timeout=timeout_seconds) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"Ollama embed HTTPError {exc.code}: {detail[:240]}") from exc
        except Exception as exc:
            raise ValueError(f"Ollama embed request failed: {exc}") from exc

        try:
            data = json.loads(body)
        except Exception as exc:
            raise ValueError(f"Ollama embed returned invalid JSON: {body[:240]}") from exc

        embedding = None
        if isinstance(data, dict):
            emb = data.get("embeddings")
            if isinstance(emb, list) and emb and isinstance(emb[0], list):
                embedding = emb[0]
            elif isinstance(data.get("embedding"), list):
                embedding = data.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("Ollama embed returned empty vector.")
        dense = [float(x) for x in embedding if isinstance(x, (int, float))]
        if not dense:
            raise ValueError("Ollama embed vector has no numeric dimensions.")
        return self._compress_dense_vector(dense)

    def _compress_dense_vector(self, dense: list[float], max_dims: int = 256) -> dict[str, float]:
        indexed = list(enumerate(dense))
        indexed.sort(key=lambda x: abs(x[1]), reverse=True)
        top = indexed[: max_dims]
        norm = math.sqrt(sum(v * v for _, v in top))
        if norm <= 0:
            return {}
        return {str(i): (v / norm) for i, v in top}

    def _cosine_similarity(self, a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        common = set(a.keys()) & set(b.keys())
        return sum(a[k] * b[k] for k in common)

    def _dedupe_key(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
        return normalized[:180]

    def _resolve_vectorizer_metadata(self, hint: dict[str, Any] | None) -> dict[str, Any]:
        if isinstance(hint, dict) and hint.get("type") in {"ollama", "lexical"}:
            return hint
        cfg = self.embedding_runtime_config or {}
        provider_type = str(cfg.get("provider_type", "")).strip().lower()
        model = str(cfg.get("embedding_model", "")).strip()
        base_url = str(cfg.get("base_url", "")).strip() or "http://localhost:11434"
        timeout_seconds = int(cfg.get("timeout_seconds", 8) or 8)
        api_key = str(cfg.get("api_key", "")).strip()
        if provider_type == "ollama" and model:
            return {
                "type": "ollama",
                "provider_type": "ollama",
                "model": model,
                "base_url": base_url,
                "timeout_seconds": timeout_seconds,
                "api_key": api_key,
            }
        return {"type": "lexical"}
