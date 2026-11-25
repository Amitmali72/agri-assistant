# System Architecture — KrishiMitra (कृषीमित्र)

## 1. End-to-End Pipeline Flowchart

```mermaid
flowchart TD
    A[Farmer Input: Voice or Text] --> B{Channel}
    B -->|Web App / Mic| C[React + Vite Web UI]
    B -->|WhatsApp| D[WhatsApp Cloud Webhook]
    C --> E[FastAPI /query or /voice-query]
    D --> E
    E -->|If Audio| F[FFmpeg Normalize + Whisper STT]
    F --> G[STT Confidence Check]
    G -->|Low Confidence| H[CLARIFY: Ask to repeat]
    G -->|OK| I[Language Detection: mr / hi / en]
    E -->|If Text| I
    I --> J[Intent Classifier & Entity Extractor]
    J --> K{Route Decision}
    K -->|out_of_scope / banned| L[Safety Gate: REFUSE / REFER]
    K -->|mandi_prices| M[Agmarknet Live Mandi Service]
    K -->|weather| N[Open-Meteo / OWM Weather + Advisory]
    K -->|crop / pest / disease / schemes| O[Hybrid Retriever: FAISS + BM25 + RRF]
    O --> P[Approved Docs Filter + Crop/Region Boost]
    P --> Q[Confidence Gate: ANSWER / CLARIFY / REFUSE / REFER]
    Q -->|Pass| R[Grounded LLM / Extractive Synthesizer + Glossary]
    M --> S[TTS Audio Synthesis: gTTS / Bhashini]
    N --> S
    R --> S
    L --> S
    H --> S
    S --> T[Return Text + MP3 Audio + Source Citations + Disclaimer]
    T --> U[SQLite Audit Log + Review Queue + User Feedback]
```

## 2. Module Responsibilities

| Layer | Modules | Core Responsibility |
|---|---|---|
| **Channel & UI** | `frontend-web/`, `backend/api/whatsapp.py` | Mobile-first React UI with mic recording; Meta WhatsApp webhook & audio media dispatch |
| **Speech & Language** | `speech_to_text.py`, `text_to_speech.py`, `language_detection.py`, `translation.py` | Whisper ASR + imageio-ffmpeg normalization, gTTS/Bhashini audio, Devanagari/langdetect, SQLite Glossary |
| **Intent & Safety** | `intent_classifier.py`, `safety_service.py` | 8 agricultural intents, 7 entity types, 4-way gate (`ANSWER`, `CLARIFY`, `REFUSE`, `REFER`) |
| **Trusted RAG** | `document_processor.py`, `embeddings.py`, `vector_store.py`, `retriever.py` | PyMuPDF + SHA-256 hash dedup, MiniLM-L12 embeddings, FAISS IndexFlatIP, BM25 + RRF fusion |
| **Live Data** | `weather_service.py`, `mandi_service.py` | Open-Meteo (no key) & OpenWeatherMap live weather + Agmarknet APMC pricing with TTL caching |
| **Governance & Eval** | `db.py`, `routes.py`, `scripts/benchmark.py` | Document approval workflow, expert review queue, feedback loop, Recall@5 & safety metrics |
