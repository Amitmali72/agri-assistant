"""
WhatsApp Business Cloud API Integration Router (Module 1).
Supports:
- GET /whatsapp/webhook: Meta Cloud API verification challenge
- POST /whatsapp/webhook: Inbound text & voice note messages with deduplication & consent check
- POST /whatsapp/test-mock: Realistic mock payload testing when live credentials are absent
- Outbound text & audio media upload + dispatch with retry handling
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from backend.config import settings
from backend.database.db import get_user_session, upsert_user_session
from backend.api.routes import _execute_pipeline, stt_service

logger = logging.getLogger(__name__)

whatsapp_router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

_processed_message_ids: Dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 3600


class WhatsAppMockRequest(BaseModel):
    sender_phone: str = "919876543210"
    message_type: str = "text"  # "text" or "audio"
    text_content: Optional[str] = "गव्हाच्या पिकावर कोणती खते द्यावी?"
    audio_path: Optional[str] = None
    language: Optional[str] = "mr"


@whatsapp_router.get("/webhook")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    expected_token = settings.WHATSAPP_VERIFY_TOKEN or "agri_assistant_webhook_verify_token"
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verified successfully.")
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@whatsapp_router.post("/webhook")
async def handle_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    entry = body.get("entry", [])
    if not entry:
        return {"status": "ignored", "reason": "no entry"}
    changes = entry[0].get("changes", [])
    if not changes:
        return {"status": "ignored", "reason": "no changes"}
    value = changes[0].get("value", {})
    messages = value.get("messages", [])
    if not messages:
        return {"status": "ok", "type": "status_update"}

    message = messages[0]
    msg_id = message.get("id") or f"msg_{time.time()}"
    sender_phone = message.get("from", "unknown")
    msg_type = message.get("type", "text")

    # Deduplication
    now = time.time()
    for old_id, ts in list(_processed_message_ids.items()):
        if now - ts > DEDUP_WINDOW_SECONDS:
            del _processed_message_ids[old_id]

    if msg_id in _processed_message_ids:
        return {"status": "duplicate", "message_id": msg_id}
    _processed_message_ids[msg_id] = now

    background_tasks.add_task(
        _process_and_reply_whatsapp,
        sender_phone=sender_phone,
        message=message,
        msg_type=msg_type,
    )
    return {"status": "received", "message_id": msg_id}


async def _process_and_reply_whatsapp(sender_phone: str, message: Dict[str, Any], msg_type: str):
    session_id = f"whatsapp_{sender_phone}"
    session = get_user_session(session_id)
    pref_lang = session.get("preferred_language", "mr")

    query_text = ""
    stt_conf = None
    if msg_type == "text":
        query_text = message.get("text", {}).get("body", "").strip()
        # Handle quick opt-out / language commands
        if query_text.lower() in ("stop", "unsubscribe"):
            upsert_user_session(session_id, channel="whatsapp", consent_given=False)
            await _send_whatsapp_text(sender_phone, "You have been opted out of KrishiMitra alerts. Reply START anytime.")
            return
        if query_text.lower() in ("start", "marathi", "मराठी"):
            upsert_user_session(session_id, channel="whatsapp", preferred_language="mr", consent_given=True)
        elif query_text.lower() in ("hindi", "हिन्दी", "हिंदी"):
            upsert_user_session(session_id, channel="whatsapp", preferred_language="hi", consent_given=True)

    elif msg_type in ("audio", "voice"):
        media_id = message.get("audio", {}).get("id") or message.get("voice", {}).get("id")
        if media_id and settings.WHATSAPP_TOKEN:
            downloaded_audio = await _download_whatsapp_media(media_id)
            if downloaded_audio:
                stt_res = stt_service.transcribe(downloaded_audio, language=pref_lang)
                query_text = stt_res.get("text", "")
                stt_conf = stt_res.get("confidence", 0.0)

    if not query_text:
        await _send_whatsapp_text(
            sender_phone,
            "कृषीमित्र (KrishiMitra): आवाज स्पष्ट ऐकू आला नाही किंवा संदेश रिकामा आहे. कृपया पुन्हा स्पष्टपणे बोला किंवा संदेश टाइप करा.",
        )
        return

    res = await _execute_pipeline(
        query_text=query_text,
        session_id=session_id,
        return_audio=True,
        channel="whatsapp",
        transcript=query_text if msg_type in ("audio", "voice") else None,
        stt_confidence=stt_conf,
    )

    sources_txt = ", ".join({s.filename for s in res.source_documents}) if res.source_documents else ""
    reply_body = res.answer
    if sources_txt:
        reply_body += f"\n\n📚 Sources: {sources_txt}"

    await _send_whatsapp_text(sender_phone, reply_body)
    if res.audio_path and os.path.exists(res.audio_path) and settings.WHATSAPP_TOKEN:
        await _send_whatsapp_audio(sender_phone, res.audio_path)


async def _download_whatsapp_media(media_id: str) -> Optional[str]:
    if not settings.WHATSAPP_TOKEN:
        return None
    try:
        import httpx
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            url_resp = await client.get(f"https://graph.facebook.com/v19.0/{media_id}", headers=headers)
            url_resp.raise_for_status()
            media_url = url_resp.json().get("url")
            if not media_url:
                return None

            audio_resp = await client.get(media_url, headers=headers)
            audio_resp.raise_for_status()
            out_dir = settings.BASE_DIR / "audio" / "uploads"
            out_dir.mkdir(parents=True, exist_ok=True)
            saved_path = out_dir / f"wa_{media_id}.ogg"
            with open(saved_path, "wb") as f:
                f.write(audio_resp.content)
            return str(saved_path)
    except Exception as e:
        logger.error(f"Failed to download WhatsApp media {media_id}: {e}")
        return None


async def _send_whatsapp_text(to_phone: str, text: str, max_retries: int = 2):
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_ID:
        logger.info(f"[WhatsApp Mock Dispatch] To: {to_phone} | Message: {text[:80]}...")
        return
    import httpx
    url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to_phone, "type": "text", "text": {"body": text}}

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"WhatsApp text dispatch failed after retries: {e}")


async def _send_whatsapp_audio(to_phone: str, audio_path: str):
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_ID or not os.path.exists(audio_path):
        return
    try:
        import httpx
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
        upload_url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_ID}/media"
        async with httpx.AsyncClient(timeout=20.0) as client:
            with open(audio_path, "rb") as af:
                files = {"file": (os.path.basename(audio_path), af, "audio/mpeg")}
                data = {"messaging_product": "whatsapp"}
                up_resp = await client.post(upload_url, headers=headers, data=data, files=files)
                up_resp.raise_for_status()
                media_id = up_resp.json().get("id")

            if media_id:
                msg_url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_ID}/messages"
                payload = {"messaging_product": "whatsapp", "to": to_phone, "type": "audio", "audio": {"id": media_id}}
                await client.post(msg_url, headers={**headers, "Content-Type": "application/json"}, json=payload)
    except Exception as e:
        logger.error(f"WhatsApp audio dispatch failed: {e}")


@whatsapp_router.post("/test-mock")
async def test_mock_whatsapp_message(req: WhatsAppMockRequest):
    query_text = req.text_content or ""
    stt_conf = None
    if req.message_type == "audio" and req.audio_path and os.path.exists(req.audio_path):
        stt_res = stt_service.transcribe(req.audio_path, language=req.language)
        query_text = stt_res.get("text", query_text)
        stt_conf = stt_res.get("confidence", 0.0)

    result = await _execute_pipeline(
        query_text=query_text,
        session_id=f"whatsapp_{req.sender_phone}",
        language_override=req.language,
        return_audio=True,
        channel="whatsapp_mock",
        transcript=query_text if req.message_type == "audio" else None,
        stt_confidence=stt_conf,
    )

    return {
        "status": "success",
        "simulated_phone": req.sender_phone,
        "transcribed_input": query_text,
        "reply_text": result.answer,
        "intent": result.intent,
        "decision": result.decision,
        "language": result.detected_lang,
        "audio_url": result.audio_url,
        "sources": [s.filename for s in result.source_documents],
    }
