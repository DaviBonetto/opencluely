# -*- coding: utf-8 -*-
"""
Opencluely - Brief Manager
Reusable session-brief persistence and CRUD helpers.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from typing import List, Optional

try:
    from storage_paths import get_runtime_file, get_seed_file
except ImportError:
    from src.storage_paths import get_runtime_file, get_seed_file

logger = logging.getLogger("template_manager")


@dataclass
class Template:
    """Represents a reusable session brief."""

    id: str
    name: str
    description: str
    version: int
    icon: str
    system_instructions: str
    user_context_example: str
    is_builtin: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            version=data.get("version", 1),
            icon=data.get("icon", "📄"),
            system_instructions=data.get("system_instructions", ""),
            user_context_example=data.get("user_context_example", ""),
            is_builtin=data.get("is_builtin", False),
        )


class TemplateManager:
    """Manage reusable session briefs."""

    DEFAULT_CONFIG_PATH = str(get_runtime_file("templates.json"))
    DEFAULT_SEED_PATH = str(get_seed_file("templates.seed.json"))

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.templates: List[Template] = []
        self.last_used: str = "interview_assistant"
        self.language: str = "en"
        self._load()

    def _load(self) -> None:
        """Load runtime data or seeds."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self._apply_payload(data)
                logger.info("[TemplateManager] Loaded %s briefs", len(self.templates))
                return

            if os.path.exists(self.DEFAULT_SEED_PATH):
                with open(self.DEFAULT_SEED_PATH, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self._apply_payload(data)
                logger.info("[TemplateManager] Loaded %s seed briefs", len(self.templates))
                self.save()
                return

            logger.warning("[TemplateManager] Brief file not found: %s", self.config_path)
            self._create_defaults()
        except Exception as exc:
            logger.error("[TemplateManager] Failed to load briefs: %s", exc)
            self._create_defaults()

    def _apply_payload(self, data: dict) -> None:
        self.last_used = data.get("last_used", "interview_assistant")
        self.language = data.get("language", "en")
        self.templates = [Template.from_dict(item) for item in data.get("templates", [])]

    def _create_defaults(self) -> None:
        """Create built-in briefs when no runtime file exists."""
        self.templates = [
            Template(
                id="interview_assistant",
                name="Interview Loop",
                description="Structured support for hiring conversations and candidate stories",
                version=1,
                icon="💼",
                system_instructions=(
                    "You are Opencluely Assist. Help the operator answer clearly, "
                    "confidently, and with credible detail during an interview."
                ),
                user_context_example=(
                    "Role: Backend Engineer\n"
                    "Company: Acme Cloud\n"
                    "Themes to emphasize: ownership, debugging, APIs"
                ),
                is_builtin=True,
            ),
            Template(
                id="leetcode_helper",
                name="Technical Review",
                description="Code-focused reasoning for live problem solving and architecture prompts",
                version=1,
                icon="🧩",
                system_instructions=(
                    "You are Opencluely Assist. Explain the approach, highlight tradeoffs, "
                    "produce concise Python code when needed, and summarize complexity."
                ),
                user_context_example=(
                    "Preparing for: systems design or coding round\n"
                    "Preferred language: Python\n"
                    "Watch for: graphs, DP, edge cases"
                ),
                is_builtin=True,
            ),
            Template(
                id="sales_assistant",
                name="Sales Call",
                description="Clear objection handling and value framing for customer conversations",
                version=1,
                icon="📈",
                system_instructions=(
                    "You are Opencluely Assist. Keep responses concise, commercially sharp, "
                    "and anchored in customer value with a clear next step."
                ),
                user_context_example=(
                    "Product: B2B SaaS platform\n"
                    "Key pain: manual reporting\n"
                    "Goal: secure next meeting"
                ),
                is_builtin=True,
            ),
            Template(
                id="custom",
                name="Blank Brief",
                description="Start from a clean brief",
                version=1,
                icon="✏️",
                system_instructions="",
                user_context_example="",
                is_builtin=True,
            ),
        ]
        self.save()

    def save(self) -> None:
        """Persist briefs to the runtime JSON file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {
                "version": "1.0",
                "last_used": self.last_used,
                "language": self.language,
                "templates": [template.to_dict() for template in self.templates],
            }
            with open(self.config_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
            logger.info("[TemplateManager] Saved %s briefs", len(self.templates))
        except Exception as exc:
            logger.error("[TemplateManager] Failed to save briefs: %s", exc)

    def get_all(self) -> List[Template]:
        return self.templates

    def get_by_id(self, template_id: str) -> Optional[Template]:
        for template in self.templates:
            if template.id == template_id:
                return template
        return None

    def get_last_used(self) -> Optional[Template]:
        return self.get_by_id(self.last_used)

    def set_last_used(self, template_id: str) -> None:
        self.last_used = template_id
        self.save()

    def create(
        self,
        name: str,
        description: str,
        icon: str,
        system_instructions: str,
        user_context_example: str = "",
    ) -> Template:
        template = Template(
            id=f"custom_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            version=1,
            icon=icon,
            system_instructions=system_instructions,
            user_context_example=user_context_example,
            is_builtin=False,
        )
        self.templates.append(template)
        self.save()
        logger.info("[TemplateManager] Created brief: %s", template.name)
        return template

    def update(self, template_id: str, **kwargs) -> Optional[Template]:
        template = self.get_by_id(template_id)
        if template and not template.is_builtin:
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            template.version += 1
            self.save()
            logger.info("[TemplateManager] Updated brief: %s", template.name)
            return template
        return None

    def delete(self, template_id: str) -> bool:
        template = self.get_by_id(template_id)
        if template and not template.is_builtin:
            self.templates.remove(template)
            self.save()
            logger.info("[TemplateManager] Deleted brief: %s", template.name)
            return True
        return False


_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Return a singleton TemplateManager instance."""
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager
