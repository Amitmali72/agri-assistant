"""
Text-to-Speech Service with provider abstraction.
Supports gTTS (free) and Bhashini (Indian govt API).
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

AUDIO_RESPONSES_DIR = Path("d:/mdm_ia_voice/agri_assistant/audio/responses")

# Language code mapping for gTTS
GTTS_LANG_MAP = {
    "mr": "mr",   # Marathi
    "hi": "hi",   # Hindi
    "en": "en",   # English
}

# Bhashini language codes
BHASHINI_LANG_MAP = {
    "mr": "mr",
    "hi": "hi",
    "en": "en",
}


class TTSService:
    """Text-to-Speech service with gTTS and Bhashini provider support."""

    def __init__(self):
        self.bhashini_api_key = os.getenv("BHASHINI_API_KEY", "")
        self.bhashini_user_id = os.getenv("BHASHINI_USER_ID", "")
        AUDIO_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

    def synthesize(
        self,
        text: str,
        language: str = "hi",
        output_path: Optional[str] = None,
    ) -> dict:
        """
        Convert text to speech.

        Args:
            text: Text to synthesize
            language: Language code (mr, hi, en)
            output_path: Optional explicit output path

        Returns:
            dict with keys: audio_path, provider, success
            On failure: adds 'error', audio_path=None, success=False
        """
        # Try Bhashini first if API key available
        if self.bhashini_api_key:
            result = self._synthesize_bhashini(text, language, output_path)
            if result["success"]:
                return result
            logger.warning(
                f"Bhashini TTS failed: {result.get('error')}, falling back to gTTS"
            )

        return self._synthesize_gtts(text, language, output_path)

    # ------------------------------------------------------------------
    # Provider: gTTS
    # ------------------------------------------------------------------
    def _synthesize_gtts(
        self, text: str, language: str, output_path: Optional[str]
    ) -> dict:
        """Synthesize using Google Text-to-Speech (gtts library)."""
        try:
            from gtts import gTTS

            lang_code = GTTS_LANG_MAP.get(language, "hi")
            tts = gTTS(text=text, lang=lang_code, slow=False)

            if output_path is None:
                filename = f"response_{uuid.uuid4().hex[:12]}_{language}.mp3"
                output_path = str(AUDIO_RESPONSES_DIR / filename)

            tts.save(output_path)
            logger.info(f"gTTS synthesized: {output_path}")
            return {
                "audio_path": output_path,
                "provider": "gtts",
                "success": True,
            }
        except ImportError:
            err = "gtts is not installed. Run: pip install gtts"
            logger.error(err)
            return {"audio_path": None, "provider": "gtts", "success": False, "error": err}
        except Exception as e:
            err = str(e)
            logger.error(f"gTTS synthesis failed: {err}")
            return {"audio_path": None, "provider": "gtts", "success": False, "error": err}

    # ------------------------------------------------------------------
    # Provider: Bhashini
    # ------------------------------------------------------------------
    def _synthesize_bhashini(
        self, text: str, language: str, output_path: Optional[str]
    ) -> dict:
        """Synthesize using Bhashini ULCA API (Indian govt TTS)."""
        try:
            import httpx
            import base64

            lang_code = BHASHINI_LANG_MAP.get(language, "hi")

            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {"sourceLanguage": lang_code},
                            "serviceId": "",  # Will use default for language
                            "gender": "female",
                            "samplingRate": 8000,
                        },
                    }
                ],
                "inputData": {"input": [{"source": text}]},
            }

            headers = {
                "Authorization": self.bhashini_api_key,
                "userID": self.bhashini_user_id,
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

            # Extract audio bytes from response
            audio_b64 = (
                data.get("pipelineResponse", [{}])[0]
                .get("audio", [{}])[0]
                .get("audioContent", "")
            )
            if not audio_b64:
                return {
                    "audio_path": None,
                    "provider": "bhashini",
                    "success": False,
                    "error": "No audio content in Bhashini response",
                }

            audio_bytes = base64.b64decode(audio_b64)

            if output_path is None:
                filename = f"response_{uuid.uuid4().hex[:12]}_{language}.wav"
                output_path = str(AUDIO_RESPONSES_DIR / filename)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"Bhashini TTS synthesized: {output_path}")
            return {
                "audio_path": output_path,
                "provider": "bhashini",
                "success": True,
            }

        except Exception as e:
            err = str(e)
            logger.error(f"Bhashini TTS failed: {err}")
            return {
                "audio_path": None,
                "provider": "bhashini",
                "success": False,
                "error": err,
            }
