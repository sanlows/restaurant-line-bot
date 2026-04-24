from services.url_parser import extract_urls, parse_urls


def test_extract_urls_deduplicates_and_strips_trailing_punctuation():
    text = "午餐 https://example.com/a, 晚餐 https://example.com/a https://youtu.be/abc）"

    assert extract_urls(text) == ["https://example.com/a", "https://youtu.be/abc"]


def test_parse_urls_keeps_order():
    parsed = parse_urls(
        "推薦 https://www.instagram.com/p/abc 和 https://maps.google.com/?q=test"
    )

    assert [item.url for item in parsed] == [
        "https://www.instagram.com/p/abc",
        "https://maps.google.com/?q=test",
    ]
    assert [item.source for item in parsed] == ["Instagram", "Google Maps"]


def test_extract_urls_returns_empty_list_without_urls():
    assert extract_urls("今天吃什麼？") == []
