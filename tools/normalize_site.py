#!/usr/bin/env python3
"""Make every existing HTML page share one header and the shared i18n script."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEADER = """<header class="app-header">
  <div class="nav-btns">
    <a class="nav-btn" href="index.html" title="Home">🏠</a>
    <a class="nav-btn" href="javascript:history.back()" title="Terug">←</a>
  </div>
  <a class="logo" href="index.html"><span class="logo-icon">🔅</span><span class="logo-text">Hello <span>Kos</span></span></a>
  <div class="lang-wrap">
    <button class="lang-btn" id="langBtn" type="button" aria-haspopup="true" aria-expanded="false"><span id="flag">🇳🇱</span> <span id="code">NL</span></button>
    <div class="lang-menu" id="langMenu">
      <button class="lang-option" data-lang="nl" data-flag="🇳🇱" type="button">🇳🇱 Nederlands</button>
      <button class="lang-option" data-lang="de" data-flag="🇩🇪" type="button">🇩🇪 Deutsch</button>
      <button class="lang-option" data-lang="en" data-flag="🇬🇧" type="button">🇬🇧 English</button>
      <button class="lang-option" data-lang="it" data-flag="🇮🇹" type="button">🇮🇹 Italiano</button>
      <button class="lang-option" data-lang="tr" data-flag="🇹🇷" type="button">🇹🇷 Türkçe</button>
      <button class="lang-option" data-lang="es" data-flag="🇪🇸" type="button">🇪🇸 Español</button>
    </div>
  </div>
</header>"""

# Wrong filename in a link -> the file that already exists.
ALIASES = {
    "borden-kapot-gooien.html": "borden-kapotgooien.html",
    "bonnen.html": "bonnen-op-tafel.html",
    "winter-kos.html": "kos-in-de-winter.html",
    "zonsondergang.html": "zonsondergang-zia.html",
    "fastfood-mcdonald-s.html": "fastfood-mcdonalds.html",
    "route-auto-kort.html": "route-auto-1dag.html",
    "route-auto-lang.html": "route-auto-2dagen.html",
    "route-kos-stad-tegels.html": "route-wandel.html",
    "beste-stranden.html": "stranden.html",
    "sight-albergo.html": "sight-albergo-gelsomino.html",
    "sight-museum.html": "sight-archeologisch-museum.html",
    "sight-palm-lane.html": "sight-palm-tree-lane.html",
    "sight-palazzo.html": "sight-palazzo-giustizia.html",
    "sight-aquaduct.html": "sight-aquaduct-linopotas.html",
    "sight-antimachia-kasteel.html": "sight-kasteel-antimachia.html",
    "sight-traditioneel-huis.html": "sight-traditioneel-huis-antimachia.html",
    "sight-hasan-moskee.html": "sight-gazi-hasan.html",
    "sight-mausoleum.html": "sight-hatzi-pasha.html",
    "sight-zoutmeer.html": "sight-zoutmeer-tigaki.html",
    "sight-agios-stefanos.html": "sight-agios-stefanos-kefalos.html",
    "sight-agios-nikolaos.html": "sight-kapel-agios-nikolaos.html",
    "sight-vlag.html": "vlag-hijsen.html",
    "restaurant-soul-kitchen.html": "beste-soul-kitchen.html",
    "restaurant-chesapak.html": "beste-chesapak.html",
    "restaurant-kostasken.html": "beste-kostasken.html",
    "restaurant-oromedon.html": "beste-oromedon.html",
    "restaurant-magic-mountain.html": "beste-magic-mountain.html",
    "wjd-quake-gallery-02.jpg": "wjd-quake-gallery-02.jpeg",
    "wjd-bodrum-intro.jpg": "wjd-bodrum-vliegtuig.jpg",
}

LIGHT = {"sight-hatzi-pasha.html", "sight-defterdar.html"}


def clean_edges(text: str) -> str:
    lower = text.lower()
    start = lower.find("<!doctype")
    if start < 0:
        start = lower.find("<html")
    if start > 0:
        text = text[start:]
        lower = text.lower()
    end = lower.rfind("</html>")
    if end >= 0:
        text = text[: end + len("</html>")]
        if not text.endswith("\n"):
            text += "\n"
    return text


def apply_aliases(text: str) -> str:
    for old, new in ALIASES.items():
        text = text.replace(f'href="{old}"', f'href="{new}"')
        text = text.replace(f"href='{old}'", f"href='{new}'")
        text = text.replace(f'src="{old}"', f'src="{new}"')
        text = text.replace(f"src='{old}'", f"src='{new}'")
    return text


def ensure_header(text: str) -> str:
    text2, n = re.subn(
        r"<header\s+class=\"app-header\"[^>]*>.*?</header>",
        HEADER,
        text,
        count=1,
        flags=re.S,
    )
    if n == 0:
        text2 = re.sub(r"<body([^>]*)>", r"<body\1>\n" + HEADER, text, count=1)
    if 'id="overlay"' not in text2:
        text2 = text2.replace(HEADER, HEADER + '\n<div class="overlay" id="overlay"></div>', 1)
    return text2


def ensure_assets(text: str) -> str:
    if "hello-kos.css" not in text:
        text = text.replace("</head>", '<link rel="stylesheet" href="hello-kos.css">\n</head>', 1)
    if "hello-kos-i18n.js" not in text:
        text = text.replace("</body>", '<script src="hello-kos-i18n.js"></script>\n</body>', 1)
    return text


def mark_html(text: str, name: str) -> str:
    own = "function setLang" in text or "function setLang(" in text
    tts = "btnPlay" in text and "addEventListener" in text
    # Add attributes on the opening <html> tag.
    def repl(m):
        tag = m.group(0)
        if own and "data-hk-own" not in tag:
            tag = tag[:-1] + ' data-hk-own="1">'
        if tts and "data-hk-tts" not in tag:
            tag = tag[:-1] + ' data-hk-tts="1">'
        if name in LIGHT and "hk-fix-light" not in text:
            if 'class="' in tag:
                tag = tag.replace('class="', 'class="hk-fix-light ', 1)
            else:
                tag = tag[:-1] + ' class="hk-fix-light">'
        return tag
    return re.sub(r"<html\b[^>]*>", repl, text, count=1)


def fix_lang_default(text: str) -> str:
    text = text.replace("localStorage.getItem('hk-lang')||'en'", "localStorage.getItem('hk-lang')||'nl'")
    text = text.replace('localStorage.getItem("hk-lang")||"en"', 'localStorage.getItem("hk-lang")||"nl"')
    text = text.replace("localStorage.getItem('hk-lang') || 'en'", "localStorage.getItem('hk-lang') || 'nl'")
    text = text.replace('localStorage.getItem("hk-lang") || "en"', 'localStorage.getItem("hk-lang") || "nl"')
    return text


def add_es_voice(text: str) -> str:
    if "es-ES" in text or "es:" in text and "es-ES" in text:
        return text
    text = re.sub(
        r"tr\s*:\s*'tr-TR'(?!\s*,\s*es)",
        "tr:'tr-TR',es:'es-ES'",
        text,
    )
    text = re.sub(
        r'tr\s*:\s*"tr-TR"(?!\s*,\s*es)',
        'tr:"tr-TR",es:"es-ES"',
        text,
    )
    return text


def fix_mailto(text: str) -> str:
    text = text.replace(
        '<a href="mailto:info@hellokos.nl">info@hellokos.nl</a>',
        '<a href="mailto:info@hellokos.com">info@hellokos.com</a>',
    )
    text = text.replace("https://www.hellokos.nl", "")
    text = text.replace("http://www.hellokos.nl", "")
    text = text.replace("https://hellokos.nl", "")
    text = text.replace("http://hellokos.nl", "")
    return text


def main():
    n = 0
    for path in sorted(ROOT.glob("*.html")):
        original = path.read_text(encoding="utf-8", errors="replace")
        text = clean_edges(original)
        text = apply_aliases(text)
        text = ensure_header(text)
        text = ensure_assets(text)
        text = fix_lang_default(text)
        text = add_es_voice(text)
        text = fix_mailto(text)
        text = mark_html(text, path.name)
        if text != original:
            path.write_text(text, encoding="utf-8")
            n += 1
    print("updated", n)


if __name__ == "__main__":
    main()
