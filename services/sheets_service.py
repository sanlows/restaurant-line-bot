from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

from config.settings import Settings
from services.id_generator import next_row_id


SHEET_HEADERS = [
    "id",
    "created_at",
    "group_id",
    "room_id",
    "user_id",
    "source",
    "original_url",
    "status",
    "restaurant_name",
    "category",
    "city",
    "district",
    "address",
    "google_maps_url",
    "note",
    "raw_title",
    "raw_description",
    "parse_confidence",
]

DEFAULT_STATUS = "已收藏"
TAIPEI = ZoneInfo("Asia/Taipei")


@dataclass(frozen=True)
class UrlRecord:
    group_id: str
    room_id: str
    user_id: str
    source: str
    original_url: str
    status: str = DEFAULT_STATUS
    restaurant_name: str = ""
    category: str = ""
    city: str = ""
    district: str = ""
    address: str = ""
    google_maps_url: str = ""
    note: str = ""
    raw_title: str = ""
    raw_description: str = ""
    parse_confidence: str = ""


class SheetsService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def append_records(self, records: list[UrlRecord]) -> list[int]:
        if not records:
            return []

        worksheet = self._worksheet()
        self._ensure_headers(worksheet)
        values = worksheet.get_all_values()
        headers = self._headers(values)
        existing_rows = len(values)
        first_id = next_row_id(existing_rows)
        now = datetime.now(TAIPEI).strftime("%Y-%m-%d %H:%M:%S")

        rows = []
        ids = []
        for offset, record in enumerate(records):
            record_id = first_id + offset
            ids.append(record_id)
            record_data = asdict(record)
            row_data = {"id": record_id, "created_at": now, **record_data}
            rows.append(
                [
                    row_data.get(header, "")
                    for header in headers
                ]
            )

        worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        return ids

    def get_recent_records(
        self,
        context_id: str,
        context_type: str,
        limit: int = 5,
    ) -> list[dict[str, str]]:
        records = self._context_records(context_id, context_type)
        return list(reversed(records))[:limit]

    def search_records(
        self,
        keyword: str,
        context_id: str,
        context_type: str,
        limit: int = 5,
    ) -> list[dict[str, str]]:
        keyword = keyword.strip().lower()
        if not keyword:
            return []

        searchable_fields = (
            "restaurant_name",
            "category",
            "city",
            "district",
            "address",
            "note",
            "original_url",
            "source",
            "raw_title",
            "raw_description",
        )
        matches = []
        for record in reversed(self._context_records(context_id, context_type)):
            haystack = " ".join(record.get(field, "") for field in searchable_fields).lower()
            if keyword in haystack:
                matches.append(record)
            if len(matches) >= limit:
                break
        return matches

    def update_record(
        self,
        record_id: str | int,
        updates: dict[str, object],
        context_id: str = "",
        context_type: str = "",
    ) -> bool:
        if not updates:
            return False

        worksheet = self._worksheet()
        self._ensure_headers(worksheet)
        values = worksheet.get_all_values()
        if not values:
            return False

        headers = self._headers(values)
        row_number = self._find_row_number(values, str(record_id), context_id, context_type, headers)
        if not row_number:
            return False

        allowed_updates = {
            key: "" if value is None else str(value)
            for key, value in updates.items()
            if key in headers and key != "id"
        }
        for key, value in allowed_updates.items():
            column_number = headers.index(key) + 1
            worksheet.update_cell(row_number, column_number, value)
        return bool(allowed_updates)

    def _worksheet(self):
        if not self.settings.google_sheet_id:
            raise RuntimeError("GOOGLE_SHEET_ID is required")

        client = self._client()
        spreadsheet = client.open_by_key(self.settings.google_sheet_id)
        return spreadsheet.sheet1

    def _client(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        if self.settings.google_service_account_json:
            service_account_info = json.loads(self.settings.google_service_account_json)
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=scopes,
            )
            return gspread.authorize(credentials)

        if not self.settings.service_account_path.exists():
            raise RuntimeError(
                "Google credentials not found. Set GOOGLE_SERVICE_ACCOUNT_JSON or "
                "GOOGLE_SERVICE_ACCOUNT_JSON_PATH."
            )

        return gspread.service_account(
            filename=str(self.settings.service_account_path),
            scopes=scopes,
        )

    def _ensure_headers(self, worksheet) -> None:
        values = worksheet.get_all_values()
        if not values:
            worksheet.append_row(SHEET_HEADERS, value_input_option="USER_ENTERED")
            return

        existing_headers = values[0]
        if existing_headers[: len(SHEET_HEADERS)] == SHEET_HEADERS:
            return

        merged_headers = existing_headers[:]
        for header in SHEET_HEADERS:
            if header not in merged_headers:
                merged_headers.append(header)
        worksheet.update("A1:R1", [merged_headers])

    def _context_records(self, context_id: str, context_type: str) -> list[dict[str, str]]:
        worksheet = self._worksheet()
        self._ensure_headers(worksheet)
        values = worksheet.get_all_values()
        if len(values) <= 1:
            return []

        headers = self._headers(values)
        return [
            record
            for record in (self._row_to_record(headers, row) for row in values[1:])
            if self._record_matches_context(record, context_id, context_type)
        ]

    def _headers(self, values: list[list[str]]) -> list[str]:
        return values[0] if values else SHEET_HEADERS

    def _row_to_record(self, headers: list[str], row: list[str]) -> dict[str, str]:
        padded_row = row + [""] * (len(headers) - len(row))
        return dict(zip(headers, padded_row))

    def _find_row_number(
        self,
        values: list[list[str]],
        record_id: str,
        context_id: str,
        context_type: str,
        headers: list[str],
    ) -> int | None:
        for offset, row in enumerate(values[1:], start=2):
            record = self._row_to_record(headers, row)
            if record.get("id") != record_id:
                continue
            if context_id and context_type and not self._record_matches_context(
                record,
                context_id,
                context_type,
            ):
                continue
            return offset
        return None

    def _record_matches_context(
        self,
        record: dict[str, str],
        context_id: str,
        context_type: str,
    ) -> bool:
        if context_type == "group":
            return record.get("group_id") == context_id
        if context_type == "room":
            return record.get("room_id") == context_id
        if context_type == "user":
            return record.get("user_id") == context_id
        return False
