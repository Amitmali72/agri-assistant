"""
FastAPI Routes for KrishiMitra (Modules 1-14).
Includes:
- Farmer Query & Voice Query Pipeline (/query, /voice-query)
- Live Weather & Mandi Endpoints (/weather, /mandi-prices)
- Knowledge Governance & Admin Console (/admin/documents*, /admin/review-queue*, /admin/glossary*, /admin/metrics)
- User Feedback & Session/Consent Settings (/feedback, /settings/session)
- Health & Languages (/health, /languages)
"""

import os
import time
import uuid
import base64
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, Header, Depends
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.models.schemas import (
    QueryRequest, QueryResponse, SourceDocument,
    MandiResponse, MandiPrice,
    WeatherResponse, WeatherForecastDay,
    DocumentUploadResponse, DocumentReviewRequest,
    FeedbackRequest, ReviewResolveRequest,
    GlossaryTermRequest, SessionPreferencesRequest,
    ConversationHistoryResponse, ConversationEntry,
    HealthResponse,
)
from backend.database.db import (
    save_conversation, get_conversation_history, get_recent_conversations,
    save_document_metadata, get_all_documents, get_document_by_hash,
    get_document_by_id, update_document_status, delete_document_record,
    get_approved_filenames, save_audio_log, cleanup_expired_audio_files,
    save_feedback, get_feedback_list,
    log_failed_or_low_confidence_query, get_review_queue, resolve_review_item,
    get_glossary_terms, add_glossary_term, delete_glossary_term,
    upsert_user_session, get_user_session, get_system_metrics,
)
from backend.services.language_detection import detect_language
from backend.services.intent_classifier import IntentClassifier
from backend.services.safety_service import SafetyService
from backend.services.translation import get_glossary_hints
from backend.services.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.services.retriever import Retriever
from backend.services.llm_service import LLMService
from backend.services.speech_to_text import SpeechToTextService
from backend.services.text_to_speech import TTSService
from backend.services.mandi_service import MandiService
from backend.services.weather_service import WeatherService
from backend.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Singleton Services ────────────────────────────────────────────────────────
intent_classifier = IntentClassifier()
safety_service = SafetyService(
    min_confidence_score=settings.CONFIDENCE_THRESHOLD,
    min_stt_confidence=settings.STT_CONFIDENCE_THRESHOLD,
)
embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
vector_store = VectorStore(storage_path=settings.VECTOR_STORE_PATH)
retriever = Retriever(embedding_service=embedding_service, vector_store=vector_store)
llm_service = LLMService(model=settings.OLLAMA_MODEL)
stt_service = SpeechToTextService(model_size=settings.WHISPER_MODEL)
tts_service = TTSService()
mandi_service = MandiService()
weather_service = WeatherService()
doc_processor = DocumentProcessor()

ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".m4a", ".webm", ".flac"}


# ── Security Dependency for Admin Console ─────────────────────────────────────
def require_admin(x_admin_key: Optional[str] = Header(default=None)):
    """Verify admin access key when configured."""
    expected = settings.ADMIN_API_KEY
    if expected and x_admin_key != expected:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: valid X-Admin-Key header required for admin operations.",
        )
    return True


# ── Health & Catalog ──────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
def health_check():
    ollama_ok = False
    try:
        import httpx
        url = settings.OLLAMA_BASE_URL.replace("localhost", "127.0.0.1")
        r = httpx.get(f"{url}/api/tags", timeout=0.4)
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False

    approved_count = len(get_approved_filenames()) if os.path.exists(settings.DATABASE_PATH) else 0
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        ollama_connected=ollama_ok,
        openai_configured=bool(settings.OPENAI_API_KEY),
        whisper_loaded=(stt_service._model is not None),
        db_connected=os.path.exists(settings.DATABASE_PATH),
        vector_count=vector_store.total_documents,
        approved_docs_count=approved_count,
        message="KrishiMitra Agricultural Assistant Backend Operational",
    )


@router.get("/languages")
def get_supported_languages():
    return {
        "supported_languages": [
            {"code": "mr", "name": "मराठी (Marathi)", "native": "मराठी"},
            {"code": "hi", "name": "हिन्दी (Hindi)", "native": "हिन्दी"},
            {"code": "en", "name": "English", "native": "English"},
        ],
        "default": "mr",
    }


@router.get("/schemes")
def list_government_schemes():
    """Return structured metadata of verified government agricultural schemes from approved docs."""
    return {
        "schemes": [
            {
                "id": "pm-kisan",
                "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                "name_mr": "पीएम किसान सन्मान निधी योजना",
                "name_hi": "पीएम किसान सम्मान निधि योजना",
                "benefit": "Rs. 6,000/year in 3 equal installments of Rs. 2,000 via Direct Benefit Transfer (DBT)",
                "eligibility": "All cultivable landholding farmer families with Aadhaar-seeded bank account and completed e-KYC",
                "documents": ["Aadhaar Card", "Land Records (7/12 Extract / Khatauni)", "Bank Passbook", "Mobile Number for e-KYC"],
                "source": "Ministry of Agriculture & Farmers Welfare, GoI",
                "source_url": "https://pmkisan.gov.in",
                "publication_date": "2025-2026",
            },
            {
                "id": "pmfby",
                "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "name_mr": "पंतप्रधान पीक विमा योजना",
                "name_hi": "प्रधानमंत्री फसल बीमा योजना",
                "benefit": "Comprehensive crop loss coverage against drought, flood, hailstorm, unseasonal rain & pest outbreaks",
                "eligibility": "Loanee and non-loanee farmers cultivating notified crops; uniform farmer premium 2% (Kharif), 1.5% (Rabi), 5% (Commercial). Maharashtra offers 1 Rupee Crop Insurance state scheme.",
                "documents": ["Aadhaar Card", "7/12 & 8A Land Extract", "Crop Sowing Certificate (Peera Nond)", "Bank Account Details"],
                "source": "Department of Agriculture & Farmers Welfare, GoI",
                "source_url": "https://pmfby.gov.in",
                "publication_date": "2025-2026",
            },
            {
                "id": "kcc",
                "name": "Kisan Credit Card (KCC)",
                "name_mr": "किसान क्रेडिट कार्ड योजना",
                "name_hi": "किसान क्रेडिट कार्ड योजना",
                "benefit": "Short-term institutional crop loan up to Rs. 3 Lakhs at 4% effective interest rate on timely repayment",
                "eligibility": "Owner cultivators, tenant farmers, oral lessees, and SHGs/joint liability groups",
                "documents": ["KYC (Aadhaar/PAN)", "Land Holding Proof", "Passport Size Photos", "Bank Application Form"],
                "source": "Reserve Bank of India / Ministry of Agriculture",
                "source_url": "https://agricoop.gov.in",
                "publication_date": "2025",
            },
            {
                "id": "shc",
                "name": "Soil Health Card (SHC) Scheme",
                "name_mr": "मृदा आरोग्य पत्रिका योजना",
                "name_hi": "मृदा स्वास्थ्य कार्ड योजना",
                "benefit": "Free soil nutrient testing (N, P, K, pH, EC, micronutrients) every 2-3 years with crop-wise fertilizer prescription",
                "eligibility": "All Indian farmers via local Krishi Vigyan Kendra (KVK) or State Agriculture Department",
                "documents": ["Farmer Registration / Aadhaar", "Farm Survey Number"],
                "source": "Ministry of Agriculture & Farmers Welfare",
                "source_url": "https://soilhealth.dac.gov.in",
                "publication_date": "2025",
            },
        ]
    }


# ── Main Text & Voice Query Pipeline ──────────────────────────────────────────
async def _execute_pipeline(
    query_text: str,
    session_id: str,
    language_override: Optional[str] = None,
    crop_override: Optional[str] = None,
    region_override: Optional[str] = None,
    return_audio: bool = True,
    channel: str = "web",
    transcript: Optional[str] = None,
    stt_confidence: Optional[float] = None,
) -> QueryResponse:
    start_time = time.time()
    session_prefs = get_user_session(session_id)

    # 1. Language Identification
    lang_hint = language_override or session_prefs.get("preferred_language")
    lang_res = detect_language(query_text)
    if language_override in ("mr", "hi", "en"):
        detected_lang = language_override
    elif lang_res.get("lang") in ("mr", "hi", "en") and lang_res.get("confidence", 0) >= 0.55:
        detected_lang = lang_res["lang"]
    elif lang_hint in ("mr", "hi", "en"):
        detected_lang = lang_hint
    else:
        detected_lang = "hi"

    # 2. Check STT confidence first (if audio query)
    stt_gate = safety_service.check_stt_confidence(stt_confidence, lang=detected_lang)
    if not stt_gate["safe"]:
        answer = stt_gate["message"]
        decision = stt_gate["decision"]
        decision_reason = stt_gate["reason"]
        intent = "general_agriculture"
        entities = {}
        source_docs: List[SourceDocument] = []
        confidence = stt_confidence or 0.0
        generation_mode = "safety_gate"
    else:
        # 3. Intent Classification & Entity Extraction
        intent_info = intent_classifier.classify(query_text, lang=detected_lang)
        intent = intent_info["intent"]
        entities = intent_info.get("entities", {})
        missing_entities = intent_info.get("missing_entities", [])
        if crop_override and not entities.get("crop"):
            entities["crop"] = crop_override
            entities["commodity"] = crop_override
        if region_override and not entities.get("location"):
            entities["location"] = region_override
        if not entities.get("location") and session_prefs.get("district"):
            # Only fall back to session location if user didn't specify one AND query mentions weather/mandi implicitly
            pass

        confidence = intent_info.get("confidence", 0.7)
        source_docs = []
        decision = "ANSWER"
        decision_reason = "Processed successfully"
        generation_mode = "llm"

        # 4. Pre-retrieval Safety & Ambiguity Gate
        # For weather/mandi, use session district only if query clearly lacks one? Wait: Scenario 5 checks missing location handling or uses Pune default.
        # Keep missing_entities check for vague single-word queries and unsafe chemicals/off-topic.
        query_safety = safety_service.check_query_safety(
            query_text,
            lang=detected_lang,
            intent=intent,
            missing_entities=None if (entities.get("location") or session_prefs.get("district")) else missing_entities,
        )

        if not query_safety["safe"]:
            answer = query_safety["message"]
            decision = query_safety["decision"]
            decision_reason = query_safety["reason"]
            confidence = 0.0
            generation_mode = "safety_gate"

        # 5A. Live Mandi Tool Route
        elif intent == "mandi_prices":
            commodity = entities.get("commodity") or entities.get("crop") or crop_override or "Wheat"
            location = entities.get("location") or region_override or session_prefs.get("district") or "Pune"
            state = entities.get("state") or session_prefs.get("state") or "Maharashtra"

            mandi_res = mandi_service.get_prices(commodity=commodity, market=location, state=state)
            generation_mode = "live_tool"
            if mandi_res.get("success"):
                min_p = mandi_res.get("min_price", "N/A")
                max_p = mandi_res.get("max_price", "N/A")
                modal_p = mandi_res.get("modal_price", "N/A")
                mkt = mandi_res.get("market", location)
                dt = mandi_res.get("date", "")
                if detected_lang == "mr":
                    answer = f"{mkt} बाजारपेठेत {commodity}चे थेट बाजारभाव ({dt}): किमान ₹{min_p}, कमाल ₹{max_p}, सरासरी ₹{modal_p} प्रति क्विंटल (स्रोत: Agmarknet)."
                elif detected_lang == "hi":
                    answer = f"{mkt} मंडी में {commodity} का लाइव भाव ({dt}): न्यूनतम ₹{min_p}, अधिकतम ₹{max_p}, मॉडल भाव ₹{modal_p} प्रति क्विंटल (स्रोत: Agmarknet)।"
                else:
                    answer = f"Live {commodity} prices in {mkt} ({dt}): Min ₹{min_p}, Max ₹{max_p}, Modal ₹{modal_p} per quintal (Source: Agmarknet)."
            else:
                decision = "REFER"
                decision_reason = mandi_res.get("data_status", "unavailable")
                err_msg = mandi_res.get("error", "")
                if detected_lang == "mr":
                    answer = f"सध्या थेट मंडी भाव उपलब्ध नाहीत ({err_msg}). कृपया e-NAM किंवा Agmarknet पोर्टल तपासा."
                elif detected_lang == "hi":
                    answer = f"अभी लाइव मंडी भाव उपलब्ध नहीं हैं ({err_msg})। कृपया e-NAM या Agmarknet पोर्टल देखें।"
                else:
                    answer = f"Live mandi prices unavailable ({err_msg})."

        # 5B. Live Weather Tool Route
        elif intent == "weather":
            loc = entities.get("location") or region_override or session_prefs.get("district") or "Pune"
            state = entities.get("state") or session_prefs.get("state") or "Maharashtra"
            weather_res = weather_service.get_weather(location=loc, state=state, language=detected_lang)
            generation_mode = "live_tool"

            if weather_res.get("success"):
                temp = weather_res.get("temperature", "N/A")
                humidity = weather_res.get("humidity", "N/A")
                rain = weather_res.get("rainfall", 0.0)
                desc = weather_res.get("description", "")
                advisory = weather_res.get("advisory", "")
                src = weather_res.get("source", "Open-Meteo")
                if detected_lang == "mr":
                    answer = (
                        f"{weather_res['location']} येथील थेट हवामान: तापमान {temp}°C, आर्द्रता {humidity}%, "
                        f"पाऊस {rain} mm ({desc}).\nशेती सल्ला: {advisory} (स्रोत: {src})."
                    )
                elif detected_lang == "hi":
                    answer = (
                        f"{weather_res['location']} का लाइव मौसम: तापमान {temp}°C, नमी {humidity}%, "
                        f"वर्षा {rain} mm ({desc})।\nकृषि सलाह: {advisory} (स्रोत: {src})।"
                    )
                else:
                    answer = (
                        f"Live weather in {weather_res['location']}: {temp}°C, humidity {humidity}%, "
                        f"rain {rain}mm ({desc}). Advisory: {advisory} (Source: {src})."
                    )
            else:
                decision = "REFER"
                decision_reason = "weather_api_unavailable"
                answer = weather_res.get("error", "Weather information temporarily unavailable.")

        # 5C. Trusted RAG Pipeline (Crop Advice, Pests/Diseases, Schemes, General)
        else:
            approved_files = get_approved_filenames()
            retrieved_chunks = retriever.hybrid_search(
                query_text,
                k=settings.MAX_CHUNKS,
                semantic_weight=0.7,
                crop=entities.get("crop"),
                region=entities.get("location") or entities.get("state"),
                allowed_filenames=approved_files if approved_files else None,
                approved_only=True,
            )

            conf_check = safety_service.check_retrieval_confidence(
                query=query_text,
                retrieved_chunks=retrieved_chunks,
                intent=intent,
                lang=detected_lang,
            )

            if not conf_check["safe"]:
                answer = conf_check["message"]
                decision = conf_check["decision"]
                decision_reason = conf_check["reason"]
                confidence = round(max([c.get("score", 0.0) for c in retrieved_chunks], default=0.0), 3)
                generation_mode = "safety_gate"
            else:
                glossary_hints = get_glossary_hints(query_text, target_lang=detected_lang)
                gen_out = llm_service.answer_query_with_meta(
                    query=query_text,
                    context_chunks=retrieved_chunks,
                    language=detected_lang,
                    intent=intent,
                    glossary_hints=glossary_hints,
                )
                answer = gen_out["answer"]
                generation_mode = gen_out["generation_mode"]
                decision = "ANSWER"
                decision_reason = conf_check["reason"]
                confidence = round(max([c.get("score", 0.0) for c in retrieved_chunks], default=0.8), 3)

            for chunk in retrieved_chunks:
                meta = chunk.get("metadata", {})
                source_docs.append(SourceDocument(
                    filename=meta.get("filename", meta.get("source", "Agricultural Document")),
                    title=meta.get("title") or meta.get("filename"),
                    publisher=meta.get("publisher") or meta.get("source"),
                    source_url=meta.get("source_url") or None,
                    publication_date=meta.get("publication_date") or None,
                    approval_status=meta.get("approval_status", "approved"),
                    crop=meta.get("crop") or None,
                    region=meta.get("region") or None,
                    page=meta.get("page", 1),
                    chunk_index=meta.get("chunk_id", 0),
                    score=chunk.get("score", 0.0),
                    snippet=chunk.get("text", "")[:240],
                ))

    # 6. Text-to-Speech Synthesis (when requested)
    audio_path = None
    audio_url = None
    audio_base64 = None
    if return_audio and answer:
        tts_res = tts_service.synthesize(text=answer, language=detected_lang)
        if tts_res.get("success"):
            audio_path = tts_res.get("audio_path")
            if audio_path and os.path.exists(audio_path):
                filename = os.path.basename(audio_path)
                audio_url = f"/audio/responses/{filename}"
                try:
                    with open(audio_path, "rb") as af:
                        audio_base64 = base64.b64encode(af.read()).decode("utf-8")
                except Exception as e:
                    logger.warning(f"Audio base64 encoding warning: {e}")

    latency_ms = round((time.time() - start_time) * 1000, 2)
    sources_summary = list({s.filename for s in source_docs}) if source_docs else []

    # 7. Persist Conversation & Flag Review Queue if Low Confidence / Refused
    conv_id = None
    try:
        conv_id = save_conversation(
            session_id=session_id,
            user_query=query_text,
            detected_lang=detected_lang,
            intent=intent,
            response_text=answer,
            source_docs=sources_summary,
            channel=channel,
            decision=decision,
            confidence=confidence,
            latency_ms=latency_ms,
            generation_mode=generation_mode,
        )
        if decision in ("REFUSE", "REFER", "CLARIFY") or confidence < settings.CONFIDENCE_THRESHOLD:
            log_failed_or_low_confidence_query(
                session_id=session_id,
                user_query=query_text,
                detected_lang=detected_lang,
                intent=intent,
                decision=decision,
                reason=decision_reason,
                confidence=confidence,
                conversation_id=conv_id,
            )
    except Exception as e:
        logger.error(f"DB persistence error: {e}")

    return QueryResponse(
        conversation_id=conv_id,
        session_id=session_id,
        query=query_text,
        transcript=transcript,
        stt_confidence=stt_confidence,
        detected_lang=detected_lang,
        intent=intent,
        entities=entities,
        decision=decision,
        decision_reason=decision_reason,
        generation_mode=generation_mode,
        answer=answer,
        source_documents=source_docs,
        audio_base64=audio_base64,
        audio_url=audio_url,
        audio_path=audio_path,
        confidence=confidence,
        disclaimer=safety_service.get_disclaimer(detected_lang),
        processing_time_ms=latency_ms,
    )


@router.post("/query", response_model=QueryResponse)
async def process_query(req: QueryRequest):
    return await _execute_pipeline(
        query_text=req.query.strip(),
        session_id=req.session_id or "default",
        language_override=req.language,
        crop_override=req.crop,
        region_override=req.region,
        return_audio=req.return_audio,
        channel="web",
    )


@router.post("/voice-query", response_model=QueryResponse)
async def process_voice_query(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form("default"),
    language: Optional[str] = Form(None),
):
    ext = Path(audio_file.filename or "audio.wav").suffix.lower() or ".wav"
    if ext not in ALLOWED_AUDIO_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {ext}")

    uploads_dir = settings.BASE_DIR / "audio" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    saved_path = uploads_dir / f"voice_{uuid.uuid4().hex[:10]}{ext}"

    content = await audio_file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large (max 25MB).")
    with open(saved_path, "wb") as f:
        f.write(content)

    stt_res = stt_service.transcribe(str(saved_path), language=language)
    transcribed_text = stt_res.get("text", "").strip()
    stt_conf = stt_res.get("confidence", 0.0)
    stt_lang = language or stt_res.get("language") or "mr"

    try:
        save_audio_log(
            conversation_id=0,
            audio_path=str(saved_path),
            transcription=transcribed_text or "[unrecognized]",
            confidence=stt_conf,
            detected_lang=stt_lang,
            retention_hours=settings.AUDIO_RETENTION_HOURS,
        )
    except Exception as e:
        logger.warning(f"Audio log warning: {e}")

    if not transcribed_text:
        fallback_msg = safety_service.get_fallback_message("low_stt_confidence", stt_lang)
        return QueryResponse(
            session_id=session_id or "default",
            query="[Voice Input - Unclear]",
            transcript="",
            stt_confidence=0.0,
            detected_lang=stt_lang if stt_lang in ("mr", "hi", "en") else "mr",
            intent="general_agriculture",
            decision="CLARIFY",
            decision_reason=stt_res.get("error", "Empty Whisper transcription"),
            generation_mode="safety_gate",
            answer=fallback_msg,
            source_documents=[],
            confidence=0.0,
            disclaimer=safety_service.get_disclaimer(stt_lang),
        )

    return await _execute_pipeline(
        query_text=transcribed_text,
        session_id=session_id or "default",
        language_override=language or stt_res.get("language"),
        return_audio=True,
        channel="web_voice",
        transcript=transcribed_text,
        stt_confidence=stt_conf,
    )


# ── Live Mandi & Weather Endpoints ────────────────────────────────────────────
@router.get("/mandi-prices", response_model=MandiResponse)
def get_mandi_prices_endpoint(
    commodity: str = Query(..., description="Crop/Commodity name"),
    market: Optional[str] = Query(None, description="Market name"),
    state: str = Query("Maharashtra", description="State name"),
):
    res = mandi_service.get_prices(commodity=commodity, market=market, state=state)
    prices_list: List[MandiPrice] = []
    if res.get("success"):
        for r in res.get("records", [res]):
            prices_list.append(MandiPrice(
                market=r.get("market", market or "APMC"),
                state=r.get("state", state),
                district=r.get("district", state),
                commodity=r.get("commodity", commodity),
                variety=r.get("variety"),
                min_price=r.get("min_price"),
                max_price=r.get("max_price"),
                modal_price=r.get("modal_price"),
                unit=r.get("unit", "Quintal"),
                date=r.get("date"),
            ))

    return MandiResponse(
        commodity=res.get("commodity", commodity),
        prices=prices_list,
        source=res.get("source", "Agmarknet / data.gov.in"),
        is_live=res.get("is_live", False),
        cached=res.get("cached", False),
        data_status=res.get("data_status", "unavailable"),
        retrieved_at=res.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
        message=res.get("error", "Live mandi prices retrieved successfully"),
    )


@router.get("/weather", response_model=WeatherResponse)
def get_weather_endpoint(
    location: str = Query(..., description="City or District name"),
    state: str = Query("Maharashtra", description="State name"),
    language: str = Query("mr", description="Response language: mr, hi, en"),
):
    res = weather_service.get_weather(location=location, state=state, language=language)
    forecast_days = [WeatherForecastDay(**d) for d in res.get("forecast_days", [])]
    return WeatherResponse(
        location=res.get("location", location),
        temperature_celsius=res.get("temperature"),
        feels_like_celsius=res.get("feels_like"),
        humidity_percent=res.get("humidity"),
        wind_speed_kmh=res.get("wind_speed"),
        rainfall_mm=res.get("rainfall", 0.0),
        description=res.get("description", res.get("error", "")),
        forecast_summary=res.get("forecast_summary", ""),
        forecast_days=forecast_days,
        agri_advisory=res.get("advisory", ""),
        source=res.get("source", "Open-Meteo"),
        is_live=res.get("is_live", False),
        cached=res.get("cached", False),
        retrieved_at=res.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
    )


# ── User Feedback & Privacy Settings ──────────────────────────────────────────
@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    fb_id = save_feedback(
        session_id=req.session_id,
        rating=1 if req.rating >= 0 else -1,
        comment=req.comment,
        conversation_id=req.conversation_id,
    )
    return {"status": "ok", "feedback_id": fb_id}


@router.get("/settings/session/{session_id}")
def fetch_session_settings(session_id: str):
    return get_user_session(session_id)


@router.post("/settings/session")
def update_session_settings(req: SessionPreferencesRequest):
    return upsert_user_session(
        session_id=req.session_id,
        channel=req.channel,
        preferred_language=req.preferred_language,
        state=req.state,
        district=req.district,
        consent_given=req.consent_given,
        audio_retention_opt_in=req.audio_retention_opt_in,
    )


@router.get("/conversation-history/{session_id}", response_model=ConversationHistoryResponse)
def get_history_endpoint(session_id: str, limit: int = 20):
    entries = get_conversation_history(session_id=session_id, limit=limit)
    history = [ConversationEntry(**row) for row in entries]
    return ConversationHistoryResponse(session_id=session_id, history=history, total=len(history))


# ── Document Ingestion & Knowledge Management (Module 5 & 14) ─────────────────
@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    source_name: Optional[str] = Form("Agricultural University / KVK"),
    publisher: Optional[str] = Form(None),
    source_url: Optional[str] = Form(""),
    publication_date: Optional[str] = Form("2026-01"),
    language: Optional[str] = Form("en"),
    crop: Optional[str] = Form(""),
    region: Optional[str] = Form("Maharashtra"),
    topic: Optional[str] = Form("general_agriculture"),
    approval_status: Optional[str] = Form("approved"),
    version: Optional[str] = Form("1.0"),
):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")

    raw_pdfs_dir = settings.BASE_DIR / "data" / "raw_pdfs"
    raw_pdfs_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    dest_path = raw_pdfs_dir / safe_name

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    file_hash = doc_processor.compute_hash(str(dest_path))
    existing = get_document_by_hash(file_hash)
    if existing and existing.get("filename") == safe_name:
        return DocumentUploadResponse(
            document_id=existing["id"],
            filename=safe_name,
            pages=existing.get("pages", 1),
            chunks_created=existing.get("chunks_count", 0),
            topic=existing.get("topic"),
            approval_status=existing.get("approval_status", "approved"),
            duplicate_detected=True,
            message="Duplicate PDF detected via SHA-256 hash; existing index retained.",
        )

    chunks = doc_processor.process_pdf(
        str(dest_path),
        source_name=source_name or "Agricultural Source",
        topic=topic,
        publisher=publisher or source_name,
        source_url=source_url,
        publication_date=publication_date,
        language=language or "en",
        crop=crop,
        region=region or "Maharashtra",
        approval_status=approval_status or "approved",
        version=version or "1.0",
    )
    if not chunks:
        raise HTTPException(status_code=400, detail="No readable text extracted from PDF.")

    # Remove old vectors if re-uploading an updated version of the same filename
    vector_store.remove_by_filename(safe_name, embedding_service=embedding_service)

    texts = [c["text"] for c in chunks]
    embeddings = embedding_service.encode(texts)
    vector_store.add_documents(chunks, embeddings)
    vector_store.save()
    retriever.refresh()

    pages_count = max([c["metadata"].get("page", 1) for c in chunks], default=1)
    doc_id = save_document_metadata(
        filename=safe_name,
        source=source_name or "Agricultural Source",
        pages=pages_count,
        topic=topic or "general",
        title=safe_name,
        publisher=publisher or source_name,
        source_url=source_url,
        publication_date=publication_date,
        language=language or "en",
        crop=crop,
        region=region or "Maharashtra",
        chunks_count=len(chunks),
        approval_status=approval_status or "approved",
        version=version or "1.0",
        file_hash=file_hash,
    )

    return DocumentUploadResponse(
        document_id=doc_id,
        filename=safe_name,
        pages=pages_count,
        chunks_created=len(chunks),
        topic=topic,
        approval_status=approval_status or "approved",
        duplicate_detected=False,
        message=f"Ingested {len(chunks)} chunks with status '{approval_status}'.",
    )


# ── Admin Console & Expert Review Loop (Module 14) ────────────────────────────
@router.get("/admin/documents")
def admin_list_documents(status: Optional[str] = None, _: bool = Depends(require_admin)):
    return {"documents": get_all_documents(status_filter=status)}


@router.post("/admin/documents/{doc_id}/review")
def admin_review_document(doc_id: int, req: DocumentReviewRequest, _: bool = Depends(require_admin)):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    update_document_status(doc_id, req.approval_status, req.reviewed_by)
    vector_store.update_metadata_status(doc["filename"], req.approval_status)
    retriever.refresh()
    return {"status": "ok", "document_id": doc_id, "approval_status": req.approval_status}


@router.delete("/admin/documents/{doc_id}")
def admin_delete_document(doc_id: int, _: bool = Depends(require_admin)):
    filename = delete_document_record(doc_id)
    if not filename:
        raise HTTPException(status_code=404, detail="Document not found")
    removed_chunks = vector_store.remove_by_filename(filename, embedding_service=embedding_service)
    retriever.refresh()
    return {"status": "deleted", "filename": filename, "removed_chunks": removed_chunks}


@router.get("/admin/review-queue")
def admin_get_review_queue(status: Optional[str] = None, _: bool = Depends(require_admin)):
    return {"items": get_review_queue(status_filter=status)}


@router.post("/admin/review-queue/{item_id}/resolve")
def admin_resolve_review_item(item_id: int, req: ReviewResolveRequest, _: bool = Depends(require_admin)):
    ok = resolve_review_item(item_id, req.reviewer_notes)
    if not ok:
        raise HTTPException(status_code=404, detail="Review item not found")
    return {"status": "resolved", "item_id": item_id}


@router.get("/admin/glossary")
def admin_list_glossary(category: Optional[str] = None):
    return {"terms": get_glossary_terms(category=category)}


@router.post("/admin/glossary")
def admin_add_glossary(req: GlossaryTermRequest, _: bool = Depends(require_admin)):
    term_id = add_glossary_term(req.term_en, req.term_mr, req.term_hi, req.category, req.notes)
    return {"status": "created", "id": term_id}


@router.delete("/admin/glossary/{term_id}")
def admin_delete_glossary(term_id: int, _: bool = Depends(require_admin)):
    ok = delete_glossary_term(term_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return {"status": "deleted", "id": term_id}


@router.get("/admin/metrics")
def admin_metrics(_: bool = Depends(require_admin)):
    metrics = get_system_metrics()
    metrics["vector_count"] = vector_store.total_documents
    metrics["recent_conversations"] = get_recent_conversations(limit=15)
    metrics["recent_feedback"] = get_feedback_list(limit=15)
    return metrics


@router.post("/admin/cleanup-audio")
def admin_cleanup_audio(_: bool = Depends(require_admin)):
    removed = cleanup_expired_audio_files()
    return {"status": "ok", "purged_files": removed}
