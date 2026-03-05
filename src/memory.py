"""Persistent memory for the agent - tracks past digests, trends, and notes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta


DEFAULT_MEMORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memory",
)


class AgentMemory:
    """Simple file-based persistent memory for the agent."""

    def __init__(self, memory_dir: str = DEFAULT_MEMORY_DIR):
        self.memory_dir = memory_dir
        self.memory_file = os.path.join(memory_dir, "memory.json")
        os.makedirs(memory_dir, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        """Load memory from disk."""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {"entries": [], "reported_titles": []}

    def _save(self) -> None:
        """Save memory to disk."""
        with open(self.memory_file, "w") as f:
            json.dump(self._data, f, indent=2)

    def add(self, note: str, category: str) -> None:
        """Add a memory entry."""
        entry = {
            "date": datetime.now().isoformat(),
            "note": note,
            "category": category,
        }
        self._data["entries"].append(entry)
        # Keep last 500 entries
        self._data["entries"] = self._data["entries"][-500:]
        self._save()

    def mark_reported(self, titles: list[str]) -> None:
        """Mark article titles as already reported to avoid repeats."""
        self._data["reported_titles"].extend(titles)
        # Keep last 1000 titles
        self._data["reported_titles"] = self._data["reported_titles"][-1000:]
        self._save()

    def was_reported(self, title: str) -> bool:
        """Check if a title was already reported."""
        normalized = title.lower().strip()
        return any(
            normalized == t.lower().strip()
            for t in self._data["reported_titles"]
        )

    def search(self, query: str) -> list[dict]:
        """Search memory entries by keyword."""
        query_lower = query.lower()
        return [
            entry for entry in self._data["entries"]
            if query_lower in entry["note"].lower()
            or query_lower in entry.get("category", "").lower()
        ][-20:]

    def get_recent(self, days: int = 7) -> list[dict]:
        """Get memory entries from the last N days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return [
            entry for entry in self._data["entries"]
            if entry["date"] >= cutoff
        ][-20:]

    def get_reported_count(self) -> int:
        """How many titles have been reported."""
        return len(self._data["reported_titles"])
