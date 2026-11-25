"""
Mandi Price Service (Module 8).
Integrates with the Government of India Agmarknet API (data.gov.in).
Features:
- Multilingual commodity translation (Marathi / Hindi -> Agmarknet English)
- TTL caching & rate limiting
- Clear distinction between live data, no records, and unconfigured credentials
- Never fabricates or stores live prices as static knowledge-base data
"""

from __future__ import annotations

import os
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from backend.config import settings

logger = logging.getLogger(__name__)

COMMODITY_TRANSLATION: Dict[str, str] = {
    "गेहू": "Wheat", "गहू": "Wheat", "गेहूं": "Wheat", "गेहूँ": "Wheat", "wheat": "Wheat",
    "तांदूळ": "Rice", "तंदूल": "Rice", "चावल": "Rice", "भात": "Paddy(Dhan)(Common)", "rice": "Rice",
    "चना": "Bengal Gram(Gram)(Whole)", "हरभरा": "Bengal Gram(Gram)(Whole)", "gram": "Bengal Gram(Gram)(Whole)",
    "सोयाबीन": "Soyabean", "soybean": "Soyabean", "soyabean": "Soyabean",
    "कांदा": "Onion", "प्याज": "Onion", "onion": "Onion",
    "बटाटा": "Potato", "आलू": "Potato", "potato": "Potato",
    "टोमॅटो": "Tomato", "टमाटर": "Tomato", "tomato": "Tomato",
    "कापूस": "Cotton", "कपास": "Cotton", "cotton": "Cotton",
    "मका": "Maize", "मक्का": "Maize", "maize": "Maize",
    "ज्वारी": "Jowar(Sorghum)", "ज्वार": "Jowar(Sorghum)", "jowar": "Jowar(Sorghum)",
    "बाजरी": "Bajra(Pearl Millet/Cumbu)", "बाजरा": "Bajra(Pearl Millet/Cumbu)", "bajra": "Bajra(Pearl Millet/Cumbu)",
    "ऊस": "Sugarcane", "उस": "Sugarcane", "गन्ना": "Sugarcane", "sugarcane": "Sugarcane",
    "तूर": "Arhar (Tur/Red Gram)(Whole)", "अरहर": "Arhar (Tur/Red Gram)(Whole)", "tur": "Arhar (Tur/Red Gram)(Whole)",
    "हळद": "Turmeric", "हल्दी": "Turmeric", "turmeric": "Turmeric",
}

AGMARKNET_API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

MandiResult = Dict[str, Any]


class MandiService:
    """Fetches live APMC mandi prices from Agmarknet (data.gov.in)."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("AGMARKNET_API_KEY", settings.AGMARKNET_API_KEY)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_ts: float = 0.0

    def get_prices(
        self,
        commodity: str,
        market: Optional[str] = None,
        state: str = "Maharashtra",
    ) -> MandiResult:
        english_commodity = self._translate_commodity(commodity)
        cache_key = f"{english_commodity.lower()}_{(market or '').lower()}_{state.lower()}"

        # Check fresh TTL cache
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached["stored_at"] < settings.MANDI_CACHE_TTL_SECONDS):
            out = dict(cached["data"])
            out["cached"] = True
            return out

        if not self.api_key:
            logger.warning("AGMARKNET_API_KEY not configured; returning credentials_required status.")
            return {
                "success": False,
                "is_live": False,
                "cached": False,
                "data_status": "credentials_required",
                "commodity": english_commodity,
                "market": market or "Any",
                "state": state,
                "source": "Agmarknet / data.gov.in",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": (
                    "Live mandi API unavailable — configure AGMARKNET_API_KEY in .env "
                    "(free registration at https://data.gov.in). "
                    "Alternatively check https://agmarknet.gov.in or e-NAM portal directly."
                ),
            }

        # Rate limiting
        elapsed = time.time() - self._last_request_ts
        if elapsed < 0.2:
            time.sleep(0.2 - elapsed)
        self._last_request_ts = time.time()

        try:
            result = self._fetch_from_agmarknet(english_commodity, market, state)
            if result.get("success"):
                self._cache[cache_key] = {"stored_at": time.time(), "data": result}
            return result
        except requests.RequestException as exc:
            logger.error(f"Agmarknet API request failed: {exc}")
            return {
                "success": False,
                "is_live": False,
                "cached": False,
                "data_status": "error",
                "commodity": english_commodity,
                "market": market or "Any",
                "state": state,
                "source": "Agmarknet / data.gov.in",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Network error while fetching live mandi prices: {exc}",
            }

    def _translate_commodity(self, commodity: str) -> str:
        stripped = (commodity or "Wheat").strip()
        return COMMODITY_TRANSLATION.get(stripped, COMMODITY_TRANSLATION.get(stripped.lower(), stripped))

    def _fetch_from_agmarknet(
        self,
        commodity: str,
        market: Optional[str],
        state: str,
    ) -> MandiResult:
        params: Dict[str, Any] = {
            "api-key": self.api_key,
            "format": "json",
            "filters[commodity]": commodity,
            "filters[state]": state,
            "limit": 15,
            "offset": 0,
        }
        if market:
            params["filters[market]"] = market

        response = requests.get(AGMARKNET_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])

        # Retry without market filter if market filter yielded nothing
        if not records and market:
            params.pop("filters[market]", None)
            response = requests.get(AGMARKNET_API_URL, params=params, timeout=10)
            response.raise_for_status()
            records = response.json().get("records", [])

        if not records:
            return {
                "success": False,
                "is_live": True,
                "cached": False,
                "data_status": "no_records",
                "commodity": commodity,
                "market": market or "Any",
                "state": state,
                "source": "Agmarknet / data.gov.in",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"No live mandi arrivals reported today for '{commodity}' in {state}.",
            }

        def _float(val: Any) -> float:
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0.0

        parsed_records: List[Dict[str, Any]] = []
        for r in records:
            parsed_records.append({
                "market": r.get("market", market or "APMC"),
                "state": r.get("state", state),
                "district": r.get("district", state),
                "commodity": r.get("commodity", commodity),
                "variety": r.get("variety"),
                "min_price": _float(r.get("min_price")),
                "max_price": _float(r.get("max_price")),
                "modal_price": _float(r.get("modal_price")),
                "unit": "Quintal",
                "date": r.get("arrival_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            })

        first = parsed_records[0]
        return {
            "success": True,
            "is_live": True,
            "cached": False,
            "data_status": "live",
            "commodity": first["commodity"],
            "market": first["market"],
            "state": first["state"],
            "district": first["district"],
            "min_price": first["min_price"],
            "max_price": first["max_price"],
            "modal_price": first["modal_price"],
            "unit": "Quintal",
            "date": first["date"],
            "records": parsed_records,
            "source": "Agmarknet / data.gov.in",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
