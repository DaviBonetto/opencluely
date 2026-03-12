# -*- coding: utf-8 -*-
"""
Opencluely - Notes Manager
Sprint E5: Sistema de notas com persistencia

Gerencia notas do usuario com:
- CRUD (Create, Read, Update, Delete)
- Persistencia em JSON
- Titulos e conteudo
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

logger = logging.getLogger("notes_manager")

NOTES_FILE = str(get_runtime_file("notes.json"))


@dataclass
class Note:
    """Representa uma nota do usuario."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = "Nova Nota"
    content: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Note":
        return Note(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", "Sem Titulo"),
            content=data.get("content", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


class NotesManager:
    """Gerenciador de notas com persistencia local."""

    def __init__(self, filepath: str = NOTES_FILE):
        self.filepath = filepath
        self.notes: List[Note] = []
        self.load()
        logger.info("[NotesManager] Carregadas %s notas", len(self.notes))

    def load(self) -> None:
        """Carrega notas do arquivo JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.notes = [Note.from_dict(note) for note in data.get("notes", [])]
                return
            except Exception as exc:
                logger.error("[NotesManager] Erro ao carregar: %s", exc)

        self.notes = []
        self.add("Interview Notes", "Capture stories, reminders, and proof points here.")

    def save(self) -> None:
        """Salva notas no arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            data = {
                "version": "1.0",
                "notes": [note.to_dict() for note in self.notes],
            }
            with open(self.filepath, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            logger.info("[NotesManager] Salvas %s notas", len(self.notes))
        except Exception as exc:
            logger.error("[NotesManager] Erro ao salvar: %s", exc)

    def add(self, title: str = "Nova Nota", content: str = "") -> Note:
        """Adiciona nova nota."""
        note = Note(title=title, content=content)
        self.notes.append(note)
        self.save()
        logger.info("[NotesManager] Nota adicionada: %s", note.title)
        return note

    def update(self, note_id: str, title: str = None, content: str = None) -> Optional[Note]:
        """Atualiza nota existente."""
        for note in self.notes:
            if note.id != note_id:
                continue
            if title is not None:
                note.title = title
            if content is not None:
                note.content = content
            note.updated_at = datetime.now().isoformat()
            self.save()
            logger.info("[NotesManager] Nota atualizada: %s", note.title)
            return note
        return None

    def delete(self, note_id: str) -> bool:
        """Remove nota."""
        for index, note in enumerate(self.notes):
            if note.id != note_id:
                continue
            deleted = self.notes.pop(index)
            self.save()
            logger.info("[NotesManager] Nota removida: %s", deleted.title)
            return True
        return False

    def get_by_id(self, note_id: str) -> Optional[Note]:
        """Busca nota por ID."""
        for note in self.notes:
            if note.id == note_id:
                return note
        return None

    def get_all(self) -> List[Note]:
        """Retorna todas as notas."""
        return self.notes

    def get_titles(self) -> List[tuple]:
        """Retorna lista de (id, title) para exibicao."""
        return [(note.id, note.title) for note in self.notes]
