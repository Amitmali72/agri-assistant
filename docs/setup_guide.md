# Setup & Deployment Guide — KrishiMitra

## 1. Prerequisites
- **Python 3.10+** (virtual environment `venv/` included)
- **Node.js 20+** & **npm** (for building or developing `frontend-web/`)
- **Ollama** (optional, for local generative LLM `qwen2.5:7b`)
- **Docker** (optional, for containerized deployment)

## 2. Backend & Python Environment
```powershell
cd d:\mdm_ia_voice\agri_assistant
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Frontend Build (React + Vite + Tailwind)
```powershell
cd d:\mdm_ia_voice\agri_assistant\frontend-web
npm install
npm run build
```
Once built, FastAPI automatically serves the production UI from `frontend-web/dist` at `http://localhost:8000`!

## 4. Environment Variables (`.env`)
Copy `.env.example` to `.env`:
- **No keys needed** for: Whisper STT, MiniLM-L12 Embeddings, FAISS RAG, gTTS Audio, SQLite, and **Open-Meteo Live Weather**.
- **Optional keys**:
  - `OLLAMA_BASE_URL` / `OLLAMA_MODEL=qwen2.5:7b` (local LLM; run `ollama pull qwen2.5:7b`)
  - `OPENAI_API_KEY` (hosted LLM fallback)
  - `AGMARKNET_API_KEY` (free from [data.gov.in](https://data.gov.in) for live mandi prices)
  - `OPENWEATHER_API_KEY` (optional Weather provider)
  - `BHASHINI_API_KEY` & `BHASHINI_USER_ID` (optional Indian Govt TTS)
  - `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_VERIFY_TOKEN` (Meta WhatsApp Business Cloud API)

## 5. Document Ingestion
```powershell
.\venv\Scripts\python.exe scripts\ingest_documents.py --dir data\raw_pdfs --source "ICAR & MPKV Rahuri"
```

## 6. Running the Application
```powershell
# Single-command production mode (FastAPI + built React UI on port 8000):
.\venv\Scripts\python.exe run.py backend

# Or full dev mode (Backend on :8000 + Vite HMR dev server on :5173):
.\venv\Scripts\python.exe run.py all
```

## 7. Docker Deployment
```bash
docker compose up --build
```
