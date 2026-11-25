"""
Tests for Live Mandi & Weather Services (Module 8) and Translation Glossary (Module 4).
"""

from backend.services.mandi_service import MandiService
from backend.services.weather_service import WeatherService
from backend.services.translation import translate, get_glossary_hints
from backend.database.db import init_db


def test_mandi_credentials_gate_and_translation():
    ms = MandiService()
    ms.api_key = ""
    res = ms.get_prices("कापूस", market="Pune", state="Maharashtra")
    assert res["success"] is False
    assert res["is_live"] is False
    assert res["data_status"] == "credentials_required"
    assert res["commodity"] == "Cotton"


def test_weather_live_open_meteo_and_cache():
    ws = WeatherService()
    ws.api_key = ""
    res = ws.get_weather("Pune", state="Maharashtra", language="mr")
    if res["success"]:
        assert res["is_live"] is True
        assert res["cached"] is False
        assert res["temperature"] is not None
        assert len(res["advisory"]) > 5

        # Second immediate call should come from TTL cache
        res2 = ws.get_weather("Pune", state="Maharashtra", language="mr")
        assert res2["cached"] is True


def test_glossary_preservation():
    init_db()
    hints = get_glossary_hints("Wheat crop aphids control under PMFBY", target_lang="mr")
    en_terms = [h["en"] for h in hints]
    assert any("Wheat" in t for t in en_terms)
    assert any("Aphids" in t for t in en_terms)

    tr = translate("गहू आणि कापूस", "mr", "mr")
    assert tr["success"] is True
    assert len(tr["glossary_matches"]) >= 1
