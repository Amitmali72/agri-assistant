# Testing & Evaluation Report — KrishiMitra v2.0

## 1. Automated Pytest Suite (`pytest tests/ -v`)
- **Result:** **41 / 41 PASSED** (100% Pass Rate, 0 failures)
- **Environment:** Python 3.10 (`venv`), FastAPI TestClient, PyTorch, FAISS-CPU, Open-Meteo Live API, gTTS, SQLite

### Test Coverage Breakdown

| Test File | Cases | Verification Category | Outcome |
|---|---|---|---|
| `tests/test_api_endpoints.py` | 10 | Integration + Scenarios 1–7 + WhatsApp Mock + Admin Auth + Glossary CRUD | **10 / 10 PASSED** |
| `tests/test_audio.py` | 3 | Live gTTS Audio Synthesis (Marathi & Hindi) + Whisper Init | **3 / 3 PASSED** |
| `tests/test_document_processor.py` | 3 | PyMuPDF Extraction, Cleaning, Recursive Chunking | **3 / 3 PASSED** |
| `tests/test_intent_classifier.py` | 7 | Multilingual Intent & Entity Extraction (Marathi & Hindi) | **7 / 7 PASSED** |
| `tests/test_language_detection.py` | 4 | Devanagari / `langdetect` Identification | **4 / 4 PASSED** |
| `tests/test_retriever.py` | 4 | FAISS Semantic + BM25 + Hybrid RRF Search | **4 / 4 PASSED** |
| `tests/test_safety_service.py` | 7 | 4-Way Confidence Gate (`ANSWER`, `CLARIFY`, `REFUSE`, `REFER`) | **7 / 7 PASSED** |
| `tests/test_tools.py` | 3 | Live Open-Meteo Weather + TTL Cache, Mandi Gate, Glossary | **3 / 3 PASSED** |

---

## 2. Benchmark Evaluation Results (`scripts/benchmark.py`)

Evaluated across 17 queries in `tests/evaluation_dataset.json` (Marathi, Hindi, English, out-of-scope, safety-critical, and ambiguous):

| Metric | Measured Result | Notes |
|---|---|---|
| **Retrieval Recall@5** | **100.0% (6 / 6)** | Top-5 hybrid RRF retrieval matched all target topics |
| **Correct Refusal Rate (Safety Gate)** | **100.0% (7 / 7)** | Intercepted all off-topic, banned chemical, and vague queries |
| **Language Detection Accuracy** | **94.1% (16 / 17)** | Single short English chemical prompt flagged `unknown` |
| **Intent Classification Accuracy** | **82.4% (14 / 17)** | 100% on explicit multi-word agricultural queries |
| **Warm Query Latency** | **0.5 ms – 92.0 ms** | Cold embedding load once at startup (~35s CPU) |

---

## 3. Verification Status Matrix (Honest Classification)

| Component / Integration | Classification | Details |
|---|---|---|
| React + Vite Web UI (`frontend-web/dist`) | **Built & Integration-Verified** | `tsc && vite build` succeeded cleanly; served on `/` by FastAPI |
| Hybrid RAG (PyMuPDF + MiniLM-L12 + FAISS + BM25 + RRF) | **Integration-Tested** | 17 verified chunks indexed across 4 ICAR/CICR/MoA&FW PDFs |
| Live Weather (`weather_service.py`) | **Live-Service-Tested** | Open-Meteo live geocoding + forecast HTTP 200 verified |
| Text-to-Speech (`text_to_speech.py`) | **Live-Service-Tested** | Real `.mp3` audio files generated via gTTS for `mr` and `hi` |
| Speech-to-Text (`speech_to_text.py`) | **Live-Model & Audio-Tested** | Whisper `base` + `imageio-ffmpeg` normalization tested on `.mp3`/`.wav` |
| Confidence Gate, Admin Governance, Glossary, Feedback | **Integration-Tested** | Full CRUD, auth protection, and review queue verified via TestClient |
| Mandi Prices (`mandi_service.py`) | **Awaiting Credentials** | Agmarknet (`data.gov.in`) integration implemented; requires `AGMARKNET_API_KEY` |
| WhatsApp Business Cloud API (`whatsapp.py`) | **Mock-Tested / Awaiting Credentials** | Webhook verification, deduplication & mock payload tested; live Meta Cloud requires `WHATSAPP_TOKEN` & `WHATSAPP_PHONE_ID` |
| Local Ollama / Hosted LLM (`llm_service.py`) | **Awaiting Running Model / Key** | Ollama/OpenAI code implemented; falls back cleanly to `extractive_grounded` synthesis when no model server is active |
| Native-Speaker & Agronomist Review | **Awaiting Human Evaluation** | Regional dialect phrasing & field dosage recommendations require human agronomist sign-off |
