"""
SQLite database layer for KrishiMitra Agricultural Assistant.
Supports:
- Conversation logs (with confidence decision, latency, generation mode, channel)
- Knowledge documents (with full provenance, approval_status, versioning, file_hash)
- Audio logs (with transcription confidence and retention expiry)
- User feedback (thumbs up/down + comments)
- Expert review queue (failed, low-confidence, and refused queries)
- Agricultural terminology glossary (Marathi / Hindi / English)
- User sessions & privacy consent preferences
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.config import settings


DEFAULT_GLOSSARY = [
    ("Wheat", "गहू", "गेहूं", "crop", "Rabi cereal crop"),
    ("Rice / Paddy", "भात / तांदूळ", "धान / चावल", "crop", "Kharif staple cereal"),
    ("Cotton", "कापूस", "कपास", "crop", "Major cash fiber crop in Vidarbha/Marathwada"),
    ("Soybean", "सोयाबीन", "सोयाबीन", "crop", "Kharif oilseed crop"),
    ("Onion", "कांदा", "प्याज", "crop", "Major horticulture crop in Nashik/Pune"),
    ("Sugarcane", "ऊस", "गन्ना", "crop", "Perennial cash crop"),
    ("Gram / Chickpea", "हरभरा", "चना", "crop", "Rabi pulse crop"),
    ("Tur / Pigeonpea", "तूर", "अरहर / तूर", "crop", "Kharif pulse crop"),
    ("Aphids", "मावा", "माहू / चेपा", "pest", "Sap-sucking insect pest"),
    ("Bollworm", "बोंड अळी", "सुंडी / इल्ली", "pest", "Major cotton pest"),
    ("Whitefly", "पांढरी माशी", "सफेद मक्खी", "pest", "Vector for cotton leaf curl virus"),
    ("Armyworm", "लष्करी अळी", "सैनिक कीट", "pest", "Spodoptera leaf-eating caterpillar"),
    ("Blight", "करपा रोग", "झुलसा रोग", "disease", "Fungal/bacterial leaf spot & blight"),
    ("Rust", "तांबेरा / गेरूआ", "गेरुआ / रतुआ", "disease", "Puccinia fungal disease on wheat"),
    ("Wilt", "मर रोग", "उकठा / मुरझान", "disease", "Fusarium vascular wilt"),
    ("Yellowing / Chlorosis", "पाने पिवळी पडणे", "पत्ते पीले पड़ना", "disease", "Nitrogen/Iron/Magnesium deficiency or viral/fungal stress"),
    ("Neem Oil / NSKE", "निंबोळी अर्क / निम तेल", "नीम तेल / निंबोली अर्क", "chemical", "Botanical biopesticide"),
    ("Urea", "युरिया", "यूरिया", "chemical", "Nitrogenous fertilizer (46% N)"),
    ("DAP", "डीएपी", "डीएपी", "chemical", "Diammonium Phosphate (18-46-0)"),
    ("PM-KISAN", "पीएम किसान सन्मान निधी", "पीएम किसान सम्मान निधि", "scheme", "Rs 6,000/year direct income support"),
    ("PMFBY", "पंतप्रधान पीक विमा योजना", "प्रधानमंत्री फसल बीमा योजना", "scheme", "Crop insurance against natural calamities"),
    ("KCC", "किसान क्रेडिट कार्ड", "किसान क्रेडिट कार्ड", "scheme", "Short-term crop credit at 4% effective interest"),
    ("Soil Health Card", "मृदा आरोग्य पत्रिका", "मृदा स्वास्थ्य कार्ड", "scheme", "Periodic soil nutrient testing card"),
    ("KVK", "कृषी विज्ञान केंद्र", "कृषि विज्ञान केंद्र", "general", "District agricultural extension center"),
    ("APMC / Mandi", "कृषी उत्पन्न बाजार समिती (मंडी)", "कृषि उपज मंडी", "general", "Regulated agricultural produce market"),
]


def _get_connection() -> sqlite3.Connection:
    """Return a new database connection with row_factory set."""
    os.makedirs(os.path.dirname(os.path.abspath(settings.DATABASE_PATH)), exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_columns(cursor: sqlite3.Cursor, table: str, columns: Dict[str, str]) -> None:
    """Safely add new columns to an existing SQLite table."""
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row["name"] for row in cursor.fetchall()}
    for col_name, col_def in columns.items():
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")


def init_db() -> None:
    """Create and migrate all required tables."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      TEXT    NOT NULL,
                channel         TEXT    DEFAULT 'web',
                user_query      TEXT    NOT NULL,
                detected_lang   TEXT,
                intent          TEXT,
                decision        TEXT    DEFAULT 'ANSWER',
                confidence      REAL    DEFAULT 0.0,
                response_text   TEXT,
                source_docs     TEXT,
                latency_ms      REAL    DEFAULT 0.0,
                generation_mode TEXT    DEFAULT 'llm',
                timestamp       TEXT    NOT NULL
            )
        """)
        _ensure_columns(cursor, "conversations", {
            "channel": "TEXT DEFAULT 'web'",
            "decision": "TEXT DEFAULT 'ANSWER'",
            "confidence": "REAL DEFAULT 0.0",
            "latency_ms": "REAL DEFAULT 0.0",
            "generation_mode": "TEXT DEFAULT 'llm'",
        })

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                filename         TEXT    NOT NULL,
                title            TEXT,
                publisher        TEXT,
                source           TEXT,
                source_url       TEXT,
                publication_date TEXT,
                language         TEXT    DEFAULT 'en',
                crop             TEXT,
                region           TEXT    DEFAULT 'India',
                pages            INTEGER DEFAULT 1,
                chunks_count     INTEGER DEFAULT 0,
                ingested_at      TEXT    NOT NULL,
                topic            TEXT,
                approval_status  TEXT    DEFAULT 'approved',
                version          TEXT    DEFAULT '1.0',
                file_hash        TEXT,
                reviewed_by      TEXT,
                reviewed_at      TEXT
            )
        """)
        _ensure_columns(cursor, "documents", {
            "title": "TEXT",
            "publisher": "TEXT",
            "source_url": "TEXT",
            "publication_date": "TEXT",
            "language": "TEXT DEFAULT 'en'",
            "crop": "TEXT",
            "region": "TEXT DEFAULT 'India'",
            "chunks_count": "INTEGER DEFAULT 0",
            "approval_status": "TEXT DEFAULT 'approved'",
            "version": "TEXT DEFAULT '1.0'",
            "file_hash": "TEXT",
            "reviewed_by": "TEXT",
            "reviewed_at": "TEXT",
        })

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                audio_path      TEXT,
                transcription   TEXT,
                confidence      REAL    DEFAULT 0.0,
                detected_lang   TEXT,
                expires_at      TEXT,
                timestamp       TEXT    NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        _ensure_columns(cursor, "audio_logs", {
            "confidence": "REAL DEFAULT 0.0",
            "detected_lang": "TEXT",
            "expires_at": "TEXT",
        })

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                session_id      TEXT    NOT NULL,
                rating          INTEGER NOT NULL,
                comment         TEXT,
                created_at      TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failed_queries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                session_id      TEXT    NOT NULL,
                user_query      TEXT    NOT NULL,
                detected_lang   TEXT,
                intent          TEXT,
                decision        TEXT,
                reason          TEXT,
                confidence      REAL    DEFAULT 0.0,
                status          TEXT    DEFAULT 'open',
                reviewer_notes  TEXT,
                created_at      TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS glossary_terms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                term_en     TEXT    NOT NULL,
                term_mr     TEXT    NOT NULL,
                term_hi     TEXT    NOT NULL,
                category    TEXT    DEFAULT 'general',
                notes       TEXT,
                created_at  TEXT    NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id              TEXT PRIMARY KEY,
                channel                 TEXT DEFAULT 'web',
                preferred_language      TEXT DEFAULT 'mr',
                state                   TEXT DEFAULT 'Maharashtra',
                district                TEXT DEFAULT 'Pune',
                consent_given           INTEGER DEFAULT 1,
                consent_timestamp       TEXT,
                audio_retention_opt_in  INTEGER DEFAULT 0,
                updated_at              TEXT NOT NULL
            )
        """)

        # Seed default glossary if empty
        cursor.execute("SELECT COUNT(*) AS cnt FROM glossary_terms")
        if cursor.fetchone()["cnt"] == 0:
            now = datetime.now(timezone.utc).isoformat()
            cursor.executemany(
                """
                INSERT INTO glossary_terms (term_en, term_mr, term_hi, category, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [(en, mr, hi, cat, notes, now) for en, mr, hi, cat, notes in DEFAULT_GLOSSARY],
            )

        conn.commit()
    finally:
        conn.close()


# ── Conversations ────────────────────────────────────────────────────────────

def save_conversation(
    session_id: str,
    user_query: str,
    detected_lang: str,
    intent: str,
    response_text: str,
    source_docs: Any,
    channel: str = "web",
    decision: str = "ANSWER",
    confidence: float = 0.8,
    latency_ms: float = 0.0,
    generation_mode: str = "llm",
) -> int:
    if isinstance(source_docs, (list, dict)):
        source_docs = json.dumps(source_docs, ensure_ascii=False)

    timestamp = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations
                (session_id, channel, user_query, detected_lang, intent, decision,
                 confidence, response_text, source_docs, latency_ms, generation_mode, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id, channel, user_query, detected_lang, intent, decision,
                confidence, response_text, source_docs, latency_ms, generation_mode, timestamp
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_conversation_history(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM conversations
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        rows = cursor.fetchall()
        history = [dict(row) for row in reversed(rows)]
        for entry in history:
            try:
                entry["source_docs"] = json.loads(entry["source_docs"] or "[]")
            except (json.JSONDecodeError, TypeError):
                pass
        return history
    finally:
        conn.close()


def get_recent_conversations(limit: int = 50) -> List[Dict[str, Any]]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = [dict(r) for r in cursor.fetchall()]
        for entry in rows:
            try:
                entry["source_docs"] = json.loads(entry["source_docs"] or "[]")
            except (json.JSONDecodeError, TypeError):
                pass
        return rows
    finally:
        conn.close()


# ── Documents & Governance ───────────────────────────────────────────────────

def save_document_metadata(
    filename: str,
    source: str,
    pages: int,
    topic: str,
    title: Optional[str] = None,
    publisher: Optional[str] = None,
    source_url: Optional[str] = None,
    publication_date: Optional[str] = None,
    language: str = "en",
    crop: Optional[str] = None,
    region: str = "India",
    chunks_count: int = 0,
    approval_status: str = "approved",
    version: str = "1.0",
    file_hash: Optional[str] = None,
) -> int:
    ingested_at = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        # Update if same filename already tracked, else insert
        cursor.execute("SELECT id FROM documents WHERE filename = ?", (filename,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE documents SET
                    title = ?, publisher = ?, source = ?, source_url = ?,
                    publication_date = ?, language = ?, crop = ?, region = ?,
                    pages = ?, chunks_count = ?, ingested_at = ?, topic = ?,
                    approval_status = ?, version = ?, file_hash = ?
                WHERE id = ?
                """,
                (
                    title or filename, publisher or source, source, source_url,
                    publication_date, language, crop, region,
                    pages, chunks_count, ingested_at, topic,
                    approval_status, version, file_hash, existing["id"]
                ),
            )
            conn.commit()
            return existing["id"]

        cursor.execute(
            """
            INSERT INTO documents (
                filename, title, publisher, source, source_url, publication_date,
                language, crop, region, pages, chunks_count, ingested_at, topic,
                approval_status, version, file_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename, title or filename, publisher or source, source, source_url,
                publication_date, language, crop, region, pages, chunks_count,
                ingested_at, topic, approval_status, version, file_hash
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_documents(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        if status_filter:
            cursor.execute(
                "SELECT * FROM documents WHERE approval_status = ? ORDER BY id DESC",
                (status_filter,),
            )
        else:
            cursor.execute("SELECT * FROM documents ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_document_by_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    if not file_hash:
        return None
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_document_status(
    doc_id: int,
    approval_status: str,
    reviewed_by: str = "admin",
) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE documents
            SET approval_status = ?, reviewed_by = ?, reviewed_at = ?
            WHERE id = ?
            """,
            (approval_status, reviewed_by, now, doc_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_document_record(doc_id: int) -> Optional[str]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT filename FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        if not row:
            return None
        filename = row["filename"]
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        return filename
    finally:
        conn.close()


def get_approved_filenames() -> set:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT filename FROM documents WHERE approval_status = 'approved'")
        return {row["filename"] for row in cursor.fetchall()}
    finally:
        conn.close()


# ── Audio Logs & Retention ───────────────────────────────────────────────────

def save_audio_log(
    conversation_id: int,
    audio_path: str,
    transcription: str,
    confidence: float = 0.0,
    detected_lang: str = "unknown",
    retention_hours: int = 24,
) -> int:
    now_dt = datetime.now(timezone.utc)
    timestamp = now_dt.isoformat()
    expires_at = (now_dt + timedelta(hours=retention_hours)).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audio_logs
                (conversation_id, audio_path, transcription, confidence, detected_lang, expires_at, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (conversation_id, audio_path, transcription, confidence, detected_lang, expires_at, timestamp),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def cleanup_expired_audio_files() -> int:
    """Remove expired uploaded audio files per privacy retention policy."""
    now = datetime.now(timezone.utc).isoformat()
    removed = 0
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, audio_path FROM audio_logs WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,),
        )
        rows = cursor.fetchall()
        for row in rows:
            path = row["audio_path"]
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    removed += 1
                except OSError:
                    pass
            cursor.execute("UPDATE audio_logs SET audio_path = '[purged]' WHERE id = ?", (row["id"],))
        conn.commit()
        return removed
    finally:
        conn.close()


# ── Feedback & Review Queue ──────────────────────────────────────────────────

def save_feedback(
    session_id: str,
    rating: int,
    comment: Optional[str] = None,
    conversation_id: Optional[int] = None,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO feedback (conversation_id, session_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, session_id, rating, comment, now),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_feedback_list(limit: int = 50) -> List[Dict[str, Any]]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def log_failed_or_low_confidence_query(
    session_id: str,
    user_query: str,
    detected_lang: str,
    intent: str,
    decision: str,
    reason: str,
    confidence: float,
    conversation_id: Optional[int] = None,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO failed_queries
                (conversation_id, session_id, user_query, detected_lang, intent, decision, reason, confidence, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (conversation_id, session_id, user_query, detected_lang, intent, decision, reason, confidence, now),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_review_queue(status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        if status_filter:
            cursor.execute(
                "SELECT * FROM failed_queries WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status_filter, limit),
            )
        else:
            cursor.execute("SELECT * FROM failed_queries ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def resolve_review_item(item_id: int, reviewer_notes: str = "") -> bool:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE failed_queries SET status = 'resolved', reviewer_notes = ? WHERE id = ?",
            (reviewer_notes, item_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── Glossary ─────────────────────────────────────────────────────────────────

def get_glossary_terms(category: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM glossary_terms WHERE category = ? ORDER BY term_en", (category,))
        else:
            cursor.execute("SELECT * FROM glossary_terms ORDER BY category, term_en")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def add_glossary_term(
    term_en: str,
    term_mr: str,
    term_hi: str,
    category: str = "general",
    notes: str = "",
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO glossary_terms (term_en, term_mr, term_hi, category, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (term_en, term_mr, term_hi, category, notes, now),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def delete_glossary_term(term_id: int) -> bool:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM glossary_terms WHERE id = ?", (term_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── User Sessions & Consent ──────────────────────────────────────────────────

def upsert_user_session(
    session_id: str,
    channel: str = "web",
    preferred_language: str = "mr",
    state: str = "Maharashtra",
    district: str = "Pune",
    consent_given: bool = True,
    audio_retention_opt_in: bool = False,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_sessions
                (session_id, channel, preferred_language, state, district,
                 consent_given, consent_timestamp, audio_retention_opt_in, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                channel = excluded.channel,
                preferred_language = excluded.preferred_language,
                state = excluded.state,
                district = excluded.district,
                consent_given = excluded.consent_given,
                consent_timestamp = COALESCE(user_sessions.consent_timestamp, excluded.consent_timestamp),
                audio_retention_opt_in = excluded.audio_retention_opt_in,
                updated_at = excluded.updated_at
            """,
            (
                session_id, channel, preferred_language, state, district,
                1 if consent_given else 0, now if consent_given else None,
                1 if audio_retention_opt_in else 0, now
            ),
        )
        conn.commit()
        return get_user_session(session_id)
    finally:
        conn.close()


def get_user_session(session_id: str) -> Dict[str, Any]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["consent_given"] = bool(data.get("consent_given", 1))
            data["audio_retention_opt_in"] = bool(data.get("audio_retention_opt_in", 0))
            return data
        return {
            "session_id": session_id,
            "channel": "web",
            "preferred_language": "mr",
            "state": "Maharashtra",
            "district": "Pune",
            "consent_given": True,
            "audio_retention_opt_in": False,
        }
    finally:
        conn.close()


# ── Monitoring Metrics ───────────────────────────────────────────────────────

def get_system_metrics() -> Dict[str, Any]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM conversations")
        total_queries = cursor.fetchone()["total"]

        cursor.execute("SELECT AVG(latency_ms) AS avg_lat, AVG(confidence) AS avg_conf FROM conversations")
        agg = cursor.fetchone()

        cursor.execute("SELECT decision, COUNT(*) AS cnt FROM conversations GROUP BY decision")
        decisions = {r["decision"] or "ANSWER": r["cnt"] for r in cursor.fetchall()}

        cursor.execute("SELECT intent, COUNT(*) AS cnt FROM conversations GROUP BY intent")
        intents = {r["intent"] or "general_agriculture": r["cnt"] for r in cursor.fetchall()}

        cursor.execute("SELECT detected_lang, COUNT(*) AS cnt FROM conversations GROUP BY detected_lang")
        languages = {r["detected_lang"] or "unknown": r["cnt"] for r in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) AS pos FROM feedback WHERE rating > 0")
        pos_fb = cursor.fetchone()["pos"]
        cursor.execute("SELECT COUNT(*) AS neg FROM feedback WHERE rating < 0")
        neg_fb = cursor.fetchone()["neg"]

        cursor.execute("SELECT COUNT(*) AS open_q FROM failed_queries WHERE status = 'open'")
        open_review = cursor.fetchone()["open_q"]

        cursor.execute("SELECT approval_status, COUNT(*) AS cnt FROM documents GROUP BY approval_status")
        doc_stats = {r["approval_status"] or "approved": r["cnt"] for r in cursor.fetchall()}

        return {
            "total_queries": total_queries,
            "avg_latency_ms": round(agg["avg_lat"] or 0.0, 1),
            "avg_confidence": round(agg["avg_conf"] or 0.0, 3),
            "decisions_breakdown": decisions,
            "intents_breakdown": intents,
            "languages_breakdown": languages,
            "feedback_summary": {"positive": pos_fb, "negative": neg_fb},
            "open_review_queue": open_review,
            "documents_by_status": doc_stats,
        }
    finally:
        conn.close()
