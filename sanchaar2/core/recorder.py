from __future__ import annotations

import threading
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover - dependency fallback
    cv2 = None

try:
    import pyaudio
except Exception:  # pragma: no cover - dependency fallback
    pyaudio = None


class SessionRecorder:
    def __init__(self) -> None:
        self.video_writer = None
        self.audio_frames: list[bytes] = []
        self.is_recording = False
        self.is_paused = False
        self.cap = cv2.VideoCapture(0) if cv2 is not None else None
        self.output_dir: Path | None = None
        self.video_path: Path | None = None
        self.audio_path: Path | None = None
        self._lock = threading.Lock()
        self._video_thread: threading.Thread | None = None
        self._audio_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._latest_frame = self._empty_frame()
        self._frame_size = (640, 480)
        self._audio_rate = 44100
        self._audio_channels = 1
        self._audio_chunk = 1024
        self._audio_sample_width = 2
        self._audio_stream = None
        self._audio_interface = None
        self._audio_device_index: int | None = None
        self._audio_device_name: str = ""
        self._video_fps = 30.0
        self._start_time = 0.0
        self._elapsed_offset = 0.0

    def _select_input_device(self) -> int | None:
        if self._audio_interface is None:
            return None
        preferred_terms = ("microphone", "mic", "headset", "array")

        # Prefer the OS default input device if it is valid.
        try:
            default_info = self._audio_interface.get_default_input_device_info()
            default_index = int(default_info.get("index", -1))
            if default_index >= 0 and int(default_info.get("maxInputChannels", 0)) > 0:
                self._audio_device_name = str(default_info.get("name", "Default input"))
                return default_index
        except Exception:
            pass

        # Fallback: pick the best available input device.
        best_index: int | None = None
        best_score = -1
        try:
            device_count = int(self._audio_interface.get_device_count())
            for index in range(device_count):
                info = self._audio_interface.get_device_info_by_index(index)
                max_input_channels = int(info.get("maxInputChannels", 0))
                if max_input_channels <= 0:
                    continue
                name = str(info.get("name", "")).lower()
                score = max_input_channels
                if any(term in name for term in preferred_terms):
                    score += 10
                if score > best_score:
                    best_score = score
                    best_index = index
                    self._audio_device_name = str(info.get("name", "Input device"))
        except Exception:
            return None

        return best_index

    @staticmethod
    def _empty_frame() -> np.ndarray:
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def start(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        self.video_path = output_dir / "video.mp4"
        self.audio_path = output_dir / "audio.wav"
        self.audio_frames = []
        self._stop_event.clear()
        self._pause_event.clear()
        self.is_recording = True
        self.is_paused = False
        self._start_time = time.time()
        self._elapsed_offset = 0.0

        if self.cap is None and cv2 is not None:
            self.cap = cv2.VideoCapture(0)
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError("Webcam could not be opened.")

        width = int(self.cap.get(getattr(cv2, "CAP_PROP_FRAME_WIDTH", 3)) or 640)
        height = int(self.cap.get(getattr(cv2, "CAP_PROP_FRAME_HEIGHT", 4)) or 480)
        self._frame_size = (width if width > 0 else 640, height if height > 0 else 480)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v") if cv2 is not None else None
        if cv2 is not None:
            self.video_writer = cv2.VideoWriter(str(self.video_path), fourcc, self._video_fps, self._frame_size)
            if not self.video_writer.isOpened():
                raise RuntimeError("Could not open video writer.")

        if pyaudio is not None:
            self._audio_interface = pyaudio.PyAudio()
            self._audio_device_index = self._select_input_device()
            try:
                self._audio_stream = self._audio_interface.open(
                    format=pyaudio.paInt16,
                    channels=self._audio_channels,
                    rate=self._audio_rate,
                    input=True,
                    input_device_index=self._audio_device_index,
                    frames_per_buffer=self._audio_chunk,
                )
            except Exception:
                # Retry without forcing device index.
                self._audio_stream = self._audio_interface.open(
                    format=pyaudio.paInt16,
                    channels=self._audio_channels,
                    rate=self._audio_rate,
                    input=True,
                    frames_per_buffer=self._audio_chunk,
                )
        else:
            self._audio_interface = None
            self._audio_stream = None

        self._video_thread = threading.Thread(target=self._record_video_loop, daemon=True)
        self._audio_thread = threading.Thread(target=self._record_audio_loop, daemon=True)
        self._video_thread.start()
        self._audio_thread.start()

    def pause(self) -> None:
        if not self.is_recording:
            return
        self.is_paused = True
        self._pause_event.set()
        self._elapsed_offset += max(0.0, time.time() - self._start_time)

    def resume(self) -> None:
        if not self.is_recording:
            return
        self.is_paused = False
        self._pause_event.clear()
        self._start_time = time.time()

    def get_elapsed_seconds(self) -> float:
        elapsed = self._elapsed_offset
        if self.is_recording and not self.is_paused:
            elapsed += max(0.0, time.time() - self._start_time)
        return elapsed

    def get_live_frame(self) -> np.ndarray:
        with self._lock:
            return self._latest_frame.copy()

    def _record_video_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.05)
                continue
            if self.cap is None:
                self._latest_frame = self._empty_frame()
                time.sleep(0.05)
                continue
            ok, frame = self.cap.read()
            if not ok or frame is None:
                frame = self._empty_frame()
            else:
                frame = cv2.resize(frame, self._frame_size) if cv2 is not None else frame
            with self._lock:
                self._latest_frame = frame.copy()
            if self.video_writer is not None:
                self.video_writer.write(frame)
            time.sleep(max(0.0, 1.0 / self._video_fps))

    def _record_audio_loop(self) -> None:
        if self._audio_stream is None:
            return
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.05)
                continue
            try:
                data = self._audio_stream.read(self._audio_chunk, exception_on_overflow=False)
                self.audio_frames.append(data)
            except Exception:
                time.sleep(0.05)

    def stop(self) -> tuple[Path, Path]:
        self.is_recording = False
        self._stop_event.set()
        if self._video_thread and self._video_thread.is_alive():
            self._video_thread.join(timeout=2.0)
        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=2.0)

        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        if self.cap is not None:
            self.cap.release()
        if self._audio_stream is not None:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except Exception:
                pass
            self._audio_stream = None
        if self._audio_interface is not None:
            try:
                self._audio_interface.terminate()
            except Exception:
                pass
            self._audio_interface = None

        if self.output_dir is None or self.video_path is None or self.audio_path is None:
            raise RuntimeError("Recorder was not started properly.")

        if not self.audio_frames:
            device_hint = f" ({self._audio_device_name})" if self._audio_device_name else ""
            raise RuntimeError(
                "No microphone audio was captured during recording"
                f"{device_hint}. Check input device selection and Windows microphone privacy settings."
            )

        with wave.open(str(self.audio_path), "wb") as wav_file:
            wav_file.setnchannels(self._audio_channels)
            wav_file.setsampwidth(self._audio_sample_width)
            wav_file.setframerate(self._audio_rate)
            wav_file.writeframes(b"".join(self.audio_frames))

        return self.video_path, self.audio_path

    def cleanup(self) -> None:
        self._stop_event.set()
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self._audio_stream is not None:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except Exception:
                pass
            self._audio_stream = None
        if self._audio_interface is not None:
            try:
                self._audio_interface.terminate()
            except Exception:
                pass
            self._audio_interface = None

    def __del__(self) -> None:
        try:
            self.cleanup()
        except Exception:
            pass
