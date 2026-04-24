import pytest

from services.url_parser import detect_source


@pytest.mark.parametrize(
    ("url", "source"),
    [
        ("https://facebook.com/share/r/abc", "Facebook"),
        ("https://www.facebook.com/share/r/abc", "Facebook"),
        ("https://fb.watch/abc", "Facebook"),
        ("https://fb.com/abc", "Facebook"),
        ("https://instagram.com/p/abc", "Instagram"),
        ("https://www.youtube.com/watch?v=abc", "YouTube"),
        ("https://youtu.be/abc", "YouTube"),
        ("https://maps.google.com/?q=restaurant", "Google Maps"),
        ("https://www.google.com/maps/place/test", "Google Maps"),
        ("https://goo.gl/maps/abc", "Google Maps"),
        ("https://example.com/post", "Other"),
    ],
)
def test_detect_source(url, source):
    assert detect_source(url) == source
