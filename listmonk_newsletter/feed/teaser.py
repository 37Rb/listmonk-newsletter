"""Fetches OG metadata and article teaser text from a URL in a single HTTP request."""

import re

import requests
from lxml import etree

TEASER_WORD_COUNT = 55
MIN_PARAGRAPH_WORDS = 8


def _first_n_words(text: str, n: int) -> str:
    words = text.split()
    if len(words) <= n:
        return " ".join(words)
    return " ".join(words[:n]) + "..."


def _paragraph_text(p) -> str:
    return " ".join("".join(p.itertext()).split())


def _extract_teaser(tree, word_count: int) -> str:
    for tag in tree.iter("script", "style", "nav", "header", "footer", "aside"):
        tag.getparent().remove(tag)

    container = tree.find(".//article")
    if container is None:
        container = tree.find(".//main")
    paragraphs = container.findall(".//p") if container is not None else tree.findall(".//p")

    text = " ".join(
        _paragraph_text(p)
        for p in paragraphs
        if len(_paragraph_text(p).split()) >= MIN_PARAGRAPH_WORDS
    )
    text = re.sub(r"\s+", " ", text).strip()

    return _first_n_words(text, word_count)


def fetch_article_metadata(url: str, word_count: int = TEASER_WORD_COUNT) -> tuple[str | None, str | None, str]:
    """Fetch og:image, og:description, and article teaser text in a single HTTP request.

    Returns (image, og_description, teaser).
    """
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    tree = etree.fromstring(response.content, etree.HTMLParser())

    og_image = tree.find("head/meta[@property='og:image']")
    og_description = tree.find("head/meta[@property='og:description']")

    image = og_image.get("content") if og_image is not None else None
    description = og_description.get("content") if og_description is not None else None
    teaser = _extract_teaser(tree, word_count)

    return image, description, teaser
