from types import SimpleNamespace

from services.sheets_service import SheetsService


class FakeWorksheet:
    def __init__(self, values):
        self.values = values
        self.updated_cells = []

    def get_all_values(self):
        return self.values

    def update(self, range_name, values):
        self.values[0] = values[0]

    def update_cell(self, row, col, value):
        self.updated_cells.append((row, col, value))
        while len(self.values[row - 1]) < col:
            self.values[row - 1].append("")
        self.values[row - 1][col - 1] = value


class FakeSheetsService(SheetsService):
    def __init__(self, worksheet):
        self.worksheet = worksheet
        super().__init__(SimpleNamespace())

    def _worksheet(self):
        return self.worksheet


HEADERS = [
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


def row(record_id, group_id, name, category="", district="", url="https://example.com"):
    return [
        str(record_id),
        "2026-04-24 12:00:00",
        group_id,
        "",
        "user",
        "Instagram",
        url,
        "待解析",
        name,
        category,
        "新北市" if district else "",
        district,
        "",
        "",
        "",
        name,
        category,
        "0.4",
    ]


def test_get_recent_records_filters_group_and_limits_to_five():
    worksheet = FakeWorksheet(
        [HEADERS]
        + [row(index, "group-a", f"餐廳{index}") for index in range(1, 8)]
        + [row(8, "group-b", "別群餐廳")]
    )
    service = FakeSheetsService(worksheet)

    records = service.get_recent_records("group-a", "group", limit=5)

    assert [record["id"] for record in records] == ["7", "6", "5", "4", "3"]
    assert all(record["group_id"] == "group-a" for record in records)


def test_search_records_filters_group_and_keyword():
    worksheet = FakeWorksheet(
        [
            HEADERS,
            row(1, "group-a", "板橋牛肉麵", "牛肉麵", "板橋區"),
            row(2, "group-b", "板橋燒肉", "燒肉", "板橋區"),
            row(3, "group-a", "", "火鍋", "中山區"),
        ]
    )
    service = FakeSheetsService(worksheet)

    records = service.search_records("板橋", "group-a", "group")

    assert [record["id"] for record in records] == ["1"]


def test_update_record_respects_context():
    worksheet = FakeWorksheet(
        [
            HEADERS,
            row(1, "group-a", ""),
            row(1, "group-b", ""),
        ]
    )
    service = FakeSheetsService(worksheet)

    assert service.update_record("1", {"restaurant_name": "阿城鵝肉"}, "group-b", "group")

    assert worksheet.values[2][8] == "阿城鵝肉"
    assert worksheet.values[1][8] == ""
