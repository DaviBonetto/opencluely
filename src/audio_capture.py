# -*- coding: utf-8 -*-
"""
ParakeetAI Clone - Módulo de Captura de Áudio Dual
Captura MICROFONE + SISTEMA (WASAPI Loopback) simultaneamente

Este módulo implementa:
- Captura de microfone (input) via pyaudiowpatch
- Captura de áudio do sistema (loopback) via WASAPI
- Mixagem dos dois streams
- Resampling 48kHz→16kHz para sistema
- Emissão de chunks de 3 segundos
"""

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime
import logging

logger = logging.getLogger('audio_capture')

# Importar pyaudiowpatch (fork com WASAPI loopback)
try:
    import pyaudiowpatch as pyaudio
    PYAUDIO_AVAILABLE = True
    logger.info("pyaudiowpatch importado com sucesso")
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("pyaudiowpatch não encontrado. Instale: pip install pyaudiowpatch")
    pyaudio = None

# Importar scipy para resample
try:
    from scipy import signal as scipy_signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy não encontrado. Resample desabilitado.")


# ============================================================================
# CONSTANTES
# ============================================================================

TARGET_SAMPLE_RATE = 16000    # Whisper espera 16kHz
CHUNK_DURATION = 3            # Segundos por chunk
FRAMES_PER_BUFFER = 1024


class AudioCapture(QThread):
    """
    Captura de áudio dual: Microfone + Sistema (WASAPI Loopback).
    
    Sinais:
        audio_chunk_ready(bytes): Emitido a cada 3s com dados mixados
        error_occurred(str): Emitido em caso de erro
        recording_started(): Emitido quando inicia
        recording_stopped(): Emitido quando para
    """
    
    audio_chunk_ready = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._is_recording = False
        self._should_stop = False
        
        # Buffers separados
        self._mic_buffer = b''
        self._sys_buffer = b''
        
        # pyaudio instance
        self._pyaudio = None
        self._mic_stream = None
        self._sys_stream = None
        
        # Info dos dispositivos
        self._mic_info = None
        self._sys_info = None
        self._sys_sample_rate = 48000  # Padrão, será detectado
        self._sys_channels = 2         # Padrão stereo
    
    def run(self):
        """Loop principal da thread."""
        if not PYAUDIO_AVAILABLE:
            self.error_occurred.emit("pyaudiowpatch não disponível")
            return
        
        try:
            self._pyaudio = pyaudio.PyAudio()
            
            # Detectar dispositivos
            if not self._detect_devices():
                return
            
            # Abrir streams
            self._open_streams()
            
            self._is_recording = True
            self.recording_started.emit()
            logger.info("🎤🔊 Captura dual iniciada (Mic + Sistema)")
            
            # Loop de captura
            while not self._should_stop:
                self._process_audio()
                self.msleep(50)  # 50ms
                
        except Exception as e:
            logger.error(f"Erro na captura: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self._cleanup()
    
    def _detect_devices(self) -> bool:
        """Detecta microfone e dispositivo de loopback."""
        try:
            # 1. Microfone padrão
            try:
                self._mic_info = self._pyaudio.get_default_input_device_info()
                logger.info(f"🎤 Microfone: {self._mic_info['name']}")
            except Exception as e:
                logger.warning(f"Microfone não encontrado: {e}")
                self._mic_info = None
            
            # 2. Sistema (WASAPI Loopback)
            try:
                wasapi_info = self._pyaudio.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_output_idx = wasapi_info["defaultOutputDevice"]
                self._sys_info = self._pyaudio.get_device_info_by_index(default_output_idx)
                
                # Verificar se suporta loopback
                if not self._sys_info.get("isLoopbackDevice", False):
                    # Procurar dispositivo de loopback correspondente
                    for i in range(self._pyaudio.get_device_count()):
                        dev = self._pyaudio.get_device_info_by_index(i)
                        if dev.get("isLoopbackDevice", False):
                            self._sys_info = dev
                            break
                
                self._sys_sample_rate = int(self._sys_info["defaultSampleRate"])
                self._sys_channels = self._sys_info["maxInputChannels"]
                logger.info(f"🔊 Sistema: {self._sys_info['name']} ({self._sys_sample_rate}Hz, {self._sys_channels}ch)")
                
            except Exception as e:
                logger.warning(f"Loopback não encontrado: {e}")
                self._sys_info = None
            
            # Pelo menos um deve funcionar
            if not self._mic_info and not self._sys_info:
                self.error_occurred.emit("Nenhum dispositivo de áudio encontrado")
                return False
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Erro ao detectar dispositivos: {e}")
            return False
    
    def _open_streams(self):
        """Abre streams de microfone e sistema."""
        # Stream do microfone (16kHz mono)
        if self._mic_info:
            try:
                self._mic_stream = self._pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=TARGET_SAMPLE_RATE,
                    input=True,
                    input_device_index=self._mic_info["index"],
                    frames_per_buffer=FRAMES_PER_BUFFER,
                    stream_callback=self._mic_callback
                )
                self._mic_stream.start_stream()
                logger.info("✓ Stream microfone aberto")
            except Exception as e:
                logger.warning(f"Erro ao abrir microfone: {e}")
                self._mic_stream = None
        
        # Stream do sistema (sample rate nativo)
        if self._sys_info:
            try:
                self._sys_stream = self._pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=self._sys_channels,
                    rate=self._sys_sample_rate,
                    input=True,
                    input_device_index=self._sys_info["index"],
                    frames_per_buffer=FRAMES_PER_BUFFER,
                    stream_callback=self._sys_callback
                )
                self._sys_stream.start_stream()
                logger.info("✓ Stream sistema aberto")
            except Exception as e:
                logger.warning(f"Erro ao abrir sistema: {e}")
                self._sys_stream = None
    
    def _mic_callback(self, in_data, frame_count, time_info, status):
        """Callback do microfone."""
        if self._is_recording:
            self._mic_buffer += in_data
        return (None, pyaudio.paContinue)
    
    def _sys_callback(self, in_data, frame_count, time_info, status):
        """Callback do sistema."""
        if self._is_recording:
            self._sys_buffer += in_data
        return (None, pyaudio.paContinue)
    
    def _process_audio(self):
        """Processa e mixa os buffers."""
        # Tamanho esperado para 3s a 16kHz mono (int16)
        target_bytes = CHUNK_DURATION * TARGET_SAMPLE_RATE * 2  # 96000 bytes
        
        # Tamanho do buffer do sistema para 3s
        sys_bytes_needed = CHUNK_DURATION * self._sys_sample_rate * 2 * self._sys_channels
        
        # Verificar se temos dados suficientes
        mic_ready = len(self._mic_buffer) >= target_bytes if self._mic_stream else False
        sys_ready = len(self._sys_buffer) >= sys_bytes_needed if self._sys_stream else False
        
        # Precisamos de pelo menos um stream pronto
        if not mic_ready and not sys_ready:
            return
        
        # Extrair chunks
        mic_chunk = None
        sys_chunk = None
        
        if mic_ready:
            mic_chunk = self._mic_buffer[:target_bytes]
            self._mic_buffer = self._mic_buffer[target_bytes:]
        
        if sys_ready:
            sys_raw = self._sys_buffer[:sys_bytes_needed]
            self._sys_buffer = self._sys_buffer[sys_bytes_needed:]
            sys_chunk = self._process_system_audio(sys_raw)
        
        # Mixar
        mixed = self._mix_audio(mic_chunk, sys_chunk)
        
        if mixed is not None:
            self.audio_chunk_ready.emit(mixed)
    
    def _process_system_audio(self, raw_data: bytes) -> bytes:
        """Processa áudio do sistema: stereo→mono, resample→16kHz."""
        try:
            # Converter para numpy
            audio = np.frombuffer(raw_data, dtype=np.int16)
            
            # Stereo → Mono (média dos canais)
            if self._sys_channels == 2:
                audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
            # Resample se necessário
            if self._sys_sample_rate != TARGET_SAMPLE_RATE and SCIPY_AVAILABLE:
                # Calcular número de amostras alvo
                num_samples = int(len(audio) * TARGET_SAMPLE_RATE / self._sys_sample_rate)
                audio = scipy_signal.resample(audio, num_samples).astype(np.int16)
            
            return audio.tobytes()
            
        except Exception as e:
            logger.warning(f"Erro ao processar áudio do sistema: {e}")
            return None
    
    def _mix_audio(self, mic_data: bytes, sys_data: bytes) -> bytes:
        """Mixa áudio do microfone e sistema."""
        try:
            if mic_data and sys_data:
                # Ambos disponíveis - mixar
                mic_arr = np.frombuffer(mic_data, dtype=np.int16).astype(np.float32)
                sys_arr = np.frombuffer(sys_data, dtype=np.int16).astype(np.float32)
                
                # Garantir mesmo tamanho
                min_len = min(len(mic_arr), len(sys_arr))
                mic_arr = mic_arr[:min_len]
                sys_arr = sys_arr[:min_len]
                
                # Mixar (média ponderada - sistema um pouco mais alto)
                mixed = (mic_arr * 0.4 + sys_arr * 0.6)
                
                # Normalizar para evitar clipping
                max_val = np.abs(mixed).max()
                if max_val > 32767:
                    mixed = mixed * (32767 / max_val)
                
                return mixed.astype(np.int16).tobytes()
                
            elif mic_data:
                return mic_data
            elif sys_data:
                return sys_data
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Erro ao mixar áudio: {e}")
            return mic_data or sys_data
    
    def stop_recording(self):
        """Para a gravação."""
        logger.info("⏹️ Parando captura...")
        self._should_stop = True
        self._is_recording = False
    
    def _cleanup(self):
        """Limpa recursos."""
        # Fechar streams
        for stream in [self._mic_stream, self._sys_stream]:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
        
        self._mic_stream = None
        self._sys_stream = None
        
        # Terminar pyaudio
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except:
                pass
            self._pyaudio = None
        
        # Limpar buffers
        self._mic_buffer = b''
        self._sys_buffer = b''
        
        # Resetar flags
        self._is_recording = False
        self._should_stop = False
        
        self.recording_stopped.emit()
        logger.info("⏹️ Captura finalizada")
    
    def is_recording(self) -> bool:
        return self._is_recording


# ============================================================================
# TESTE STANDALONE
# ============================================================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    
    logging.basicConfig(level=logging.INFO)
    
    def on_chunk(data):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Chunk: {len(data)} bytes")
    
    def on_error(msg):
        print(f"ERRO: {msg}")
    
    app = QApplication(sys.argv)
    
    capture = AudioCapture()
    capture.audio_chunk_ready.connect(on_chunk)
    capture.error_occurred.connect(on_error)
    
    print("Iniciando captura dual (10s)...")
    capture.start()
    
    QTimer.singleShot(10000, capture.stop_recording)
    QTimer.singleShot(11000, app.quit)
    
    sys.exit(app.exec_())
