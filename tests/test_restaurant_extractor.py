from services.restaurant_extractor import detect_area, detect_category, extract_restaurant_hint


def test_detect_area():
    assert detect_area("板橋新開的燒肉") == {"city": "新北市", "district": "板橋區"}


def test_detect_category():
    assert detect_category("台北火鍋推薦") == "火鍋"


def test_extract_restaurant_hint_low_confidence_without_signals():
    hint = extract_restaurant_hint("", "")

    assert hint["possible_name"] == ""
    assert hint["category"] == ""
    assert hint["confidence"] == 0.0


def test_extract_restaurant_hint_builds_query():
    hint = extract_restaurant_hint("阿城鵝肉｜台北中山小吃", "")

    assert hint["possible_name"] == "阿城鵝肉"
    assert hint["city"] == "台北市"
    assert hint["district"] == "中山區"
    assert hint["category"] == "小吃"
    assert "阿城鵝肉" in hint["query"]
