from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
from json import JSONDecodeError

from config import DB_DIR


class MockDB:
    def __init__(self, db_dir: Path = DB_DIR) -> None:
        self.db_dir = db_dir
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.leads_path = self.db_dir / "leads.json"
        self.conversations_path = self.db_dir / "conversations.json"
        self.escalations_path = self.db_dir / "escalations.jsonl"
        self._ensure_files()

    def _ensure_files(self) -> None:
        for path in (self.leads_path, self.conversations_path):
            if not path.exists() or not path.read_text(encoding="utf-8").strip():
                path.write_text("[]", encoding="utf-8")
        if not self.escalations_path.exists():
            self.escalations_path.write_text("", encoding="utf-8")

    def _read_json_list(self, path: Path) -> list[dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except JSONDecodeError:
            self._write_json_list(path, [])
            return []

    def _write_json_list(self, path: Path, rows: list[dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(rows, file, indent=2, ensure_ascii=False)

    def save_lead(self, lead: dict[str, Any]) -> None:
        rows = self._read_json_list(self.leads_path)
        rows.append({**lead, "created_at": datetime.now(timezone.utc).isoformat()})
        self._write_json_list(self.leads_path, rows)

    def save_conversation(self, conversation: dict[str, Any]) -> None:
        rows = self._read_json_list(self.conversations_path)
        rows.append({**conversation, "created_at": datetime.now(timezone.utc).isoformat()})
        self._write_json_list(self.conversations_path, rows)

    def log_escalation(self, escalation: dict[str, Any]) -> None:
        row = {**escalation, "created_at": datetime.now(timezone.utc).isoformat()}
        with open(self.escalations_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
