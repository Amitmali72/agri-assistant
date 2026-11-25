"""
Tests for Language Detection Service (Marathi, Hindi, English).
"""

import pytest
from backend.services.language_detection import detect_language


def test_detect_marathi():
    res = detect_language("गव्हाच्या पिकाला खत कधी द्यावे?")
    assert res["lang"] == "mr"
    assert res["confidence"] > 0.8


def test_detect_hindi():
    res = detect_language("गेहूं की फसल में पहली सिंचाई कब करें?")
    assert res["lang"] == "hi"
    assert res["confidence"] > 0.8


def test_detect_english():
    res = detect_language("What is the fertilizer schedule for soybean crop?")
    assert res["lang"] == "en"
    assert res["confidence"] > 0.8


def test_short_text_handling():
    res = detect_language("शेती")
    assert res["lang"] in ["mr", "hi"]
