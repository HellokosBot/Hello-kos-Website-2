#!/usr/bin/env python3
"""Download public water-cut notices from Δ.Ε.Υ.Α. Δήμου Κω (deyakos.gr).

The RSS feed has no CORS header, so the browser cannot read it.
This script writes data/deya-outages.json for the static site.
"""
import json
import re
import urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "deya-outages.json"
ATHENS = ZoneInfo("Europe/Athens")
FEED = (
    "https://www.deyakos.gr/"
    "%CE%B5%CE%BD%CE%B7%CE%BC%CE%AD%CF%81%CF%89%CF%83%CE%B7/"
    "%CE%B4%CE%B9%CE%B1%CE%BA%CE%BF%CF%80%CE%AD%CF%82-"
    "%CF%85%CE%B4%CF%81%CE%BF%CE%B4%CF%8C%CF%84%CE%B7%CF%83%CE%B7%CF%82"
    "?format=feed&type=rss"
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "HelloKos/1.0 (water notices)"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return response.read()


def plain(html):
    text = unescape(html or "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def ampm_hour(hour, marker):
    hour = int(hour)
    marker = re.sub(r"[\s.]", "", marker or "").lower()
    if marker.startswith("μ") and hour < 12:
        hour += 12
    if marker.startswith("π") and hour == 12:
        hour = 0
    return hour


def parse_window(text, published):
    date_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
    if date_match:
        day, month, year = (int(part) for part in date_match.groups())
    elif published:
        day, month, year = published.day, published.month, published.year
    else:
        return None, None
    times = re.findall(
        r"(\d{1,2})[:.](\d{2})\s*(π\s*\.?\s*μ\.?|μ\s*\.?\s*μ\.?)?",
        text,
        re.I,
    )
    parsed = []
    for hour, minute, marker in times:
        if not marker and int(hour) > 23:
            continue
        parsed.append((ampm_hour(hour, marker), int(minute)))
        if len(parsed) == 2:
            break
    if not parsed:
        return None, None
    start_h, start_m = parsed[0]
    end_h, end_m = parsed[1] if len(parsed) > 1 else parsed[0]

    def stamp(hour, minute):
        return datetime(year, month, day, hour, minute, tzinfo=ATHENS).isoformat()

    if len(parsed) == 1:
        # One clock time is the announced end, when the sentence gives only that.
        return None, stamp(end_h, end_m)
    return stamp(start_h, start_m), stamp(end_h, end_m)


def kind_of(text):
    if "προγραμματισ" in text:
        return "planned"
    if "βλάβ" in text or "ζημι" in text:
        return "fault"
    return "announced"


def main():
    raw = fetch(FEED)
    if b"<rss" not in raw[:200].lower() and b"<rss" not in raw[:500].lower():
        raise RuntimeError("DEYAK did not return an RSS feed")
    root = ET.fromstring(raw)
    items = []
    for item in root.findall("./channel/item"):
        text = plain(item.findtext("description"))
        published = item.findtext("pubDate")
        published_dt = parsedate_to_datetime(published).astimezone(ATHENS) if published else None
        start, end = parse_window(text, published_dt)
        link = item.findtext("link") or ""
        items.append({
            "id": item.findtext("guid") or link,
            "title": plain(item.findtext("title")),
            "publishedAt": published_dt.isoformat() if published_dt else None,
            "from": start,
            "to": end,
            "kind": kind_of(text),
            "text": text,
            "url": link,
        })
    if not items:
        raise RuntimeError("DEYAK feed had no notices")
    payload = {
        "fetchedAt": datetime.now(ATHENS).isoformat(),
        "sourceName": "Δ.Ε.Υ.Α. Δήμου Κω",
        "sourceUrl": "https://www.deyakos.gr/",
        "area": "Δήμος Κω",
        "notices": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "notices", len(items))


if __name__ == "__main__":
    main()
