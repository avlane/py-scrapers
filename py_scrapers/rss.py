"""Read RSS feeds."""
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_rfc822(text):
    """'Tue, 02 Jul 2019 09:30:00 +0100' -> aware datetime in UTC, or None."""
    if not text:
        return None
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc)


def parse_rss(xml_text):
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "published": parse_rfc822((item.findtext("pubDate") or "").strip()),
            "summary": (item.findtext("description") or "").strip(),
        })
    return items


def newest_first(items):
    """Sort by date, newest first; items without a date go last."""
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(items, key=lambda item: item["published"] or oldest, reverse=True)
