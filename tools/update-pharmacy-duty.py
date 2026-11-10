#!/usr/bin/env python3
"""Download the Kos pharmacy duty roster from Φαρμακευτικός Σύλλογος Δωδεκανήσου.

fs12.gr has no CORS header, so the browser cannot read it.
This script writes data/pharmacy-duty.json for the static site.
It keeps the current Athens week for Kos town and the two Kos municipal units.
"""
import json
import re
import urllib.request
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "pharmacy-duty.json"
ATHENS = ZoneInfo("Europe/Athens")
MONTHS = {
    "ΙΑΝ": 1,
    "ΦΕΒ": 2,
    "ΜΑΡ": 3,
    "ΑΠΡ": 4,
    "ΜΑΙ": 5,
    "ΜΑΪ": 5,
    "ΙΟΥΝ": 6,
    "ΙΟΥΛ": 7,
    "ΑΥΓ": 8,
    "ΣΕΠ": 9,
    "ΟΚΤ": 10,
    "ΝΟΕ": 11,
    "ΔΕΚ": 12,
}
SOURCES = (
    (
        "https://www.fs12.gr/index.php/efimeries-ko/",
        "Κως",
    ),
    (
        "https://www.fs12.gr/index.php/efimeries-dim-en-irakleidon-ko/",
        "Δημ. Εν. Ηρακλειδών Κω",
    ),
    (
        "https://www.fs12.gr/index.php/efimeries-dim-en-dikaiou-ko/",
        "Δημ. Εν. Δικαίου Κω",
    ),
)
DUTY_RANK = {"day": 0, "both": 1, "night": 2}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "HelloKos/1.0 (pharmacy duty)"})
    with urllib.request.urlopen(req, timeout=40) as response:
        raw = response.read()
    return raw.decode("utf-8", "replace")


def lines_of(block):
    text = unescape(block)
    text = re.sub(r"</?br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(?:div|p|b|span|a|em)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    lines = []
    for line in text.splitlines():
        line = " ".join(line.split())
        if line:
            lines.append(line)
    return lines


def month_num(token):
    key = token.upper()
    for src, dst in (("Ά", "Α"), ("Έ", "Ε"), ("Ή", "Η"), ("Ί", "Ι"), ("Ό", "Ο"), ("Ύ", "Υ"), ("Ώ", "Ω"), ("Ϊ", "Ι"), ("Ϋ", "Υ")):
        key = key.replace(src, dst)
    return MONTHS.get(key[:4]) or MONTHS.get(key[:3])


def parse_date(lines):
    for line in lines:
        match = re.search(r"(\d{1,2})\s+([^\W\d_]{3,12})\s+(\d{4})", line, re.U)
        if not match:
            continue
        month = month_num(match.group(2))
        if not month:
            continue
        return datetime(int(match.group(3)), month, int(match.group(1))).date().isoformat()
    return None


def duty_of(lines):
    for line in lines:
        day = "Διημέρευση" in line
        night = "Διανυκτέρευση" in line
        if day and night:
            return "both", "Διημέρευση & Διανυκτέρευση"
        if day:
            return "day", "Διημέρευση"
        if night:
            return "night", "Διανυκτέρευση"
    return None, None


def phones_of(lines):
    found = []
    for line in lines:
        match = re.search(r"[TΤ]ηλ\s*:\s*(.+)", line)
        if not match:
            continue
        for number in re.findall(r"\d{10}", match.group(1)):
            if number not in found:
                found.append(number)
    return found


def parse_page(html, area, rank):
    blocks = re.findall(r"<div\s+class='jevright'[^>]*>(.*?)</div>", html, re.S)
    if not blocks:
        raise RuntimeError("no duty rows on " + area)
    rows = []
    for block in blocks:
        if "ev_link_row" not in block:
            continue
        name_match = re.search(r'class="ev_link_row"[^>]*>\s*(.*?)\s*</a>', block, re.S)
        name = " ".join(unescape(re.sub(r"<[^>]+>", " ", name_match.group(1))).split()) if name_match else ""
        lines = lines_of(block)
        date = parse_date(lines)
        duty, label = duty_of(lines)
        if not name or not date or not duty:
            raise RuntimeError("could not read a duty row on " + area)
        address = []
        for line in lines:
            if line == name or parse_date([line]):
                continue
            phone_at = re.search(r"[TΤ]ηλ", line)
            if phone_at:
                before = line[:phone_at.start()].strip(" ,")
                if before and before != name:
                    address.append(before)
                continue
            rest = re.sub(r"^(?:Διημέρευση(?:\s*&\s*Διανυκτέρευση)?|Διανυκτέρευση)\s*", "", line).strip()
            if rest == line and ("Διημέρευση" in line or "Διανυκτέρευση" in line):
                continue
            if not rest or rest == name:
                continue
            address.append(rest)
        href = re.search(r'href="([^"]+)"', block)
        rows.append({
            "date": date,
            "name": name,
            "address": ", ".join(address),
            "phones": phones_of(lines),
            "duty": duty,
            "dutyLabel": label,
            "area": area,
            "areaRank": rank,
            "id": href.group(1) if href else name + "|" + date + "|" + duty,
        })
    if not rows:
        raise RuntimeError("no pharmacies parsed on " + area)
    return rows


def week_url(base, today):
    monday = today - timedelta(days=today.weekday())
    return base.rstrip("/") + monday.strftime("/eventsbyweek/%Y/%m/%d/-")


def load_source(base, area, rank, today):
    url = week_url(base, today)
    try:
        html = fetch(url)
        if "jevright" not in html:
            raise RuntimeError("week page had no roster")
    except Exception:
        html = fetch(base)
        url = base
    return parse_page(html, area, rank), url


def main():
    today = datetime.now(ATHENS).date()
    pharmacies = []
    sources = []
    for rank, (base, area) in enumerate(SOURCES):
        rows, url = load_source(base, area, rank, today)
        pharmacies.extend(rows)
        sources.append({"area": area, "url": url, "count": len(rows)})
    pharmacies.sort(key=lambda row: (row["date"], row["areaRank"], DUTY_RANK[row["duty"]], row["name"]))
    for row in pharmacies:
        row.pop("areaRank", None)
    payload = {
        "fetchedAt": datetime.now(ATHENS).isoformat(),
        "timezone": "Europe/Athens",
        "sourceName": "Φαρμακευτικός Σύλλογος Δωδεκανήσου",
        "sourceUrl": "https://www.fs12.gr/index.php/efimeries-ko/",
        "sources": sources,
        "pharmacies": pharmacies,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "pharmacies", len(pharmacies))


if __name__ == "__main__":
    main()
