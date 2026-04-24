from services.id_generator import next_row_id


def test_next_row_id_starts_at_one_for_empty_or_header_only_sheet():
    assert next_row_id(0) == 1
    assert next_row_id(1) == 1


def test_next_row_id_uses_existing_data_count_after_header():
    assert next_row_id(12) == 12
