# -*- coding: utf-8 -*-
"""
ParakeetAI Clone - Analisador de Tela (Vision)
Sprint E3: Groq Llama Vision para análise de screenshots

Este módulo implementa:
- Captura de screenshot da tela
- Análise com Groq Llama 3.2 Vision (multimodal)
- Alta precisão para texto e código
- Processamento em thread separada
"""

import os
import re
import io
import base64
import time
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot

# Configurar logger
logger = logging.getLogger('screen_analyzer')

# Tentar importar bibliotecas necessárias
try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
    logger.info("Pillow (PIL) importado com sucesso")
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow não disponível")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
    logger.info("Groq SDK importado com sucesso (Vision)")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK não disponível")


# ============================================================================
# CONSTANTES
# ============================================================================

# Modelo de visão - Llama 4 Scout (Multimodal Preview)
# Substitui o Llama 3.2 Vision que foi descontinuado
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

VISION_TIMEOUT = 30

# Prompt otimizado para ANÁLISE e SOLUÇÃO (Multimodal Agent)
VISION_PROMPT = """Você é um assistente de IA especialista (Parakeet).
Analise esta captura de tela com atenção.

SE FOR CÓDIGO/PROBLEMA TÉCNICO:
1. Identifique o problema ou bug.
2. Forneça a solução corrigida ou resposta da questão.
3. Explique brevemente o raciocínio.

SE FOR TEXTO GERAL:
1. Resuma ou extraia as informações mais importantes.
2. Formate com clareza.

SE FOR INTERFACE (UI):
1. Descreva o que está acontecendo ou sugira melhorias se parecer um erro.

Responda SEMPRE em Português (Brasil).
Seja direto, técnico e prestativo. Use Markdown para formatar código."""


# ============================================================================
# TAREFA VISION (THREAD SEPARADA)
# ============================================================================

class VisionTask(QRunnable):
    """
    Tarefa que executa captura + análise de visão em thread separada.
    Usa Groq Llama Vision para análise de imagem.
    """
    
    class Signals(QObject):
        """Sinais para comunicação thread-safe."""
        started = pyqtSignal()
        completed = pyqtSignal(str)
        error = pyqtSignal(str)
        method_used = pyqtSignal(str)
    
    def __init__(self, groq_client):
        super().__init__()
        self.client = groq_client
        self.signals = self.Signals()
    
    @pyqtSlot()
    def run(self):
        """Executa captura e análise."""
        try:
            self.signals.started.emit()
            logger.info("=== Analyze Screen iniciado ===")
            
            # 1. Capturar screenshot
            screenshot = ImageGrab.grab()
            logger.info(f"[VisionTask] Screenshot capturado: {screenshot.size}")
            
            # 2. Analisar com Groq Vision
            start_time = time.time()
            
            try:
                logger.info("[VisionTask] Analisando com Groq Llama Vision...")
                text = self._analyze_with_groq(screenshot)
                elapsed = time.time() - start_time
                logger.info(f"✅ Groq Vision: sucesso ({len(text)} chars em {elapsed:.2f}s)")
                self.signals.method_used.emit("Llama 3.2 Vision")
                self.signals.completed.emit(text)
                
            except Exception as e:
                logger.error(f"❌ Groq Vision falhou: {e}")
                self.signals.error.emit(f"Análise falhou: {str(e)}")
            
        except Exception as e:
            error_msg = f"Erro na captura: {str(e)}"
            logger.error(f"[VisionTask] {error_msg}")
            self.signals.error.emit(error_msg)
    
    def _analyze_with_groq(self, screenshot: Image.Image) -> str:
        """
        Analisa screenshot usando Groq Llama Vision.
        
        Args:
            screenshot: PIL Image object
            
        Returns:
            Texto extraído
        """
        # 1. Reduzir resolução para otimizar (max 1280x720)
        max_width = 1280
        max_height = 720
        
        if screenshot.width > max_width or screenshot.height > max_height:
            # Manter proporção
            ratio = min(max_width / screenshot.width, max_height / screenshot.height)
            new_size = (int(screenshot.width * ratio), int(screenshot.height * ratio))
            screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"[VisionTask] Screenshot redimensionado para: {screenshot.size}")
        
        # 2. Converter para base64
        buffered = io.BytesIO()
        screenshot.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        logger.debug(f"[VisionTask] Imagem base64: {len(img_base64)} chars")
        
        # 3. Chamar Groq Vision API
        logger.info(f"[VisionTask] Enviando para Groq ({VISION_MODEL})...")
        
        response = self.client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": VISION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        # 4. Extrair texto
        text = response.choices[0].message.content.strip()
        
        logger.info(f"[VisionTask] Análise concluída: {len(text)} chars")
        
        return text


class ScreenAnalyzer(QObject):
    """
    Analisador de tela com Vision AI.
    
    Usa Groq Llama 3.2 Vision para análise de screenshots.
    
    Sinais:
        ocr_started(): quando análise começa
        ocr_completed(str): quando análise termina com sucesso
        ocr_method(str): método usado
        error_occurred(str): quando ocorre erro
    """
    
    # Sinais PyQt
    ocr_started = pyqtSignal()
    ocr_completed = pyqtSignal(str)
    ocr_method = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.client = None
        self.vision_available = False
        
        self._init_groq_client()
        
        logger.info("[ScreenAnalyzer] Inicializado")
    
    def _init_groq_client(self):
        """Inicializa cliente Groq para Vision."""
        if not GROQ_AVAILABLE:
            logger.warning("[ScreenAnalyzer] Groq SDK não disponível")
            return
        
        api_key = os.environ.get("GROQ_API_KEY", "")
        
        if not api_key or not api_key.startswith("gsk_"):
            logger.warning("[ScreenAnalyzer] GROQ_API_KEY não configurada")
            return
        
        try:
            self.client = Groq(api_key=api_key)
            self.vision_available = True
            logger.info("[ScreenAnalyzer] Groq Vision disponível (Llama 3.2)")
        except Exception as e:
            logger.error(f"[ScreenAnalyzer] Erro ao inicializar Groq: {e}")
    
    def capture_and_ocr(self):
        """
        Inicia captura de tela e análise.
        Executa em thread separada via QThreadPool.
        """
        if not self.vision_available:
            self.error_occurred.emit(
                "Análise de tela não disponível.\n"
                "Configure a GROQ_API_KEY."
            )
            return
        
        # Criar tarefa Vision
        from PyQt5.QtCore import QThreadPool
        
        task = VisionTask(self.client)
        
        # Conectar sinais
        task.signals.started.connect(self._on_started)
        task.signals.completed.connect(self._on_completed)
        task.signals.error.connect(self._on_error)
        task.signals.method_used.connect(self._on_method)
        
        # Executar em thread pool
        QThreadPool.globalInstance().start(task)
    
    def _on_started(self):
        """Handler quando análise inicia."""
        self.ocr_started.emit()
    
    def _on_completed(self, text: str):
        """Handler quando análise completa."""
        self.ocr_completed.emit(text)
    
    def _on_error(self, error_msg: str):
        """Handler quando ocorre erro."""
        self.error_occurred.emit(error_msg)
    
    def _on_method(self, method: str):
        """Handler para método usado."""
        self.ocr_method.emit(method)


# ============================================================================
# TESTE STANDALONE
# ============================================================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    
    app = QApplication(sys.argv)
    
    analyzer = ScreenAnalyzer()
    
    def on_completed(text):
        print(f"✅ Texto extraído ({len(text)} chars):")
        print(text[:500] + "..." if len(text) > 500 else text)
        app.quit()
    
    def on_error(msg):
        print(f"❌ Erro: {msg}")
        app.quit()
    
    def on_method(method):
        print(f"📝 Método usado: {method}")
    
    analyzer.ocr_completed.connect(on_completed)
    analyzer.error_occurred.connect(on_error)
    analyzer.ocr_method.connect(on_method)
    
    print("Analyze Screen Test (Groq Llama Vision)")
    print(f"  Vision disponível: {analyzer.vision_available}")
    print("\nCapturando tela em 2s...")
    
    QTimer.singleShot(2000, analyzer.capture_and_ocr)
    
    sys.exit(app.exec_())
