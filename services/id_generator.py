def next_row_id(existing_row_count: int) -> int:
    """Return the next logical id, assuming row 1 is the header."""
    return max(existing_row_count, 1)
