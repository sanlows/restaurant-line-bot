from __future__ import annotations

import logging

import httpx

from config.settings import Settings


logger = logging.getLogger("restaurant-line-bot")
PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"


class PlacesService:
    def __init__(self, settings: Settings):
        self.api_key = settings.google_places_api_key.strip()

    def text_search(self, query: str) -> list[dict]:
        if not self.api_key or not query.strip():
            return []
        try:
            response = httpx.get(
                PLACES_TEXT_SEARCH_URL,
                params={"query": query, "key": self.api_key, "language": "zh-TW"},
                timeout=5,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            logger.exception("Places text search failure")
            return []
        if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
            logger.warning("Places text search returned status=%s", payload.get("status"))
        return payload.get("results", []) or []

    def get_place_detail(self, place_id: str) -> dict:
        if not self.api_key or not place_id:
            return {}
        try:
            response = httpx.get(
                PLACES_DETAIL_URL,
                params={
                    "place_id": place_id,
                    "key": self.api_key,
                    "language": "zh-TW",
                    "fields": "name,formatted_address,url,types,place_id",
                },
                timeout=5,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            logger.exception("Places detail failure")
            return {}
        return payload.get("result", {}) or {}


def normalize_place_result(result: dict) -> dict[str, object]:
    name = result.get("name", "")
    address = result.get("formatted_address", "")
    types = result.get("types", []) or []
    return {
        "restaurant_name": name,
        "category": _category_from_types(types),
        "city": _detect_city(address),
        "district": _detect_district(address),
        "address": address,
        "google_maps_url": result.get("url", ""),
        "place_id": result.get("place_id", ""),
        "confidence": 0.8 if name else 0.0,
    }


def _category_from_types(types: list[str]) -> str:
    if "restaurant" in types:
        return "餐廳"
    if "cafe" in types:
        return "咖啡"
    if "bakery" in types:
        return "甜點"
    return ""


def _detect_city(address: str) -> str:
    for city in ("台北市", "新北市", "桃園市", "新竹市", "台中市", "台南市", "高雄市"):
        if city in address:
            return city
    return ""


def _detect_district(address: str) -> str:
    marker = "區"
    if marker not in address:
        return ""
    before = address.split(marker, 1)[0]
    district = before[-2:] + marker
    return district if len(district) >= 3 else ""
