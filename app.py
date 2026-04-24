from __future__ import annotations

import logging
from json import JSONDecodeError

from fastapi import FastAPI, Header, HTTPException, Request

from config.settings import get_settings
from services.command_parser import parse_command
from services.line_service import LineService, is_valid_signature
from services.metadata_parser import fetch_metadata
from services.places_service import PlacesService, normalize_place_result
from services.restaurant_extractor import detect_area, extract_restaurant_hint
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
    places_service = PlacesService(settings)
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
        parsed_urls = _collection_urls_from_text(message_text)
        logger.info(
            "message text=%r extracted urls=%s",
            message_text,
            [parsed.url for parsed in parsed_urls],
        )
        if not parsed_urls:
            command = parse_command(message_text)
            if command.get("type") != "none" and reply_token:
                try:
                    line_service.reply_text(
                        reply_token,
                        _handle_command(command, source, sheets_service),
                    )
                except Exception:
                    logger.exception("command handling failure")
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

        results = []
        for record_id, parsed in zip(ids, parsed_urls):
            result = _try_enrich_record(
                record_id,
                parsed.url,
                parsed.source,
                source,
                sheets_service,
                places_service,
            )
            results.append(result)

        if reply_token:
            try:
                line_service.reply_text(reply_token, _collection_message(results))
            except Exception:
                logger.exception("LINE reply failure")

    return {"status": "ok"}


def _success_message(ids: list[int]) -> str:
    if len(ids) == 1:
        return f"已收藏餐廳連結 #{ids[0]}"

    formatted_ids = ", ".join(f"#{record_id}" for record_id in ids)
    return f"已收藏 {len(ids)} 筆餐廳連結：{formatted_ids}"


def _collection_urls_from_text(text: str):
    stripped_text = (text or "").strip()
    if stripped_text == "存" or not stripped_text.startswith("存"):
        return []

    rest = stripped_text[1:]
    if not rest or not rest[0].isspace():
        return []

    return parse_urls(rest)


def _try_enrich_record(
    record_id: int,
    url: str,
    source: str,
    line_source: dict,
    sheets_service: SheetsService,
    places_service: PlacesService,
) -> dict[str, str]:
    context = _context_from_source(line_source)
    metadata = fetch_metadata(url)
    title = str(metadata.get("title") or "")
    description = str(metadata.get("description") or "")
    hint = extract_restaurant_hint(title, description)
    updates: dict[str, object] = {
        "raw_title": title,
        "raw_description": description,
        "parse_confidence": hint.get("confidence", 0),
    }

    place = _find_place(url, source, hint, places_service)
    if place:
        updates.update(place)
        updates["status"] = "已解析"
    elif title or description:
        updates.update(
            {
                "restaurant_name": hint.get("possible_name", ""),
                "category": hint.get("category", ""),
                "city": hint.get("city", ""),
                "district": hint.get("district", ""),
                "status": "待解析",
            }
        )
    else:
        updates["status"] = "待解析"

    sheets_service.update_record(
        record_id,
        updates,
        context_id=context["id"],
        context_type=context["type"],
    )
    return {
        "id": str(record_id),
        "status": str(updates.get("status", "已收藏")),
        "restaurant_name": str(updates.get("restaurant_name", "")),
        "category": str(updates.get("category", "")),
        "city": str(updates.get("city", "")),
        "district": str(updates.get("district", "")),
        "google_maps_url": str(updates.get("google_maps_url", "")),
    }


def _find_place(
    url: str,
    source: str,
    hint: dict[str, object],
    places_service: PlacesService,
) -> dict[str, object]:
    query = str(hint.get("query") or "")
    if source == "Google Maps" and not query:
        query = url
    results = places_service.text_search(query)
    if not results:
        return {}
    normalized = normalize_place_result(results[0])
    detail = places_service.get_place_detail(str(normalized.get("place_id", "")))
    if detail:
        normalized = normalize_place_result({**results[0], **detail})
    return normalized if normalized.get("restaurant_name") else {}


def _handle_command(
    command: dict,
    source: dict,
    sheets_service: SheetsService,
) -> str:
    context = _context_from_source(source)
    command_type = command.get("type")
    if command_type == "list":
        records = sheets_service.get_recent_records(context["id"], context["type"])
        return _recent_records_message(records)
    if command_type == "search":
        keyword = str(command.get("keyword", ""))
        records = sheets_service.search_records(keyword, context["id"], context["type"])
        return _search_records_message(keyword, records)
    if command_type in {"rename", "set_category", "set_area"}:
        return _handle_update_command(command, context, sheets_service)
    return ""


def _handle_update_command(command: dict, context: dict[str, str], sheets_service: SheetsService) -> str:
    record_id = str(command.get("id", ""))
    value = str(command.get("value", "")).strip()
    if command["type"] == "rename":
        updates = {"restaurant_name": value}
        label = "店名"
    elif command["type"] == "set_category":
        updates = {"category": value}
        label = "分類"
    else:
        area = detect_area(value)
        updates = {
            "city": area.get("city", ""),
            "district": area.get("district") or value,
        }
        label = "地區"

    updated = sheets_service.update_record(
        record_id,
        updates,
        context_id=context["id"],
        context_type=context["type"],
    )
    if not updated:
        return f"找不到可更新的 #{record_id}。"
    return f"已更新 #{record_id} {label}：{value}"


def _context_from_source(source: dict) -> dict[str, str]:
    if source.get("type") == "group":
        return {"type": "group", "id": source.get("groupId", "")}
    if source.get("type") == "room":
        return {"type": "room", "id": source.get("roomId", "")}
    return {"type": "user", "id": source.get("userId", "")}


def _collection_message(results: list[dict[str, str]]) -> str:
    ids = [int(result["id"]) for result in results]
    if len(results) == 1:
        result = results[0]
        base = _success_message(ids)
        if result.get("status") == "已解析":
            lines = [
                base,
                "",
                f"店名：{result.get('restaurant_name') or '尚未命名'}",
                f"分類：{result.get('category') or '未分類'}",
                f"地區：{_area_text(result)}",
            ]
            if result.get("google_maps_url"):
                lines.append(f"地圖：{result['google_maps_url']}")
            lines.append("狀態：已解析")
            return "\n".join(lines)
        return (
            f"{base}\n\n"
            "目前無法自動判斷店名，已標記為待解析。\n"
            "可之後輸入：\n"
            f"命名 #{result['id']} 店名\n"
            f"分類 #{result['id']} 類型\n"
            f"地區 #{result['id']} 地區"
        )

    lines = [_success_message(ids), ""]
    for result in results:
        name = result.get("restaurant_name") or "尚未命名"
        lines.append(f"#{result['id']}：{result.get('status', '已收藏')}｜{name}")
    return "\n".join(lines)


def _recent_records_message(records: list[dict[str, str]]) -> str:
    if not records:
        return "目前沒有收藏餐廳。"
    lines = ["最近收藏餐廳", ""]
    for record in records:
        lines.extend(_record_lines(record))
    return "\n".join(lines).strip()


def _search_records_message(keyword: str, records: list[dict[str, str]]) -> str:
    if not records:
        return f"找不到「{keyword}」相關收藏。"
    lines = [f"找到 {len(records)} 筆「{keyword}」相關收藏", ""]
    for record in records:
        lines.extend(_record_lines(record))
    return "\n".join(lines).strip()


def _record_lines(record: dict[str, str]) -> list[str]:
    name = record.get("restaurant_name") or "尚未命名"
    category_or_status = record.get("category") or record.get("source") or record.get("status", "")
    area_or_status = _area_text(record) or record.get("status", "")
    return [
        f"#{record.get('id')}｜{name}",
        f"{category_or_status}｜{area_or_status}",
        record.get("google_maps_url") or record.get("original_url", ""),
        "",
    ]


def _area_text(record: dict[str, str]) -> str:
    return "".join(part for part in (record.get("city", ""), record.get("district", "")) if part)
