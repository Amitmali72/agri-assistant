# KrishiMitra (कृषीमित्र / किसान मित्र) — v2.0
### Voice-First Multilingual Agricultural Assistant for Indian Farmers
**Sagveek Technologies Pvt. Ltd. — Complete 14-Module Production Implementation**

KrishiMitra enables Indian farmers to interact by **voice or text** in **Marathi (मराठी)**, **Hindi (हिन्दी)**, and **English**, delivering **verified, source-grounded agricultural advice** with **synthesized speech**, **live weather & advisories**, **APMC mandi prices**, **WhatsApp integration**, and an **Admin & Expert Review Console**.

---

## Key Capabilities (All 14 Modules)

1. **Channel & Audio Interface (`whatsapp.py`, `frontend-web/`):** React + Vite + Tailwind CSS web platform with live microphone recording (`MediaRecorder`), audio upload, plus Meta WhatsApp Business Cloud API webhook with deduplication, retry handling, and user consent sessions.
2. **Speech-to-Text (`speech_to_text.py`):** OpenAI Whisper (`base`) transcription for Marathi & Hindi with bundled `imageio-ffmpeg` audio normalization (`.webm`, `.ogg`, `.mp3`, `.m4a`, `.wav`) and confidence gating.
3. **Language ID, Intent & Entities (`language_detection.py`, `intent_classifier.py`):** Hybrid Devanagari/`langdetect` detection + 8 intents (`crop_advice`, `pest_info`, `disease_info`, `government_schemes`, `mandi_prices`, `weather`, `general_agriculture`, `out_of_scope`) + 7 extracted entity types + code-mixed support.
4. **Translation & Agricultural Glossary (`translation.py`, `db.py`):** SQLite-backed Marathi/Hindi/English terminology glossary preserving technical crop, pest, disease, chemical, and scheme terms.
5. **Knowledge Ingestion & Governance (`document_processor.py`, `ingest_documents.py`):** PyMuPDF extraction, optional OCR fallback, SHA-256 duplicate detection, rich provenance metadata, and `approved`/`pending`/`rejected` workflow.
6. **Embeddings & Vector Store (`embeddings.py`, `vector_store.py`):** `paraphrase-multilingual-MiniLM-L12-v2` (384-dim) + FAISS `IndexFlatIP` with persistent storage, metadata filtering, and live index rebuilding.
7. **Hybrid Retrieval Engine (`retriever.py`):** Semantic FAISS + Okapi BM25 combined via **Reciprocal Rank Fusion (RRF)** with crop/region boosting and strict approved-only filtering.
8. **Live Data Tools (`weather_service.py`, `mandi_service.py`):** Zero-config live weather & 3-day forecasts via **Open-Meteo** (plus OpenWeatherMap support) + **Agmarknet** (`data.gov.in`) live mandi lookup with TTL caching and explicit `is_live` status.
9. **Grounded Answer Generation (`llm_service.py`):** Intent-specific prompt templates for Ollama (`qwen2.5:7b`) or OpenAI-compatible APIs, with transparent `extractive_grounded` synthesis when no generative server is running.
10. **4-Way Confidence & Safety Gate (`safety_service.py`):** Explicit `ANSWER`, `CLARIFY`, `REFUSE`, and `REFER` decisions; strict pesticide dosage guardrails; National Kisan Call Centre (`1800-180-1551`) & KVK referrals.
11. **Text-to-Speech (`text_to_speech.py`):** Regional Marathi & Hindi MP3 generation via gTTS + Bhashini ULCA pipeline integration.
12. **Safety, Privacy & Compliance (`routes.py`, `db.py`):** Role-gated Admin API (`X-Admin-Key`), `.env` secrets, user consent controls, and automatic 24-hour uploaded audio retention purging.
13. **Evaluation & Feedback (`scripts/benchmark.py`, `tests/`):** Automated pytest suite, benchmark runner (Recall@5, Refusal Rate, Accuracy, Latency), and 👍/👎 UI feedback loop.
14. **Admin & Expert Review Console (`frontend-web/src/components/AdminConsole.tsx`):** Manage PDFs (upload, approve, reject, delete/re-index), resolve failed/low-confidence queries, edit glossary terms, view metrics, and simulate WhatsApp messages.

---

## Quick Start

### 1. Install Dependencies & Build Frontend
```powershell
cd d:\mdm_ia_voice\agri_assistant
.\venv\Scripts\python.exe -m pip install -r requirements.txt

cd frontend-web
npm install
npm run build
```

### 2. Ingest Agricultural Knowledge Base
```powershell
cd d:\mdm_ia_voice\agri_assistant
.\venv\Scripts\python.exe scripts\ingest_documents.py --dir data\raw_pdfs --source "ICAR & MPKV Rahuri"
```

### 3. Run the Application
```powershell
# Single-command mode (FastAPI backend + built React Web App at http://localhost:8000):
.\venv\Scripts\python.exe run.py backend

# Full development mode (Backend :8000 + Vite HMR :5173):
.\venv\Scripts\python.exe run.py all

# Or via Docker:
docker compose up --build
```

### 4. Run Tests & Benchmark
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
.\venv\Scripts\python.exe scripts\benchmark.py
```

---

## Project Documentation
- [Requirements Traceability Matrix](docs/requirements_traceability.md)
- [System Architecture & Flowchart](docs/architecture.md)
- [API Documentation](docs/api_documentation.md)
- [Setup & Deployment Guide](docs/setup_guide.md)
- [Data Sources & Provenance](docs/data_sources.md)
- [Testing & Evaluation Report](docs/testing_report.md)
- [Farmer User Manual](docs/user_manual.md)
