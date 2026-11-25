"""
LLM Answer Generation Service (Module 9).
Supports:
- Local Ollama inference (with fast connect timeout so unavailable servers fail over cleanly)
- Configurable OpenAI-compatible hosted LLM API
- Separate prompt templates per agricultural intent (crop_advice, pest_disease, government_schemes, mandi_prices, weather)
- Grounded extractive evidence synthesizer fallback when no generative LLM server is reachable
"""

import os
import re
import logging
from typing import Optional, List, Dict, Any

from backend.config import settings

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    "hi": "Hindi (Devanagari script, simple farmer-friendly language)",
    "mr": "Marathi (Devanagari script, simple farmer-friendly language)",
    "en": "English (clear, simple farmer-friendly language)",
}

INTENT_TEMPLATES = {
    "crop_advice": (
        "You are KrishiMitra, a trusted agricultural advisor for Indian farmers.\n"
        "Answer ONLY from the verified Context below. Keep the response concise (3-5 clear points or sentences), "
        "use simple everyday {language}, preserve technical crop/fertilizer figures accurately, and mention the source document. "
        "If context is insufficient, clearly state so and suggest contacting KVK or Kisan Call Centre 1800-180-1551."
    ),
    "pest_disease": (
        "You are KrishiMitra, an agricultural plant-protection specialist.\n"
        "Answer ONLY using the verified Context below. Explain possible causes/symptoms, safe organic/IPM steps first, "
        "and ONLY include chemical dosages if explicitly stated in the verified Context. Mention the source document. "
        "Respond in {language}. Never invent pesticide dosages."
    ),
    "government_schemes": (
        "You are KrishiMitra, an Indian agricultural schemes advisor.\n"
        "Answer ONLY using the verified Context below. State eligibility, benefits, and required documents clearly. "
        "Include the official source and publication date if present. Respond in {language}."
    ),
    "mandi_prices": (
        "You are KrishiMitra. Summarize the provided live mandi price figures clearly in {language} without altering numbers."
    ),
    "weather": (
        "You are KrishiMitra. Summarize the live weather and agricultural advisory clearly in {language}."
    ),
    "general_agriculture": (
        "You are KrishiMitra, an agricultural assistant for Indian farmers. "
        "Answer ONLY based on the provided Context in {language}. Mention the source document. "
        "If information is insufficient, state so explicitly."
    ),
}

FALLBACK_MESSAGES = {
    "hi": "क्षमा करें, अभी इस विषय पर पर्याप्त जानकारी उपलब्ध नहीं है। कृपया किसान कॉल सेंटर 1800-180-1551 पर संपर्क करें।",
    "mr": "क्षमा करा, सध्या या विषयावर पुरेशी माहिती उपलब्ध नाही. कृपया किसान कॉल सेंटर 1800-180-1551 वर संपर्क करा.",
    "en": "Sorry, sufficient information is not available right now. Please call the Kisan Call Centre at 1800-180-1551.",
}


class LLMService:
    """Centralized grounded answer-generation service."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.OLLAMA_MODEL
        self.ollama_url = settings.OLLAMA_BASE_URL.replace("localhost", "127.0.0.1")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", settings.OPENAI_BASE_URL)
        self.openai_model = os.getenv("OPENAI_MODEL", settings.OPENAI_MODEL)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict:
        use_model = model or self.model

        # 1. Try local Ollama (fast 2s connect timeout)
        result = self._call_ollama(prompt, system_prompt, use_model)
        if result["success"]:
            return result

        # 2. Try OpenAI-compatible API if key is configured
        if self.openai_api_key:
            result = self._call_openai(prompt, system_prompt)
            if result["success"]:
                return result

        return {
            "response": "",
            "model": use_model,
            "success": False,
            "error": result.get("error", "No generative LLM available"),
        }

    def answer_query_with_meta(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        language: str = "mr",
        intent: str = "general_agriculture",
        glossary_hints: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, str]:
        """
        Generate a grounded response and return {answer, generation_mode, model}.
        Falls back transparently to extractive grounded synthesis when Ollama/OpenAI
        are offline so verified RAG facts are still delivered safely with citations.
        """
        language_name = LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["hi"])
        template = INTENT_TEMPLATES.get(intent, INTENT_TEMPLATES["general_agriculture"])
        system_prompt = template.format(language=language_name)

        context_str = self._format_context(context_chunks)
        glossary_str = ""
        if glossary_hints:
            pairs = [f"{g['en']} = {g.get(language) or g['hi']}" for g in glossary_hints[:8]]
            glossary_str = "\nAgricultural Terminology Glossary:\n" + "; ".join(pairs)

        full_prompt = (
            f"Verified Agricultural Context:\n{context_str}\n"
            f"{glossary_str}\n\n"
            f"Farmer's Question ({language}): {query}\n\n"
            f"Respond concisely in {language_name}, citing the source name:"
        )

        result = self.generate(full_prompt, system_prompt=system_prompt)
        if result["success"] and result["response"]:
            return {
                "answer": result["response"],
                "generation_mode": "llm",
                "model": result.get("model", self.model),
            }

        # Honest extractive grounded synthesis when LLM server is offline
        extractive = self._extractive_grounded_answer(query, context_chunks, language)
        return {
            "answer": extractive,
            "generation_mode": "extractive_grounded",
            "model": "extractive-rag-synthesizer",
        }

    def answer_query(
        self,
        query: str,
        context_chunks: list,
        language: str = "hi",
        intent: str = "general_agriculture",
    ) -> str:
        return self.answer_query_with_meta(query, context_chunks, language, intent)["answer"]

    def _format_context(self, context_chunks: List[Any]) -> str:
        if not context_chunks:
            return "No specific context available."
        parts = []
        for i, chunk in enumerate(context_chunks, 1):
            if isinstance(chunk, dict):
                text = chunk.get("text", chunk.get("content", ""))
                meta = chunk.get("metadata", {})
                src = meta.get("publisher") or meta.get("source") or meta.get("filename", "Agricultural Source")
                pub_date = meta.get("publication_date", "")
                page = meta.get("page", "")
                header = f"[Source {i}: {src}"
                if page:
                    header += f", p.{page}"
                if pub_date:
                    header += f", {pub_date}"
                header += "]"
                parts.append(f"{header}\n{text}")
            else:
                parts.append(f"[{i}]\n{chunk}")
        return "\n\n".join(parts)

    def _extractive_grounded_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        language: str,
    ) -> str:
        """
        Synthesize a concise, strictly source-grounded answer from top retrieved chunks
        when no external Ollama/OpenAI generative model is running.
        """
        if not context_chunks:
            return FALLBACK_MESSAGES.get(language, FALLBACK_MESSAGES["hi"])

        top = context_chunks[0]
        second = context_chunks[1] if len(context_chunks) > 1 else None
        meta = top.get("metadata", {})
        src_name = meta.get("publisher") or meta.get("source") or meta.get("filename", "ICAR / KVK Guide")
        pub_date = meta.get("publication_date", "")
        src_label = f"{src_name} ({pub_date})" if pub_date else src_name

        # Pick most relevant sentences from top 2 chunks
        combined_text = top.get("text", "")
        if second and second.get("score", 0) >= 0.30:
            combined_text += " " + second.get("text", "")

        sentences = [s.strip() for s in re.split(r'(?<=[.?!।])\s+', combined_text) if len(s.strip()) > 20]
        # Score sentences by token overlap with query
        q_tokens = set(re.findall(r'\w+', query.lower()))
        ranked = sorted(
            sentences,
            key=lambda s: len(q_tokens.intersection(set(re.findall(r'\w+', s.lower())))),
            reverse=True,
        )
        selected = " ".join(ranked[:3]) if ranked else combined_text[:450]

        if language == "mr":
            return (
                f"अधिकृत कृषी संदर्भानुसार ({src_label}):\n"
                f"{selected}\n\n"
                f"स्रोत: {meta.get('filename', src_name)} (पृष्ठ {meta.get('page', 1)})."
            )
        elif language == "hi":
            return (
                f"आधिकारिक कृषि दस्तावेज़ ({src_label}) के अनुसार:\n"
                f"{selected}\n\n"
                f"स्रोत: {meta.get('filename', src_name)} (पृष्ठ {meta.get('page', 1)})।"
            )
        else:
            return (
                f"Based on verified agricultural reference ({src_label}):\n"
                f"{selected}\n\n"
                f"Source: {meta.get('filename', src_name)} (Page {meta.get('page', 1)})."
            )

    def _call_ollama(self, prompt: str, system_prompt: Optional[str], model: str) -> dict:
        try:
            import httpx
            payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
            if system_prompt:
                payload["system"] = system_prompt

            timeout = httpx.Timeout(settings.LLM_READ_TIMEOUT, connect=settings.LLM_CONNECT_TIMEOUT)
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(f"{self.ollama_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()

            return {
                "response": data.get("response", "").strip(),
                "model": data.get("model", model),
                "success": True,
            }
        except Exception as e:
            logger.debug(f"Ollama unavailable: {e}")
            return {"response": "", "model": model, "success": False, "error": str(e)}

    def _call_openai(self, prompt: str, system_prompt: Optional[str]) -> dict:
        try:
            import httpx
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }
            timeout = httpx.Timeout(settings.LLM_READ_TIMEOUT, connect=5.0)
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    f"{self.openai_base_url}/chat/completions",
                    json={"model": self.openai_model, "messages": messages, "temperature": 0.2},
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

            text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return {"response": text, "model": self.openai_model, "success": True}
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
            return {"response": "", "model": self.openai_model, "success": False, "error": str(e)}
