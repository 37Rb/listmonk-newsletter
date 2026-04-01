"""Fetches feed entries from an RSS URL using feedparser."""

import time
from datetime import datetime

import feedparser
from structlog_config import configure_logger

from .entry import Entry
from .teaser import fetch_article_metadata

log = configure_logger()


def _format_published(entry) -> str | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")

    if parsed is None:
        return None

    return datetime.fromtimestamp(time.mktime(parsed)).strftime("%B %-d, %Y")


def fetch_entries(rss_url: str) -> list[Entry]:
    feed: feedparser.FeedParserDict = feedparser.parse(rss_url)

    if "bozo_exception" in feed:
        log.error("feed parsing error", error=feed["bozo_exception"])
        return []

    if not feed:
        log.error("feed is empty")
        return []

    entries = []

    for e in feed.entries:
        link = e.get("link", "")
        _, og_description, teaser = fetch_article_metadata(link) if link else (None, None, "")

        entries.append(Entry(
            title=e.get("title", ""),
            link=link,
            description=teaser,
            summary=e.get("summary", ""),
            og_description=og_description,
            published=_format_published(e),
        ))

    return entries
