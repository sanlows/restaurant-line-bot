from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse


URL_PATTERN = re.compile(r"https?://[^\s<>()\"']+", re.IGNORECASE)
TRAILING_PUNCTUATION = ".,;:!?)]}、。，！？）】"


@dataclass(frozen=True)
class ParsedUrl:
    url: str
    source: str


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for match in URL_PATTERN.finditer(text or ""):
        url = match.group(0).rstrip(TRAILING_PUNCTUATION)
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    return urls


def detect_source(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()

    if host.startswith("www."):
        host = host[4:]

    if _host_matches(host, ("facebook.com", "fb.watch", "fb.com")):
        return "Facebook"
    if _host_matches(host, ("instagram.com",)):
        return "Instagram"
    if _host_matches(host, ("youtube.com", "youtu.be")):
        return "YouTube"
    if _host_matches(host, ("maps.google.com", "goo.gl")) or (
        _host_matches(host, ("google.com",)) and path.startswith("/maps")
    ):
        return "Google Maps"
    return "Other"


def parse_urls(text: str) -> list[ParsedUrl]:
    return [ParsedUrl(url=url, source=detect_source(url)) for url in extract_urls(text)]


def _host_matches(host: str, domains: Iterable[str]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)
