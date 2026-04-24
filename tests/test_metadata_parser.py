from types import SimpleNamespace

import httpx

from services import metadata_parser


class FakeResponse:
    text = """
    <html>
      <head>
        <meta property="og:title" content="阿城鵝肉">
        <meta property="og:description" content="台北中山小吃">
      </head>
    </html>
    """

    def raise_for_status(self):
        return None


def test_fetch_metadata_parses_title_and_description(monkeypatch):
    monkeypatch.setattr(metadata_parser.httpx, "get", lambda *args, **kwargs: FakeResponse())

    metadata = metadata_parser.fetch_metadata("https://example.com")

    assert metadata == {"title": "阿城鵝肉", "description": "台北中山小吃", "error": None}


def test_fetch_metadata_timeout_does_not_crash(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(metadata_parser.httpx, "get", raise_timeout)

    metadata = metadata_parser.fetch_metadata("https://example.com")

    assert metadata["title"] == ""
    assert metadata["description"] == ""
    assert "timeout" in metadata["error"]


def test_fetch_metadata_without_metadata_does_not_crash(monkeypatch):
    response = SimpleNamespace(text="<html><head></head><body></body></html>", raise_for_status=lambda: None)
    monkeypatch.setattr(metadata_parser.httpx, "get", lambda *args, **kwargs: response)

    metadata = metadata_parser.fetch_metadata("https://example.com")

    assert metadata == {"title": "", "description": "", "error": None}
