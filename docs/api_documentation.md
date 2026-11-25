# API Documentation — KrishiMitra Backend (v2.0)

Base URL: `http://localhost:8000` (Interactive OpenAPI Docs at `http://localhost:8000/docs`)

---

## 1. Core Farmer Endpoints

### `GET /health`
Returns backend status, LLM connectivity, vector count, and approved document count.

### `POST /query`
Processes a text agricultural question through language ID, intent routing, RAG/live tools, confidence gate, LLM generation, and TTS.

**Request:**
```json
{
  "query": "कापसाच्या पानांवर पिवळे डाग पडत आहेत. याचे कारण काय असू शकते?",
  "session_id": "farmer_01",
  "language": "mr",
  "return_audio": true
}
```
**Response (200 OK):**
```json
{
  "conversation_id": 12,
  "session_id": "farmer_01",
  "detected_lang": "mr",
  "intent": "pest_disease",
  "decision": "ANSWER",
  "generation_mode": "extractive_grounded",
  "answer": "...",
  "source_documents": [
    {
      "filename": "cotton_and_soybean_advisory_icarcicr.pdf",
      "publisher": "ICAR-CICR & MPKV Rahuri",
      "page": 1,
      "approval_status": "approved",
      "score": 0.68
    }
  ],
  "audio_url": "/audio/responses/response_xxx_mr.mp3",
  "confidence": 0.68
}
```

### `POST /voice-query`
Accepts multipart form audio (`.wav`, `.webm`, `.mp3`, `.ogg`, `.m4a`), transcribes via Whisper, and returns `QueryResponse` including `transcript` and `stt_confidence`.

### `GET /weather?location=Pune&state=Maharashtra&language=mr`
Returns live temperature, humidity, rainfall, wind speed, 3-day forecast, and localized farming advisory via Open-Meteo / OpenWeatherMap.

### `GET /mandi-prices?commodity=Onion&market=Pune&state=Maharashtra`
Queries Agmarknet (`data.gov.in`). Returns `data_status: "live"` with prices or `"credentials_required"` if `AGMARKNET_API_KEY` is unconfigured.

### `GET /schemes`
Returns verified government schemes (`PM-KISAN`, `PMFBY`, `KCC`, `Soil Health Card`) with eligibility, benefits, documents, and official URLs.

### `POST /feedback`
Submits farmer rating (`1` helpful, `-1` unhelpful) and optional comment.

---

## 2. Admin Console Endpoints (`X-Admin-Key` header required)

- `POST /documents/upload` — Upload PDF with provenance metadata (`publisher`, `source_url`, `publication_date`, `crop`, `region`, `approval_status`)
- `GET /admin/documents` — List all tracked documents
- `POST /admin/documents/{doc_id}/review` — Approve or reject a document (`approved` / `rejected` / `pending`)
- `DELETE /admin/documents/{doc_id}` — Remove document and rebuild FAISS index
- `GET /admin/review-queue` — Inspect failed, refused, and low-confidence queries
- `POST /admin/review-queue/{item_id}/resolve` — Resolve review queue item
- `GET /admin/glossary` & `POST /admin/glossary` — Manage Marathi/Hindi/English terminology
- `GET /admin/metrics` — Aggregated latency, decision breakdown, feedback, and recent logs

---

## 3. WhatsApp Cloud API Webhook

- `GET /whatsapp/webhook` — Meta verification (`hub.mode`, `hub.verify_token`, `hub.challenge`)
- `POST /whatsapp/webhook` — Inbound WhatsApp JSON notifications (text & audio) with 1h deduplication
- `POST /whatsapp/test-mock` — Developer simulation endpoint without live Meta credentials
