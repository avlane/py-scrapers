"""Read RSS feeds."""
import xml.etree.ElementTree as ET


def parse_rss(xml_text):
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "published": (item.findtext("pubDate") or "").strip(),
            "summary": (item.findtext("description") or "").strip(),
        })
    return items
