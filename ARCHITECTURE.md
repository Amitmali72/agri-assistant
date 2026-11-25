# System Architecture: KrishiMitra Voice-First Agricultural Assistant

## 1. Executive Summary

**KrishiMitra** is a voice-first, multilingual AI assistant built specifically for Indian farmers. It enables farmers in rural communities to ask agricultural questions by voice or text in their regional language (**Marathi** and **Hindi**) and receive accurate, source-grounded agricultural answers via synthesized audio and text.

---

## 2. Architectural Paradigm

The system implements a **Modular Monolithic Architecture**. All core components (speech transcription, NLP language/intent detection, safety gates, hybrid vector retrieval, and speech synthesis) operate as decoupled Python modules under a unified **FastAPI** backend, serving a **Streamlit** reactive frontend and optional **WhatsApp Business Cloud API** webhooks.

```
                          ┌────────────────────────┐
                          │     Indian Farmer      │
                          └───────────┬────────────┘
                                      │
                   Voice / Text (Marathi / Hindi)
                                      ▼
               ┌──────────────────────────────────────────────┐
               │         Frontend Presentation Layer          │
               │  - Streamlit Web App (Port 8501)             │
               │  - WhatsApp Business Cloud API Webhook       │
               └──────────────────────┬───────────────────────┘
                                      │ REST API / Webhooks
                                      ▼
               ┌──────────────────────────────────────────────┐
               │            FastAPI Backend Engine            │
               │  - Request Router & Static File Audio Server │
               │  - SQLite Audit Trail & Interaction History  │
               └──────────────────────┬───────────────────────┘
                                      │
       ┌──────────────────────────────┼─────────────────────────────┐
       ▼                              ▼                             ▼
┌──────────────┐              ┌───────────────┐              ┌───────────────┐
│ Speech Input │              │ Understanding │              │  Tool Router  │
│ OpenAI       │              │  - LangDetect │              │  Intent &     │
│ Whisper      │              │  - Classifier │              │  Entities     │
└──────────────┘              └───────┬───────┘              └───────┬───────┘
                                      │                              │
                     ┌────────────────┴──────────────────────────────┤
                     │                                               │
           [Live Tools Route]                               [RAG Pipeline]
                     ▼                                               ▼
         ┌────────────────────────┐                      ┌────────────────────────┐
         │ Mandi / Weather Tools  │                      │   Safety & Confidence  │
         │ - Agmarknet APMC       │                      │   - Off-topic Filter   │
         │ - OpenWeather API      │                      │   - Lethal Chem Gate   │
         └───────────┬────────────┘                      │   - Confidence Score   │
                     │                                   └───────────┬────────────┘
                     │                                               ▼
                     │                                   ┌────────────────────────┐
                     │                                   │ Hybrid Document Search │
                     │                                   │ - FAISS Inner Product  │
                     │                                   │ - BM25 Keyword Search  │
                     └────────────────┬──────────────────┤ - MiniLM-L12 Vectors   │
                                      │                  └───────────┬────────────┘
                                      ▼                              ▼
                          ┌────────────────────────────────────────────────┐
                          │              Grounded LLM Service              │
                          │ - Local Ollama (Qwen2.5 7B) / OpenAI API       │
                          │ - Strict Source Grounding & Fallback Escalate  │
                          └───────────────────────┬────────────────────────┘
                                                  │ Grounded Answer Text
                                                  ▼
                          ┌────────────────────────────────────────────────┐
                          │               Speech Synthesis                 │
                          │ - gTTS / Bhashini Indian Regional TTS          │
                          │ - MP3/WAV Audio Stream Generation              │
                          └───────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
                                      [Audio & Text Response]
```

---

## 3. Core Component Modules

### 3.1 Document Ingestion and Hybrid Vector Database (Phase 1)
- **Text Extraction:** PyMuPDF (`fitz`) handles multi-page PDF documents from agricultural research institutes (ICAR, MPKV Rahuri, State Agriculture Departments).
- **Chunking Engine:** Recursive boundary chunking with 500-character windows and 50-character overlaps.
- **Multilingual Embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` produces 384-dimensional dense vectors natively mapping Devanagari (Marathi/Hindi) queries to English and regional documents.
- **FAISS Vector Store:** `IndexFlatIP` performs cosine similarity searches over L2-normalized embeddings.
- **BM25 Hybrid Retrieval:** `rank-bm25` (Okapi BM25) indexes Devanagari tokens and combines keyword scores with semantic vector scores (70% semantic / 30% keyword).

### 3.2 NLP Understanding: Language & Intent (Phase 2)
- **Language Detection:** Hybrid detection combining Unicode script range verification with `langdetect` to identify `mr` (Marathi), `hi` (Hindi), and `en` (English).
- **Intent Classifier:** Rule-based matching supporting 6 intents:
  1. `crop_advice`
  2. `pest_disease`
  3. `government_schemes`
  4. `mandi_prices`
  5. `weather`
  6. `general_agriculture`
- **Entity Extraction:** Extracts normalized crop names (`Onion`, `Wheat`, `Cotton`, `Soybean`), APMC market districts (`Pune`, `Nashik`, `Nagpur`, `Aurangabad`), and agricultural seasons (`Kharif`, `Rabi`, `Summer`).

### 3.3 Safety & Confidence Gate (Phase 7)
- **Refusal Gate:** Rejects queries with low retrieval scores (< 0.30) to prevent hallucinations.
- **Dangerous Chemical Filter:** Detects lethal organophosphates, banned pesticides, or unverified chemical dosage questions.
- **Ambiguity Escalator:** Intercepts single-word or vague queries and prompts farmers for specific details.
- **Official Escalation:** Recommends consulting the **National Kisan Call Centre (Toll-Free 1800-180-1551)** or local Krishi Vigyan Kendra (KVK).

### 3.4 Grounded LLM Generation (Phase 3)
- **LLM Interface:** Local **Ollama** (`qwen2.5:7b`) with optional OpenAI-compatible hosted API fallback.
- **Grounding Instructions:** Restricts answering strictly to retrieved document snippets and returns responses directly in the farmer's target language.

### 3.5 Voice Pipeline (Phases 4 & 5)
- **Speech-to-Text (STT):** OpenAI Whisper model (`base` or `medium`) converts spoken Hindi and Marathi into text with log-probability confidence scores.
- **Audio Normalization:** Converts uploaded audio to mono 16kHz WAV format.
- **Text-to-Speech (TTS):** Provider abstraction supporting **gTTS** (Google Text-to-Speech) and **Bhashini ULCA API** to produce natural audio responses.

### 3.6 Live Agricultural Tools (Phase 6)
- **Mandi Service:** Queries data.gov.in Agmarknet API for minimum, maximum, and modal commodity prices per quintal.
- **Weather Service:** Queries OpenWeatherMap API for temperature, humidity, rainfall, and generates agricultural advisories.

### 3.7 WhatsApp Business Cloud API (Phase 9)
- **Webhook Handlers:** `/whatsapp/webhook` receives inbound messages, downloads voice notes, and returns answers via text and audio.
- **Deduplication Cache:** Prevents duplicate processing of re-transmitted WhatsApp message IDs.
- **Mock Testing Endpoint:** `/whatsapp/test-mock` enables local validation without external webhook credentials.

---

## 4. Database Schema (SQLite)

- **`conversations`:** `id`, `session_id`, `user_query`, `detected_lang`, `intent`, `response_text`, `source_docs`, `timestamp`
- **`documents`:** `id`, `filename`, `source`, `pages`, `ingested_at`, `topic`
- **`audio_logs`:** `id`, `conversation_id`, `audio_path`, `transcription`, `timestamp`
