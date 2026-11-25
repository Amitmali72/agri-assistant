"""
Speech-to-Text Service using OpenAI Whisper (Module 2).
Supports Marathi (mr), Hindi (hi), and English (en) with:
- Automatic multi-format audio normalization (webm, ogg, mp3, m4a, wav) via bundled ffmpeg (imageio-ffmpeg) or stdlib wave
- Basic voice band-pass filtering when ffmpeg is available
- Lazy model loading & confidence scoring from segment avg_logprob
"""

import os
import math
import wave
import uuid
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

AUDIO_UPLOADS_DIR = settings.BASE_DIR / "audio" / "uploads"


def _get_ffmpeg_binary() -> Optional[str]:
    """Return system ffmpeg or bundled imageio-ffmpeg binary if available."""
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


class SpeechToTextService:
    """Transcribes farmer voice notes using OpenAI Whisper with audio normalization."""

    LANG_MAP = {
        "mr": "marathi",
        "hi": "hindi",
        "en": "english",
    }

    REVERSE_LANG_MAP = {
        "marathi": "mr",
        "hindi": "hi",
        "english": "en",
        "mr": "mr",
        "hi": "hi",
        "en": "en",
    }

    def __init__(self, model_size: Optional[str] = None):
        self._model_size = model_size or settings.WHISPER_MODEL
        self._model = None
        self._ffmpeg_exe = _get_ffmpeg_binary()
        if self._ffmpeg_exe:
            # Ensure whisper's internal subprocess calls can find ffmpeg on PATH
            ffmpeg_dir = str(Path(self._ffmpeg_exe).parent)
            if ffmpeg_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

    def _get_model(self):
        if self._model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self._model_size}")
                self._model = whisper.load_model(self._model_size)
            except ImportError:
                raise RuntimeError("openai-whisper is not installed. Run: pip install openai-whisper")
        return self._model

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        """
        Transcribe audio file to text with confidence scoring.
        Never pretends a failed transcription succeeded.
        """
        if not audio_path or not os.path.exists(audio_path):
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "segments": [],
                "error": "Audio file not found",
            }

        try:
            normalized_path = self.normalize_audio(audio_path)
            model = self._get_model()

            options = {"fp16": False}
            if language and language in self.LANG_MAP:
                options["language"] = self.LANG_MAP[language]

            # Use ffmpeg-free WAV loading via wave/numpy when normalized WAV exists
            audio_input = self._load_wav_as_float32(normalized_path)
            if audio_input is None:
                audio_input = str(normalized_path)

            result = model.transcribe(audio_input, **options)

            segments = result.get("segments", [])
            if segments:
                avg_logprob = sum(s.get("avg_logprob", -0.6) for s in segments) / len(segments)
                no_speech_prob = sum(s.get("no_speech_prob", 0.0) for s in segments) / len(segments)
                raw_conf = math.exp(avg_logprob) * (1.0 - min(no_speech_prob, 0.9))
                confidence = float(round(min(1.0, max(0.0, raw_conf)), 3))
            else:
                confidence = 0.0 if not result.get("text", "").strip() else 0.75

            raw_lang = result.get("language", language or "unknown")
            iso_lang = self.REVERSE_LANG_MAP.get(str(raw_lang).lower(), language or "unknown")
            text = result.get("text", "").strip()

            return {
                "text": text,
                "language": iso_lang,
                "confidence": confidence,
                "segments": [
                    {
                        "start": s.get("start"),
                        "end": s.get("end"),
                        "text": s.get("text", "").strip(),
                    }
                    for s in segments
                ],
            }
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "segments": [],
                "error": str(e),
            }

    def _load_wav_as_float32(self, wav_path: Path):
        """Read mono 16kHz PCM WAV directly into float32 numpy array for Whisper (no ffmpeg needed at inference)."""
        try:
            import numpy as np
            if wav_path.suffix.lower() != ".wav":
                return None
            with wave.open(str(wav_path), "rb") as wf:
                if wf.getnchannels() != 1 or wf.getframerate() != 16000 or wf.getsampwidth() != 2:
                    return None
                raw = wf.readframes(wf.getnframes())
            if not raw:
                return None
            return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception:
            return None

    def normalize_audio(self, audio_path: str) -> Path:
        """
        Normalize uploaded audio (.webm, .ogg, .mp3, .m4a, .wav) to mono 16kHz 16-bit WAV
        with gentle voice-band filtering using bundled ffmpeg or stdlib wave.
        """
        AUDIO_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        src = Path(audio_path)
        out_name = f"norm_{uuid.uuid4().hex[:8]}_{src.stem}.wav"
        out_path = AUDIO_UPLOADS_DIR / out_name

        # Prefer ffmpeg when available — handles webm, ogg, mp3, m4a, wav + noise reduction
        if self._ffmpeg_exe:
            try:
                cmd = [
                    self._ffmpeg_exe,
                    "-y",
                    "-i", str(src),
                    "-ac", "1",
                    "-ar", "16000",
                    "-af", "highpass=f=80,lowpass=f=7600",
                    "-sample_fmt", "s16",
                    str(out_path),
                ]
                proc = subprocess.run(cmd, capture_output=True, timeout=30)
                if proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 44:
                    return out_path
            except Exception as e:
                logger.warning(f"ffmpeg normalization fallback triggered: {e}")

        # Stdlib WAV fallback
        if src.suffix.lower() == ".wav":
            try:
                self._normalize_wav_stdlib(src, out_path)
                return out_path
            except Exception as e:
                logger.warning(f"stdlib WAV normalization failed: {e}")

        return src

    def _normalize_wav_stdlib(self, src: Path, out_path: Path):
        """Pure-Python mono 16kHz WAV conversion for standard PCM WAVs."""
        import numpy as np

        with wave.open(str(src), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            raw = wf.readframes(wf.getnframes())

        if sampwidth == 2:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 1:
            samples = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            shutil.copy2(str(src), str(out_path))
            return

        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        if framerate != 16000 and len(samples) > 0:
            target_len = max(1, int(round(len(samples) * 16000 / framerate)))
            samples = np.interp(
                np.linspace(0, len(samples) - 1, target_len),
                np.arange(len(samples)),
                samples,
            )

        pcm16 = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
        with wave.open(str(out_path), "wb") as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)
            out_wf.setframerate(16000)
            out_wf.writeframes(pcm16.tobytes())
