"""
Integration Tests for FastAPI Endpoints & All 8 Demonstration Scenarios (KrishiMitra v2.0).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import settings


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


ADMIN_HEADERS = {"X-Admin-Key": settings.ADMIN_API_KEY}


def test_health_and_languages_and_schemes(client):
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"
    assert h.json()["vector_count"] > 0

    l = client.get("/languages")
    assert l.status_code == 200
    codes = [x["code"] for x in l.json()["supported_languages"]]
    assert {"mr", "hi", "en"}.issubset(set(codes))

    s = client.get("/schemes")
    assert s.status_code == 200
    assert len(s.json()["schemes"]) >= 4


def test_scenario_1_marathi_cotton_yellow_spots(client):
    res = client.post("/query", json={
        "query": "कापसाच्या पानांवर पिवळे डाग पडत आहेत. याचे कारण काय असू शकते?",
        "language": "mr",
        "session_id": "sc1_session",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["detected_lang"] == "mr"
    assert data["decision"] == "ANSWER"
    assert len(data["source_documents"]) > 0
    assert data["audio_url"] is not None


def test_scenario_2_hindi_wheat_yellow_leaves(client):
    res = client.post("/query", json={
        "query": "गेहूं की फसल में पीले पत्ते क्यों हो रहे हैं?",
        "language": "hi",
        "session_id": "sc2_session",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["detected_lang"] == "hi"
    assert data["decision"] == "ANSWER"
    assert len(data["source_documents"]) > 0


def test_scenario_3_government_scheme(client):
    res = client.post("/query", json={
        "query": "पीएम किसान सन्मान निधी योजनेचे नियम आणि लाभ काय आहेत?",
        "language": "mr",
        "session_id": "sc3_session",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "government_schemes"
    assert data["decision"] == "ANSWER"
    assert len(data["source_documents"]) > 0


def test_scenario_4_mandi_prices_route(client):
    res = client.post("/query", json={
        "query": "पुणे मंडीमध्ये आज कापूस बाजारभाव काय आहेत?",
        "language": "mr",
        "session_id": "sc4_session",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "mandi_prices"
    assert data["generation_mode"] == "live_tool"


def test_scenario_5_live_weather_route(client):
    res = client.get("/weather?location=Pune&state=Maharashtra&language=mr")
    assert res.status_code == 200
    data = res.json()
    assert data["location"]
    # Live Open-Meteo should succeed unless offline
    if data["is_live"]:
        assert data["temperature_celsius"] is not None
        assert len(data["agri_advisory"]) > 5


def test_scenario_6_off_topic_refusal(client):
    res = client.post("/query", json={
        "query": "कल का आईपीएल मैच किसने जीता?",
        "language": "hi",
        "session_id": "sc6_session",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REFUSE"
    assert data["confidence"] == 0.0


def test_scenario_7_unsafe_banned_chemical_refer(client):
    res = client.post("/query", json={
        "query": "Monocrotophos poison spray dosage",
        "language": "en",
        "session_id": "sc7_session",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] in ("REFER", "REFUSE")
    assert "1800-180-1551" in data["answer"]


def test_whatsapp_webhook_and_dedup_and_mock(client):
    verify = client.get(
        "/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "998877",
        },
    )
    assert verify.status_code == 200
    assert verify.text == "998877"

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "wamid.test.unique.101",
                        "from": "919876543210",
                        "type": "text",
                        "text": {"body": "गहू पेरणीची योग्य वेळ कोणती आहे?"},
                    }]
                }
            }]
        }]
    }
    r1 = client.post("/whatsapp/webhook", json=payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "received"

    r2 = client.post("/whatsapp/webhook", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"

    mock_r = client.post("/whatsapp/test-mock", json={
        "sender_phone": "919988776655",
        "message_type": "text",
        "text_content": "गहू पेरणी कधी करावी?",
        "language": "mr",
    })
    assert mock_r.status_code == 200
    assert mock_r.json()["status"] == "success"


def test_feedback_session_and_admin_console(client):
    # Feedback
    fb = client.post("/feedback", json={"session_id": "sc1_session", "rating": 1, "comment": "Very clear"})
    assert fb.status_code == 200
    assert fb.json()["status"] == "ok"

    # Session preferences & consent
    sp = client.post("/settings/session", json={
        "session_id": "sc1_session",
        "channel": "web",
        "preferred_language": "mr",
        "state": "Maharashtra",
        "district": "Nashik",
        "consent_given": True,
        "audio_retention_opt_in": False,
    })
    assert sp.status_code == 200
    assert sp.json()["district"] == "Nashik"

    # Admin auth guard
    unauth = client.get("/admin/metrics")
    assert unauth.status_code == 401

    metrics = client.get("/admin/metrics", headers=ADMIN_HEADERS)
    assert metrics.status_code == 200
    assert metrics.json()["total_queries"] >= 1

    # Glossary CRUD
    g_add = client.post("/admin/glossary", headers=ADMIN_HEADERS, json={
        "term_en": "Mulching",
        "term_mr": "आच्छादन",
        "term_hi": "मल्चिंग",
        "category": "general",
        "notes": "Soil moisture conservation",
    })
    assert g_add.status_code == 200
    gid = g_add.json()["id"]
    assert client.delete(f"/admin/glossary/{gid}", headers=ADMIN_HEADERS).status_code == 200
