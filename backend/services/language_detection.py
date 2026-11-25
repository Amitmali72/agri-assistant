"""
Language Detection Service
Detects whether text is in Marathi (mr), Hindi (hi), English (en), or unknown.
Uses langdetect with fallback to Unicode Devanagari range heuristics.
"""

import re
from typing import Dict, Optional


# Devanagari Unicode range: U+0900 to U+097F
DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]')

# Marathi-specific characters/words that distinguish it from Hindi
# These are common Marathi words/suffixes that rarely appear in Hindi
MARATHI_INDICATORS = [
    'आहे', 'आहेत', 'करायचे', 'मला', 'तुम्ही', 'आपण', 'कसे', 'कसा',
    'म्हणजे', 'आणि', 'किंवा', 'पण', 'तर', 'नाही', 'हवे', 'हवी',
    'सांगा', 'द्यावी', 'द्यावे', 'करावे', 'करावी', 'बद्दल',
    'वाटतो', 'वाटते', 'भाताला', 'भात', 'पीक', 'शेती',
]

# Hindi-specific words that rarely appear in Marathi
HINDI_INDICATORS = [
    'है', 'हैं', 'कैसे', 'करें', 'करना', 'होना', 'रहा', 'रही',
    'चाहिए', 'बताओ', 'बताएं', 'क्या', 'कब', 'कहाँ', 'किसान',
    'फसल', 'खेती', 'गेहूं', 'धान',
]


def _count_devanagari(text: str) -> int:
    """Count the number of Devanagari characters in the text."""
    return len(DEVANAGARI_PATTERN.findall(text))


def _heuristic_mr_hi(text: str) -> Optional[str]:
    """
    Use keyword heuristics to differentiate Marathi from Hindi.
    Returns 'mr', 'hi', or None if ambiguous.
    """
    mr_score = sum(1 for w in MARATHI_INDICATORS if w in text)
    hi_score = sum(1 for w in HINDI_INDICATORS if w in text)

    if mr_score > hi_score:
        return 'mr'
    elif hi_score > mr_score:
        return 'hi'
    return None


def detect_language(
    text: str,
    hint: Optional[str] = None
) -> Dict[str, object]:
    """
    Detect the language of the given text.

    Args:
        text: Input text to analyze
        hint: Optional user-provided language hint ('mr', 'hi', 'en').
              If provided and matches a supported language, it is returned
              with high confidence (overrides detection).

    Returns:
        dict with keys:
            - 'lang': 'mr' | 'hi' | 'en' | 'unknown'
            - 'confidence': float between 0.0 and 1.0
    """
    # Apply hint if provided and valid
    if hint and hint in ('mr', 'hi', 'en'):
        return {"lang": hint, "confidence": 1.0}

    if not text or not text.strip():
        return {"lang": "unknown", "confidence": 0.0}

    text_stripped = text.strip()
    devanagari_count = _count_devanagari(text_stripped)
    total_chars = len(text_stripped.replace(' ', ''))
    devanagari_ratio = devanagari_count / total_chars if total_chars > 0 else 0.0

    # Try langdetect first
    langdetect_lang = None
    langdetect_confidence = 0.0
    try:
        from langdetect import detect_langs
        results = detect_langs(text_stripped)
        if results:
            top = results[0]
            langdetect_lang = top.lang
            langdetect_confidence = float(top.prob)
    except Exception:
        pass

    # Map langdetect codes to our codes
    lang_map = {
        'mr': 'mr',
        'hi': 'hi',
        'en': 'en',
        'mai': 'hi',   # Maithili -> treat as Hindi
        'ne': 'hi',    # Nepali -> treat as Hindi (Devanagari)
    }

    # Case 1: High Devanagari ratio -> definitely Indian language
    if devanagari_ratio > 0.3:
        # Try heuristic to distinguish mr vs hi
        heuristic_lang = _heuristic_mr_hi(text_stripped)

        if langdetect_lang in ('mr', 'hi', 'mai', 'ne') and langdetect_confidence > 0.7:
            # Trust langdetect for Devanagari scripts if confident
            detected = lang_map.get(langdetect_lang, 'hi')
            # Cross-check with heuristic
            if heuristic_lang and heuristic_lang != detected and langdetect_confidence < 0.9:
                detected = heuristic_lang
                return {"lang": detected, "confidence": 0.75}
            return {"lang": detected, "confidence": langdetect_confidence}

        # langdetect failed or not confident for Devanagari
        if heuristic_lang:
            return {"lang": heuristic_lang, "confidence": 0.65}

        # Default to Hindi for unrecognized Devanagari text
        return {"lang": "hi", "confidence": 0.5}

    # Case 2: Devanagari present but minor ratio
    if devanagari_count > 0:
        # Some Devanagari but mixed — try heuristic
        heuristic_lang = _heuristic_mr_hi(text_stripped)
        if heuristic_lang:
            return {"lang": heuristic_lang, "confidence": 0.6}
        # Fallback
        if langdetect_lang in lang_map:
            return {"lang": lang_map[langdetect_lang], "confidence": langdetect_confidence}
        return {"lang": "hi", "confidence": 0.5}

    # Case 3: No Devanagari — rely on langdetect for English/others
    if langdetect_lang == 'en' and langdetect_confidence > 0.5:
        return {"lang": "en", "confidence": langdetect_confidence}

    if langdetect_lang in lang_map and langdetect_confidence > 0.5:
        return {"lang": lang_map[langdetect_lang], "confidence": langdetect_confidence}

    # Fallback
    if langdetect_lang == 'en':
        return {"lang": "en", "confidence": max(langdetect_confidence, 0.4)}

    return {"lang": "unknown", "confidence": 0.0}


if __name__ == "__main__":
    test_cases = [
        ("मला भाताबद्दल माहिती हवी", "Marathi"),
        ("चावल कैसे उगाएं?", "Hindi"),
        ("How to grow rice?", "English"),
        ("What is PM-Kisan scheme?", "English"),
        ("किसान सम्मान निधि क्या है?", "Hindi"),
        ("महाराष्ट्रात भात पिकाचे व्यवस्थापन कसे करावे?", "Marathi"),
    ]
    for text, expected in test_cases:
        result = detect_language(text)
        status = "✓" if result["lang"] == expected.lower()[:2] else "?"
        print(f"{status} [{expected}] -> {result} | '{text[:40]}'")
