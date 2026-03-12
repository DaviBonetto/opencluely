# -*- coding: utf-8 -*-
"""
Opencluely - Módulo de Transcrição (Groq API)
Transcrição em tempo real via Groq Whisper API

Este módulo implementa:
- Transcrição de áudio via Groq Whisper API (gratuita)
- Conversão de áudio bytes → formato compatível
- Sinais PyQt para comunicação thread-safe

Vantagens do Groq:
- Sem instalação de modelo local (evita crash ctranslate2)
- Latência baixa (~0.5-1s)
- Qualidade superior (whisper-large-v3)
- 100% gratuito (30 req/min)
"""

import io
import wave
import logging
import traceback
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

# Configurar logger
logger = logging.getLogger('transcription_groq')

# Tentar importar Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    logger.info("Groq SDK importado com sucesso")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK não disponível. Instale: pip install groq")


# ============================================================================
# CONSTANTES
# ============================================================================

SAMPLE_RATE = 16000       # Taxa de amostragem
CHANNELS = 1              # Mono
SAMPLE_WIDTH = 2          # 16-bit = 2 bytes

# API Key - Configurar via variável de ambiente ou aqui
# Obtenha grátis em: https://console.groq.com/keys
GROQ_API_KEY = None  # Será configurado dinamicamente


class TranscriptionTaskGroq(QRunnable):
    """
    Tarefa de transcrição que roda no QThreadPool.
    Usa Groq Whisper API para transcrever áudio.
    """
    
    class Signals(QObject):
        """Sinais para comunicação thread-safe."""
        started = pyqtSignal()
        finished = pyqtSignal(str)
        error = pyqtSignal(str)
    
    def __init__(self, client, audio_bytes: bytes):
        super().__init__()
        self.client = client
        self.audio_bytes = audio_bytes
        self.signals = self.Signals()
    
    @pyqtSlot()
    def run(self):
        """Executa a transcrição do chunk de áudio."""
        try:
            self.signals.started.emit()
            logger.info(f"[TranscriptionTaskGroq] Processando {len(self.audio_bytes)} bytes")
            
            # Converter bytes PCM → arquivo WAV em memória
            wav_buffer = self._create_wav_buffer(self.audio_bytes)
            
            # Enviar para Groq API
            transcription = self.client.audio.transcriptions.create(
                file=("audio.wav", wav_buffer, "audio/wav"),
                model="whisper-large-v3",
                language=None,  # Auto-detect
                response_format="text"
            )
            
            text = transcription.strip() if transcription else ""
            logger.info(f"[TranscriptionTaskGroq] Resultado: '{text[:50]}...'")
            
            self.signals.finished.emit(text)
                
        except Exception as e:
            error_msg = f"Erro na transcrição Groq: {str(e)}"
            logger.error(f"[TranscriptionTaskGroq] {error_msg}")
            logger.error(traceback.format_exc())
            self.signals.error.emit(error_msg)
    
    def _create_wav_buffer(self, audio_bytes: bytes) -> io.BytesIO:
        """
        Converte bytes PCM para formato WAV em memória.
        
        Args:
            audio_bytes: Bytes de áudio (PCM 16-bit, 16kHz, mono)
        
        Returns:
            BytesIO contendo arquivo WAV válido
        """
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(SAMPLE_WIDTH)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_bytes)
        
        wav_buffer.seek(0)
        return wav_buffer


class TranscriberGroq(QObject):
    """
    Gerenciador de transcrição de áudio via Groq API.
    
    Responsável por:
    - Gerenciar cliente Groq
    - Processar chunks de áudio via QThreadPool
    - Emitir sinais quando transcrição estiver pronta
    
    Sinais:
        transcription_ready(str): Texto transcrito
        transcription_started(): Iniciou processamento
        error_occurred(str): Erro ocorrido
        model_loading(): Iniciando configuração
        model_loaded(): Pronto para uso
    """
    
    # Sinais PyQt
    transcription_ready = pyqtSignal(str)
    transcription_started = pyqtSignal()
    error_occurred = pyqtSignal(str)
    model_loading = pyqtSignal()
    model_loaded = pyqtSignal()
    
    def __init__(self, api_key: str = None, parent=None):
        super().__init__(parent)
        
        self._client = None
        self._is_ready = False
        self._api_key = api_key or GROQ_API_KEY
        self._thread_pool = QThreadPool.globalInstance()
        self._thread_pool.setMaxThreadCount(2)
        
        logger.info("[TranscriberGroq] Inicializado")
    
    def load_model(self):
        """
        Configura o cliente Groq.
        (Não há modelo local para carregar, mas mantemos a interface)
        """
        logger.info("[TranscriberGroq] Configurando cliente Groq...")
        self.model_loading.emit()
        
        if not GROQ_AVAILABLE:
            error_msg = "Groq SDK não disponível. Instale: pip install groq"
            logger.error(f"[TranscriberGroq] {error_msg}")
            self.error_occurred.emit(error_msg)
            return
        
        if not self._api_key:
            error_msg = "API key Groq não configurada. Obtenha grátis em: https://console.groq.com/keys"
            logger.error(f"[TranscriberGroq] {error_msg}")
            self.error_occurred.emit(error_msg)
            return
        
        try:
            self._client = Groq(api_key=self._api_key)
            self._is_ready = True
            logger.info("[TranscriberGroq] ✓ Cliente Groq configurado com sucesso!")
            self.model_loaded.emit()
            
        except Exception as e:
            error_msg = f"Erro ao configurar Groq: {str(e)}"
            logger.error(f"[TranscriberGroq] {error_msg}")
            logger.error(traceback.format_exc())
            self.error_occurred.emit(error_msg)
    
    def set_api_key(self, api_key: str):
        """Define a API key do Groq."""
        self._api_key = api_key
        logger.info("[TranscriberGroq] API key configurada")
    
    def transcribe_chunk(self, audio_bytes: bytes):
        """
        Transcreve um chunk de áudio.
        
        Args:
            audio_bytes: Bytes de áudio (PCM 16-bit, 16kHz, mono)
        """
        if not self._is_ready:
            self.error_occurred.emit("Cliente Groq não configurado.")
            return
        
        if not audio_bytes:
            return
        
        # Criar tarefa de transcrição
        task = TranscriptionTaskGroq(self._client, audio_bytes)
        
        # Conectar sinais
        task.signals.started.connect(self._on_transcription_started)
        task.signals.finished.connect(self._on_transcription_finished)
        task.signals.error.connect(self._on_transcription_error)
        
        # Executar no pool de threads
        self._thread_pool.start(task)
    
    def _on_transcription_started(self):
        """Callback quando transcrição inicia."""
        self.transcription_started.emit()
    
    def _on_transcription_finished(self, text: str):
        """Callback quando transcrição termina."""
        self.transcription_ready.emit(text)
    
    def _on_transcription_error(self, error_msg: str):
        """Callback quando há erro na transcrição."""
        self.error_occurred.emit(error_msg)
    
    def is_model_loaded(self) -> bool:
        """Retorna True se cliente está pronto."""
        return self._is_ready
    
    def cleanup(self):
        """Limpa recursos."""
        self._client = None
        self._is_ready = False


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
        print("   export GROQ_API_KEY='sua_key_aqui'")
        sys.exit(1)
    
    def on_loaded():
        print("✓ Cliente Groq configurado!")
        # Criar áudio de teste (3 segundos de silêncio)
        test_audio = bytes(96000)  # 3s × 16kHz × 2 bytes
        transcriber.transcribe_chunk(test_audio)
    
    def on_ready(text):
        print(f"Transcrição: '{text}'")
        app.quit()
    
    def on_error(msg):
        print(f"Erro: {msg}")
        app.quit()
    
    app = QApplication(sys.argv)
    
    transcriber = TranscriberGroq(api_key=api_key)
    transcriber.model_loaded.connect(on_loaded)
    transcriber.transcription_ready.connect(on_ready)
    transcriber.error_occurred.connect(on_error)
    
    print("Configurando cliente Groq...")
    transcriber.load_model()
    
    # Timeout de 30 segundos
    QTimer.singleShot(30000, app.quit)
    
    sys.exit(app.exec_())
