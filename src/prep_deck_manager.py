# -*- coding: utf-8 -*-
"""
Opencluely - Prep Deck manager.

Stores reusable prep prompts for interviews, calls, and other live sessions.
"""

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional

try:
    from storage_paths import get_runtime_file
except ImportError:
    from src.storage_paths import get_runtime_file

try:
    from brand import PREP_DECK_NAME
except ImportError:
    from src.brand import PREP_DECK_NAME

logger = logging.getLogger("prep_deck_manager")

PREP_DECK_FILE = str(get_runtime_file("prep_deck.json"))
LEGACY_PREP_FILE = str(get_runtime_file("lala_prep.json"))

DEFAULT_PROMPTS = [
    {"title": "1. What outcome matters most in this conversation?", "content": ""},
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
class PrepQuestion:
    """A reusable preparation prompt."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    content: str = ""
    starred: bool = False
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "PrepQuestion":
        return PrepQuestion(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            content=data.get("content", ""),
            starred=data.get("starred", False),
            completed=data.get("completed", False),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


class PrepDeckManager:
    """Persistent store for Opencluely Prep Deck prompts."""

    def __init__(self, filepath: str = PREP_DECK_FILE):
        self.filepath = filepath
        self.questions: List[PrepQuestion] = []
        self.load()
        logger.info("[%s] Loaded %s prompts", PREP_DECK_NAME, len(self.questions))

    def load(self) -> None:
        """Load prompts from the primary file or legacy fallback."""
        candidates = [self.filepath]
        if self.filepath != LEGACY_PREP_FILE:
            candidates.append(LEGACY_PREP_FILE)

        for path in candidates:
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.questions = [PrepQuestion.from_dict(question) for question in data.get("questions", [])]
                if path != self.filepath:
                    logger.info("[%s] Migrating prompts from legacy runtime file", PREP_DECK_NAME)
                    self.save()
                return
            except Exception as exc:
                logger.error("[%s] Load failed: %s", PREP_DECK_NAME, exc)
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load built-in prompts."""
        self.questions = [PrepQuestion(title=item["title"], content=item["content"]) for item in DEFAULT_PROMPTS]
        self.save()

    def save(self) -> None:
        """Persist prompts to disk."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            data = {
                "version": "1.0",
                "questions": [question.to_dict() for question in self.questions],
            }
            with open(self.filepath, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            logger.info("[%s] Saved %s prompts", PREP_DECK_NAME, len(self.questions))
        except Exception as exc:
            logger.error("[%s] Save failed: %s", PREP_DECK_NAME, exc)

    def add(self, title: str, content: str = "") -> PrepQuestion:
        """Add a new prompt."""
        question = PrepQuestion(title=title, content=content)
        self.questions.append(question)
        self.save()
        return question

    def update(
        self,
        question_id: str,
        title: str = None,
        content: str = None,
        starred: bool = None,
        completed: bool = None,
    ) -> Optional[PrepQuestion]:
        """Update an existing prompt."""
        for question in self.questions:
            if question.id != question_id:
                continue
            if title is not None:
                question.title = title
            if content is not None:
                question.content = content
            if starred is not None:
                question.starred = starred
            if completed is not None:
                question.completed = completed
            self.save()
            return question
        return None

    def move_up(self, question_id: str) -> bool:
        """Move a prompt higher in the list."""
        for index, question in enumerate(self.questions):
            if question.id == question_id and index > 0:
                self.questions[index], self.questions[index - 1] = self.questions[index - 1], self.questions[index]
                self.save()
                return True
        return False

    def move_down(self, question_id: str) -> bool:
        """Move a prompt lower in the list."""
        for index, question in enumerate(self.questions):
            if question.id == question_id and index < len(self.questions) - 1:
                self.questions[index], self.questions[index + 1] = self.questions[index + 1], self.questions[index]
                self.save()
                return True
        return False

    def delete(self, question_id: str) -> bool:
        """Delete a prompt."""
        for index, question in enumerate(self.questions):
            if question.id == question_id:
                self.questions.pop(index)
                self.save()
                return True
        return False

    def get_by_id(self, question_id: str) -> Optional[PrepQuestion]:
        """Get a prompt by ID."""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def get_all(self) -> List[PrepQuestion]:
        """Return all prompts."""
        return self.questions

    def reset_to_defaults(self) -> None:
        """Reset to the built-in prompts."""
        self._load_defaults()
