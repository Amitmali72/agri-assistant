"""
Tests for Speech-to-Text (Whisper) and Text-to-Speech (gTTS/Bhashini).
"""

import os
import pytest
from backend.services.text_to_speech import TTSService
from backend.services.speech_to_text import SpeechToTextService


def test_tts_synthesis_hindi():
    tts = TTSService()
    res = tts.synthesize("किसान भाइयों का स्वागत है।", language="hi")
    assert res["success"] is True
    assert res["audio_path"] is not None
    assert os.path.exists(res["audio_path"])
    assert res["provider"] == "gtts"


def test_tts_synthesis_marathi():
    tts = TTSService()
    res = tts.synthesize("शेतकरी मित्रांनो, नमस्कार.", language="mr")
    assert res["success"] is True
    assert res["audio_path"] is not None
    assert os.path.exists(res["audio_path"])


def test_stt_initialization():
    stt = SpeechToTextService(model_size="base")
    assert stt._model_size == "base"
