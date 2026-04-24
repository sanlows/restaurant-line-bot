from services.command_parser import parse_command


def test_parse_list_commands():
    assert parse_command("list") == {"type": "list"}
    assert parse_command("List") == {"type": "list"}
    assert parse_command("LIST") == {"type": "list"}
    assert parse_command("查 最近") == {"type": "list"}


def test_parse_search_commands():
    assert parse_command("查 板橋") == {"type": "search", "keyword": "板橋"}
    assert parse_command("查 燒肉") == {"type": "search", "keyword": "燒肉"}


def test_parse_manual_update_commands():
    assert parse_command("命名 #3 阿城鵝肉") == {
        "type": "rename",
        "id": "3",
        "value": "阿城鵝肉",
    }
    assert parse_command("分類 #3 台式小吃") == {
        "type": "set_category",
        "id": "3",
        "value": "台式小吃",
    }
    assert parse_command("地區 #3 板橋") == {
        "type": "set_area",
        "id": "3",
        "value": "板橋",
    }


def test_parse_plain_chat_as_none():
    assert parse_command("今天想吃什麼") == {"type": "none"}
