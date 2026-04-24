from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request

from config.settings import get_settings
from services.line_service import LineService, is_valid_signature
from services.sheets_service import SheetsService, UrlRecord
from services.url_parser import parse_urls


app = FastAPI(title="restaurant-line-bot")


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "restaurant-line-bot"}


@app.post("/callback")
async def callback(
    request: Request,
    x_line_signature: str = Header(default="", alias="X-Line-Signature"),
) -> dict[str, str]:
    settings = get_settings()
    body = await request.body()

    if not is_valid_signature(settings.line_channel_secret, body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid LINE signature")

    payload = await request.json()
    line_service = LineService(settings)
    sheets_service = SheetsService(settings)

    for event in payload.get("events", []):
        if event.get("type") != "message":
            continue
        message = event.get("message", {})
        if message.get("type") != "text":
            continue

        reply_token = event.get("replyToken", "")
        parsed_urls = parse_urls(message.get("text", ""))
        if not parsed_urls:
            if reply_token:
                line_service.reply_text(reply_token, "請傳送餐廳貼文或地圖網址，我會幫你記錄。")
            continue

        source = event.get("source", {})
        records = [
            UrlRecord(
                group_id=source.get("groupId", ""),
                room_id=source.get("roomId", ""),
                user_id=source.get("userId", ""),
                source=parsed.source,
                original_url=parsed.url,
            )
            for parsed in parsed_urls
        ]
        ids = sheets_service.append_records(records)

        if reply_token:
            line_service.reply_text(reply_token, _success_message(ids))

    return {"status": "ok"}


def _success_message(ids: list[int]) -> str:
    if len(ids) == 1:
        return f"已收到並記錄 #{ids[0]}"

    formatted_ids = ", ".join(f"#{record_id}" for record_id in ids)
    return f"已收到 {len(ids)} 筆並記錄：{formatted_ids}"
