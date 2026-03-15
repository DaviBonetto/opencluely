"""Windows-first audio capture for microphone, loopback, and mixed session audio."""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QThread, Signal

from ..contracts import AudioSource


logger = logging.getLogger("backend.audio_capture.capture")

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import pyaudiowpatch as pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

try:
    from scipy import signal as scipy_signal

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    scipy_signal = None


TARGET_SAMPLE_RATE = 16000
FRAME_DURATION_MS = 100
CHUNK_DURATION_MS = 4000
PROCESS_INTERVAL_MS = 20


class AudioCapture(QThread):
    """Captures session audio and emits detailed frames plus compatibility chunks."""

    audio_chunk_ready = Signal(bytes)
    audio_chunk_ready_detailed = Signal(bytes, str, int, int)
    audio_frame_ready = Signal(bytes, str, int, int)
    error_occurred = Signal(str)
    recording_started = Signal()
    recording_stopped = Signal()
    recording_paused = Signal()
    recording_resumed = Signal()
    status_changed = Signal(str)
    devices_ready = Signal(object)

    def __init__(self, source: AudioSource = AudioSource.AUTO, parent=None):
        super().__init__(parent)
        self._desired_source = source
        self._selected_source = AudioSource.AUTO
        self._is_recording = False
        self._is_paused = False
        self._should_stop = False
        self._buffers_lock = threading.Lock()
        self._mic_buffer = bytearray()
        self._sys_buffer = bytearray()
        self._chunk_buffer = bytearray()
        self._emitted_ms = 0
        self._next_chunk_start_ms = 0

        self._pyaudio = None
        self._mic_stream = None
        self._sys_stream = None
        self._mic_info = None
        self._sys_info = None
        self._mic_sample_rate = TARGET_SAMPLE_RATE
        self._mic_channels = 1
        self._sys_sample_rate = 48000
        self._sys_channels = 2

    @property
    def selected_source(self) -> AudioSource:
        return self._selected_source

    def set_audio_source(self, source: AudioSource | str) -> None:
        self._desired_source = source if isinstance(source, AudioSource) else AudioSource(source)

    def run(self) -> None:
        if not PYAUDIO_AVAILABLE:
            self.error_occurred.emit("pyaudiowpatch is unavailable.")
            return
        if not NUMPY_AVAILABLE:
            self.error_occurred.emit("numpy is unavailable.")
            return

        try:
            self._pyaudio = pyaudio.PyAudio()
            if not self._detect_devices():
                return
            self._selected_source = self._resolve_selected_source()
            self._open_streams()
            self._emit_device_snapshot()

            self._is_recording = True
            self.status_changed.emit("listening")
            self.recording_started.emit()

            while not self._should_stop:
                if not self._is_paused:
                    self._process_audio()
                self.msleep(PROCESS_INTERVAL_MS)
        except Exception as exc:
            logger.error("Audio capture failed", exc_info=True)
            self.error_occurred.emit(f"Audio capture failed: {exc}")
        finally:
            self._flush_partial_chunk()
            self._cleanup()

    def pause_recording(self) -> None:
        if not self._is_recording or self._is_paused:
            return
        self._is_paused = True
        with self._buffers_lock:
            self._mic_buffer.clear()
            self._sys_buffer.clear()
        self.status_changed.emit("paused")
        self.recording_paused.emit()

    def resume_recording(self) -> None:
        if not self._is_recording or not self._is_paused:
            return
        self._is_paused = False
        self.status_changed.emit("listening")
        self.recording_resumed.emit()

    def stop_recording(self) -> None:
        self._should_stop = True
        self._is_recording = False

    def is_recording(self) -> bool:
        return self._is_recording and not self._is_paused

    def _detect_devices(self) -> bool:
        try:
            try:
                self._mic_info = self._pyaudio.get_default_input_device_info()
                self._mic_sample_rate = int(self._mic_info["defaultSampleRate"])
                self._mic_channels = max(1, min(2, int(self._mic_info["maxInputChannels"] or 1)))
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
                self._sys_channels = max(1, int(self._sys_info["maxInputChannels"] or 1))
            except Exception as exc:
                logger.warning("Loopback not found: %s", exc)
                self._sys_info = None

            if not self._mic_info and not self._sys_info:
                self.error_occurred.emit("No audio input device was found.")
                return False

            return True
        except Exception as exc:
            self.error_occurred.emit(f"Device detection failed: {exc}")
            return False

    def _resolve_selected_source(self) -> AudioSource:
        if self._desired_source == AudioSource.AUTO:
            if self._mic_info and self._sys_info:
                return AudioSource.MIXED
            if self._mic_info:
                return AudioSource.MICROPHONE
            return AudioSource.LOOPBACK

        if self._desired_source == AudioSource.MIXED:
            if self._mic_info and self._sys_info:
                return AudioSource.MIXED
            if self._mic_info:
                return AudioSource.MICROPHONE
            return AudioSource.LOOPBACK

        if self._desired_source == AudioSource.MICROPHONE:
            if self._mic_info:
                return AudioSource.MICROPHONE
            return AudioSource.LOOPBACK

        if self._desired_source == AudioSource.LOOPBACK:
            if self._sys_info:
                return AudioSource.LOOPBACK
            return AudioSource.MICROPHONE

        return AudioSource.MICROPHONE

    def _emit_device_snapshot(self) -> None:
        self.devices_ready.emit(
            {
                "microphone_available": bool(self._mic_info),
                "loopback_available": bool(self._sys_info),
                "selected_source": self._selected_source.value,
                "microphone_name": self._mic_info["name"] if self._mic_info else "",
                "loopback_name": self._sys_info["name"] if self._sys_info else "",
            }
        )
        logger.info(
            "Audio devices ready | selected=%s | mic=%s | loopback=%s",
            self._selected_source.value,
            bool(self._mic_stream),
            bool(self._sys_stream),
        )

    def _open_streams(self) -> None:
        if self._mic_info:
            try:
                self._mic_stream = self._pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=self._mic_channels,
                    rate=self._mic_sample_rate,
                    input=True,
                    input_device_index=self._mic_info["index"],
                    frames_per_buffer=1024,
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
                    frames_per_buffer=1024,
                    stream_callback=self._sys_callback,
                )
                self._sys_stream.start_stream()
            except Exception as exc:
                logger.warning("Failed to open loopback stream: %s", exc)
                self._sys_stream = None

        self._selected_source = self._resolve_runtime_source()

    def _resolve_runtime_source(self) -> AudioSource:
        mic_ready = self._mic_stream is not None
        loopback_ready = self._sys_stream is not None

        if self._desired_source == AudioSource.MIXED:
            if mic_ready and loopback_ready:
                return AudioSource.MIXED
            if mic_ready:
                return AudioSource.MICROPHONE
            if loopback_ready:
                return AudioSource.LOOPBACK

        if self._desired_source == AudioSource.LOOPBACK and loopback_ready:
            return AudioSource.LOOPBACK
        if self._desired_source == AudioSource.LOOPBACK and mic_ready:
            return AudioSource.MICROPHONE

        if self._desired_source == AudioSource.MICROPHONE and mic_ready:
            return AudioSource.MICROPHONE
        if self._desired_source == AudioSource.MICROPHONE and loopback_ready:
            return AudioSource.LOOPBACK

        if self._desired_source == AudioSource.AUTO and mic_ready and loopback_ready:
            return AudioSource.MIXED
        if mic_ready:
            return AudioSource.MICROPHONE
        if loopback_ready:
            return AudioSource.LOOPBACK
        return AudioSource.AUTO

    def _mic_callback(self, in_data, _frame_count, _time_info, _status):
        if self._is_recording and not self._is_paused and in_data:
            with self._buffers_lock:
                self._mic_buffer.extend(in_data)
        return (None, pyaudio.paContinue)

    def _sys_callback(self, in_data, _frame_count, _time_info, _status):
        if self._is_recording and not self._is_paused and in_data:
            with self._buffers_lock:
                self._sys_buffer.extend(in_data)
        return (None, pyaudio.paContinue)

    def _process_audio(self) -> None:
        if not self._has_required_frame_data():
            return

        frame_bytes = int(TARGET_SAMPLE_RATE * (FRAME_DURATION_MS / 1000) * 2)
        mic_raw = self._pull_source_bytes(self._mic_buffer, self._mic_sample_rate, self._mic_channels)
        sys_raw = self._pull_source_bytes(self._sys_buffer, self._sys_sample_rate, self._sys_channels)

        mic_frame = self._prepare_source_audio(mic_raw, self._mic_sample_rate, self._mic_channels)
        sys_frame = self._prepare_source_audio(sys_raw, self._sys_sample_rate, self._sys_channels)
        mixed = self._select_or_mix_frame(mic_frame, sys_frame)
        if mixed is None or len(mixed) < frame_bytes:
            return

        start_ms = self._emitted_ms
        end_ms = start_ms + FRAME_DURATION_MS
        self._emitted_ms = end_ms
        self.audio_frame_ready.emit(mixed, self._selected_source.value, start_ms, end_ms)

        self._chunk_buffer.extend(mixed)
        chunk_target = int(TARGET_SAMPLE_RATE * (CHUNK_DURATION_MS / 1000) * 2)
        while len(self._chunk_buffer) >= chunk_target:
            chunk = bytes(self._chunk_buffer[:chunk_target])
            del self._chunk_buffer[:chunk_target]
            chunk_start_ms = self._next_chunk_start_ms
            chunk_end_ms = chunk_start_ms + CHUNK_DURATION_MS
            self._next_chunk_start_ms = chunk_end_ms
            self.audio_chunk_ready.emit(chunk)
            self.audio_chunk_ready_detailed.emit(
                chunk,
                self._selected_source.value,
                chunk_start_ms,
                chunk_end_ms,
            )

    def _has_required_frame_data(self) -> bool:
        with self._buffers_lock:
            mic_ready = len(self._mic_buffer) >= self._required_bytes(self._mic_sample_rate, self._mic_channels)
            sys_ready = len(self._sys_buffer) >= self._required_bytes(self._sys_sample_rate, self._sys_channels)

        if self._selected_source == AudioSource.MICROPHONE:
            return mic_ready
        if self._selected_source == AudioSource.LOOPBACK:
            return sys_ready
        return mic_ready and sys_ready

    def _required_bytes(self, sample_rate: int, channels: int) -> int:
        return int(sample_rate * (FRAME_DURATION_MS / 1000) * channels * 2)

    def _pull_source_bytes(self, buffer: bytearray, sample_rate: int, channels: int) -> bytes | None:
        if not buffer:
            return None
        bytes_needed = self._required_bytes(sample_rate, channels)
        with self._buffers_lock:
            if len(buffer) < bytes_needed:
                return None
            raw = bytes(buffer[:bytes_needed])
            del buffer[:bytes_needed]
            return raw

    def _prepare_source_audio(self, raw_data: bytes | None, sample_rate: int, channels: int) -> bytes | None:
        if not raw_data:
            return None
        audio = np.frombuffer(raw_data, dtype=np.int16)
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)
        if sample_rate != TARGET_SAMPLE_RATE:
            audio = self._resample_audio(audio, sample_rate)
        return audio.astype(np.int16).tobytes()

    def _resample_audio(self, audio, source_rate: int):
        if SCIPY_AVAILABLE:
            num_samples = int(len(audio) * TARGET_SAMPLE_RATE / source_rate)
            return scipy_signal.resample(audio, num_samples).astype(np.int16)
        target_positions = np.linspace(
            0,
            len(audio) - 1,
            int(len(audio) * TARGET_SAMPLE_RATE / source_rate),
        )
        return np.interp(target_positions, np.arange(len(audio)), audio).astype(np.int16)

    def _select_or_mix_frame(self, mic_data: bytes | None, sys_data: bytes | None) -> bytes | None:
        if self._selected_source == AudioSource.MICROPHONE:
            return mic_data
        if self._selected_source == AudioSource.LOOPBACK:
            return sys_data
        if not mic_data or not sys_data:
            return mic_data or sys_data

        mic_arr = np.frombuffer(mic_data, dtype=np.int16).astype(np.float32)
        sys_arr = np.frombuffer(sys_data, dtype=np.int16).astype(np.float32)
        min_len = min(len(mic_arr), len(sys_arr))
        mixed = mic_arr[:min_len] * 0.6 + sys_arr[:min_len] * 0.4
        peak = float(np.abs(mixed).max()) if len(mixed) else 0.0
        if peak > 32767:
            mixed = mixed * (32767 / peak)
        return mixed.astype(np.int16).tobytes()

    def _flush_partial_chunk(self) -> None:
        frame_floor = int(TARGET_SAMPLE_RATE * (FRAME_DURATION_MS / 1000) * 2)
        if len(self._chunk_buffer) < frame_floor:
            return
        chunk = bytes(self._chunk_buffer)
        chunk_duration_ms = int((len(chunk) / 2) / TARGET_SAMPLE_RATE * 1000)
        start_ms = self._next_chunk_start_ms
        end_ms = start_ms + chunk_duration_ms
        self._next_chunk_start_ms = end_ms
        self.audio_chunk_ready.emit(chunk)
        self.audio_chunk_ready_detailed.emit(
            chunk,
            self._selected_source.value,
            start_ms,
            end_ms,
        )
        self._chunk_buffer.clear()

    def _cleanup(self) -> None:
        for stream in (self._mic_stream, self._sys_stream):
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

        with self._buffers_lock:
            self._mic_buffer.clear()
            self._sys_buffer.clear()
            self._chunk_buffer.clear()

        self._is_recording = False
        self._is_paused = False
        self._should_stop = False
        self._emitted_ms = 0
        self._next_chunk_start_ms = 0
        self.status_changed.emit("stopped")
        self.recording_stopped.emit()
