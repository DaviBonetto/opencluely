# -*- coding: utf-8 -*-
"""
Opencluely - AI Helper
Sprint 4: Respostas automáticas para perguntas de entrevista

Este módulo implementa:
- Integração com Groq Llama 3 70B API
- Prompt engineering otimizado para entrevistas
- Rate limit tracking (30 req/min)
- Execução em thread separada (não trava UI)
"""

import logging
import traceback
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

# Configurar logger
logger = logging.getLogger('ai_helper')

# Tentar importar Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    logger.info("Groq SDK importado com sucesso (AI Helper)")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK não disponível para AI Helper")


# ============================================================================
# CONSTANTES
# ============================================================================

# Modelo Groq atualizado (Jan 2025)
# Alternativas se não funcionar:
# - "llama-3.1-70b-versatile" 
# - "llama-3.1-8b-instant" (mais rápido, menor qualidade)
AI_MODEL = "llama-3.3-70b-versatile"  # Versão mais recente
AI_MAX_TOKENS = 500             # Limite de tokens na resposta
AI_TEMPERATURE = 0.7            # Criatividade (0-1)
AI_TIMEOUT = 15.0               # Timeout em segundos
RATE_LIMIT = 30                 # Máximo de requisições por minuto

# Prompt do sistema otimizado para entrevistas
SYSTEM_PROMPT = """Você é um assistente de preparação para entrevistas de emprego. 
Sua função é gerar respostas profissionais, concisas e estratégicas para perguntas de entrevista.

REGRAS IMPORTANTES:
- Respostas com 100-200 palavras (2-4 frases curtas e impactantes)
- Tom profissional mas natural (não robótico)
- Incluir exemplo concreto quando relevante
- Evitar clichês ("sou perfeccionista", "trabalho demais")
- Ser honesto mas estratégico
- Responder no MESMO IDIOMA da pergunta (português ou inglês)
- Estrutura: Resposta direta → Exemplo → Conclusão

NÃO inclua prefácios como "Claro!" ou "Com certeza!". Vá direto à resposta."""


class AIHelperTask(QRunnable):
    """
    Tarefa que executa a chamada à API Groq em thread separada.
    Evita travar a UI durante a geração de resposta.
    """
    
    class Signals(QObject):
        """Sinais para comunicação thread-safe."""
        started = pyqtSignal()
        finished = pyqtSignal(str)
        error = pyqtSignal(str)
    
    def __init__(self, client, question: str, resume_context: str = "", session_context: dict = None):
        super().__init__()
        self.client = client
        self.question = question
        self.resume_context = resume_context  # Contexto do currículo
        self.session_context = session_context or {}  # Contexto da sessão (Sprint E2)
        self.signals = self.Signals()
    
    @pyqtSlot()
    def run(self):
        """Executa a geração de resposta."""
        try:
            self.signals.started.emit()
            logger.info(f"[AIHelperTask] Gerando resposta para: '{self.question[:50]}...'")
            
            # DEBUG: Log session_context received
            print(f"[DEBUG AIHelperTask] session_context recebido: {self.session_context}")
            print(f"[DEBUG AIHelperTask] user_context: '{self.session_context.get('user_context', '')[:100]}...'")
            
            # Construir prompt do usuário
            user_prompt = f"""Pergunta da entrevista: "{self.question}"

Gere uma resposta profissional e estratégica para esta pergunta de entrevista."""
            
            # Usar system_instructions da sessão (se configurada) ou fallback
            if self.session_context.get("system_instructions"):
                system_prompt = self.session_context["system_instructions"]
                logger.info("[AIHelperTask] Usando system_instructions da sessão")
            else:
                system_prompt = SYSTEM_PROMPT
            
            # Adicionar user context da sessão
            if self.session_context.get("user_context"):
                system_prompt += f"\n\nUSER CONTEXT:\n{self.session_context['user_context']}"
                logger.info(f"[AIHelperTask] User context injetado: {len(self.session_context['user_context'])} chars")
            
            # Adicionar currículo (se houver)
            if self.resume_context:
                system_prompt += f"\n\nRESUME/CV:\n{self.resume_context}"
                logger.info(f"[AIHelperTask] Resume injetado: {len(self.resume_context)} chars")
            
            # Chamar API Groq
            response = self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                timeout=AI_TIMEOUT
            )
            
            # Extrair resposta
            answer = response.choices[0].message.content.strip()
            logger.info(f"[AIHelperTask] Resposta gerada: '{answer[:50]}...'")
            
            self.signals.finished.emit(answer)
            
        except Exception as e:
            error_msg = f"Erro ao gerar resposta: {str(e)}"
            logger.error(f"[AIHelperTask] {error_msg}")
            logger.error(traceback.format_exc())
            self.signals.error.emit(error_msg)


class AIHelper(QObject):
    """
    Gerenciador de respostas AI para perguntas de entrevista.
    
    Responsável por:
    - Gerenciar cliente Groq (Llama 3 70B)
    - Processar perguntas via QThreadPool
    - Controlar rate limit (30 req/min)
    - Emitir sinais quando resposta estiver pronta
    
    Sinais:
        answer_ready(str): Resposta gerada
        answer_started(): Iniciou processamento
        error_occurred(str): Erro ocorrido
        rate_limit_hit(): Limite de requisições atingido
    """
    
    # Sinais PyQt
    answer_ready = pyqtSignal(str)
    answer_started = pyqtSignal()
    error_occurred = pyqtSignal(str)
    rate_limit_hit = pyqtSignal()
    
    def __init__(self, api_key: str = None, parent=None):
        super().__init__(parent)
        
        self._client = None
        self._api_key = api_key
        self._is_ready = False
        self._is_processing = False
        
        # Rate limit tracking
        self._request_count = 0
        self._last_reset = datetime.now()
        
        # Thread pool
        self._thread_pool = QThreadPool.globalInstance()
        
        logger.info("[AIHelper] Inicializado")
    
    def initialize(self):
        """
        Inicializa o cliente Groq.
        Deve ser chamado após configurar a API key.
        """
        logger.info("[AIHelper] Inicializando cliente Groq...")
        
        if not GROQ_AVAILABLE:
            error_msg = "Groq SDK não disponível. Instale: pip install groq"
            logger.error(f"[AIHelper] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        if not self._api_key:
            error_msg = "API key não configurada"
            logger.error(f"[AIHelper] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
        
        try:
            self._client = Groq(api_key=self._api_key)
            self._is_ready = True
            logger.info("[AIHelper] ✓ Cliente Groq (Llama 3) configurado!")
            return True
            
        except Exception as e:
            error_msg = f"Erro ao configurar Groq: {str(e)}"
            logger.error(f"[AIHelper] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def generate_answer(self, question: str, resume_context: str = "", session_context: dict = None):
        """
        Gera resposta para uma pergunta de entrevista.
        Roda em thread separada para não travar a UI.
        
        Args:
            question: A pergunta transcrita
            resume_context: Contexto do currículo/notas (Sprint 5)
            session_context: Contexto da sessão com system_instructions e user_context (Sprint E2)
        """
        if not self._is_ready:
            self.error_occurred.emit("AI Helper não inicializado")
            return
        
        if self._is_processing:
            logger.warning("[AIHelper] Já está processando uma pergunta")
            return
        
        if not question or not question.strip():
            self.error_occurred.emit("Pergunta vazia")
            return
        
        # Verificar rate limit
        if not self._check_rate_limit():
            logger.warning("[AIHelper] Rate limit atingido!")
            self.rate_limit_hit.emit()
            return
        
        self._is_processing = True
        
        # Criar tarefa com contextos (Sprint E2)
        task = AIHelperTask(self._client, question.strip(), resume_context, session_context)
        
        # Conectar sinais
        task.signals.started.connect(self._on_task_started)
        task.signals.finished.connect(self._on_task_finished)
        task.signals.error.connect(self._on_task_error)
        
        # Executar no pool de threads
        self._thread_pool.start(task)
    
    def _check_rate_limit(self) -> bool:
        """
        Verifica se pode fazer requisição (máx 30/min).
        
        Returns:
            True se pode fazer requisição, False se atingiu limite
        """
        # Reset contador a cada minuto
        self._reset_counter_if_needed()
        
        # Verificar limite
        if self._request_count >= RATE_LIMIT:
            return False
        
        return True
    
    def _reset_counter_if_needed(self):
        """Reset contador se passou 1 minuto desde último reset."""
        now = datetime.now()
        if (now - self._last_reset) >= timedelta(minutes=1):
            self._request_count = 0
            self._last_reset = now
            logger.info("[AIHelper] Contador de rate limit resetado")
    
    def _on_task_started(self):
        """Callback quando tarefa inicia."""
        self._request_count += 1
        logger.info(f"[AIHelper] Requisições: {self._request_count}/{RATE_LIMIT}")
        self.answer_started.emit()
    
    def _on_task_finished(self, answer: str):
        """Callback quando tarefa termina com sucesso."""
        self._is_processing = False
        self.answer_ready.emit(answer)
    
    def _on_task_error(self, error_msg: str):
        """Callback quando tarefa falha."""
        self._is_processing = False
        self.error_occurred.emit(error_msg)
    
    def is_ready(self) -> bool:
        """Retorna True se AI Helper está pronto."""
        return self._is_ready
    
    def is_processing(self) -> bool:
        """Retorna True se está processando uma pergunta."""
        return self._is_processing
    
    def get_request_count(self) -> tuple:
        """Retorna (count, limit) para exibir na UI."""
        self._reset_counter_if_needed()
        return (self._request_count, RATE_LIMIT)


# ============================================================================
# TESTE STANDALONE
# ============================================================================

if __name__ == "__main__":
    import sys
    import os
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Obter API key do ambiente
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        print("❌ Configure GROQ_API_KEY")
        sys.exit(1)
    
    def on_started():
        print("⏳ Gerando resposta...")
    
    def on_ready(answer):
        print(f"\n✅ Resposta:\n{answer}\n")
        app.quit()
    
    def on_error(msg):
        print(f"❌ Erro: {msg}")
        app.quit()
    
    app = QApplication(sys.argv)
    
    helper = AIHelper(api_key=api_key)
    helper.initialize()
    helper.answer_started.connect(on_started)
    helper.answer_ready.connect(on_ready)
    helper.error_occurred.connect(on_error)
    
    # Testar com pergunta comum
    print("Pergunta: What is your biggest weakness?")
    helper.generate_answer("What is your biggest weakness?")
    
    # Timeout de 30 segundos
    QTimer.singleShot(30000, app.quit)
    
    sys.exit(app.exec_())
