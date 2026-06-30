from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from typing import Any
from urllib import error, request

from app.models.entities import EmbeddingProviderConfig
from app.services.embedding_runtime import EmbeddingRuntime
from app.services.vector_store.storage_manager import RagStorageManager, utc_now_iso


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
        self.embedding_runtime = EmbeddingRuntime()
        self.rag_storage = RagStorageManager(storage_root)

    def build_index(
        self,
        task_id: str,
        text: str,
        chunk_chars: int = 500,
        overlap_chars: int = 120,
        source_metadata: dict[str, Any] | None = None,
    ) -> dict:
        source_metadata = source_metadata or {}
        source_hash = str(source_metadata.get("file_hash") or "").strip() or self._content_hash(text)
        existing_doc = self.rag_storage.get_document_by_hash(source_hash)
        if existing_doc and existing_doc.get("parse_status") == "INDEXED":
            document_id = str(existing_doc.get("document_id", ""))
            if document_id and self._materialize_task_index_from_document(task_id, document_id):
                return {
                    "task_id": task_id,
                    "document_id": document_id,
                    "chunk_count": int(existing_doc.get("chunk_count", 0) or 0),
                    "index_path": str(self._index_path(task_id).resolve()),
                    "vectorizer_type": existing_doc.get("vectorizer_type"),
                    "vectorizer_model": existing_doc.get("vectorizer_model"),
                    "reused_existing_index": True,
                }

        document_id = f"doc_{source_hash[:16]}"
        self.rag_storage.upsert_document(
            {
                "document_id": document_id,
                "user_id": str(self.embedding_runtime_config.get("user_id", "default_user") or "default_user"),
                "project_id": "default_project",
                "file_name": str(source_metadata.get("file_name") or f"{task_id}.txt"),
                "file_hash": source_hash,
                "file_path": str(source_metadata.get("file_path") or ""),
                "file_type": str(source_metadata.get("file_type") or "text"),
                "parse_status": "CHUNKING",
                "error_message": None,
            }
        )
        raw_chunks = self._chunk_text(text, chunk_chars, overlap_chars)
        chunks = [
            {
                "chunk_id": f"{document_id}_chunk_{idx:04d}",
                "content": chunk_text,
                "content_hash": self._content_hash(chunk_text),
                "section_id": None,
                "section_title": None,
                "section_path": None,
                "page_number": None,
                "chunk_index": idx,
                "token_count": len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", chunk_text)),
                "content_type": "body",
            }
            for idx, chunk_text in enumerate(raw_chunks, start=1)
        ]
        chunks_path = self.rag_storage.save_chunks(document_id, chunks)
        sections_path = self.rag_storage.save_sections(document_id, [])
        self.rag_storage.update_document_status(document_id, "EMBEDDING")
        vectorizer_meta = self._resolve_vectorizer_metadata(None)
        vector_chunks: list[VectorChunk] = []
        for chunk in chunks:
            chunk_text = str(chunk.get("content", ""))
            vector_chunks.append(
                VectorChunk(
                    chunk_id=str(chunk["chunk_id"]),
                    text=chunk_text,
                    vector=self._vectorize(chunk_text, vectorizer_meta),
                    source="task_file",
                    metadata={k: v for k, v in chunk.items() if k != "content"},
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
            "document_id": document_id,
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
        rag_index_path = self.rag_storage.index_dir(document_id) / "index.json"
        rag_index_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        metadata_path = self.rag_storage.save_index_metadata(
            document_id,
            {
                "document_id": document_id,
                "task_id": task_id,
                "source_hash": source_hash,
                "index_path": str(rag_index_path.resolve()),
                "chunks_path": str(chunks_path.resolve()),
                "sections_path": str(sections_path.resolve()),
                "vectors": [
                    {
                        "vector_id": idx,
                        "chunk_id": c.chunk_id,
                        **(c.metadata or {}),
                    }
                    for idx, c in enumerate(vector_chunks)
                ],
                "updated_at": utc_now_iso(),
            },
        )
        self.rag_storage.upsert_document(
            {
                **(self.rag_storage.get_document_by_id(document_id) or {}),
                "document_id": document_id,
                "parse_status": "INDEXED",
                "chunk_count": len(vector_chunks),
                "chunks_path": str(chunks_path.resolve()),
                "sections_path": str(sections_path.resolve()),
                "index_path": str(rag_index_path.resolve()),
                "index_metadata_path": str(metadata_path.resolve()),
                "vectorizer_type": vectorizer_meta.get("type"),
                "vectorizer_model": vectorizer_meta.get("model"),
                "error_message": None,
            }
        )
        return {
            "task_id": task_id,
            "document_id": document_id,
            "chunk_count": len(vector_chunks),
            "index_path": str(index_path.resolve()),
            "vectorizer_type": vectorizer_meta.get("type"),
            "vectorizer_model": vectorizer_meta.get("model"),
            "reused_existing_index": False,
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
        exact = self._exact_match_chunks(payload, query_text, top_k=top_k)
        vectorizer_meta = payload.get("vectorizer") if isinstance(payload, dict) else None
        query_vector = self._vectorize(query_text, vectorizer_meta)
        scored: list[tuple[float, str]] = []
        for chunk in payload.get("chunks", []):
            score = self._cosine_similarity(query_vector, chunk.get("vector", {}))
            if score > 0:
                scored.append((score, chunk.get("text", "")))
        scored.sort(key=lambda x: x[0], reverse=True)
        merged = exact + [text for _, text in scored if text and text not in exact]
        return merged[:top_k]

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
                return self._vectorize_lexical(text)
        if meta.get("type") in {"huggingface", "local_embedding"}:
            try:
                return self._vectorize_embedding_runtime(text, meta)
            except Exception:
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

    def _vectorize_embedding_runtime(self, text: str, meta: dict[str, Any]) -> dict[str, float]:
        cfg = EmbeddingProviderConfig(
            provider_id=str(meta.get("provider_id", "vector_runtime")),
            user_id=str(meta.get("user_id", "runtime")),
            provider_type=meta.get("provider_type") or meta.get("type"),
            display_name=str(meta.get("display_name", "Vector Embedding")),
            model_name=str(meta.get("model", "")).strip() or None,
            base_url=str(meta.get("base_url", "")).strip() or None,
            local_path=str(meta.get("local_path", "")).strip() or None,
            cache_dir=str(meta.get("cache_dir", "")).strip() or None,
            dimension=int(meta["dimension"]) if meta.get("dimension") else None,
            is_default=bool(meta.get("is_default", False)),
        )
        dense = self.embedding_runtime.embed_query(cfg, text)
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

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

    def _materialize_task_index_from_document(self, task_id: str, document_id: str) -> bool:
        source = self.rag_storage.index_dir(document_id) / "index.json"
        if not source.exists():
            return False
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except Exception:
            return False
        payload["task_id"] = task_id
        target = self._index_path(task_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return True

    def _exact_match_chunks(self, payload: dict[str, Any], query_text: str, top_k: int) -> list[str]:
        query = re.sub(r"\s+", " ", query_text.strip())
        if len(query) < 2:
            return []
        needles = [query]
        table_match = re.search(r"\b(?:table|figure|fig\.?)\s*\d+\b", query, flags=re.IGNORECASE)
        if table_match:
            needles.insert(0, table_match.group(0))
        section_match = re.search(r"(?:第\s*)?(\d+(?:\.\d+)*)\s*(?:节|section)?|([A-Za-z][A-Za-z ]{2,40})\s+section", query, flags=re.IGNORECASE)
        if section_match:
            needles.insert(0, section_match.group(1) or section_match.group(2) or "")
        hits: list[str] = []
        for chunk in payload.get("chunks", []):
            text = str(chunk.get("text", ""))
            haystack = text.lower()
            metadata = chunk.get("metadata", {}) if isinstance(chunk.get("metadata"), dict) else {}
            meta_text = " ".join(str(metadata.get(k, "")) for k in ["section_id", "section_title", "section_path"]).lower()
            for needle in needles:
                n = str(needle or "").strip().lower()
                if n and (n in haystack or n in meta_text):
                    hits.append(text)
                    break
            if len(hits) >= top_k:
                break
        return hits

    def _resolve_vectorizer_metadata(self, hint: dict[str, Any] | None) -> dict[str, Any]:
        if isinstance(hint, dict) and hint.get("type") in {"ollama", "lexical", "huggingface", "local_embedding"}:
            return hint
        cfg = self.embedding_runtime_config or {}
        provider_type = str(cfg.get("provider_type", "")).strip().lower()
        model = str(cfg.get("model_name", "")).strip()
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
        if provider_type == "huggingface" and model:
            return {
                "type": "huggingface",
                "provider_type": "huggingface",
                "model": model,
                "cache_dir": str(cfg.get("cache_dir", "") or ""),
                "dimension": cfg.get("dimension"),
            }
        if provider_type == "local_embedding":
            return {
                "type": "local_embedding",
                "provider_type": "local_embedding",
                "model": model,
                "local_path": str(cfg.get("local_path", "") or ""),
                "dimension": cfg.get("dimension"),
            }
        if provider_type or model:
            return {
                "type": "lexical",
                "provider_type": provider_type or "lexical",
                "model": model,
            }
        return {"type": "lexical"}
