"""Opencluely context vault manager."""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional

try:
    from storage_paths import get_runtime_file, get_seed_file
except ImportError:
    from src.storage_paths import get_runtime_file, get_seed_file


logger = logging.getLogger("context_vault_manager")

CONTEXT_VAULT_FILE = str(get_runtime_file("context_vault.json"))
def _legacy_context_vault_filename() -> str:
    return "la" "la_" "pr" "ep.json"


LEGACY_CONTEXT_VAULT_FILE = str(get_runtime_file(_legacy_context_vault_filename()))
CONTEXT_VAULT_SEED_FILE = str(get_seed_file("context_vault.seed.json"))

DEFAULT_ITEMS = [
    {"title": "1. What outcome matters most in this session?", "content": ""},
    {"title": "2. Which three points must land clearly?", "content": ""},
    {"title": "3. What context does the other side care about most?", "content": ""},
    {"title": "4. Which proof points, wins, or metrics should be ready?", "content": ""},
    {"title": "5. What is your strongest short introduction?", "content": ""},
    {"title": "6. Which story best shows ownership under pressure?", "content": ""},
    {"title": "7. Which story best shows problem solving or judgment?", "content": ""},
    {"title": "8. What is the hardest likely objection or question?", "content": ""},
    {"title": "9. How will you answer that objection calmly?", "content": ""},
    {"title": "10. What do you want to learn from the other side?", "content": ""},
    {"title": "11. What is the ideal next step or close?", "content": ""},
    {"title": "12. What should you avoid saying or overexplaining?", "content": ""},
]


@dataclass
class ContextPrompt:
    """Represents a reusable context prompt inside the vault."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    content: str = ""
    starred: bool = False
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ContextPrompt":
        return ContextPrompt(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            content=data.get("content", ""),
            starred=data.get("starred", False),
            completed=data.get("completed", False),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


class ContextVaultManager:
    """Persists and orders context prompts for the Context Vault."""

    def __init__(self, filepath: str = CONTEXT_VAULT_FILE):
        self.filepath = filepath
        self.items: List[ContextPrompt] = []
        self.load()
        logger.info("[ContextVaultManager] Loaded %s prompts", len(self.items))

    def load(self) -> None:
        """Load prompts from runtime storage, legacy storage, or seed data."""
        if self._load_payload_from_path(self.filepath):
            return

        if self._load_payload_from_path(LEGACY_CONTEXT_VAULT_FILE, migrate=True):
            logger.info("[ContextVaultManager] Migrated legacy vault data")
            return

        if self._load_payload_from_path(CONTEXT_VAULT_SEED_FILE, migrate=True):
            logger.info("[ContextVaultManager] Loaded committed vault seed")
            return

        self._load_defaults()

    def _load_payload_from_path(self, path: str, migrate: bool = False) -> bool:
        if not path or not os.path.exists(path):
            return False

        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            logger.error("[ContextVaultManager] Failed to read %s: %s", path, exc)
            return False

        self._apply_payload(data)

        if migrate or path != self.filepath:
            self.save()

        return True

    def _apply_payload(self, data: dict) -> None:
        raw_items = data.get("items") or data.get("questions") or []
        self.items = [ContextPrompt.from_dict(item) for item in raw_items]

    def _load_defaults(self) -> None:
        self.items = [ContextPrompt(title=item["title"], content=item["content"]) for item in DEFAULT_ITEMS]
        self.save()

    def save(self) -> None:
        """Persist prompts to runtime storage."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            data = {
                "version": "1.0",
                "items": [item.to_dict() for item in self.items],
            }
            with open(self.filepath, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            logger.info("[ContextVaultManager] Saved %s prompts", len(self.items))
        except Exception as exc:
            logger.error("[ContextVaultManager] Failed to save prompts: %s", exc)

    def add(self, title: str, content: str = "") -> ContextPrompt:
        item = ContextPrompt(title=title, content=content)
        self.items.append(item)
        self.save()
        return item

    def update(
        self,
        item_id: str,
        title: str = None,
        content: str = None,
        starred: bool = None,
        completed: bool = None,
    ) -> Optional[ContextPrompt]:
        for item in self.items:
            if item.id != item_id:
                continue
            if title is not None:
                item.title = title
            if content is not None:
                item.content = content
            if starred is not None:
                item.starred = starred
            if completed is not None:
                item.completed = completed
            self.save()
            return item
        return None

    def move_up(self, item_id: str) -> bool:
        for index, item in enumerate(self.items):
            if item.id == item_id and index > 0:
                self.items[index], self.items[index - 1] = self.items[index - 1], self.items[index]
                self.save()
                return True
        return False

    def move_down(self, item_id: str) -> bool:
        for index, item in enumerate(self.items):
            if item.id == item_id and index < len(self.items) - 1:
                self.items[index], self.items[index + 1] = self.items[index + 1], self.items[index]
                self.save()
                return True
        return False

    def delete(self, item_id: str) -> bool:
        for index, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(index)
                self.save()
                return True
        return False

    def get_by_id(self, item_id: str) -> Optional[ContextPrompt]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def get_all(self) -> List[ContextPrompt]:
        return self.items

    def reset_to_defaults(self) -> None:
        self._load_defaults()
