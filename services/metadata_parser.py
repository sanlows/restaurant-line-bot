from __future__ import annotations

from html.parser import HTMLParser

import httpx


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def fetch_metadata(url: str, timeout: int = 5) -> dict[str, str | None]:
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=timeout,
        )
        response.raise_for_status()
    except Exception as exc:
        return {"title": "", "description": "", "error": str(exc)}

    parser = _MetadataHtmlParser()
    try:
        parser.feed(response.text)
    except Exception as exc:
        return {"title": "", "description": "", "error": str(exc)}

    return {
        "title": parser.title(),
        "description": parser.description(),
        "error": None,
    }


class _MetadataHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.page_title = ""
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self._in_title = True
            return
        if tag.lower() != "meta":
            return

        key = attrs_dict.get("property") or attrs_dict.get("name")
        content = attrs_dict.get("content", "")
        if key and content:
            self.meta[key.lower()] = content.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
            self.page_title = " ".join(self._title_parts).strip()

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data.strip())

    def title(self) -> str:
        return (
            self.meta.get("og:title")
            or self.meta.get("twitter:title")
            or self.page_title
            or ""
        )

    def description(self) -> str:
        return (
            self.meta.get("og:description")
            or self.meta.get("twitter:description")
            or self.meta.get("description")
            or ""
        )
