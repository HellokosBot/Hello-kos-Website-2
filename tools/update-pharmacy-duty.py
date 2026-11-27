#!/usr/bin/env python3
"""Download the Kos pharmacy duty roster from Φαρμακευτικός Σύλλογος Δωδεκανήσου.

fs12.gr has no CORS header, so the browser cannot read it.
This script writes data/pharmacy-duty.json for the static site.
It keeps the current Athens week for Kos town and the two Kos municipal units.
"""
import json
import re
import sys
import time
import urllib.error
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
FETCH_ATTEMPTS = 3
FETCH_BACKOFF = (2, 5)
SOURCE_ERRORS = (urllib.error.URLError, TimeoutError, OSError, RuntimeError)

# ELOT 743 Type 2 (transcription), the form used for modern Greek names.
_ACCENTS = str.maketrans({
    "ά": "α", "έ": "ε", "ή": "η", "ί": "ι", "ό": "ο", "ύ": "υ", "ώ": "ω",
    "ϊ": "ι", "ϋ": "υ", "ΐ": "ι", "ΰ": "υ",
    "Ά": "α", "Έ": "ε", "Ή": "η", "Ί": "ι", "Ό": "ο", "Ύ": "υ", "Ώ": "ω",
    "Ϊ": "ι", "Ϋ": "υ",
})
_GREEK = set("αβγδεζηθικλμνξοπρσςτυφχψω")
_VOICED = set("αεηιουωβγδζλμνρ")
_SINGLE = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x",
    "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y",
    "φ": "f", "χ": "ch", "ψ": "ps", "ω": "o",
}
# Longer phrases first. These are translated, not only transliterated.
_PHRASES = (
    ("ΔΙΗΜΕΡΕΥΣΗ & ΔΙΑΝΥΚΤΕΡΕΥΣΗ", "Daytime duty & overnight duty"),
    ("ΔΙΗΜΕΡΕΥΣΗ ΚΑΙ ΔΙΑΝΥΚΤΕΡΕΥΣΗ", "Daytime duty & overnight duty"),
    ("ΔΙΗΜΕΡΕΥΣΗ", "Daytime duty"),
    ("ΔΙΑΝΥΚΤΕΡΕΥΣΗ", "Overnight duty"),
    ("ΔΗΜ. ΕΝ. ΗΡΑΚΛΕΙΔΩΝ ΚΩ", "Municipal Unit of Irakleidon, Kos"),
    ("ΔΗΜ. ΕΝ. ΔΙΚΑΙΟΥ ΚΩ", "Municipal Unit of Dikaiou, Kos"),
    ("ΚΥΚΛΟΣ ΑΕΡΟΔΡΟΜΙΟΥ", "Airport roundabout"),
    ("ΔΗΜ. ΔΙΑΜ.", "Municipal District"),
    ("24ΩΡΗ", "24-hour"),
    ("24ΩΡΟ", "24-hour"),
    ("24 ΩΡΟ", "24-hour"),
    ("24 ΩΡΕΣ", "24 hours"),
)
_WORDS = {
    "ΚΑΙ": "and",
    "ΤΟΥ": "of",
    "ΤΗΣ": "of",
    "ΤΩΝ": "of",
    "ΚΩΣ": "Kos",
    "ΚΩ": "Kos",
    "ΟΔΟΣ": "Street",
    "ΟΔ": "Street",
    "ΛΕΩΦΟΡΟΣ": "Avenue",
    "ΛΕΩΦ": "Avenue",
    "ΠΛΑΤΕΙΑ": "Square",
    "ΠΛ": "Square",
    "ΤΕΡΜΑ": "end of",
    "ΟΕ": "G.P.",
    "ΕΕ": "L.P.",
    "ΔΕΥΤΕΡΑ": "Monday",
    "ΤΡΙΤΗ": "Tuesday",
    "ΤΕΤΑΡΤΗ": "Wednesday",
    "ΠΕΜΠΤΗ": "Thursday",
    "ΠΑΡΑΣΚΕΥΗ": "Friday",
    "ΣΑΒΒΑΤΟ": "Saturday",
    "ΚΥΡΙΑΚΗ": "Sunday",
    "ΩΡΑ": "hour",
    "ΩΡΕΣ": "hours",
    "ΠΜ": "a.m.",
    "ΜΜ": "p.m.",
    "ΙΑΝΟΥΑΡΙΟΥ": "January",
    "ΦΕΒΡΟΥΑΡΙΟΥ": "February",
    "ΜΑΡΤΙΟΥ": "March",
    "ΑΠΡΙΛΙΟΥ": "April",
    "ΜΑΙΟΥ": "May",
    "ΙΟΥΝΙΟΥ": "June",
    "ΙΟΥΛΙΟΥ": "July",
    "ΑΥΓΟΥΣΤΟΥ": "August",
    "ΣΕΠΤΕΜΒΡΙΟΥ": "September",
    "ΟΚΤΩΒΡΙΟΥ": "October",
    "ΝΟΕΜΒΡΙΟΥ": "November",
    "ΔΕΚΕΜΒΡΙΟΥ": "December",
    "ΤΙΓΚΑΚΙ": "Tigaki",
    "ΚΑΡΔΑΜΑΙΝΑ": "Kardamena",
    "ΑΝΤΙΜΑΧΕΙΑ": "Antimachia",
}


def fetch(url):
    last = None
    for attempt in range(FETCH_ATTEMPTS):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HelloKos/1.0 (pharmacy duty)"})
            with urllib.request.urlopen(req, timeout=40) as response:
                raw = response.read()
            return raw.decode("utf-8", "replace")
        except SOURCE_ERRORS as exc:
            last = exc
            if attempt + 1 < FETCH_ATTEMPTS:
                wait = FETCH_BACKOFF[attempt]
                print(
                    "warning: fetch failed ({0}/{1}) {2}: {3}; retrying in {4}s".format(
                        attempt + 1, FETCH_ATTEMPTS, url, exc, wait
                    ),
                    file=sys.stderr,
                )
                time.sleep(wait)
    raise last


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


def fold_greek(text):
    text = unescape(text).translate(_ACCENTS)
    return " ".join(text.upper().split())


def elot743(token):
    """Transcribe one Greek token with ELOT 743 Type 2."""
    chars = list(token.translate(_ACCENTS).lower())
    out = []
    i = 0
    n = len(chars)

    def is_greek(ch):
        return ch in _GREEK

    def word_initial():
        return i == 0

    while i < n:
        ch = chars[i]
        nxt = chars[i + 1] if i + 1 < n else ""
        pair = ch + nxt if is_greek(ch) and is_greek(nxt) else ""
        if pair == "γγ":
            out.append("ng")
            i += 2
            continue
        if pair == "γξ":
            out.append("nx")
            i += 2
            continue
        if pair == "γχ":
            out.append("nch")
            i += 2
            continue
        if pair == "γκ":
            out.append("gk" if word_initial() else "ng")
            i += 2
            continue
        if pair == "μπ":
            out.append("b" if word_initial() else "mp")
            i += 2
            continue
        if pair == "ντ":
            out.append("nt")
            i += 2
            continue
        if pair in ("αυ", "ευ", "ηυ"):
            follower = chars[i + 2] if i + 2 < n else ""
            voiced = follower in _VOICED
            spoken = {"αυ": ("av", "af"), "ευ": ("ev", "ef"), "ηυ": ("iv", "if")}[pair]
            out.append(spoken[0] if voiced else spoken[1])
            i += 2
            continue
        if pair in ("ου", "αι", "ει", "οι", "υι", "ωυ"):
            out.append({"ου": "ou", "αι": "ai", "ει": "ei", "οι": "oi", "υι": "yi", "ωυ": "oy"}[pair])
            i += 2
            continue
        if is_greek(ch):
            out.append(_SINGLE[ch])
        else:
            out.append(chars[i])
        i += 1
    return "".join(out)


def cap_transliteration(text):
    """Capitalise a freshly transliterated token. One-letter initials stay capitals."""
    def repl(match):
        word = match.group(0)
        if len(word) == 1:
            return word.upper()
        return word[0].upper() + word[1:]

    return re.sub(r"[A-Za-z]+", repl, text)


def space_abbreviations(text):
    return re.sub(r"([A-Za-z]{2,})\.([A-Za-z])", r"\1. \2", text)


def to_english(text):
    """Latin-script English for a Greek pharmacy field. Latin text is left as written."""
    if not text:
        return ""
    folded = fold_greek(text)
    for src, dst in _PHRASES:
        folded = folded.replace(src, dst)

    def repl_token(match):
        token = match.group(0)
        key = token.replace(".", "")
        if key in _WORDS:
            return _WORDS[key]
        ordinal = re.fullmatch(r"(\d+)ΗΣ", key)
        if ordinal:
            return ordinal.group(1) + "th"
        if re.search(r"[Α-Ω]", token):
            return cap_transliteration(elot743(token))
        return token

    folded = re.sub(r"[Α-ΩA-Za-z0-9]+(?:\.[Α-ΩA-Za-z0-9]+)*\.?", repl_token, folded)
    return space_abbreviations(folded).strip()


def add_english(row):
    row["nameEn"] = to_english(row["name"])
    row["addressEn"] = to_english(row["address"])
    row["areaEn"] = to_english(row["area"])
    row["dutyLabelEn"] = to_english(row["dutyLabel"])
    return row


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


def write_roster():
    today = datetime.now(ATHENS).date()
    pharmacies = []
    sources = []
    for rank, (base, area) in enumerate(SOURCES):
        rows, url = load_source(base, area, rank, today)
        pharmacies.extend(add_english(row) for row in rows)
        sources.append({"area": area, "areaEn": to_english(area), "url": url, "count": len(rows)})
    pharmacies.sort(key=lambda row: (row["date"], row["areaRank"], DUTY_RANK[row["duty"]], row["name"]))
    for row in pharmacies:
        row.pop("areaRank", None)
    payload = {
        "fetchedAt": datetime.now(ATHENS).isoformat(),
        "timezone": "Europe/Athens",
        "sourceName": "Φαρμακευτικός Σύλλογος Δωδεκανήσου",
        "sourceNameEn": "Pharmaceutical Association of the Dodecanese",
        "sourceUrl": "https://www.fs12.gr/index.php/efimeries-ko/",
        "sources": sources,
        "pharmacies": pharmacies,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "pharmacies", len(pharmacies))


def main():
    try:
        write_roster()
    except SOURCE_ERRORS as exc:
        print(
            "warning: pharmacy source unavailable, leaving {0} unchanged: {1}".format(OUT, exc),
            file=sys.stderr,
        )
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
