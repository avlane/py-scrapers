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


ATOM = "{http://www.w3.org/2005/Atom}"


def parse_iso8601(text):
    """'2019-07-04T17:45:00Z' (or with an offset) -> aware datetime in UTC, or None."""
    text = (text or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+0000"
    text = text[:-3] + text[-2:] if len(text) > 6 and text[-3] == ":" else text  # +01:00 -> +0100
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)
    except ValueError:
        return None


def _atom_link(entry):
    for link in entry.findall(ATOM + "link"):
        if link.get("rel", "alternate") == "alternate":
            return link.get("href", "")
    return ""


def parse_atom(root):
    items = []
    for entry in root.iter(ATOM + "entry"):
        date = entry.findtext(ATOM + "published") or entry.findtext(ATOM + "updated")
        items.append({
            "title": (entry.findtext(ATOM + "title") or "").strip(),
            "link": _atom_link(entry),
            "published": parse_iso8601(date),
            "summary": (entry.findtext(ATOM + "summary") or entry.findtext(ATOM + "content") or "").strip(),
        })
    return items


def parse_rss(xml_text):
    """Parse an RSS 2.0 or Atom feed into a list of dicts."""
    root = ET.fromstring(xml_text)
    if root.tag == ATOM + "feed":
        return parse_atom(root)
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
