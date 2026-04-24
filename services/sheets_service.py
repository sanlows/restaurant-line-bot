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
    "address",
    "google_maps_url",
    "note",
]

DEFAULT_STATUS = "received"
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
    address: str = ""
    google_maps_url: str = ""
    note: str = ""


class SheetsService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def append_records(self, records: list[UrlRecord]) -> list[int]:
        if not records:
            return []

        worksheet = self._worksheet()
        self._ensure_headers(worksheet)
        existing_rows = len(worksheet.get_all_values())
        first_id = next_row_id(existing_rows)
        now = datetime.now(TAIPEI).strftime("%Y-%m-%d %H:%M:%S")

        rows = []
        ids = []
        for offset, record in enumerate(records):
            record_id = first_id + offset
            ids.append(record_id)
            record_data = asdict(record)
            rows.append(
                [
                    record_id,
                    now,
                    record_data["group_id"],
                    record_data["room_id"],
                    record_data["user_id"],
                    record_data["source"],
                    record_data["original_url"],
                    record_data["status"],
                    record_data["restaurant_name"],
                    record_data["address"],
                    record_data["google_maps_url"],
                    record_data["note"],
                ]
            )

        worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        return ids

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

        if values[0][: len(SHEET_HEADERS)] != SHEET_HEADERS:
            worksheet.update("A1:L1", [SHEET_HEADERS])
