"""
Translation & Agricultural Terminology Glossary Service (Module 4).
Preserves technical agricultural terminology (crops, pests, diseases, chemicals, schemes)
using the SQLite glossary + optional Helsinki-NLP Opus-MT translation.
"""

import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

OPUS_MT_MODELS = {
    ("hi", "mr"): "Helsinki-NLP/opus-mt-hi-mr",
    ("mr", "hi"): "Helsinki-NLP/opus-mt-mr-hi",
    ("hi", "en"): "Helsinki-NLP/opus-mt-hi-en",
    ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
    ("mr", "en"): "Helsinki-NLP/opus-mt-mr-en",
    ("en", "mr"): "Helsinki-NLP/opus-mt-en-mr",
}

_model_cache: dict = {}


def get_glossary_hints(text: str, target_lang: str = "mr") -> List[Dict[str, str]]:
    """
    Look up verified agricultural glossary terms appearing in *text* so that
    downstream translation or LLM generation preserves exact regional terminology.
    """
    try:
        from backend.database.db import get_glossary_terms
        terms = get_glossary_terms()
    except Exception:
        return []

    lower_text = text.lower()
    matches: List[Dict[str, str]] = []
    for t in terms:
        en = (t.get("term_en") or "").lower()
        mr = t.get("term_mr") or ""
        hi = t.get("term_hi") or ""
        if (en and any(part.strip() in lower_text for part in en.split("/"))) or (mr and mr in text) or (hi and hi in text):
            matches.append({
                "en": t.get("term_en", ""),
                "mr": mr,
                "hi": hi,
                "category": t.get("category", "general"),
            })
    return matches


def translate(
    text: str,
    source_lang: str,
    target_lang: str,
    use_neural_mt: bool = False,
) -> dict:
    """
    Translate text while preserving agricultural glossary terms.
    Neural MT (Opus-MT) is opt-in (use_neural_mt=True) to prevent multi-hundred-MB downloads
    during synchronous API calls when multilingual LLM handles native output directly.
    """
    if not text or not text.strip():
        return {"translated_text": text, "success": True, "glossary_matches": []}

    glossary_matches = get_glossary_hints(text, target_lang)

    if source_lang == target_lang:
        return {"translated_text": text, "success": True, "glossary_matches": glossary_matches}

    if use_neural_mt and (source_lang, target_lang) in OPUS_MT_MODELS:
        try:
            result = _translate_opus(text, source_lang, target_lang)
            if result:
                return {"translated_text": result, "success": True, "glossary_matches": glossary_matches}
        except Exception as e:
            logger.warning(f"Opus-MT translation failed: {e}")

    return {
        "translated_text": text,
        "success": False,
        "glossary_matches": glossary_matches,
        "note": (
            f"Direct multilingual LLM output preferred over machine translation "
            f"({source_lang} -> {target_lang}); glossary hints attached."
        ),
    }


def _translate_opus(text: str, src: str, tgt: str) -> Optional[str]:
    from transformers import MarianMTModel, MarianTokenizer
    key = (src, tgt)
    if key not in _model_cache:
        model_name = OPUS_MT_MODELS[key]
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        _model_cache[key] = (tokenizer, model)

    tokenizer, model = _model_cache[key]
    inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True, max_length=512)
    translated = model.generate(**inputs)
    decoded = tokenizer.batch_decode(translated, skip_special_tokens=True)
    return decoded[0] if decoded else None
