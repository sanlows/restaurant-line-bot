from fastapi.testclient import TestClient

import app as app_module
from app import _all_records_message, _collection_urls_from_text, _success_message


client = TestClient(app_module.app)


def test_success_message_for_single_url():
    assert _success_message([12]) == "已收藏餐廳連結 #12"


def test_success_message_for_multiple_urls():
    assert _success_message([12, 13, 14]) == "已收藏 3 筆餐廳連結：#12, #13, #14"


def test_collection_urls_require_save_prefix():
    assert _collection_urls_from_text("https://example.com/a") == []
    assert _collection_urls_from_text("這間不錯 https://example.com/a") == []


def test_collection_urls_parse_after_save_prefix():
    parsed_urls = _collection_urls_from_text("存 https://example.com/a")

    assert [parsed.url for parsed in parsed_urls] == ["https://example.com/a"]


def test_all_records_message_includes_requested_fields_only():
    message = _all_records_message(
        [
            {
                "original_url": "https://example.com/a",
                "restaurant_name": "測試餐廳",
                "category": "咖啡",
                "note": "靠窗",
                "google_maps_url": "https://maps.example.com/a",
            }
        ]
    )

    assert message == (
        "全部收藏餐廳\n\n"
        "original_url：https://example.com/a\n"
        "restaurant_name：測試餐廳\n"
        "category：咖啡\n"
        "note：靠窗"
    )


def test_callback_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(app_module, "is_valid_signature", lambda *_: False)

    response = client.post(
        "/callback",
        json={"events": []},
        headers={"X-Line-Signature": "bad-signature"},
    )

    assert response.status_code == 400


def test_callback_ignores_text_without_urls(monkeypatch):
    class FakeLineService:
        def __init__(self, settings):
            self.settings = settings

        def reply_text(self, reply_token, text):
            raise AssertionError("Text without URLs should not be replied to")

    class FakeSheetsService:
        def __init__(self, settings):
            self.settings = settings

        def append_records(self, records):
            raise AssertionError("Text without URLs should not be written to Sheets")

    monkeypatch.setattr(app_module, "is_valid_signature", lambda *_: True)
    monkeypatch.setattr(app_module, "LineService", FakeLineService)
    monkeypatch.setattr(app_module, "SheetsService", FakeSheetsService)

    response = client.post(
        "/callback",
        json={
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"type": "group", "groupId": "group-id", "userId": "user-id"},
                    "message": {"type": "text", "text": "今天想吃什麼"},
                }
            ]
        },
        headers={"X-Line-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_callback_ignores_plain_urls_without_save_prefix(monkeypatch):
    class FakeLineService:
        def __init__(self, settings):
            self.settings = settings

        def reply_text(self, reply_token, text):
            raise AssertionError("Plain URLs without the save prefix should not be replied to")

    class FakeSheetsService:
        def __init__(self, settings):
            self.settings = settings

        def append_records(self, records):
            raise AssertionError("Plain URLs without the save prefix should not be saved")

    monkeypatch.setattr(app_module, "is_valid_signature", lambda *_: True)
    monkeypatch.setattr(app_module, "LineService", FakeLineService)
    monkeypatch.setattr(app_module, "SheetsService", FakeSheetsService)

    response = client.post(
        "/callback",
        json={
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"type": "group", "groupId": "group-id", "userId": "user-id"},
                    "message": {"type": "text", "text": "https://example.com/a"},
                }
            ]
        },
        headers={"X-Line-Signature": "valid-signature"},
    )

    assert response.status_code == 200
