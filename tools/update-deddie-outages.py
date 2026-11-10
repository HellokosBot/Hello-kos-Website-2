#!/usr/bin/env python3
"""Download the public DEDDIE planned-outage list for the Dodecanese and Kos.

The official page is HTML only and does not allow browser reads (no CORS).
This script writes data/deddie-outages.json so the static site can show it.
"""
import json
import re
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "deddie-outages.json"
ATHENS = ZoneInfo("Europe/Athens")
PARTIAL = "https://siteapps.deddie.gr/Outages2Public/Home/OutagesPartial"
PREFECTURE_ID = 15
KOS_MUNICIPALITY_ID = 304


def fetch(page, municipality_id=None):
    url = "%s?page=%d&prefectureID=%d" % (PARTIAL, page, PREFECTURE_ID)
    if municipality_id:
        url += "&municipalityID=%d" % municipality_id
    req = urllib.request.Request(url, headers={"User-Agent": "HelloKos/1.0 (planned outage list)"})
    with urllib.request.urlopen(req, timeout=40) as response:
        body = response.read().decode("utf-8", "replace")
    if 'id="tblOutages"' not in body:
        raise RuntimeError("DEDDIE did not return the outage table")
    return body


def clean(html):
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text).replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def parse_when(raw):
    match = re.match(
        r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(π\.?\s*μ\.?|μ\.?\s*μ\.?)",
        raw.strip(),
        re.I,
    )
    if not match:
        return None
    day, month, year, hour, minute, second, ampm = match.groups()
    hour = int(hour)
    marker = re.sub(r"[\s.]", "", ampm).lower()
    if marker.startswith("μ") and hour < 12:
        hour += 12
    if marker.startswith("π") and hour == 12:
        hour = 0
    moment = datetime(int(year), int(month), int(day), hour, int(minute), int(second or 0), tzinfo=ATHENS)
    return moment.isoformat()


def parse_rows(html):
    rows = []
    for row_html in re.findall(r'<tr class="align-middle">([\s\S]*?)</tr>', html):
        cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", row_html)
        if len(cells) < 6:
            continue
        start_raw = clean(cells[0])
        end_raw = clean(cells[1])
        places = [line for line in clean(cells[2]).split("\n") if line]
        rows.append({
            "from": parse_when(start_raw),
            "to": parse_when(end_raw),
            "fromRaw": start_raw,
            "toRaw": end_raw,
            "places": places,
            "area": clean(cells[3]),
            "noteNumber": clean(cells[4]),
            "purpose": clean(cells[5]),
        })
    return rows


def all_pages(municipality_id=None):
    found = []
    for page in range(1, 21):
        batch = parse_rows(fetch(page, municipality_id))
        if not batch:
            break
        found.extend(batch)
    return found


def key(row):
    return (row["fromRaw"], row["toRaw"], tuple(row["places"]), row["area"], row["purpose"])


def main():
    dodecanese = all_pages()
    kos_rows = all_pages(KOS_MUNICIPALITY_ID)
    kos_keys = {key(row) for row in kos_rows}
    for row in dodecanese:
        row["onKos"] = key(row) in kos_keys
    for row in kos_rows:
        row["onKos"] = True
    # Keep Kos rows that the prefecture list did not repeat.
    seen = {key(row) for row in dodecanese}
    for row in kos_rows:
        if key(row) not in seen:
            dodecanese.append(row)
    payload = {
        "fetchedAt": datetime.now(ATHENS).isoformat(),
        "sourceName": "ΔΕΔΔΗΕ",
        "sourceUrl": "https://siteapps.deddie.gr/Outages2Public/",
        "listType": "planned",
        "prefectureId": PREFECTURE_ID,
        "prefectureName": "ΔΩΔΕΚΑΝΗΣΟΥ",
        "kosMunicipalityId": KOS_MUNICIPALITY_ID,
        "outages": dodecanese,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    kos_count = sum(1 for row in dodecanese if row["onKos"])
    print("wrote", OUT, "total", len(dodecanese), "kos", kos_count)


if __name__ == "__main__":
    main()
