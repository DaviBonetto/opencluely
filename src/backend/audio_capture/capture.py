"""Dual audio capture for microphone and system loopback."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal


logger = logging.getLogger("backend.audio_capture.capture")

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None
    logger.warning("numpy is unavailable for audio capture")

try:
    import pyaudiowpatch as pyaudio

    PYAUDIO_AVAILABLE = True
    logger.info("pyaudiowpatch imported successfully")
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None
    logger.warning("pyaudiowpatch is unavailable. Install: pip install pyaudiowpatch")

try:
    from scipy import signal as scipy_signal

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    scipy_signal = None
    logger.warning("scipy is unavailable; numpy interpolation fallback will be used")


TARGET_SAMPLE_RATE = 16000
CHUNK_DURATION = 3
FRAMES_PER_BUFFER = 1024


class AudioCapture(QThread):
    """Captures microphone plus system audio and emits mixed chunks."""

    audio_chunk_ready = Signal(bytes)
    error_occurred = Signal(str)
    recording_started = Signal()
    recording_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_recording = False
        self._should_stop = False
        self._mic_buffer = b""
        self._sys_buffer = b""
        self._pyaudio = None
        self._mic_stream = None
        self._sys_stream = None
        self._mic_info = None
        self._sys_info = None
        self._sys_sample_rate = 48000
        self._sys_channels = 2

    def run(self):
        """Main capture loop."""
        if not PYAUDIO_AVAILABLE:
            self.error_occurred.emit("pyaudiowpatch não disponível")
            return

        if not NUMPY_AVAILABLE:
            self.error_occurred.emit("numpy não disponível")
            return

        try:
            self._pyaudio = pyaudio.PyAudio()

            if not self._detect_devices():
                return

            self._open_streams()

            self._is_recording = True
            self.recording_started.emit()
            logger.info("Dual audio capture started")

            while not self._should_stop:
                self._process_audio()
                self.msleep(50)
        except Exception as exc:
            logger.error("Capture error: %s", exc)
            self.error_occurred.emit(str(exc))
        finally:
            self._cleanup()

    def _detect_devices(self) -> bool:
        try:
            try:
                self._mic_info = self._pyaudio.get_default_input_device_info()
                logger.info("Microphone: %s", self._mic_info["name"])
            except Exception as exc:
                logger.warning("Microphone not found: %s", exc)
                self._mic_info = None

            try:
                wasapi_info = self._pyaudio.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_output_idx = wasapi_info["defaultOutputDevice"]
                self._sys_info = self._pyaudio.get_device_info_by_index(default_output_idx)

                if not self._sys_info.get("isLoopbackDevice", False):
                    for index in range(self._pyaudio.get_device_count()):
                        device = self._pyaudio.get_device_info_by_index(index)
                        if device.get("isLoopbackDevice", False):
                            self._sys_info = device
                            break

                self._sys_sample_rate = int(self._sys_info["defaultSampleRate"])
                self._sys_channels = self._sys_info["maxInputChannels"]
                logger.info(
                    "Loopback: %s (%sHz, %sch)",
                    self._sys_info["name"],
                    self._sys_sample_rate,
                    self._sys_channels,
                )
            except Exception as exc:
                logger.warning("System loopback not found: %s", exc)
                self._sys_info = None

            if not self._mic_info and not self._sys_info:
                self.error_occurred.emit("Nenhum dispositivo de áudio encontrado")
                return False

            return True
        except Exception as exc:
            self.error_occurred.emit(f"Erro ao detectar dispositivos: {exc}")
            return False

    def _open_streams(self):
        if self._mic_info:
            try:
                self._mic_stream = self._pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=TARGET_SAMPLE_RATE,
                    input=True,
                    input_device_index=self._mic_info["index"],
                    frames_per_buffer=FRAMES_PER_BUFFER,
                    stream_callback=self._mic_callback,
                )
                self._mic_stream.start_stream()
            except Exception as exc:
                logger.warning("Failed to open microphone stream: %s", exc)
                self._mic_stream = None

        if self._sys_info:
            try:
                self._sys_stream = self._pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=self._sys_channels,
                    rate=self._sys_sample_rate,
                    input=True,
                    input_device_index=self._sys_info["index"],
                    frames_per_buffer=FRAMES_PER_BUFFER,
                    stream_callback=self._sys_callback,
                )
                self._sys_stream.start_stream()
            except Exception as exc:
                logger.warning("Failed to open system stream: %s", exc)
                self._sys_stream = None

    def _mic_callback(self, in_data, frame_count, time_info, status):
        if self._is_recording:
            self._mic_buffer += in_data
        return (None, pyaudio.paContinue)

    def _sys_callback(self, in_data, frame_count, time_info, status):
        if self._is_recording:
            self._sys_buffer += in_data
        return (None, pyaudio.paContinue)

    def _process_audio(self):
        target_bytes = CHUNK_DURATION * TARGET_SAMPLE_RATE * 2
        sys_bytes_needed = CHUNK_DURATION * self._sys_sample_rate * 2 * self._sys_channels

        mic_ready = len(self._mic_buffer) >= target_bytes if self._mic_stream else False
        sys_ready = len(self._sys_buffer) >= sys_bytes_needed if self._sys_stream else False

        if not mic_ready and not sys_ready:
            return

        mic_chunk = None
        sys_chunk = None

        if mic_ready:
            mic_chunk = self._mic_buffer[:target_bytes]
            self._mic_buffer = self._mic_buffer[target_bytes:]

        if sys_ready:
            sys_raw = self._sys_buffer[:sys_bytes_needed]
            self._sys_buffer = self._sys_buffer[sys_bytes_needed:]
            sys_chunk = self._process_system_audio(sys_raw)

        mixed = self._mix_audio(mic_chunk, sys_chunk)
        if mixed is not None:
            self.audio_chunk_ready.emit(mixed)

    def _process_system_audio(self, raw_data: bytes) -> bytes | None:
        try:
            audio = np.frombuffer(raw_data, dtype=np.int16)

            if self._sys_channels > 1:
                audio = audio.reshape(-1, self._sys_channels).mean(axis=1).astype(np.int16)

            if self._sys_sample_rate != TARGET_SAMPLE_RATE:
                audio = self._resample_audio(audio)

            return audio.astype(np.int16).tobytes()
        except Exception as exc:
            logger.warning("Failed to process system audio: %s", exc)
            return None

    def _resample_audio(self, audio):
        if SCIPY_AVAILABLE:
            num_samples = int(len(audio) * TARGET_SAMPLE_RATE / self._sys_sample_rate)
            return scipy_signal.resample(audio, num_samples).astype(np.int16)

        target_positions = np.linspace(0, len(audio) - 1, int(len(audio) * TARGET_SAMPLE_RATE / self._sys_sample_rate))
        source_positions = np.arange(len(audio))
        return np.interp(target_positions, source_positions, audio).astype(np.int16)

    def _mix_audio(self, mic_data: bytes | None, sys_data: bytes | None) -> bytes | None:
        try:
            if mic_data and sys_data:
                mic_arr = np.frombuffer(mic_data, dtype=np.int16).astype(np.float32)
                sys_arr = np.frombuffer(sys_data, dtype=np.int16).astype(np.float32)

                min_len = min(len(mic_arr), len(sys_arr))
                mic_arr = mic_arr[:min_len]
                sys_arr = sys_arr[:min_len]

                mixed = mic_arr * 0.4 + sys_arr * 0.6

                max_val = np.abs(mixed).max()
                if max_val > 32767:
                    mixed = mixed * (32767 / max_val)

                return mixed.astype(np.int16).tobytes()

            if mic_data:
                return mic_data

            if sys_data:
                return sys_data

            return None
        except Exception as exc:
            logger.warning("Failed to mix audio: %s", exc)
            return mic_data or sys_data

    def stop_recording(self):
        logger.info("Stopping audio capture")
        self._should_stop = True
        self._is_recording = False

    def _cleanup(self):
        for stream in [self._mic_stream, self._sys_stream]:
            if not stream:
                continue
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass

        self._mic_stream = None
        self._sys_stream = None

        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None

        self._mic_buffer = b""
        self._sys_buffer = b""
        self._is_recording = False
        self._should_stop = False
        self.recording_stopped.emit()
        logger.info("Audio capture stopped")

    def is_recording(self) -> bool:
        return self._is_recording
