from __future__ import annotations


AREA_KEYWORDS = {
    "板橋": ("新北市", "板橋區"),
    "新莊": ("新北市", "新莊區"),
    "中和": ("新北市", "中和區"),
    "永和": ("新北市", "永和區"),
    "三重": ("新北市", "三重區"),
    "蘆洲": ("新北市", "蘆洲區"),
    "信義": ("台北市", "信義區"),
    "松山": ("台北市", "松山區"),
    "中山": ("台北市", "中山區"),
    "大安": ("台北市", "大安區"),
    "士林": ("台北市", "士林區"),
    "台北": ("台北市", ""),
    "新北": ("新北市", ""),
    "桃園": ("桃園市", ""),
    "新竹": ("新竹市", ""),
    "台中": ("台中市", ""),
    "台南": ("台南市", ""),
    "高雄": ("高雄市", ""),
}

CATEGORY_KEYWORDS = [
    "燒肉",
    "火鍋",
    "牛肉麵",
    "拉麵",
    "咖啡",
    "甜點",
    "早午餐",
    "居酒屋",
    "韓式",
    "日式",
    "義大利麵",
    "小吃",
    "便當",
    "Buffet",
    "吃到飽",
    "漢堡",
    "披薩",
    "壽司",
    "鐵板燒",
    "牛排",
]


def extract_restaurant_hint(raw_title: str, raw_description: str) -> dict[str, object]:
    text = " ".join(part for part in (raw_title, raw_description) if part).strip()
    area = detect_area(text)
    category = detect_category(text)
    possible_name = _possible_name(raw_title)
    query_parts = [part for part in (possible_name, area.get("district"), category) if part]
    confidence = 0.0
    if possible_name:
        confidence += 0.25
    if area.get("city") or area.get("district"):
        confidence += 0.15
    if category:
        confidence += 0.15

    return {
        "possible_name": possible_name,
        "city": area.get("city", ""),
        "district": area.get("district", ""),
        "category": category or "",
        "query": " ".join(query_parts),
        "confidence": round(confidence, 2),
    }


def detect_area(text: str) -> dict[str, str]:
    for keyword, (city, district) in AREA_KEYWORDS.items():
        if keyword in (text or ""):
            return {"city": city, "district": district}
    return {"city": "", "district": ""}


def detect_category(text: str) -> str | None:
    lower_text = (text or "").lower()
    for keyword in CATEGORY_KEYWORDS:
        if keyword.lower() in lower_text:
            return keyword
    return None


def _possible_name(title: str) -> str:
    title = (title or "").strip()
    if not title:
        return ""
    for separator in ("｜", "|", "-", "－", "–", "—"):
        if separator in title:
            title = title.split(separator, 1)[0].strip()
            break
    return title[:40]
