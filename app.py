from __future__ import annotations

import logging
from json import JSONDecodeError

from fastapi import FastAPI, Header, HTTPException, Request

from config.settings import get_settings
from services.line_service import LineService, is_valid_signature
from services.sheets_service import SheetsService, UrlRecord
from services.url_parser import parse_urls


app = FastAPI(title="restaurant-line-bot")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("restaurant-line-bot")


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
    logger.info("callback received body_length=%s", len(body))

    if not is_valid_signature(settings.line_channel_secret, body, x_line_signature):
        logger.warning("signature invalid body_length=%s", len(body))
        raise HTTPException(status_code=400, detail="Invalid LINE signature")

    logger.info("signature valid")

    try:
        payload = await request.json()
    except JSONDecodeError:
        logger.exception("callback json parse failure")
        return {"status": "ok"}

    line_service = LineService(settings)
    sheets_service = SheetsService(settings)
    events = payload.get("events", [])
    logger.info("number of events=%s", len(events))

    for event in events:
        event_type = event.get("type", "")
        source = event.get("source", {})
        source_type = source.get("type", "")
        logger.info("event type=%s source type=%s", event_type, source_type)

        if event.get("type") != "message":
            continue
        message = event.get("message", {})
        if message.get("type") != "text":
            continue

        reply_token = event.get("replyToken", "")
        message_text = message.get("text", "")
        parsed_urls = parse_urls(message_text)
        logger.info(
            "message text=%r extracted urls=%s",
            message_text,
            [parsed.url for parsed in parsed_urls],
        )
        if not parsed_urls:
            continue

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
        try:
            ids = sheets_service.append_records(records)
            logger.info("Google Sheets write success ids=%s", ids)
        except Exception:
            logger.exception("Google Sheets write failure")
            continue

        if reply_token:
            try:
                line_service.reply_text(reply_token, _success_message(ids))
            except Exception:
                logger.exception("LINE reply failure")

    return {"status": "ok"}


def _success_message(ids: list[int]) -> str:
    if len(ids) == 1:
        return f"已收藏餐廳連結 #{ids[0]}"

    formatted_ids = ", ".join(f"#{record_id}" for record_id in ids)
    return f"已收藏 {len(ids)} 筆餐廳連結：{formatted_ids}"
