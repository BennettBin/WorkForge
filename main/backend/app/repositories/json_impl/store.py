import json
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4


_FILE_LOCKS: dict[str, threading.RLock] = {}
_LOCK_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _LOCK_GUARD:
        if key not in _FILE_LOCKS:
            _FILE_LOCKS[key] = threading.RLock()
        return _FILE_LOCKS[key]


class JsonCollectionStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._atomic_write([])

    def read_all(self) -> list[dict[str, Any]]:
        lock = _lock_for(self.file_path)
        with lock:
            try:
                with self.file_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                    if isinstance(payload, list):
                        return payload
                    self._quarantine_corrupt("payload_not_list")
                    return []
            except json.JSONDecodeError:
                self._quarantine_corrupt("json_decode_error")
                return []

    def write_all(self, rows: list[dict[str, Any]]) -> None:
        lock = _lock_for(self.file_path)
        with lock:
            self._atomic_write(rows)

    def _atomic_write(self, rows: list[dict[str, Any]]) -> None:
        temp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
        temp_path.replace(self.file_path)

    def _quarantine_corrupt(self, reason: str) -> None:
        backup_name = f"{self.file_path.stem}.corrupt.{reason}.{uuid4().hex[:8]}{self.file_path.suffix}"
        backup_path = self.file_path.with_name(backup_name)
        if self.file_path.exists():
            self.file_path.replace(backup_path)
        self._atomic_write([])
