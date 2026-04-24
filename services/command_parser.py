from __future__ import annotations

import re
from typing import Any


ID_VALUE_PATTERN = re.compile(r"^#?(\d+)\s+(.+)$")


def parse_command(text: str) -> dict[str, Any]:
    normalized = (text or "").strip()
    if not normalized:
        return {"type": "none"}

    if normalized.lower() == "list":
        return {"type": "list"}

    if normalized == "查 最近":
        return {"type": "list"}

    if normalized.startswith("查 "):
        keyword = normalized[2:].strip()
        if keyword:
            return {"type": "search", "keyword": keyword}

    for prefix, command_type in (
        ("命名 ", "rename"),
        ("分類 ", "set_category"),
        ("地区 ", "set_area"),
        ("地區 ", "set_area"),
    ):
        if normalized.startswith(prefix):
            parsed = _parse_id_value(normalized[len(prefix) :])
            if parsed:
                return {"type": command_type, **parsed}

    return {"type": "none"}


def _parse_id_value(text: str) -> dict[str, str] | None:
    match = ID_VALUE_PATTERN.match(text.strip())
    if not match:
        return None
    return {"id": match.group(1), "value": match.group(2).strip()}
