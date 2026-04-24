from types import SimpleNamespace

from services.places_service import PlacesService, normalize_place_result


def test_places_without_api_key_does_not_crash():
    service = PlacesService(SimpleNamespace(google_places_api_key=""))

    assert service.text_search("阿城鵝肉") == []
    assert service.get_place_detail("place-id") == {}


def test_normalize_place_result():
    normalized = normalize_place_result(
        {
            "name": "阿城鵝肉",
            "formatted_address": "台北市中山區吉林路",
            "url": "https://maps.google.com/example",
            "types": ["restaurant"],
            "place_id": "abc",
        }
    )

    assert normalized["restaurant_name"] == "阿城鵝肉"
    assert normalized["category"] == "餐廳"
    assert normalized["city"] == "台北市"
    assert normalized["district"] == "中山區"
    assert normalized["confidence"] == 0.8
