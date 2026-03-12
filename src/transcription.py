# -*- coding: utf-8 -*-
"""
Opencluely - Modulo de Transcricao
Sprint 3: Transcrição em tempo real com faster-whisper

Este módulo implementa:
- Carregamento do modelo faster-whisper (tiny)
- Conversão de áudio bytes → numpy array
- Transcrição de chunks de áudio
- Sinais PyQt para comunicação thread-safe
"""

import re
import logging
import sys
import traceback
import numpy as np
from PyQt5.QtCore import QObject, QThread, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

# Configurar logger
logger = logging.getLogger('transcription')

# Importar faster-whisper com tratamento de erro
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
    logger.info("faster-whisper importado com sucesso")
except ImportError as e:
    WHISPER_AVAILABLE = False
    logger.error(f"faster-whisper não encontrado: {e}")
    print("⚠️ Biblioteca 'faster-whisper' não encontrada.")
    print("   Instale via: pip install faster-whisper")


# ============================================================================
# CONSTANTES
# ============================================================================

MODEL_SIZE = "tiny"           # Modelo tiny (~39MB, mais rápido)
DEVICE = "cpu"                # CPU (sem GPU)
COMPUTE_TYPE = "int8"         # Quantização para performance
SAMPLE_RATE = 16000           # Taxa de amostragem esperada


class ModelLoaderThread(QThread):
    """
    Thread separada para carregar o modelo faster-whisper.
    Evita travar a UI durante o carregamento inicial.
    """
    
    finished = pyqtSignal(object)  # Emite o modelo carregado
    error = pyqtSignal(str)        # Emite erro se falhar
    
    def run(self):
        """Carrega o modelo faster-whisper."""
        logger.info("[ModelLoaderThread] Iniciando carregamento do modelo...")
        try:
            logger.info(f"[ModelLoaderThread] Modelo: {MODEL_SIZE}, Device: {DEVICE}")
            print(f"[Transcriber] Carregando modelo '{MODEL_SIZE}'...")
            print(f"[Transcriber] Isso pode levar 1-2 minutos na primeira execução.")
            
            model = WhisperModel(
                MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                download_root=None  # Usa cache padrão (~/.cache/huggingface/)
            )
            
            logger.info("[ModelLoaderThread] Modelo carregado com SUCESSO!")
            print(f"[Transcriber] ✓ Modelo carregado com sucesso!")
            self.finished.emit(model)
            
        except Exception as e:
            error_msg = f"Erro ao carregar modelo: {str(e)}"
            logger.error(f"[ModelLoaderThread] {error_msg}")
            logger.error(traceback.format_exc())
            print(f"[Transcriber] ❌ {error_msg}")
            self.error.emit(error_msg)


class TranscriptionTask(QRunnable):
    """
    Tarefa de transcrição que roda no QThreadPool.
    Permite processar múltiplos chunks sem bloquear.
    """
    
    class Signals(QObject):
        """Sinais para comunicação thread-safe."""
        started = pyqtSignal()
        finished = pyqtSignal(str)
        error = pyqtSignal(str)
    
    def __init__(self, model, audio_bytes: bytes):
        super().__init__()
        self.model = model
        self.audio_bytes = audio_bytes
        self.signals = self.Signals()
    
    @pyqtSlot()
    def run(self):
        """Executa a transcrição do chunk de áudio."""
        try:
            self.signals.started.emit()
            
            # Converter bytes → numpy array
            audio_array = self._convert_bytes_to_array(self.audio_bytes)
            
            # Transcrever
            segments, info = self.model.transcribe(
                audio_array,
                language=None,      # Auto-detecta idioma
                beam_size=1,        # Mais rápido
                vad_filter=True,    # Filtrar silêncio
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                )
            )
            
            # Extrair texto
            text_parts = [segment.text for segment in segments]
            full_text = " ".join(text_parts).strip()
            
            # Limpar formatação
            clean_text = self._clean_transcription(full_text)
            
            # Emitir resultado
            if clean_text:
                self.signals.finished.emit(clean_text)
            else:
                self.signals.finished.emit("")  # Silêncio
                
        except Exception as e:
            self.signals.error.emit(f"Erro na transcrição: {str(e)}")
    
    def _convert_bytes_to_array(self, audio_bytes: bytes) -> np.ndarray:
        """
        Converte bytes de áudio PCM 16-bit → numpy array float32.
        
        Args:
            audio_bytes: Bytes de áudio (PCM 16-bit, 16kHz, mono)
        
        Returns:
            numpy array float32 com valores normalizados (-1.0 a 1.0)
        """
        # bytes → int16
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # int16 → float32 normalizado
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        
        return audio_float32
    
    def _clean_transcription(self, text: str) -> str:
        """
        Remove formatação estranha do whisper.
        
        Args:
            text: Texto bruto do whisper
        
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        # Remover espaços múltiplos
        text = re.sub(r'\s+', ' ', text)
        
        # Remover espaço antes de pontuação
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        
        # Remover pontuação duplicada
        text = re.sub(r'([.,!?])\1+', r'\1', text)
        
        # Trim
        text = text.strip()
        
        # Capitalizar primeira letra
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        
        return text


class Transcriber(QObject):
    """
    Gerenciador de transcrição de áudio.
    
    Responsável por:
    - Carregar modelo faster-whisper em background
    - Processar chunks de áudio via QThreadPool
    - Emitir sinais quando transcrição estiver pronta
    
    Sinais:
        transcription_ready(str): Texto transcrito
        transcription_started(): Iniciou processamento
        error_occurred(str): Erro ocorrido
        model_loading(): Modelo começando a carregar
        model_loaded(): Modelo pronto para uso
    """
    
    # Sinais PyQt
    transcription_ready = pyqtSignal(str)
    transcription_started = pyqtSignal()
    error_occurred = pyqtSignal(str)
    model_loading = pyqtSignal()
    model_loaded = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._model = None
        self._is_model_loaded = False
        self._loader_thread = None
        self._thread_pool = QThreadPool.globalInstance()
        
        # Limitar threads para não sobrecarregar CPU
        self._thread_pool.setMaxThreadCount(2)
    
    def load_model(self):
        """
        Carrega o modelo faster-whisper em thread separada.
        Emite model_loading ao iniciar e model_loaded ao terminar.
        """
        if not WHISPER_AVAILABLE:
            self.error_occurred.emit(
                "faster-whisper não disponível.\n"
                "Instale via: pip install faster-whisper"
            )
            return
        
        if self._is_model_loaded:
            self.model_loaded.emit()
            return
        
        if self._loader_thread is not None and self._loader_thread.isRunning():
            return  # Já está carregando
        
        # Emitir sinal de loading
        self.model_loading.emit()
        
        # Criar e iniciar thread de carregamento
        self._loader_thread = ModelLoaderThread()
        self._loader_thread.finished.connect(self._on_model_loaded)
        self._loader_thread.error.connect(self._on_model_error)
        self._loader_thread.start()
    
    def _on_model_loaded(self, model):
        """Callback quando modelo é carregado com sucesso."""
        self._model = model
        self._is_model_loaded = True
        self.model_loaded.emit()
    
    def _on_model_error(self, error_msg: str):
        """Callback quando há erro ao carregar modelo."""
        self._is_model_loaded = False
        self.error_occurred.emit(error_msg)
    
    def transcribe_chunk(self, audio_bytes: bytes):
        """
        Transcreve um chunk de áudio.
        
        Args:
            audio_bytes: Bytes de áudio (PCM 16-bit, 16kHz, mono)
        """
        if not self._is_model_loaded:
            self.error_occurred.emit("Modelo ainda não carregado.")
            return
        
        if not audio_bytes:
            return
        
        # Criar tarefa de transcrição
        task = TranscriptionTask(self._model, audio_bytes)
        
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
        """Retorna True se modelo está carregado."""
        return self._is_model_loaded
    
    def cleanup(self):
        """Limpa recursos."""
        if self._loader_thread is not None:
            self._loader_thread.quit()
            self._loader_thread.wait(2000)
        self._model = None


# ============================================================================
# TESTE STANDALONE
# ============================================================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    
    def on_loaded():
        print("✓ Modelo carregado!")
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
    
    transcriber = Transcriber()
    transcriber.model_loaded.connect(on_loaded)
    transcriber.transcription_ready.connect(on_ready)
    transcriber.error_occurred.connect(on_error)
    
    print("Carregando modelo...")
    transcriber.load_model()
    
    # Timeout de 5 minutos
    QTimer.singleShot(300000, app.quit)
    
    sys.exit(app.exec_())
