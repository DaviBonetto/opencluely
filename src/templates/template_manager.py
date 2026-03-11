# -*- coding: utf-8 -*-
"""
ParakeetAI Clone - Template Manager
Sprint E2: Gerenciamento de templates de sessao

Responsabilidades:
- Carregar/salvar templates do JSON
- CRUD de templates
- Validacao
"""

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
    """Representa um template de sessao."""

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
    """Gerencia templates de sessao."""

    DEFAULT_CONFIG_PATH = str(get_runtime_file("templates.json"))
    DEFAULT_SEED_PATH = str(get_seed_file("templates.seed.json"))

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.templates: List[Template] = []
        self.last_used: str = "interview_assistant"
        self.language: str = "en"
        self._load()

    def _load(self) -> None:
        """Carrega templates do JSON."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self._apply_payload(data)
                logger.info("[TemplateManager] Carregados %s templates", len(self.templates))
                return

            if os.path.exists(self.DEFAULT_SEED_PATH):
                with open(self.DEFAULT_SEED_PATH, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self._apply_payload(data)
                logger.info("[TemplateManager] Seeds carregados: %s templates", len(self.templates))
                self.save()
                return

            logger.warning("[TemplateManager] Arquivo nao encontrado: %s", self.config_path)
            self._create_defaults()
        except Exception as exc:
            logger.error("[TemplateManager] Erro ao carregar: %s", exc)
            self._create_defaults()

    def _apply_payload(self, data: dict) -> None:
        self.last_used = data.get("last_used", "interview_assistant")
        self.language = data.get("language", "en")
        self.templates = [Template.from_dict(item) for item in data.get("templates", [])]

    def _create_defaults(self) -> None:
        """Cria templates padrao se nao existir arquivo."""
        self.templates = [
            Template(
                id="interview_assistant",
                name="Interview Assistant",
                description="General job interview helper",
                version=1,
                icon="💼",
                system_instructions="You are Interview Copilot. Provide ready-to-speak answers for job interviews.",
                user_context_example="Position: Developer\nCompany: Tech Corp",
                is_builtin=True,
            ),
            Template(
                id="custom",
                name="Custom",
                description="Create your own template",
                version=1,
                icon="✏️",
                system_instructions="",
                user_context_example="",
                is_builtin=True,
            ),
        ]
        self.save()

    def save(self) -> None:
        """Salva templates no JSON."""
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
            logger.info("[TemplateManager] Salvos %s templates", len(self.templates))
        except Exception as exc:
            logger.error("[TemplateManager] Erro ao salvar: %s", exc)

    def get_all(self) -> List[Template]:
        """Retorna todos os templates."""
        return self.templates

    def get_by_id(self, template_id: str) -> Optional[Template]:
        """Retorna template por ID."""
        for template in self.templates:
            if template.id == template_id:
                return template
        return None

    def get_last_used(self) -> Optional[Template]:
        """Retorna ultimo template usado."""
        return self.get_by_id(self.last_used)

    def set_last_used(self, template_id: str) -> None:
        """Define ultimo template usado."""
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
        """Cria novo template."""
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
        logger.info("[TemplateManager] Template criado: %s", template.name)
        return template

    def update(self, template_id: str, **kwargs) -> Optional[Template]:
        """Atualiza template existente."""
        template = self.get_by_id(template_id)
        if template and not template.is_builtin:
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            template.version += 1
            self.save()
            logger.info("[TemplateManager] Template atualizado: %s", template.name)
            return template
        return None

    def delete(self, template_id: str) -> bool:
        """Deleta template (apenas custom)."""
        template = self.get_by_id(template_id)
        if template and not template.is_builtin:
            self.templates.remove(template)
            self.save()
            logger.info("[TemplateManager] Template deletado: %s", template.name)
            return True
        return False


_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Retorna instancia singleton do TemplateManager."""
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager
