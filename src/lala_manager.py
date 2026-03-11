# -*- coding: utf-8 -*-
"""
ParakeetAI Clone - LALA Interview Prep Manager
Gerencia perguntas e respostas para preparacao de entrevista LALA

Features:
- 21 perguntas pre-definidas
- CRUD completo
- Persistencia em JSON
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

logger = logging.getLogger("lala_manager")

LALA_FILE = str(get_runtime_file("lala_prep.json"))

DEFAULT_QUESTIONS = [
    {"title": "1. Por que o LALA?", "content": ""},
    {"title": "2. Descreva sua personalidade em 3 palavras", "content": ""},
    {"title": "3. Qual foi um momento desafiador na sua vida?", "content": ""},
    {"title": "4. Onde voce se ve em 5-10 anos?", "content": ""},
    {"title": "5. Se voce tivesse recursos ilimitados, o que faria para melhorar sua comunidade?", "content": ""},
    {"title": "6. Qual tipo de suporte voce gostaria de ter hoje e que ainda nao tem?", "content": ""},
    {"title": "7. Como voce lida com desafios e conflitos dentro de um grupo?", "content": ""},
    {"title": "8. Fale uma coisa pela qual voce esta completamente obcecado hoje.", "content": ""},
    {"title": "9. O que e sucesso para voce?", "content": ""},
    {"title": "10. O que te inspira a continuar crescendo e aprendendo?", "content": ""},
    {"title": "11. Como voce equilibra seu tempo?", "content": ""},
    {"title": "12. Me conta um pouco sobre voce e sua trajetoria ate aqui.", "content": ""},
    {"title": "13. O que te motivou a aplicar para a LALA?", "content": ""},
    {"title": "14. Qual foi uma experiencia em que voce precisou demonstrar lideranca?", "content": ""},
    {"title": "15. Me fale sobre um projeto ou iniciativa em que voce fez a diferenca.", "content": ""},
    {"title": "16. Se pudesse criar um projeto social, qual seria e por que?", "content": ""},
    {"title": "17. Qual problema social te preocupa e como voce pode ajudar a resolvelo?", "content": ""},
    {"title": "18. Se pudesse mudar algo na sua comunidade hoje, o que seria e como faria isso?", "content": ""},
    {"title": "19. O que voce espera aprender e contribuir dentro da LALA?", "content": ""},
    {"title": "20. Como pretende aplicar o que aprender na LALA no seu futuro?", "content": ""},
    {"title": "21. Por que voce acredita que deveria ser escolhido para o programa?", "content": ""}
]


@dataclass
class LALAQuestion:
    """Representa uma pergunta LALA."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    content: str = ""
    starred: bool = False
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "LALAQuestion":
        return LALAQuestion(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            content=data.get("content", ""),
            starred=data.get("starred", False),
            completed=data.get("completed", False),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


class LALAManager:
    """Gerenciador de perguntas LALA com persistencia."""

    def __init__(self, filepath: str = LALA_FILE):
        self.filepath = filepath
        self.questions: List[LALAQuestion] = []
        self.load()
        logger.info("[LALAManager] Carregadas %s perguntas", len(self.questions))

    def load(self) -> None:
        """Carrega perguntas do arquivo JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.questions = [LALAQuestion.from_dict(question) for question in data.get("questions", [])]
                return
            except Exception as exc:
                logger.error("[LALAManager] Erro ao carregar: %s", exc)
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Carrega perguntas padrao."""
        self.questions = [LALAQuestion(title=item["title"], content=item["content"]) for item in DEFAULT_QUESTIONS]
        self.save()

    def save(self) -> None:
        """Salva perguntas no arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            data = {
                "version": "1.0",
                "questions": [question.to_dict() for question in self.questions],
            }
            with open(self.filepath, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            logger.info("[LALAManager] Salvas %s perguntas", len(self.questions))
        except Exception as exc:
            logger.error("[LALAManager] Erro ao salvar: %s", exc)

    def add(self, title: str, content: str = "") -> LALAQuestion:
        """Adiciona nova pergunta."""
        question = LALAQuestion(title=title, content=content)
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
    ) -> Optional[LALAQuestion]:
        """Atualiza pergunta existente."""
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
        """Move pergunta para cima na lista."""
        for index, question in enumerate(self.questions):
            if question.id == question_id and index > 0:
                self.questions[index], self.questions[index - 1] = self.questions[index - 1], self.questions[index]
                self.save()
                return True
        return False

    def move_down(self, question_id: str) -> bool:
        """Move pergunta para baixo na lista."""
        for index, question in enumerate(self.questions):
            if question.id == question_id and index < len(self.questions) - 1:
                self.questions[index], self.questions[index + 1] = self.questions[index + 1], self.questions[index]
                self.save()
                return True
        return False

    def delete(self, question_id: str) -> bool:
        """Remove pergunta."""
        for index, question in enumerate(self.questions):
            if question.id == question_id:
                self.questions.pop(index)
                self.save()
                return True
        return False

    def get_by_id(self, question_id: str) -> Optional[LALAQuestion]:
        """Busca pergunta por ID."""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def get_all(self) -> List[LALAQuestion]:
        """Retorna todas as perguntas."""
        return self.questions

    def reset_to_defaults(self) -> None:
        """Reseta para perguntas padrao."""
        self._load_defaults()
