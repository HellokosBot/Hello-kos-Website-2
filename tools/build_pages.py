#!/usr/bin/env python3
"""Create the pages that existing links point to, in the Hello Kos style."""
import json
import re
import urllib.request
from html import unescape
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize_site import HEADER

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "img" / "hk"
IMG.mkdir(parents=True, exist_ok=True)
LANGS = ["nl", "de", "en", "it", "tr", "es"]


def L(nl, de, en, it, tr, es):
    return {"nl": nl, "de": de, "en": en, "it": it, "tr": tr, "es": es}


def download(url, dest: Path):
    if dest.exists() and dest.stat().st_size > 800:
        return True
    url = unescape(url).replace("&amp;", "&")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        data = urllib.request.urlopen(req, timeout=40).read()
    except Exception as exc:
        print("img fail", dest.name, exc)
        return False
    if len(data) < 500:
        return False
    dest.write_bytes(data)
    return True


def hero_url_for(filename):
    """Use the photo already chosen on a hub card, if there is one."""
    for page in ROOT.glob("*.html"):
        text = page.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r'href="%s"' % re.escape(filename), text):
            window = text[max(0, match.start() - 400): match.end() + 500]
            img = re.search(r"https://primary\.jwwb\.nl/[^\"')\s]+", window)
            if img:
                return unescape(img.group(0))
            src = re.search(r'src="([^"]+\.(?:jpg|jpeg|png|webp))"', window)
            if src and not src.group(1).startswith("http") and (ROOT / src.group(1)).exists():
                return "LOCAL:" + src.group(1)
    return None


def ensure_hero(filename, fallback):
    url = hero_url_for(filename)
    dest = IMG / (Path(filename).stem + ".jpg")
    if url and url.startswith("LOCAL:"):
        return url.split(":", 1)[1]
    if url and download(url, dest):
        return "img/hk/" + dest.name
    if fallback and (ROOT / fallback).exists():
        return fallback
    if fallback and str(fallback).startswith("http") and download(fallback, dest):
        return "img/hk/" + dest.name
    return "intro.jpg"


SCRAPE = {}
scrape_path = Path("/tmp/hk/scrape.json")
if scrape_path.exists():
    SCRAPE = json.loads(scrape_path.read_text(encoding="utf-8"))


def scrape_img(key, filename, fallback):
    imgs = (SCRAPE.get(key) or {}).get("imgs") or []
    dest = IMG / (Path(filename).stem + ".jpg")
    for url in imgs:
        if any(x in url for x in ("favicon", "touch-icon", "logo")):
            continue
        if download(url, dest):
            return "img/hk/" + dest.name
    return ensure_hero(filename, fallback)


def page(filename, title, lead, sections, badges, image, parent, parent_label, maps=None, note=None):
    """sections: list of (heading dict, paragraph dict). badges: list of dicts."""
    dicts = {lang: {} for lang in LANGS}
    for lang in LANGS:
        dicts[lang]["title"] = title[lang]
        dicts[lang]["lead"] = lead[lang]
        dicts[lang]["back"] = parent_label[lang]
        if note:
            dicts[lang]["note"] = note[lang]
    for i, (h, p) in enumerate(sections):
        for lang in LANGS:
            dicts[lang]["h%d" % i] = h[lang]
            dicts[lang]["p%d" % i] = p[lang]
    for i, b in enumerate(badges):
        for lang in LANGS:
            dicts[lang]["b%d" % i] = b[lang]

    badge_html = "".join(
        '<span class="badge" data-i18n="b%d">%s</span>' % (i, b["nl"]) for i, b in enumerate(badges)
    )
    section_html = []
    for i, (h, p) in enumerate(sections):
        section_html.append(
            '<article class="card"><h2 data-i18n="h%d">%s</h2><p data-i18n="p%d">%s</p></article>'
            % (i, h["nl"], i, p["nl"])
        )
    note_html = ""
    if note:
        note_html = '<div class="placeholder" data-i18n="note"><strong>Nog aan te vullen.</strong> %s</div>' % note["nl"]
    maps_html = ""
    if maps:
        q = urllib.parse.quote(maps) if False else maps.replace(" ", "%20")
        maps_html = (
            '<a class="btn btn-map" href="https://www.google.com/maps/search/?api=1&query=%s" target="_blank" rel="noopener">Google Maps</a>'
            '<a class="btn btn-map" href="https://maps.apple.com/?q=%s" target="_blank" rel="noopener">Apple Maps</a>'
            % (q, q)
        )
    html = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0D1A1A">
<title>%s – Hello Kos</title>
<link rel="stylesheet" href="hello-kos.css">
</head>
<body class="hk-page">
%s
<div class="overlay" id="overlay"></div>
<main class="main">
  <div class="hero-wrap"><img src="%s" alt=""></div>
  <p class="parent-link"><a href="%s" data-i18n="back">%s</a></p>
  <h1 data-i18n="title">%s</h1>
  <p class="lead" data-i18n="lead">%s</p>
  <div class="badges">%s</div>
  <div class="actions">
    <button type="button" class="btn btn-audio" id="btnPlay" data-i18n="read">Voorlezen</button>
    <button type="button" class="btn btn-stop" id="btnStop" data-i18n="stop">Stop</button>
    %s
  </div>
  <p class="status" id="ttsStatus"></p>
  <div id="readText">
    %s
    %s
  </div>
</main>
<footer class="hk-footer"><div>Hello Kos</div><p><a href="mailto:info@hellokos.com">info@hellokos.com</a></p></footer>
<script>window.HK_DICT = %s;</script>
<script src="hello-kos-i18n.js"></script>
</body>
</html>
""" % (
        title["nl"].replace("<", ""),
        HEADER,
        image,
        parent,
        parent_label["nl"],
        title["nl"],
        lead["nl"],
        badge_html,
        maps_html,
        "\n    ".join(section_html),
        note_html,
        json.dumps(dicts, ensure_ascii=False),
    )
    (ROOT / filename).write_text(html, encoding="utf-8")
    print("wrote", filename)


def hub(filename, title, lead, cards, parent, parent_label, image):
    """cards: list of (href, img, title dict)."""
    dicts = {lang: {} for lang in LANGS}
    for lang in LANGS:
        dicts[lang]["title"] = title[lang]
        dicts[lang]["lead"] = lead[lang]
        dicts[lang]["back"] = parent_label[lang]
    tiles = []
    for i, (href, img, label) in enumerate(cards):
        for lang in LANGS:
            dicts[lang]["c%d" % i] = label[lang]
        tiles.append(
            '<a class="tile" href="%s"><img src="%s" alt=""><span data-i18n="c%d">%s</span></a>'
            % (href, img, i, label["nl"])
        )
    html = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0D1A1A">
<title>%s – Hello Kos</title>
<link rel="stylesheet" href="hello-kos.css">
</head>
<body class="hk-page">
%s
<div class="overlay" id="overlay"></div>
<main class="main">
  <p class="parent-link"><a href="%s" data-i18n="back">%s</a></p>
  <h1 data-i18n="title">%s</h1>
  <p class="lead" data-i18n="lead">%s</p>
  <div class="grid" id="readText">
    %s
  </div>
</main>
<footer class="hk-footer"><div>Hello Kos</div><p><a href="mailto:info@hellokos.com">info@hellokos.com</a></p></footer>
<script>window.HK_DICT = %s;</script>
<script src="hello-kos-i18n.js"></script>
</body>
</html>
""" % (
        title["nl"],
        HEADER,
        parent,
        parent_label["nl"],
        title["nl"],
        lead["nl"],
        "\n    ".join(tiles),
        json.dumps(dicts, ensure_ascii=False),
    )
    # hero image is optional; hubs use tiles. Keep a small visual by not requiring hero.
    (ROOT / filename).write_text(html, encoding="utf-8")
    print("hub", filename)


BACK_HOME = L("← Home", "← Start", "← Home", "← Home", "← Ana sayfa", "← Inicio")
BACK_SIGHT = L("← Bezienswaardigheden", "← Sehenswürdigkeiten", "← Sights", "← Attrazioni", "← Gezilecek yerler", "← Lugares de interés")
BACK_BEACH = L("← Stranden", "← Strände", "← Beaches", "← Spiagge", "← Plajlar", "← Playas")
BACK_FOOD = L("← Beste & lekkerste", "← Beste & Leckerste", "← Best & tastiest", "← Il meglio", "← En iyiler", "← Lo mejor")
BACK_EX = L("← Excursies", "← Ausflüge", "← Excursions", "← Escursioni", "← Turlar", "← Excursiones")
BACK_HELP = L("← Noodgevallen", "← Notfälle", "← Emergencies", "← Emergenze", "← Acil durum", "← Emergencias")
BACK_WJD = L("← Wist je dat", "← Wusstest du", "← Did you know", "← Lo sapevi", "← Biliyor muydun", "← ¿Sabías que")
BACK_TAXI = L("← Taxi & bussen", "← Taxi & Bus", "← Taxi & buses", "← Taxi e bus", "← Taksi ve otobüs", "← Taxi y buses")
BACK_COCK = L("← Cocktails", "← Cocktails", "← Cocktails", "← Cocktail", "← Kokteyller", "← Cócteles")
BACK_ICE = L("← IJs", "← Eis", "← Ice cream", "← Gelato", "← Dondurma", "← Helado")
NOTE_PRICE = L(
    "Prijzen en openingstijden staan hier niet vast: die veranderen. Vraag het ter plaatse.",
    "Preise und Öffnungszeiten stehen hier nicht fest, sie ändern sich. Frag vor Ort nach.",
    "Prices and opening hours are not fixed here: they change. Ask on the spot.",
    "Prezzi e orari non sono fissi: cambiano. Chiedi sul posto.",
    "Fiyat ve açılış saatleri burada sabit değil, değişir. Yerinde sorun.",
    "Los precios y horarios no están fijos: cambian. Pregunta en el sitio.",
)
NOTE_PHONE = L(
    "Het telefoonnummer en het exacte adres staan nog niet in deze gids. Bel bij direct gevaar 112.",
    "Telefonnummer und genaue Adresse stehen noch nicht in diesem Guide. Bei direkter Gefahr: 112.",
    "The phone number and exact address are not in this guide yet. If you are in danger, call 112.",
    "Numero di telefono e indirizzo esatto non sono ancora in questa guida. In pericolo chiama il 112.",
    "Telefon ve tam adres bu rehberde henüz yok. Tehlike varsa 112'yi ara.",
    "El teléfono y la dirección exacta aún no están en esta guía. Si hay peligro, llama al 112.",
)
BADGE_FREE = L("Gratis", "Kostenlos", "Free", "Gratis", "Ücretsiz", "Gratis")
BADGE_FEE = L("Entree", "Eintritt", "Entrance fee", "Ingresso", "Giriş ücretli", "De pago")
BADGE_TOWN = L("Kos-stad", "Kos-Stadt", "Kos town", "Città di Kos", "Kos şehri", "Ciudad de Kos")
BADGE_CHECK = L("Prijs ter plaatse", "Preis vor Ort", "Price on site", "Prezzo sul posto", "Fiyat yerinde", "Precio en el sitio")


def build():
    # ----- homepage hubs -----
    hub(
        "bars-nightlife.html",
        L("Bars & nachtleven", "Bars & Nachtleben", "Bars & nightlife", "Bar & nightlife", "Barlar ve gece hayatı", "Bares y nightlife"),
        L(
            "Waar Kos ’s avonds leeft: cocktailbars, clubs, strandfeesten en partyboten. Tijden wisselen per seizoen.",
            "Wo Kos abends lebt: Cocktailbars, Clubs, Strandpartys und Partyboote. Die Zeiten wechseln mit der Saison.",
            "Where Kos comes alive at night: cocktail bars, clubs, beach parties and party boats. Hours change by season.",
            "Dove Kos vive di sera: cocktail bar, club, feste in spiaggia e party boat. Gli orari cambiano con la stagione.",
            "Kos akşamları nerede canlanır: kokteyl barları, kulüpler, plaj partileri ve parti tekneleri. Saatler mevsime göre değişir.",
            "Dónde vive Kos por la noche: coctelerías, clubs, fiestas de playa y barcos. Los horarios cambian con la temporada.",
        ),
        [
            ("bar-street-dicht.html", "bars-nightlife.jpg", L("Bar Street", "Bar Street", "Bar Street", "Bar Street", "Bar Street", "Bar Street")),
            ("beste-cocktails.html", "bars-nightlife.jpg", L("Cocktails", "Cocktails", "Cocktails", "Cocktail", "Kokteyller", "Cócteles")),
            ("excursie-griekse-avond.html", "excursies.jpg", L("Griekse avond", "Griechischer Abend", "Greek evening", "Serata greca", "Yunan gecesi", "Noche griega")),
            ("excursie-zia-nacht.html", "excursies.jpg", L("Zia in de avond", "Zia am Abend", "Zia at night", "Zia di sera", "Akşam Zia", "Zia de noche")),
        ],
        "index.html", BACK_HOME, "bars-nightlife.jpg",
    )
    page(
        "bars-nightlife.html",
        L("Bars & nachtleven", "Bars & Nachtleben", "Bars & nightlife", "Bar & nightlife", "Barlar ve gece hayatı", "Bares y nightlife"),
        L(
            "De oude gids deelde het nachtleven in vier groepen in. Hieronder staan de namen die daarop stonden, zonder verzonnen openingstijden.",
            "Der alte Guide teilte das Nachtleben in vier Gruppen. Unten stehen die Namen daraus, ohne erfundene Öffnungszeiten.",
            "The old guide split nightlife into four groups. The names below come from that list. Opening hours are not invented.",
            "La vecchia guida divideva la notte in quattro gruppi. I nomi qui sotto vengono da quell’elenco, senza orari inventati.",
            "Eski rehber gece hayatını dört gruba ayırıyordu. Aşağıdaki isimler o listeden. Açılış saati uydurulmadı.",
            "La guía antigua repartía la noche en cuatro grupos. Los nombres salen de esa lista, sin horarios inventados.",
        ),
        [
            (L("Cocktailbars", "Cocktailbars", "Cocktail bars", "Cocktail bar", "Kokteyl barları", "Coctelerías"),
             L("Vie, Umbra en Marina Cafe Bar stonden bij de cocktailbars. Meer tips staan bij Cocktails.",
               "Vie, Umbra und Marina Cafe Bar standen bei den Cocktailbars. Mehr Tipps stehen unter Cocktails.",
               "Vie, Umbra and Marina Cafe Bar were listed with the cocktail bars. More tips are under Cocktails.",
               "Vie, Umbra e Marina Cafe Bar erano tra i cocktail bar. Altri consigli sono sotto Cocktail.",
               "Vie, Umbra ve Marina Cafe Bar kokteyl barlarındaydı. Daha fazlası Kokteyller sayfasında.",
               "Vie, Umbra y Marina Cafe Bar estaban entre las coctelerías. Hay más en Cócteles.")),
            (L("Clubs", "Clubs", "Clubs", "Club", "Kulüpler", "Clubs"),
             L("Op de lijst: Bar Street, Mattatoio, Sitar, Mylos Beach Bar, Camel Bar, Downtown Club en Caramela. Bar Street gaat niet overal even vroeg dicht — lees de aparte pagina.",
               "Auf der Liste: Bar Street, Mattatoio, Sitar, Mylos Beach Bar, Camel Bar, Downtown Club und Caramela. Bar Street macht nicht überall früh zu — siehe die eigene Seite.",
               "On the list: Bar Street, Mattatoio, Sitar, Mylos Beach Bar, Camel Bar, Downtown Club and Caramela. Bar Street does not always close early — read the separate page.",
               "In elenco: Bar Street, Mattatoio, Sitar, Mylos Beach Bar, Camel Bar, Downtown Club e Caramela. Bar Street non chiude sempre presto — leggi la pagina dedicata.",
               "Listede: Bar Street, Mattatoio, Sitar, Mylos Beach Bar, Camel Bar, Downtown Club ve Caramela. Bar Street her yerde erken kapanmaz — ayrı sayfaya bak.",
               "En la lista: Bar Street, Mattatoio, Sitar, Mylos Beach Bar, Camel Bar, Downtown Club y Caramela. Bar Street no siempre cierra pronto — mira la página aparte.")),
            (L("Strand en boten", "Strand und Boote", "Beach and boats", "Spiaggia e barche", "Plaj ve tekneler", "Playa y barcos"),
             L("Strand- en poolfeesten: Mylos, Black Amber en Amos. Er zijn ook partyboten. Het seizoen bepaalt of ze varen.",
               "Strand- und Poolpartys: Mylos, Black Amber und Amos. Es gibt auch Partyboote. Die Saison entscheidet, ob sie fahren.",
               "Beach and pool parties: Mylos, Black Amber and Amos. There are party boats too. The season decides if they run.",
               "Feste in spiaggia e in piscina: Mylos, Black Amber e Amos. Ci sono anche party boat. La stagione decide se escono.",
               "Plaj ve havuz partileri: Mylos, Black Amber ve Amos. Parti tekneleri de var. Sezon, çalışıp çalışmayacaklarını belirler.",
               "Fiestas de playa y piscina: Mylos, Black Amber y Amos. También hay barcos. La temporada decide si salen.")),
        ],
        [L("Avond", "Abend", "Night", "Sera", "Akşam", "Noche"), BADGE_CHECK],
        "bars-nightlife.jpg",
        "index.html", BACK_HOME, "Kos town bars", NOTE_PRICE,
    )

    page(
        "rentals.html",
        L("Huren", "Mieten", "Rentals", "Noleggio", "Kiralama", "Alquiler"),
        L(
            "Op Kos huur je fiets, scooter, auto, buggy, quad of een boot. De gids noemde geen vaste prijzen, die hangen van het seizoen af.",
            "Auf Kos mietest du Fahrrad, Roller, Auto, Buggy, Quad oder ein Boot. Der Guide nannte keine festen Preise, sie hängen von der Saison ab.",
            "On Kos you can rent a bike, scooter, car, buggy, quad or a boat. The guide did not list fixed prices. They depend on the season.",
            "A Kos noleggi bici, scooter, auto, buggy, quad o una barca. La guida non indicava prezzi fissi: dipendono dalla stagione.",
            "Kos’ta bisiklet, scooter, araba, buggy, quad veya tekne kiralanır. Rehber sabit fiyat yazmadı; mevsime göre değişir.",
            "En Kos se alquila bici, scooter, coche, buggy, quad o barco. La guía no daba precios fijos: dependen de la temporada.",
        ),
        [
            (L("Wat je kunt huren", "Was du mieten kannst", "What you can rent", "Cosa puoi noleggiare", "Ne kiralayabilirsin", "Qué puedes alquilar"),
             L("Fiets, kinderfiets, elektrische fiets, tandem, mountainbike, scooter, buggy, quad, auto en boot. Boten vertrekken onder meer vanuit Kos-stad en Kardamena.",
               "Fahrrad, Kinderrad, E-Bike, Tandem, Mountainbike, Roller, Buggy, Quad, Auto und Boot. Boote legen unter anderem in Kos-Stadt und Kardamena ab.",
               "Bike, kids’ bike, e-bike, tandem, mountain bike, scooter, buggy, quad, car and boat. Boats leave from Kos town and Kardamena, among other places.",
               "Bici, bici per bambini, e-bike, tandem, mountain bike, scooter, buggy, quad, auto e barca. Le barche partono tra l’altro da Kos città e Kardamena.",
               "Bisiklet, çocuk bisikleti, elektrikli bisiklet, tandem, dağ bisikleti, scooter, buggy, quad, araba ve tekne. Tekneler Kos şehri ve Kardamena’dan da kalkar.",
               "Bici, bici infantil, bici eléctrica, tándem, montaña, scooter, buggy, quad, coche y barco. Hay barcos desde la ciudad de Kos y Kardamena.")),
            (L("Voor je tekent", "Bevor du unterschreibst", "Before you sign", "Prima di firmare", "İmzalamadan önce", "Antes de firmar"),
             L("Controleer remmen, banden en of een helm bij de scooter zit. Lees de verzekering. Voor auto en scooter gelden rijbewijs en verkeersregels — die staan op aparte pagina’s. Verhuurders verbieden soms een onverharde weg, zoals het laatste stuk naar Cavo Paradiso.",
               "Prüfe Bremsen, Reifen und ob ein Helm beim Roller dabei ist. Lies die Versicherung. Für Auto und Roller gelten Führerschein und Verkehrsregeln — eigene Seiten. Vermieter verbieten manchmal eine Schotterpiste, etwa das letzte Stück nach Cavo Paradiso.",
               "Check brakes, tyres and whether a helmet comes with the scooter. Read the insurance. Cars and scooters need a licence and traffic rules — those have their own pages. Rental firms sometimes ban a dirt road, such as the last stretch to Cavo Paradiso.",
               "Controlla freni, gomme e se il casco è incluso con lo scooter. Leggi l’assicurazione. Per auto e scooter servono patente e regole — pagine dedicate. I noleggi a volte vietano una strada sterrata, come l’ultimo tratto per Cavo Paradiso.",
               "Frene, lastiğe ve scooter ile kask verilip verilmediğine bak. Sigortayı oku. Araba ve scooter için ehliyet ve trafik kuralları ayrı sayfalarda. Kiralama şirketleri bazen toprak yolu yasaklar, Cavo Paradiso’nun son kısmı gibi.",
               "Revisa frenos, ruedas y si el casco va con el scooter. Lee el seguro. Coche y scooter exigen carnet y normas — hay páginas aparte. A veces prohíben una pista, como el último tramo a Cavo Paradiso.")),
        ],
        [BADGE_CHECK, L("Rijbewijs", "Führerschein", "Licence", "Patente", "Ehliyet", "Carnet")],
        "rentals.jpg",
        "index.html", BACK_HOME, "Kos rental", NOTE_PRICE,
    )
    # add links inside rentals by a second section already there. Append link cards via extra paragraph in lead? I'll add a tiny links block by rewriting file after... 
    # Instead include links in the paragraph as HTML? data-i18n uses innerHTML so <a> works if I put them in the string.
    # Already written. I'll append links with a follow-up replace after all pages... do it here by not. The verkeersregels link is important. I'll patch the paragraph to include anchors in a later edit if needed.
    # I'll add them now by a dedicated small HTML snippet in note? Skip, user can use search. I'll add an extra section with plain text page names. Better: I'll include HTML links in p text since innerHTML is used.

    page(
        "wellness.html",
        L("Wellness & verzorging", "Wellness & Pflege", "Wellness & care", "Wellness e cura", "Wellness ve bakım", "Wellness y cuidado"),
        L(
            "Knippen, nagels, hamam en massage. De gids noemde deze zaken. Prijzen staan er niet bij.",
            "Schneiden, Nägel, Hamam und Massage. Der Guide nannte diese Betriebe. Preise standen nicht dabei.",
            "Hair, nails, hamam and massage. The guide named these places. It did not list prices.",
            "Capelli, unghie, hamam e massaggio. La guida citava questi posti. Non indicava i prezzi.",
            "Saç, tırnak, hamam ve masaj. Rehber bu yerleri sayıyordu. Fiyat yoktu.",
            "Pelo, uñas, hamam y masaje. La guía nombraba estos sitios. No ponía precios.",
        ),
        [
            (L("Op de lijst", "Auf der Liste", "On the list", "In elenco", "Listede", "En la lista"),
             L("Nsalon van Nikos Georgiadis (ook heren en baard), Giannis Nails, Artemis Hamam, Afrodite-massage en Touch of Beauty. Massages aan het strand staan bij de excursie Massage.",
               "Nsalon von Nikos Georgiadis (auch Herren und Bart), Giannis Nails, Artemis Hamam, Afrodite-Massage und Touch of Beauty. Strandmassagen stehen bei der Tour Massage.",
               "Nsalon by Nikos Georgiadis (including men and beard), Giannis Nails, Artemis Hamam, Afrodite massage and Touch of Beauty. Beach massages are on the Massage excursion page.",
               "Nsalon di Nikos Georgiadis (anche uomini e barba), Giannis Nails, Artemis Hamam, massaggio Afrodite e Touch of Beauty. I massaggi in spiaggia sono nella pagina Escursione massaggio.",
               "Nikos Georgiadis’in Nsalon’u (erkek ve sakal dahil), Giannis Nails, Artemis Hamam, Afrodite masajı ve Touch of Beauty. Plaj masajları Masaj turunda.",
               "Nsalon de Nikos Georgiadis (también hombres y barba), Giannis Nails, Artemis Hamam, masaje Afrodita y Touch of Beauty. Los masajes de playa están en la excursión Masaje.")),
        ],
        [BADGE_CHECK],
        "wellness.jpg",
        "index.html", BACK_HOME, "Kos wellness massage", NOTE_PRICE,
    )
    page(
        "praktische-winkels.html",
        L("Praktische winkels", "Praktische Läden", "Practical shops", "Negozi pratici", "Pratik dükkanlar", "Tiendas prácticas"),
        L(
            "Geen souvenirlijst, maar zaken die je nodig hebt als er iets stuk is of op is. Adressen zijn nog niet ingevuld.",
            "Keine Souvenirliste, sondern Läden, die du brauchst, wenn etwas kaputt oder alle ist. Adressen fehlen noch.",
            "Not a souvenir list. These are the shops you need when something breaks or runs out. Addresses are not filled in yet.",
            "Non è una lista di souvenir. Sono i negozi utili quando qualcosa si rompe o finisce. Gli indirizzi non ci sono ancora.",
            "Hediyelik listesi değil. Bir şey bozulunca veya bitince lazım olan dükkanlar. Adresler henüz yok.",
            "No es una lista de souvenirs. Son las tiendas útiles cuando algo se rompe o se acaba. Las direcciones aún no están.",
        ),
        [
            (L("Dagelijks", "Alltag", "Everyday", "Ogni giorno", "Günlük", "Día a día"),
             L("Supermarkt, markt, drogist, opticien, Vodafone, telefoonreparatie (iRepair), dierenwinkel Zootopia, visspullen (Saltylife), sleutelmaker, schoenmaker, kledingreparatie en babyspullen.",
               "Supermarkt, Markt, Drogerie, Optiker, Vodafone, Handyreparatur (iRepair), Tierladen Zootopia, Angelshop (Saltylife), Schlüsseldienst, Schuster, Kleidungsreparatur und Babysachen.",
               "Supermarket, market, drugstore, optician, Vodafone, phone repair (iRepair), pet shop Zootopia, fishing shop (Saltylife), locksmith, cobbler, clothing repair and baby things.",
               "Supermercato, mercato, drogheria, ottico, Vodafone, riparazione telefoni (iRepair), pet shop Zootopia, pesca (Saltylife), chiavi, calzolaio, riparazione abiti e cose per bambini.",
               "Süpermarket, pazar, eczane/drogist, gözlükçü, Vodafone, telefon tamiri (iRepair), Zootopia pet shop, olta (Saltylife), çilingir, ayakkabıcı, giysi tamiri ve bebek eşyası.",
               "Supermercado, mercado, droguería, óptica, Vodafone, reparación de móviles (iRepair), tienda de mascotas Zootopia, pesca (Saltylife), cerrajero, zapatero, arreglos de ropa y cosas de bebé.")),
            (L("Parfum en printen", "Parfum und Drucken", "Perfume and printing", "Profumo e stampe", "Parfüm ve baskı", "Perfume e impresión"),
             L("Parfum en cosmetica: Honduros, Milva Galerie en Myrenia. Verder een print- en boekwinkel, handgemaakte sandalen (Elli), Jeans Center, Interspot en E-clik.",
               "Parfum und Kosmetik: Honduros, Milva Galerie und Myrenia. Dazu Druck- und Buchladen, handgemachte Sandalen (Elli), Jeans Center, Interspot und E-clik.",
               "Perfume and cosmetics: Honduros, Milva Galerie and Myrenia. Also a print and book shop, handmade sandals (Elli), Jeans Center, Interspot and E-clik.",
               "Profumo e cosmetici: Honduros, Milva Galerie e Myrenia. Anche stampa e libreria, sandali fatti a mano (Elli), Jeans Center, Interspot ed E-clik.",
               "Parfüm ve kozmetik: Honduros, Milva Galerie ve Myrenia. Ayrıca baskı ve kitapçı, el yapımı sandal (Elli), Jeans Center, Interspot ve E-clik.",
               "Perfume y cosmética: Honduros, Milva Galerie y Myrenia. También imprenta y librería, sandalias hechas a mano (Elli), Jeans Center, Interspot y E-clik.")),
        ],
        [L("Kos-stad", "Kos-Stadt", "Kos town", "Città di Kos", "Kos şehri", "Ciudad de Kos"), BADGE_CHECK],
        "praktische-winkels.jpg",
        "index.html", BACK_HOME, "Kos town shops",
        L(
            "Straat en huisnummer per winkel zijn nog niet ingevuld.",
            "Straße und Hausnummer pro Laden sind noch nicht eingetragen.",
            "Street and number for each shop are not filled in yet.",
            "Via e numero di ogni negozio non sono ancora inseriti.",
            "Her dükkanın sokağı ve numarası henüz yok.",
            "La calle y el número de cada tienda aún no están.",
        ),
    )

    # The first bars hub() call was overwritten by page(). Good, only page remains.
    # I accidentally called hub() then page() for bars. page() overwrites. OK.

    write_food()
    write_sights()
    write_beaches()
    write_excursions()
    write_help()
    write_wjd()
    write_walk()
    print("done pages")


def write_food():
    page(
        "beste-gyros.html",
        L("Beste gyros", "Bester Gyros", "Best gyros", "Miglior gyros", "En iyi gyros", "Mejor gyros"),
        L("Gyros is pita met vlees van de spies. Twee zaken die de gids in Kos-stad noemde, hebben al een eigen pagina.",
          "Gyros ist Pita mit Fleisch vom Spieß. Zwei Läden, die der Guide in Kos-Stadt nannte, haben schon eine eigene Seite.",
          "Gyros is pita with meat from the spit. Two places the guide named in Kos town already have their own page.",
          "Il gyros è pita con carne allo spiedo. Due locali citati in città hanno già una pagina.",
          "Gyros, şişten etle pita. Rehberin Kos şehrinde saydığı iki yerin sayfası var.",
          "El gyros es pita con carne del asador. Dos sitios de la guía en la ciudad ya tienen página."),
        [(L("Waarheen", "Wohin", "Where", "Dove", "Nereye", "Dónde"),
          L("Kostasken en O Nikos Grill staan in deze gids. Hoe een gyros in elkaar zit, lees je bij Wist je dat.",
            "Kostasken und O Nikos Grill stehen in diesem Guide. Wie ein Gyros aufgebaut ist, steht unter Wusstest du.",
            "Kostasken and O Nikos Grill are in this guide. How a gyros is built is under Did you know.",
            "Kostasken e O Nikos Grill sono in questa guida. Com’è fatto un gyros è sotto Lo sapevi.",
            "Kostasken ve O Nikos Grill bu rehberde. Gyrosun yapısı Biliyor muydun altında.",
            "Kostasken y O Nikos Grill están en esta guía. Cómo es un gyros está en ¿Sabías que."))],
        [BADGE_TOWN, BADGE_CHECK],
        "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "gyros Kos town", NOTE_PRICE,
    )
    page(
        "beste-vis.html",
        L("Beste vis", "Bester Fisch", "Best fish", "Miglior pesce", "En iyi balık", "Mejor pescado"),
        L("De gids zette Barbouni en Nick the Fisherman bij de viszaken in Kos-stad. Barbouni heeft een pagina.",
          "Der Guide setzte Barbouni und Nick the Fisherman bei den Fischlokalen in Kos-Stadt. Barbouni hat eine Seite.",
          "The guide put Barbouni and Nick the Fisherman with the fish places in Kos town. Barbouni has a page.",
          "La guida metteva Barbouni e Nick the Fisherman tra i posti di pesce in città. Barbouni ha una pagina.",
          "Rehber Barbouni ve Nick the Fisherman’ı şehirdeki balıkçılara koydu. Barbouni’nin sayfası var.",
          "La guía ponía Barbouni y Nick the Fisherman entre los de pescado en la ciudad. Barbouni tiene página."),
        [(L("Vers", "Frisch", "Fresh", "Fresco", "Taze", "Fresco"),
          L("Vraag wat vandaag van de boot komt. De prijs hangt van de vangst af en staat hier niet vast.",
            "Frag, was heute vom Boot kommt. Der Preis hängt vom Fang ab und steht hier nicht fest.",
            "Ask what came off the boat today. The price depends on the catch and is not fixed here.",
            "Chiedi cosa è arrivato oggi dalla barca. Il prezzo dipende dalla pesca e non è fisso qui.",
            "Bugün tekneden ne geldiğini sor. Fiyat ava göre değişir, burada sabit değil.",
            "Pregunta qué llegó hoy del barco. El precio depende de la pesca y no está fijo aquí."))],
        [BADGE_TOWN], "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "fish restaurant Kos town", NOTE_PRICE,
    )
    page(
        "beste-sushi.html",
        L("Beste sushi", "Bestes Sushi", "Best sushi", "Miglior sushi", "En iyi suşi", "Mejor sushi"),
        L("Sushi op een Grieks eiland is geen klassieker, maar de gids noemde Barbouni, Nama en C Food & Mood.",
          "Sushi auf einer griechischen Insel ist kein Klassiker, aber der Guide nannte Barbouni, Nama und C Food & Mood.",
          "Sushi on a Greek island is not a classic, but the guide named Barbouni, Nama and C Food & Mood.",
          "Il sushi su un’isola greca non è un classico, ma la guida citava Barbouni, Nama e C Food & Mood.",
          "Yunan adasında suşi klasik değil, ama rehber Barbouni, Nama ve C Food & Mood’u saydı.",
          "El sushi en una isla griega no es lo clásico, pero la guía citaba Barbouni, Nama y C Food & Mood."),
        [(L("Let op", "Achtung", "Note", "Nota", "Not", "Ojo"),
          L("Of een zaak sushi én vis heeft, zie je op de kaart. Openingstijden zijn niet ingevuld.",
            "Ob ein Lokal Sushi und Fisch hat, steht auf der Karte. Öffnungszeiten fehlen.",
            "Whether a place does sushi and fish is on its menu. Opening hours are not filled in.",
            "Se un locale fa sushi e pesce lo vedi sul menu. Gli orari non ci sono.",
            "Bir yerin suşi ve balık yapıp yapmadığı menüde. Saatler yok.",
            "Si un sitio hace sushi y pescado se ve en la carta. Los horarios no están."))],
        [BADGE_TOWN], "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "sushi Kos", NOTE_PRICE,
    )
    page(
        "beste-ontbijt.html",
        L("Beste ontbijt", "Bestes Frühstück", "Best breakfast", "Miglior colazione", "En iyi kahvaltı", "Mejor desayuno"),
        L("Vroege zaken in Kos-stad, zoals de gids ze noemde. De tijden kunnen gewijzigd zijn.",
          "Frühe Lokale in Kos-Stadt, wie der Guide sie nannte. Die Zeiten können sich geändert haben.",
          "Early places in Kos town, as the guide named them. The times may have changed.",
          "Locali mattutini in città, come li citava la guida. Gli orari possono essere cambiati.",
          "Rehberin saydığı Kos şehrindeki erken yerler. Saatler değişmiş olabilir.",
          "Sitios tempranos en la ciudad, como los citaba la guía. Las horas pueden haber cambiado."),
        [(L("Volgens de gids", "Laut Guide", "According to the guide", "Secondo la guida", "Rehbere göre", "Según la guía"),
          L("Ariston vanaf 8:00 (ontbijt en uitzicht). Marina Cafe vanaf 7:00 (buffet). Costa Palace vanaf 6:30 (tosti). Het toastzaakje bij Agia Paraskevi vanaf 5:00. Gregory’s vanaf 6:30 (koffie en baguette). Coffee House vanaf 6:00.",
            "Ariston ab 8:00 (Frühstück und Blick). Marina Cafe ab 7:00 (Buffet). Costa Palace ab 6:30 (Toast). Der Toastladen bei Agia Paraskevi ab 5:00. Gregory’s ab 6:30 (Kaffee und Baguette). Coffee House ab 6:00.",
            "Ariston from 8:00 (breakfast and a view). Marina Cafe from 7:00 (buffet). Costa Palace from 6:30 (toast). The toast shop by Agia Paraskevi from 5:00. Gregory’s from 6:30 (coffee and baguette). Coffee House from 6:00.",
            "Ariston dalle 8:00 (colazione e vista). Marina Cafe dalle 7:00 (buffet). Costa Palace dalle 6:30 (toast). Il toast vicino ad Agia Paraskevi dalle 5:00. Gregory’s dalle 6:30 (caffè e baguette). Coffee House dalle 6:00.",
            "Ariston 8:00’den (kahvaltı ve manzara). Marina Cafe 7:00’den (büfe). Costa Palace 6:30’dan (tost). Agia Paraskevi’deki tostçu 5:00’ten. Gregory’s 6:30’dan (kahve ve baget). Coffee House 6:00’dan.",
            "Ariston desde las 8:00 (desayuno y vistas). Marina Cafe desde las 7:00 (bufé). Costa Palace desde las 6:30 (tostada). El sitio de tostadas junto a Agia Paraskevi desde las 5:00. Gregory’s desde las 6:30 (café y baguette). Coffee House desde las 6:00."))],
        [BADGE_TOWN, BADGE_CHECK], "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "breakfast Kos town", NOTE_PRICE,
    )
    page(
        "beste-koffie.html",
        L("Beste koffie", "Bester Kaffee", "Best coffee", "Miglior caffè", "En iyi kahve", "Mejor café"),
        L("De gids zocht koffie in de marina, het centrum en net buiten het centrum. Een vaste lijst met prijzen ontbreekt.",
          "Der Guide suchte Kaffee in der Marina, im Zentrum und knapp außerhalb. Eine feste Preisliste fehlt.",
          "The guide looked for coffee in the marina, the centre and just outside the centre. There is no fixed price list.",
          "La guida cercava il caffè in marina, in centro e appena fuori. Non c’è un listino fisso.",
          "Rehber kahveyi marinada, merkezde ve merkezin hemen dışında arıyordu. Sabit fiyat listesi yok.",
          "La guía buscaba café en la marina, el centro y justo fuera. No hay una lista de precios fija."),
        [(L("Tip", "Tipp", "Tip", "Consiglio", "İpucu", "Consejo"),
          L("Marina Cafe en Coffee House staan ook bij het ontbijt. Voor een kleine bestelling is een fooi van ongeveer een euro gebruikelijk.",
            "Marina Cafe und Coffee House stehen auch beim Frühstück. Bei einer kleinen Bestellung ist etwa ein Euro Trinkgeld üblich.",
            "Marina Cafe and Coffee House are also under breakfast. For a small order a tip of about one euro is usual.",
            "Marina Cafe e Coffee House sono anche sotto colazione. Per un ordine piccolo è normale circa un euro di mancia.",
            "Marina Cafe ve Coffee House kahvaltıda da var. Küçük bir siparişte yaklaşık bir euro bahşiş normaldir.",
            "Marina Cafe y Coffee House están también en el desayuno. En un pedido pequeño es habitual cerca de un euro de propina."))],
        [BADGE_TOWN], "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "coffee Kos town", NOTE_PRICE,
    )
    page(
        "beste-broodjes.html",
        L("Beste broodjes", "Beste Brote", "Best sandwiches", "Migliori panini", "En iyi sandviç", "Mejores bocadillos"),
        L("Broodjes in de marina en in het centrum. De gids noemde Marina en Coffee House.",
          "Brote in der Marina und im Zentrum. Der Guide nannte Marina und Coffee House.",
          "Sandwiches in the marina and in the centre. The guide named Marina and Coffee House.",
          "Panini in marina e in centro. La guida citava Marina e Coffee House.",
          "Marina ve merkezde sandviç. Rehber Marina ve Coffee House’u saydı.",
          "Bocadillos en la marina y en el centro. La guía citaba Marina y Coffee House."),
        [(L("Eten", "Essen", "Food", "Cibo", "Yemek", "Comida"),
          L("Neem iets mee voor onderweg als je vroeg naar het strand gaat. Prijzen staan niet in deze gids.",
            "Nimm etwas mit, wenn du früh an den Strand fährst. Preise stehen nicht in diesem Guide.",
            "Take something if you leave early for the beach. Prices are not in this guide.",
            "Porta qualcosa se parti presto per la spiaggia. I prezzi non sono in questa guida.",
            "Plaja erken çıkıyorsan bir şey al. Fiyatlar bu rehberde yok.",
            "Llévate algo si sales pronto a la playa. Los precios no están en esta guía."))],
        [BADGE_TOWN], "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "sandwich Kos town", NOTE_PRICE,
    )
    page(
        "beste-vegan.html",
        L("Vegan & vegetarisch", "Vegan & vegetarisch", "Vegan & vegetarian", "Vegano e vegetariano", "Vegan ve vejetaryen", "Vegano y vegetariano"),
        L("Niet elke taverne heeft een vegan kaart. De gids noemde N-Joy en Exantas in Kos-stad.",
          "Nicht jede Taverne hat eine vegane Karte. Der Guide nannte N-Joy und Exantas in Kos-Stadt.",
          "Not every taverna has a vegan menu. The guide named N-Joy and Exantas in Kos town.",
          "Non ogni taverna ha un menu vegano. La guida citava N-Joy ed Exantas in città.",
          "Her taverna vegan menü vermez. Rehber şehirde N-Joy ve Exantas’ı saydı.",
          "No toda taberna tiene carta vegana. La guía citaba N-Joy y Exantas en la ciudad."),
        [(L("Vragen", "Fragen", "Ask", "Chiedere", "Sormak", "Preguntar"),
          L("Vraag of de olie en de salade zonder kaas zijn. Exantas heeft een eigen pagina. N-Joy staat ook bij de zwerfkatten, omdat de zaak katten helpt steriliseren.",
            "Frag, ob Öl und Salat ohne Käse sind. Exantas hat eine eigene Seite. N-Joy steht auch bei den Streunern, weil das Lokal Katzen kastrieren hilft.",
            "Ask if the oil and salad are without cheese. Exantas has its own page. N-Joy is also with the stray cats, because the place helps sterilise cats.",
            "Chiedi se olio e insalata sono senza formaggio. Exantas ha una pagina. N-Joy è anche con i randagi, perché il locale aiuta a sterilizzare i gatti.",
            "Yağ ve salatanın peynirsiz olup olmadığını sor. Exantas’ın sayfası var. N-Joy sokak kedilerinde de geçer, çünkü kedi kısırlaştırmaya yardım eder.",
            "Pregunta si el aceite y la ensalada van sin queso. Exantas tiene página. N-Joy sale también con los gatos callejeros, porque el local ayuda a esterilizarlos."))],
        [BADGE_TOWN], "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "vegan restaurant Kos", NOTE_PRICE,
    )
    page(
        "beste-crepes.html",
        L("Beste pannenkoeken", "Beste Crêpes", "Best crêpes", "Migliori crêpe", "En iyi krep", "Mejores crepes"),
        L("De gids noemde crêpes in Kos-stad, onder meer Crepa Crepa. Een prijslijst staat er niet bij.",
          "Der Guide nannte Crêpes in Kos-Stadt, unter anderem Crepa Crepa. Eine Preisliste fehlt.",
          "The guide named crêpes in Kos town, including Crepa Crepa. There is no price list.",
          "La guida citava le crêpe in città, tra cui Crepa Crepa. Non c’è un listino.",
          "Rehber şehirde krep saydı, Crepa Crepa dahil. Fiyat listesi yok.",
          "La guía citaba crepes en la ciudad, entre ellas Crepa Crepa. No hay lista de precios."),
        [(L("Zoet of hartig", "Süß oder herzhaft", "Sweet or savoury", "Dolce o salato", "Tatlı veya tuzlu", "Dulce o salado"),
          L("Je kunt zoet of hartig nemen. Vraag wat er die dag op de plaat gaat.",
            "Du kannst süß oder herzhaft nehmen. Frag, was an dem Tag auf die Platte kommt.",
            "You can go sweet or savoury. Ask what is on the iron that day.",
            "Puoi scegliere dolce o salato. Chiedi cosa c’è quel giorno sulla piastra.",
            "Tatlı veya tuzlu seçebilirsin. O gün tavada ne olduğuna sor.",
            "Puedes elegir dulce o salado. Pregunta qué hay ese día en la plancha."))],
        [BADGE_TOWN], "beste-lekkerste.jpg", "beste-lekkerste.html", BACK_FOOD, "crepes Kos town", NOTE_PRICE,
    )
    page(
        "restaurant-vegan.html",
        L("N-Joy", "N-Joy", "N-Joy", "N-Joy", "N-Joy", "N-Joy"),
        L("Vegetarische en vegan gerechten in Kos-stad. De gids noemde ook dat de Nederlandse uitbaatster Nicolle zwerfkatten laat steriliseren.",
          "Vegetarische und vegane Gerichte in Kos-Stadt. Der Guide schrieb auch, dass die niederländische Wirtin Nicolle Streunerkatzen kastrieren lässt.",
          "Vegetarian and vegan dishes in Kos town. The guide also said the Dutch owner Nicolle has stray cats sterilised.",
          "Piatti vegetariani e vegani in città. La guida diceva anche che la titolare olandese Nicolle fa sterilizzare i gatti randagi.",
          "Kos şehrinde vejetaryen ve vegan yemekler. Rehber, Hollandalı işletmeci Nicolle’in sokak kedilerini kısırlaştırdığını da yazdı.",
          "Platos vegetarianos y veganos en la ciudad. La guía también decía que la dueña holandesa Nicolle esteriliza gatos callejeros."),
        [(L("Eten", "Essen", "Food", "Cibo", "Yemek", "Comida"),
          L("Vraag wat er vegan is, ook bij sauzen. Openingstijden en het adres zijn hier niet ingevuld.",
            "Frag, was vegan ist, auch bei den Saucen. Öffnungszeiten und Adresse fehlen hier.",
            "Ask what is vegan, including the sauces. Opening hours and the address are not filled in here.",
            "Chiedi cosa è vegano, anche nelle salse. Orari e indirizzo non sono inseriti.",
            "Soslar dahil neyin vegan olduğunu sor. Saat ve adres burada yok.",
            "Pregunta qué es vegano, también en las salsas. Horario y dirección no están aquí."))],
        [BADGE_TOWN, L("Vegan", "Vegan", "Vegan", "Vegano", "Vegan", "Vegano")],
        "beste-lekkerste.jpg", "beste-vegan.html", BACK_FOOD, "N-Joy Kos", NOTE_PRICE,
    )
    # cocktails and ice: short pages
    cocktails = [
        ("cocktail-c-food-mood.html", "C Food & Mood", "Strandrestaurant met cocktails. Er is ook een strandpagina."),
        ("cocktail-kaseta-caf.html", "Kaseta Café", "Café dat de gids bij de cocktails zette."),
        ("cocktail-sitar.html", "Sitar", "Sitar staat ook bij de clubs en nachtleven."),
        ("cocktail-soul-kitchen.html", "Soul Kitchen", "Soul Kitchen heeft ook een restaurantpagina."),
        ("cocktail-vie-caf.html", "Vie Café", "Vie stond bij de cocktailbars van Kos."),
        ("cocktail-mylos-beach-bar.html", "Mylos Beach Bar", "Beachbar bij Mylos. Er is ook een strandpagina."),
    ]
    # We'll write these with full translations in a compact loop using a translator table.
    cock_fact = {
        "cocktail-c-food-mood.html": (
            L("C Food & Mood", "C Food & Mood", "C Food & Mood", "C Food & Mood", "C Food & Mood", "C Food & Mood"),
            L("Strandzaak met eten en cocktails. Het strand heeft een eigen pagina.",
              "Strandlokal mit Essen und Cocktails. Der Strand hat eine eigene Seite.",
              "Beach place with food and cocktails. The beach has its own page.",
              "Locale in spiaggia con cibo e cocktail. La spiaggia ha una pagina.",
              "Yemek ve kokteylli plaj yeri. Plajın kendi sayfası var.",
              "Sitio de playa con comida y cócteles. La playa tiene su página."),
        ),
        "cocktail-kaseta-caf.html": (
            L("Kaseta Café", "Kaseta Café", "Kaseta Café", "Kaseta Café", "Kaseta Café", "Kaseta Café"),
            L("De gids zette Kaseta bij de cocktails. Het precieze adres is nog niet ingevuld.",
              "Der Guide setzte Kaseta bei die Cocktails. Die genaue Adresse fehlt noch.",
              "The guide put Kaseta with the cocktails. The exact address is not filled in yet.",
              "La guida metteva Kaseta tra i cocktail. L’indirizzo esatto non c’è ancora.",
              "Rehber Kaseta’yı kokteyllere koydu. Tam adres henüz yok.",
              "La guía ponía Kaseta entre los cócteles. La dirección exacta aún no está."),
        ),
        "cocktail-sitar.html": (
            L("Sitar", "Sitar", "Sitar", "Sitar", "Sitar", "Sitar"),
            L("Sitar staat in de gids bij cocktails én bij de clubs.",
              "Sitar steht im Guide bei Cocktails und bei den Clubs.",
              "Sitar is in the guide under cocktails and under the clubs.",
              "Sitar è nella guida sotto i cocktail e sotto i club.",
              "Sitar rehberde hem kokteyllerde hem kulüplerde.",
              "Sitar está en la guía en cócteles y en clubs."),
        ),
        "cocktail-soul-kitchen.html": (
            L("Soul Kitchen", "Soul Kitchen", "Soul Kitchen", "Soul Kitchen", "Soul Kitchen", "Soul Kitchen"),
            L("Cocktails en eten. De restaurantpagina vertelt meer over de zaak.",
              "Cocktails und Essen. Die Restaurantseite erzählt mehr.",
              "Cocktails and food. The restaurant page tells more about the place.",
              "Cocktail e cibo. La pagina del ristorante racconta di più.",
              "Kokteyl ve yemek. Restoran sayfası mekanı daha çok anlatır.",
              "Cócteles y comida. La página del restaurante cuenta más."),
        ),
        "cocktail-vie-caf.html": (
            L("Vie Café", "Vie Café", "Vie Café", "Vie Café", "Vie Café", "Vie Café"),
            L("Vie stond bij de cocktailbars. Openingstijden zijn niet ingevuld.",
              "Vie stand bei den Cocktailbars. Öffnungszeiten fehlen.",
              "Vie was listed with the cocktail bars. Opening hours are not filled in.",
              "Vie era tra i cocktail bar. Gli orari non ci sono.",
              "Vie kokteyl barlarındaydı. Saatler yok.",
              "Vie estaba entre las coctelerías. Los horarios no están."),
        ),
        "cocktail-mylos-beach-bar.html": (
            L("Mylos Beach Bar", "Mylos Beach Bar", "Mylos Beach Bar", "Mylos Beach Bar", "Mylos Beach Bar", "Mylos Beach Bar"),
            L("Beachbar bij Mylos, met cocktails en soms een feest. Het strand heeft een eigen pagina.",
              "Beachbar bei Mylos, mit Cocktails und manchmal einer Party. Der Strand hat eine eigene Seite.",
              "Beach bar at Mylos, with cocktails and sometimes a party. The beach has its own page.",
              "Beach bar a Mylos, con cocktail e a volte una festa. La spiaggia ha una pagina.",
              "Mylos’ta beach bar, kokteyl ve bazen parti. Plajın sayfası var.",
              "Beach bar en Mylos, con cócteles y a veces fiesta. La playa tiene página."),
        ),
    }
    for fn, (title, lead) in cock_fact.items():
        img = ensure_hero(fn, "bars-nightlife.jpg")
        page(fn, title, lead,
             [(L("Bestellen", "Bestellen", "Order", "Ordinare", "Sipariş", "Pedir"),
               L("Vraag wat er in het glas zit als je geen alcohol wilt. Prijzen wisselen.",
                 "Frag, was im Glas ist, wenn du keinen Alkohol willst. Preise wechseln.",
                 "Ask what is in the glass if you do not want alcohol. Prices change.",
                 "Chiedi cosa c’è nel bicchiere se non vuoi alcol. I prezzi cambiano.",
                 "Alkol istemezsen bardakta ne olduğuna sor. Fiyatlar değişir.",
                 "Pregunta qué lleva el vaso si no quieres alcohol. Los precios cambian."))],
             [BADGE_CHECK], img, "beste-cocktails.html", BACK_COCK, title["en"] + " Kos", NOTE_PRICE)

    ices = {
        "ijs-gelateria-carino.html": "Gelateria Carino",
        "ijs-special-kos.html": "Special Kos",
        "ijs-special-ijs-zipari.html": "Special Zipari",
        "ijs-special-kardamena.html": "Special Kardamena",
        "ijs-special-marina.html": "Special Marina",
    }
    where = {
        "ijs-gelateria-carino.html": L("Een ijssalon die de gids apart noemde.", "Eine Eisdiele, die der Guide extra nannte.", "A gelateria the guide named on its own.", "Una gelateria che la guida citava a parte.", "Rehberin ayrı saydığı bir dondurmacı.", "Una heladería que la guía citaba aparte."),
        "ijs-special-kos.html": L("Special in Kos-stad.", "Special in Kos-Stadt.", "Special in Kos town.", "Special in città di Kos.", "Kos şehrinde Special.", "Special en la ciudad de Kos."),
        "ijs-special-ijs-zipari.html": L("Special in Zipari, landinwaarts tussen Kos-stad en Tigaki.", "Special in Zipari, landeinwärts zwischen Kos-Stadt und Tigaki.", "Special in Zipari, inland between Kos town and Tigaki.", "Special a Zipari, nell’entroterra tra la città e Tigaki.", "Zipari’de Special, Kos şehri ile Tigaki arasında iç kesimde.", "Special en Zipari, tierra adentro entre la ciudad y Tigaki."),
        "ijs-special-kardamena.html": L("Special in Kardamena, aan de zuidkust.", "Special in Kardamena, an der Südküste.", "Special in Kardamena, on the south coast.", "Special a Kardamena, sulla costa sud.", "Güney kıyıda Kardamena’da Special.", "Special en Kardamena, en la costa sur."),
        "ijs-special-marina.html": L("Special bij de marina van Kos-stad.", "Special an der Marina von Kos-Stadt.", "Special by the marina of Kos town.", "Special alla marina della città.", "Kos şehri marinasında Special.", "Special junto a la marina de la ciudad."),
    }
    for fn, name in ices.items():
        title = L(name, name, name, name, name, name)
        img = ensure_hero(fn, "beste-lekkerste.jpg")
        page(fn, title, where[fn],
             [(L("IJs", "Eis", "Ice cream", "Gelato", "Dondurma", "Helado"),
               L("Smaken wisselen per dag. De prijs per bol staat niet in deze gids.",
                 "Sorten wechseln pro Tag. Der Preis pro Kugel steht nicht in diesem Guide.",
                 "Flavours change by the day. The price per scoop is not in this guide.",
                 "I gusti cambiano ogni giorno. Il prezzo a pallina non è in questa guida.",
                 "Çeşitler güne göre değişir. Top fiyatı bu rehberde yok.",
                 "Los sabores cambian cada día. El precio por bola no está en esta guía."))],
             [BADGE_CHECK], img, "beste-ijs.html", BACK_ICE, name + " Kos", NOTE_PRICE)


def write_sights():
    note_ticket = L(
        "De actuele entreeprijs en de openingstijden zijn nog niet ingevuld.",
        "Der aktuelle Eintritt und die Öffnungszeiten sind noch nicht eingetragen.",
        "The current ticket price and opening hours are not filled in yet.",
        "Il prezzo del biglietto e gli orari non sono ancora inseriti.",
        "Güncel bilet fiyatı ve saatler henüz yok.",
        "El precio de la entrada y los horarios aún no están.",
    )
    specs = []

    def add(fn, key, fallback, title, lead, sections, badges, maps, note=None):
        img = scrape_img(key, fn, fallback) if key else ensure_hero(fn, fallback)
        page(fn, title, lead, sections, badges, img, "bezienswaardigheden.html", BACK_SIGHT, maps, note)

    add("sight-asklepion.html", "asklepion", "bezienswaardigheden.jpg",
        L("Asklepion", "Asklepion", "Asklepion", "Asklepion", "Asklepion", "Asklepion"),
        L("Het oude genezingsoord buiten Kos-stad. Hippocrates is met deze plek verbonden. De eed die artsen nog afleggen, komt uit die traditie.",
          "Die alte Heilstätte außerhalb von Kos-Stadt. Hippokrates ist mit diesem Ort verbunden. Der Eid, den Ärzte noch leisten, kommt aus dieser Tradition.",
          "The ancient healing sanctuary outside Kos town. Hippocrates is tied to this place. The oath doctors still take comes from that tradition.",
          "L’antico santuario di guarigione fuori città. Ippocrate è legato a questo luogo. Il giuramento dei medici viene da quella tradizione.",
          "Kos şehri dışındaki antik şifa yeri. Hipokrat bu yerle bağlantılı. Hekimlerin hâlâ ettiği yemin o gelenekten gelir.",
          "El antiguo santuario de curación fuera de la ciudad. Hipócrates está ligado a este lugar. El juramento de los médicos viene de esa tradición."),
        [(L("Opgraving", "Ausgrabung", "Excavation", "Scavo", "Kazı", "Excavación"),
          L("Het terrein werd in 1902 aangewezen door de Kos-historicus Iakovos Zarraftis en vanaf 1904 blootgelegd door de Duitser Rudolf Herzog.",
            "Das Gelände wurde 1902 vom Kos-Historiker Iakovos Zarraftis ausgewiesen und ab 1904 vom Deutschen Rudolf Herzog freigelegt.",
            "The site was pointed out in 1902 by the Kos historian Iakovos Zarraftis and uncovered from 1904 by the German Rudolf Herzog.",
            "Il sito fu indicato nel 1902 dallo storico di Kos Iakovos Zarraftis e riportato alla luce dal 1904 dal tedesco Rudolf Herzog.",
            "Alan 1902’de Koslu tarihçi Iakovos Zarraftis tarafından gösterildi ve 1904’ten itibaren Alman Rudolf Herzog tarafından açıldı.",
            "El lugar fue señalado en 1902 por el historiador de Kos Iakovos Zarraftis y excavado desde 1904 por el alemán Rudolf Herzog.")),
         (L("Wat het was", "Was es war", "What it was", "Cos’era", "Ne idi", "Qué era"),
          L("Meer dan een tempel: ziekenhuis, kuuroord en leerschool tegelijk. In de slaapzalen liet men vroeger ongevaarlijke slangen rondlopen. Je loopt nu over dezelfde paden.",
            "Mehr als ein Tempel: Krankenhaus, Kurort und Schule zugleich. In den Schlafsälen ließ man früher ungiftige Schlangen laufen. Du gehst heute über dieselben Wege.",
            "More than a temple: hospital, spa and school at once. Harmless snakes used to be allowed in the sleeping halls. You walk the same paths now.",
            "Più di un tempio: ospedale, terme e scuola insieme. Nei dormitori si lasciavano serpenti non velenosi. Oggi cammini sugli stessi sentieri.",
            "Tapınaktan fazlası: hastane, kaplıca ve okul bir arada. Uyku salonlarında eskiden zehirsiz yılanlar dolaşırdı. Bugün aynı patikalarda yürürsün.",
            "Más que un templo: hospital, balneario y escuela a la vez. En los dormitorios dejaban serpientes no venenosas. Hoy caminas por los mismos senderos."))],
        [BADGE_FEE, L("Buiten de stad", "Außerhalb", "Outside town", "Fuori città", "Şehir dışı", "Fuera de la ciudad")],
        "Asklepion Kos", note_ticket)

    add("sight-paraskevi.html", "paraskevi", "bezienswaardigheden.jpg",
        L("Agia Paraskevi", "Agia Paraskevi", "Agia Paraskevi", "Agia Paraskevi", "Agia Paraskevi", "Agia Paraskevi"),
        L("Grote orthodoxe parochiekerk in het centrum. Na de aardbeving van 1933 bleef ze grotendeels staan. Na 2017 was ze dicht voor herstel en is ze weer open.",
          "Große orthodoxe Pfarrkirche im Zentrum. Nach dem Beben von 1933 blieb sie weitgehend stehen. Nach 2017 war sie zur Reparatur zu und ist wieder offen.",
          "Large Orthodox parish church in the centre. After the 1933 earthquake it mostly stayed standing. After 2017 it was closed for repairs and is open again.",
          "Grande chiesa parrocchiale ortodossa in centro. Dopo il terremoto del 1933 restò in gran parte in piedi. Dopo il 2017 fu chiusa per i lavori ed è di nuovo aperta.",
          "Merkezde büyük Ortodoks mahalle kilisesi. 1933 depreminden sonra büyük ölçüde ayakta kaldı. 2017’den sonra onarım için kapalıydı, yine açık.",
          "Gran iglesia parroquial ortodoxa en el centro. Tras el terremoto de 1933 quedó en pie en gran parte. Tras 2017 cerró por obras y ya está abierta."),
        [(L("Binnen", "Innen", "Inside", "Dentro", "İçeride", "Dentro"),
          L("Fresco’s en iconen, zilveren kroonluchters en een vloer van kiezelmozaïek. Veel mensen steken een kaarsje aan. Meestal open van de ochtend tot de avond. Wees stil als er een dienst is.",
            "Fresken und Ikonen, silberne Kronleuchter und ein Kieselmosaikboden. Viele zünden eine Kerze an. Meist von morgens bis abends offen. Sei still, wenn ein Gottesdienst ist.",
            "Frescoes and icons, silver chandeliers and a pebble-mosaic floor. Many people light a candle. Often open from morning until evening. Keep quiet if there is a service.",
            "Affreschi e icone, lampadari d’argento e un pavimento a mosaico di ciottoli. Molti accendono una candela. Spesso aperta da mattina a sera. Fai silenzio se c’è una funzione.",
            "Freskler ve ikonalar, gümüş avizeler ve çakıl mozaik zemin. Birçok kişi mum yakar. Çoğu zaman sabahtan akşama açık. Ayin varsa sessiz ol.",
            "Frescos e iconos, lámparas de plata y un suelo de mosaico de guijarros. Mucha gente enciende una vela. A menudo abierta de la mañana a la noche. Guarda silencio si hay oficio."))],
        [BADGE_FREE, BADGE_TOWN], "Agia Paraskevi Kos town", None)

    add("sight-zia.html", "zia", "wjd-zonsondergang.jpg",
        L("Zia", "Zia", "Zia", "Zia", "Zia", "Zia"),
        L("Bergdorp met ongeveer 150 inwoners. Steegjes met olijfolie, kruiden, zeep en handwerk. ’s Avonds komen mensen voor de zonsondergang, met zicht op zee, Kalymnos en Pserimos.",
          "Bergdorf mit etwa 150 Einwohnern. Gassen mit Olivenöl, Kräutern, Seife und Handwerk. Abends kommen Leute zum Sonnenuntergang, mit Blick aufs Meer, Kalymnos und Pserimos.",
          "Mountain village of about 150 people. Lanes with olive oil, herbs, soap and crafts. In the evening people come for the sunset, looking over the sea, Kalymnos and Pserimos.",
          "Villaggio di montagna con circa 150 abitanti. Vicoli con olio, erbe, sapone e artigianato. La sera si viene per il tramonto, sul mare, Kalymnos e Pserimos.",
          "Yaklaşık 150 kişilik dağ köyü. Zeytinyağı, ot, sabun ve el işi sokakları. Akşam gün batımı için gelinir; deniz, Kalymnos ve Pserimos görünür.",
          "Pueblo de montaña de unos 150 habitantes. Callejones con aceite, hierbas, jabón y artesanía. Por la tarde se viene al atardecer, con mar, Kálimnos y Pserimos."),
        [(L("Drukte", "Andrang", "Crowds", "Folla", "Kalabalık", "Gente"),
          L("Rond zonsondergang is de weg vol. Er is een aparte pagina over die zonsondergang en een over fietsen naar Zia. Het natuurpark ligt in hetzelfde dorp.",
            "Zum Sonnenuntergang ist die Straße voll. Es gibt eine eigene Seite dazu und eine über das Radfahren nach Zia. Der Naturpark liegt im selben Dorf.",
            "Around sunset the road is full. There is a separate page about that sunset and one about cycling to Zia. The nature park is in the same village.",
            "Al tramonto la strada è piena. C’è una pagina sul tramonto e una sul pedalare fino a Zia. Il parco naturale è nello stesso villaggio.",
            "Gün batımında yol dolar. Gün batımı ve Zia’ya bisiklet için ayrı sayfalar var. Doğa parkı aynı köyde.",
            "Al atardecer la carretera se llena. Hay una página del atardecer y otra de ir en bici a Zia. El parque natural está en el mismo pueblo."))],
        [BADGE_FREE, L("Berg", "Berg", "Mountain", "Montagna", "Dağ", "Montaña")],
        "Zia Kos", None)

    add("sight-natuurpark-zia.html", "natuur", "wjd-zonsondergang.jpg",
        L("Natuurpark Zia", "Naturpark Zia", "Zia nature park", "Parco naturale di Zia", "Zia doğa parkı", "Parque natural de Zia"),
        L("Klein park in Zia met bankjes, een paar hangmatten en een terrasje. Fijn met kinderen. De gids noemde een dagkaart, zodat je kunt lunchen in het dorp en later terugkomen.",
          "Kleiner Park in Zia mit Bänken, ein paar Hängematten und einer Terrasse. Schön mit Kindern. Der Guide nannte eine Tageskarte, damit du im Dorf essen und später zurückkommen kannst.",
          "Small park in Zia with benches, a few hammocks and a little terrace. Good with children. The guide mentioned a day ticket, so you can eat in the village and come back later.",
          "Piccolo parco a Zia con panchine, qualche amaca e un terrazzino. Bello con i bambini. La guida parlava di un biglietto giornaliero, così pranzi in paese e torni dopo.",
          "Zia’da banklar, birkaç hamak ve küçük bir teraslı park. Çocuklarla iyi. Rehber, köyde yemek yiyip sonra dönmek için günlük biletten söz etti.",
          "Parque pequeño en Zia con bancos, unas hamacas y una terraza. Bien con niños. La guía hablaba de un pase de día, para comer en el pueblo y volver después."),
        [(L("Bezoek", "Besuch", "Visit", "Visita", "Ziyaret", "Visita"),
          L("Het is een korte wandeling, geen grote dierentuin. Hoeveel de kaart kost, staat hier niet.",
            "Es ist ein kurzer Spaziergang, kein großer Zoo. Was die Karte kostet, steht hier nicht.",
            "It is a short walk, not a big zoo. What the ticket costs is not written here.",
            "È una passeggiata breve, non un grande zoo. Quanto costa il biglietto non è scritto qui.",
            "Kısa bir yürüyüş, büyük bir hayvanat bahçesi değil. Biletin fiyatı burada yok.",
            "Es un paseo corto, no un zoo grande. Lo que cuesta la entrada no está aquí."))],
        [BADGE_FEE, L("Zia", "Zia", "Zia", "Zia", "Zia", "Zia")],
        "Zia nature park Kos", note_ticket)

    add("sight-therma.html", "therma", "strand-therma-beach.html",
        L("Therma, warmwaterbron", "Therma, heiße Quelle", "Therma hot spring", "Therma, sorgente calda", "Therma sıcak su", "Therma, fuente caliente"),
        L("Gratis warmwaterbron aan het strand. Het water komt ondergronds van het vulkanische eiland Nisyros. Italianen vonden de bron in 1934. Het bekken wordt aan het begin van het seizoen in het strand gegraven.",
          "Kostenlose heiße Quelle am Strand. Das Wasser kommt unterirdisch von der Vulkaninsel Nisyros. Italiener fanden die Quelle 1934. Das Becken wird zu Saisonbeginn in den Strand gegraben.",
          "Free hot spring on the beach. The water comes underground from the volcanic island of Nisyros. Italians found the spring in 1934. The pool is dug into the beach at the start of the season.",
          "Sorgente calda gratuita sulla spiaggia. L’acqua arriva sottoterra dall’isola vulcanica di Nisyros. Gli italiani la trovarono nel 1934. La vasca si scava nella spiaggia a inizio stagione.",
          "Plajda ücretsiz sıcak su. Su, yer altından volkanik Nisyros adasından gelir. İtalyanlar kaynağı 1934’te buldu. Havuz sezon başında kuma kazılır.",
          "Fuente caliente gratis en la playa. El agua llega bajo tierra desde la isla volcánica de Nísiros. Los italianos la hallaron en 1934. La poza se excava en la playa al empezar la temporada."),
        [(L("Bezoek", "Besuch", "Visit", "Visita", "Ziyaret", "Visita"),
          L("Altijd open, geen kassa en geen douche. In de zomer is het midden op de dag heet en druk; ochtend of late middag is rustiger. De laatste klim is steil voor een fiets. Sommige mensen smeren de modder op hun gezicht. Het ziet eruit als een gat in het strand, niet als een spa.",
            "Immer offen, keine Kasse und keine Dusche. Im Sommer ist es mittags heiß und voll; Morgen oder später Nachmittag ist ruhiger. Die letzte Steigung ist steil fürs Rad. Manche schmieren den Schlamm ins Gesicht. Es sieht aus wie ein Loch im Strand, nicht wie ein Spa.",
            "Always open, no ticket desk and no shower. In summer midday is hot and busy; morning or late afternoon is calmer. The last climb is steep on a bike. Some people put the mud on their face. It looks like a hole in the beach, not a spa.",
            "Sempre aperta, senza cassa e senza doccia. D’estate a mezzogiorno è calda e piena; mattina o tardo pomeriggio è più calmo. L’ultima salita è ripida in bici. Qualcuno si mette il fango sul viso. Sembra un buco nella spiaggia, non una spa.",
            "Her zaman açık, gişe ve duş yok. Yazın öğlen sıcak ve kalabalık; sabah veya geç öğleden sonra daha sakin. Son tırmanış bisiklet için dik. Bazıları çamuru yüze sürer. Spa değil, kumda bir çukur gibi durur.",
            "Siempre abierta, sin taquilla ni ducha. En verano al mediodía hace calor y hay gente; mañana o tarde es más tranquilo. La última cuesta es dura en bici. Algunos se ponen el barro en la cara. Parece un hoyo en la playa, no un spa."))],
        [BADGE_FREE, L("24 uur", "24 Stunden", "24 hours", "24 ore", "24 saat", "24 horas")],
        "Embros Thermes Kos", None)

    add("sight-platani.html", "platani", "bezienswaardigheden.jpg",
        L("Platani", "Platani", "Platani", "Platani", "Platani", "Platani"),
        L("Dorp net buiten Kos-stad, naast het Asklepion. Christenen en moslims van Turkse afkomst wonen hier al eeuwen naast elkaar. Veel bewoners spreken nog Turks. De tavernes hebben vaak gerechten met die invloed.",
          "Dorf knapp außerhalb von Kos-Stadt, neben dem Asklepion. Christen und Muslime türkischer Herkunft leben hier seit Jahrhunderten nebeneinander. Viele sprechen noch Türkisch. Die Tavernen haben oft Gerichte mit diesem Einfluss.",
          "Village just outside Kos town, next to the Asklepion. Christians and Muslims of Turkish origin have lived side by side here for centuries. Many residents still speak Turkish. The tavernas often have dishes with that influence.",
          "Villaggio appena fuori città, accanto all’Asklepion. Cristiani e musulmani di origine turca vivono qui fianco a fianco da secoli. Molti parlano ancora turco. Le taverne hanno spesso piatti con quell’influenza.",
          "Kos şehrinin hemen dışında, Asklepion’un yanında köy. Hristiyanlar ve Türk kökenli Müslümanlar yüzyıllardır yan yana yaşar. Birçok kişi hâlâ Türkçe konuşur. Tavernelerde çoğu zaman bu etkiden yemekler vardır.",
          "Pueblo justo fuera de la ciudad, junto al Asklepion. Cristianos y musulmanes de origen turco viven aquí juntos desde hace siglos. Muchos aún hablan turco. Las tabernas suelen tener platos con esa influencia."),
        [(L("Erfgoed", "Erbe", "Heritage", "Memoria", "Miras", "Memoria"),
          L("Buiten het dorp ligt een Joodse begraafplaats. In 1944 werden de Joden van Kos via het eiland weggevoerd naar Auschwitz. Een kleine waterval ligt ook bij Platani.",
            "Außerhalb des Dorfs liegt ein jüdischer Friedhof. 1944 wurden die Juden von Kos über die Insel nach Auschwitz deportiert. Ein kleiner Wasserfall liegt auch bei Platani.",
            "Outside the village is a Jewish cemetery. In 1944 the Jews of Kos were deported via the island to Auschwitz. A small waterfall is also near Platani.",
            "Fuori dal villaggio c’è un cimitero ebraico. Nel 1944 gli ebrei di Kos furono deportati via l’isola ad Auschwitz. Vicino a Platani c’è anche una piccola cascata.",
            "Köyün dışında bir Yahudi mezarlığı var. 1944’te Kos Yahudileri ada üzerinden Auschwitz’e sürüldü. Platani yakınında küçük bir şelale de var.",
            "Fuera del pueblo hay un cementerio judío. En 1944 los judíos de Kos fueron deportados por la isla a Auschwitz. Cerca de Platani hay también una cascada pequeña."))],
        [BADGE_FREE, L("Dorp", "Dorf", "Village", "Villaggio", "Köy", "Pueblo")],
        "Platani Kos", None)

    add("sight-waterval-platani.html", "waterval", "bezienswaardigheden.jpg",
        L("Waterval bij Platani", "Wasserfall bei Platani", "Waterfall near Platani", "Cascata vicino a Platani", "Platani şelalesi", "Cascada cerca de Platani"),
        L("Kleine waterval bij het dorp Platani. Hoe hard het water loopt, hangt van het seizoen af. Gratis.",
          "Kleiner Wasserfall beim Dorf Platani. Wie stark das Wasser läuft, hängt von der Saison ab. Kostenlos.",
          "Small waterfall by the village of Platani. How hard the water runs depends on the season. Free.",
          "Piccola cascata vicino al villaggio di Platani. Quanta acqua scende dipende dalla stagione. Gratis.",
          "Platani köyünde küçük şelale. Suyun gücü mevsime bağlı. Ücretsiz.",
          "Cascada pequeña junto al pueblo de Platani. Cuánta agua baja depende de la temporada. Gratis."),
        [(L("Combineren", "Kombinieren", "Combine", "Abbinare", "Birleştir", "Combinar"),
          L("Het Asklepion en de tavernes van Platani liggen om de hoek. Neem schoenen die nat mogen worden.",
            "Asklepion und die Tavernen von Platani liegen um die Ecke. Nimm Schuhe, die nass werden dürfen.",
            "The Asklepion and the tavernas of Platani are around the corner. Wear shoes that can get wet.",
            "L’Asklepion e le taverne di Platani sono dietro l’angolo. Porta scarpe che possono bagnarsi.",
            "Asklepion ve Platani taverneleri hemen yakında. Islanabilecek ayakkabı giy.",
            "El Asklepion y las tabernas de Platani están a un paso. Lleva zapatos que puedan mojarse."))],
        [BADGE_FREE], "waterfall Platani Kos", None)

    add("sight-plaka.html", "plaka", "bezienswaardigheden.jpg",
        L("Plaka, pauwenbos", "Plaka, Pfauenwald", "Plaka peacock forest", "Plaka, bosco dei pavoni", "Plaka tavus ormanı", "Plaka, bosque de pavos"),
        L("Gratis bos bij Antimachia. Pauwen lopen er rond. Bij een beekje zie je soms schildpadden, en katten in de schaduw. Er is een korte verharde weg vanaf de hoofdweg.",
          "Kostenloser Wald bei Antimachia. Pfauen laufen herum. An einem Bach siehst du manchmal Schildkröten, und Katzen im Schatten. Es gibt eine kurze asphaltierte Straße von der Hauptstraße.",
          "Free forest near Antimachia. Peacocks walk around. By a stream you sometimes see tortoises, and cats in the shade. There is a short paved road off the main road.",
          "Bosco gratuito vicino ad Antimachia. I pavoni passeggiano. A un ruscello a volte vedi tartarughe, e gatti all’ombra. C’è una breve strada asfaltata dalla principale.",
          "Antimachia yakınında ücretsiz orman. Tavus kuşları dolaşır. Bir derede bazen kaplumbağa, gölgede kedi görürsün. Ana yoldan kısa asfalt bir yol var.",
          "Bosque gratis cerca de Antimachia. Hay pavos reales. Junto a un arroyo a veces ves tortugas, y gatos a la sombra. Hay un tramo corto asfaltado desde la carretera principal."),
        [(L("Piknik", "Picknick", "Picnic", "Picnic", "Piknik", "Picnic"),
          L("Er zijn bankjes. Neem water mee. Het kasteel en de molen van Antimachia liggen in dezelfde streek.",
            "Es gibt Bänke. Nimm Wasser mit. Burg und Mühle von Antimachia liegen in derselben Gegend.",
            "There are benches. Bring water. The castle and the windmill of Antimachia are in the same area.",
            "Ci sono panchine. Porta acqua. Castello e mulino di Antimachia sono nella stessa zona.",
            "Banklar var. Su götür. Antimachia kalesi ve değirmeni aynı yörede.",
            "Hay bancos. Lleva agua. El castillo y el molino de Antimachia están en la misma zona."))],
        [BADGE_FREE, L("Antimachia", "Antimachia", "Antimachia", "Antimachia", "Antimachia", "Antimachia")],
        "Plaka forest Kos", None)

    add("sight-cavo-paradiso.html", "cavo", "stranden.jpg",
        L("Cavo Paradiso", "Cavo Paradiso", "Cavo Paradiso", "Cavo Paradiso", "Cavo Paradiso", "Cavo Paradiso"),
        L("Westpunt bij Kefalos. Kliffen, helder water en weinig hotels. Het laatste stuk is een smalle onverharde weg. Verhuurders verbieden die vaak met een huurauto. Scooter, buggy of quad past beter. Op het strand is een klein barretje met parasols.",
          "Westspitze bei Kefalos. Klippen, klares Wasser und wenige Hotels. Das letzte Stück ist eine schmale Schotterpiste. Vermieter verbieten sie oft mit dem Mietwagen. Roller, Buggy oder Quad passt besser. Am Strand ist eine kleine Bar mit Schirmen.",
          "Western tip near Kefalos. Cliffs, clear water and few hotels. The last stretch is a narrow dirt road. Rental firms often ban it in a hire car. A scooter, buggy or quad fits better. On the beach there is a small bar with umbrellas.",
          "Punta ovest vicino a Kefalos. Scogliere, acqua limpida e pochi hotel. L’ultimo tratto è una sterrata stretta. I noleggi spesso la vietano con l’auto a noleggio. Meglio scooter, buggy o quad. In spiaggia c’è un piccolo bar con ombrelloni.",
          "Kefalos yakınında batı ucu. Uçurum, berrak su ve az otel. Son kısım dar toprak yol. Kiralama şirketleri bunu çoğu zaman kiralık arabayla yasaklar. Scooter, buggy veya quad daha uygun. Plajda şemsiyeli küçük bir bar var.",
          "Punta oeste cerca de Kéfalos. Acantilados, agua clara y pocos hoteles. El último tramo es una pista estrecha. Los alquileres suelen prohibirla con el coche de alquiler. Mejor scooter, buggy o quad. En la playa hay un bar pequeño con sombrillas."),
        [(L("Strand", "Strand", "Beach", "Spiaggia", "Plaj", "Playa"),
          L("Het strand zelf heeft een aparte pagina: Kavo Parediso.",
            "Der Strand selbst hat eine eigene Seite: Kavo Parediso.",
            "The beach itself has its own page: Kavo Parediso.",
            "La spiaggia ha una pagina: Kavo Parediso.",
            "Plajın kendi sayfası var: Kavo Parediso.",
            "La playa tiene su página: Kavo Parediso."))],
        [BADGE_FREE, L("Kefalos", "Kefalos", "Kefalos", "Kefalos", "Kefalos", "Kéfalos")],
        "Cavo Paradiso Kos", None)

    add("sight-kardamena.html", "kardamena", "stranden.jpg",
        L("Kardamena", "Kardamena", "Kardamena", "Kardamena", "Kardamena", "Kardamena"),
        L("Badplaats aan de zuidkust. Overdag strand, ’s avonds eten en uitgaan in de straatjes. Er zijn stukken met ligbedden en stillere stukken met alleen een handdoek.",
          "Badeort an der Südküste. Tagsüber Strand, abends Essen und Ausgehen in den Gassen. Es gibt Abschnitte mit Liegen und ruhigere nur mit Handtuch.",
          "Resort on the south coast. Beach by day, food and going out in the lanes at night. There are parts with sunbeds and quieter parts with just a towel.",
          "Località sulla costa sud. Spiaggia di giorno, cibo e uscita nei vicoli di sera. Ci sono tratti con lettini e tratti più quieti solo con l’asciugamano.",
          "Güney kıyıda tatil yeri. Gündüz plaj, akşam sokaklarda yemek ve çıkış. Şezlonglu kısımlar ve yalnız havlulu sakin kısımlar var.",
          "Localidad en la costa sur. Playa de día, comida y salir por los callejones de noche. Hay tramos con hamacas y tramos más quietos solo con toalla."),
        [(L("Verder", "Weiter", "More", "Altro", "Devamı", "Más"),
          L("Er is geen volledig ziekenhuis. Bij spoed bel je 112 of 166. Het strand heeft een eigen pagina.",
            "Es gibt kein volles Krankenhaus. Im Notfall rufst du 112 oder 166. Der Strand hat eine eigene Seite.",
            "There is no full hospital. In an emergency call 112 or 166. The beach has its own page.",
            "Non c’è un ospedale completo. In emergenza chiama il 112 o il 166. La spiaggia ha una pagina.",
            "Tam bir hastane yok. Acilde 112 veya 166’yı ara. Plajın sayfası var.",
            "No hay un hospital completo. En emergencia llama al 112 o al 166. La playa tiene página."))],
        [BADGE_FREE, L("Zuidkust", "Südküste", "South coast", "Costa sud", "Güney kıyı", "Costa sur")],
        "Kardamena Kos", None)

    add("sight-tigaki.html", "tigaki", "stranden.jpg",
        L("Tigaki", "Tigaki", "Tigaki", "Tigaki", "Tigaki", "Tigaki"),
        L("Lang zandstrand aan de noordkust, stiller dan Kos-stad. Delen met ligbedden en delen onder de bomen. Naast het dorp ligt het zoutmeer Alykes, een Natura 2000-gebied. Vroeger werd hier zout gewonnen. Er is wind voor wind- en kitesurfen.",
          "Langer Sandstrand an der Nordküste, ruhiger als Kos-Stadt. Abschnitte mit Liegen und unter Bäumen. Neben dem Dorf liegt der Salzsee Alykes, ein Natura-2000-Gebiet. Früher wurde hier Salz gewonnen. Es gibt Wind zum Wind- und Kitesurfen.",
          "Long sandy beach on the north coast, calmer than Kos town. Parts with sunbeds and parts under the trees. Next to the village is the Alykes salt lake, a Natura 2000 site. Salt used to be taken here. There is wind for windsurfing and kitesurfing.",
          "Lunga spiaggia di sabbia sulla costa nord, più calma della città. Tratti con lettini e sotto gli alberi. Accanto al villaggio c’è il lago salato Alykes, sito Natura 2000. Un tempo si raccoglieva il sale. C’è vento per windsurf e kitesurf.",
          "Kuzey kıyıda uzun kumsal, Kos şehrinden daha sakin. Şezlonglu ve ağaç altı kısımlar var. Köyün yanında Natura 2000 alanı Alykes tuz gölü var. Eskiden tuz çıkarılırdı. Rüzgar sörfü ve kite için rüzgar olur.",
          "Playa larga de arena en la costa norte, más tranquila que la ciudad. Tramos con hamacas y bajo los árboles. Junto al pueblo está el lago salado de Alykes, zona Natura 2000. Antes se sacaba sal. Hay viento para windsurf y kitesurf."),
        [(L("Verder", "Weiter", "More", "Altro", "Devamı", "Más"),
          L("Het zoutmeer met flamingo’s heeft een eigen pagina, net als het strand.",
            "Der Salzsee mit Flamingos hat eine eigene Seite, genau wie der Strand.",
            "The salt lake with flamingos has its own page, as does the beach.",
            "Il lago salato con i fenicotteri ha una pagina, come la spiaggia.",
            "Flamingolu tuz gölünün sayfası var, plajın da.",
            "El lago salado con flamencos tiene página, igual que la playa."))],
        [BADGE_FREE, L("Noordkust", "Nordküste", "North coast", "Costa nord", "Kuzey kıyı", "Costa norte")],
        "Tigaki Kos", None)

    add("sight-marmari.html", "marmari", "stranden.jpg",
        L("Marmari", "Marmari", "Marmari", "Marmari", "Marmari", "Marmari"),
        L("Zandstrand en dorp aan de noordkust, tussen Tigaki en Mastichari. Paardrijden op het strand en rond het zoutmeer vertrekt hier in de buurt.",
          "Sandstrand und Dorf an der Nordküste, zwischen Tigaki und Mastichari. Ausritte am Strand und um den Salzsee starten hier in der Nähe.",
          "Sandy beach and village on the north coast, between Tigaki and Mastichari. Horse riding on the beach and around the salt lake starts near here.",
          "Spiaggia di sabbia e villaggio sulla costa nord, tra Tigaki e Mastichari. Le passeggiate a cavallo sulla spiaggia e intorno al lago salato partono qui vicino.",
          "Tigaki ile Mastichari arasında kuzey kıyıda kumsal ve köy. Plajda ve tuz gölü çevresinde at binme buradan başlar.",
          "Playa de arena y pueblo en la costa norte, entre Tigaki y Mastichari. Los paseos a caballo por la playa y el lago salado salen cerca de aquí."),
        [(L("Strand", "Strand", "Beach", "Spiaggia", "Plaj", "Playa"),
          L("Het strand heeft een eigen pagina.",
            "Der Strand hat eine eigene Seite.",
            "The beach has its own page.",
            "La spiaggia ha una pagina.",
            "Plajın sayfası var.",
            "La playa tiene página."))],
        [BADGE_FREE, L("Noordkust", "Nordküste", "North coast", "Costa nord", "Kuzey kıyı", "Costa norte")],
        "Marmari Kos", None)

    add("sight-mastichari.html", "mastichari", "stranden.jpg",
        L("Mastichari", "Mastichari", "Mastichari", "Mastichari", "Mastichari", "Mastichari"),
        L("Vissersdorp aan de noordkust met een lang strand en een veerboot naar Kalymnos. De gids noemde een Blauwe Vlag voor het strand. Er is wind voor wind- en kitesurfen. Lido Waterpark ligt in de buurt.",
          "Fischerdorf an der Nordküste mit langem Strand und einer Fähre nach Kalymnos. Der Guide nannte eine Blaue Flagge für den Strand. Es gibt Wind zum Wind- und Kitesurfen. Lido Waterpark liegt in der Nähe.",
          "Fishing village on the north coast with a long beach and a ferry to Kalymnos. The guide mentioned a Blue Flag for the beach. There is wind for windsurfing and kitesurfing. Lido Waterpark is nearby.",
          "Villaggio di pescatori sulla costa nord con una lunga spiaggia e un traghetto per Kalymnos. La guida citava una Bandiera Blu per la spiaggia. C’è vento per windsurf e kitesurf. Lido Waterpark è vicino.",
          "Kuzey kıyıda uzun plajlı ve Kalymnos feribotlu balıkçı köyü. Rehber plaj için Mavi Bayrak’tan söz etti. Rüzgar sörfü ve kite için rüzgar var. Lido Waterpark yakın.",
          "Pueblo pesquero en la costa norte con playa larga y ferry a Kálimnos. La guía citaba una Bandera Azul para la playa. Hay viento para windsurf y kitesurf. Lido Waterpark está cerca."),
        [(L("Kustpad", "Küstenweg", "Coast path", "Sentiero", "Kıyı yolu", "Sendero"),
          L("Er zijn lage duinen en een pad langs de kust, naast drukkere stukken met bars.",
            "Es gibt niedrige Dünen und einen Weg an der Küste, neben belebteren Abschnitten mit Bars.",
            "There are low dunes and a path along the coast, next to busier parts with bars.",
            "Ci sono dune basse e un sentiero lungo la costa, accanto a tratti più animati con bar.",
            "Alçak kum tepeleri ve kıyı boyunca bir patika var, barlı kalabalık kısımların yanında.",
            "Hay dunas bajas y un camino por la costa, junto a tramos más animados con bares."))],
        [BADGE_FREE, L("Veerboot", "Fähre", "Ferry", "Traghetto", "Feribot", "Ferry")],
        "Mastichari Kos", None)

    add("sight-limnionas.html", "limnionas", "stranden.jpg",
        L("Limnionas", "Limnionas", "Limnionas", "Limnionas", "Limnionas", "Limnionas"),
        L("Kleine beschutte baai bij Kefalos. Het water is helder, geschikt om te zwemmen en te snorkelen. De rotsen houden de baai rustig.",
          "Kleine geschützte Bucht bei Kefalos. Das Wasser ist klar, gut zum Schwimmen und Schnorcheln. Die Felsen halten die Bucht ruhig.",
          "Small sheltered bay near Kefalos. The water is clear, good for swimming and snorkelling. The rocks keep the bay calm.",
          "Piccola baia riparata vicino a Kefalos. L’acqua è limpida, buona per nuotare e fare snorkeling. Le rocce tengono la baia calma.",
          "Kefalos yakınında küçük korunaklı koy. Su berrak, yüzmek ve şnorkel için iyi. Kayalar koyu sakin tutar.",
          "Cala pequeña y resguardada cerca de Kéfalos. El agua es clara, buena para nadar y hacer esnórquel. Las rocas mantienen la cala en calma."),
        [(L("Strand", "Strand", "Beach", "Spiaggia", "Plaj", "Playa"),
          L("De strandpagina van Limnionas vertelt hetzelfde vanuit het water.",
            "Die Strandseite von Limnionas erzählt dasselbe vom Wasser aus.",
            "The Limnionas beach page tells the same thing from the water.",
            "La pagina spiaggia di Limnionas racconta lo stesso dall’acqua.",
            "Limnionas plaj sayfası aynı şeyi sudan anlatır.",
            "La página de playa de Limnionas cuenta lo mismo desde el agua."))],
        [BADGE_FREE, L("Kefalos", "Kefalos", "Kefalos", "Kefalos", "Kefalos", "Kéfalos")],
        "Limnionas beach Kos", None)


def write_beaches():
    rows = [
        ("strand-mylos-beach.html", "Mylos Beach",
         L("Strand met beachbar bij Kos-stad. Cocktails en soms een feest. Er is een aparte barpagina.",
           "Strand mit Beachbar bei Kos-Stadt. Cocktails und manchmal eine Party. Es gibt eine eigene Barseite.",
           "Beach with a beach bar near Kos town. Cocktails and sometimes a party. There is a separate bar page.",
           "Spiaggia con beach bar vicino alla città. Cocktail e a volte una festa. C’è una pagina del bar.",
           "Kos şehri yakınında beach barlı plaj. Kokteyl ve bazen parti. Barın ayrı sayfası var.",
           "Playa con beach bar cerca de la ciudad. Cócteles y a veces fiesta. Hay una página del bar.")),
        ("strand-c-food-mood-beach.html", "C Food & Mood",
         L("Strand met restaurant. De zaak staat ook bij de cocktails.",
           "Strand mit Restaurant. Das Lokal steht auch bei den Cocktails.",
           "Beach with a restaurant. The place is also listed under cocktails.",
           "Spiaggia con ristorante. Il locale è anche sotto i cocktail.",
           "Restoranlı plaj. Mekan kokteyllerde de var.",
           "Playa con restaurante. El sitio está también en cócteles.")),
        ("strand-aqua-blue-beach.html", "Aqua Blue",
         L("Strand dat de gids apart op de kaart zette. Ligbedden en prijzen wisselen.",
           "Strand, den der Guide extra auf die Karte setzte. Liegen und Preise wechseln.",
           "A beach the guide put on the map on its own. Sunbeds and prices change.",
           "Spiaggia che la guida metteva a parte sulla mappa. Lettini e prezzi cambiano.",
           "Rehberin haritaya ayrı koyduğu plaj. Şezlong ve fiyat değişir.",
           "Playa que la guía puso aparte en el mapa. Hamacas y precios cambian.")),
        ("strand-amos-beach.html", "Amos Beach",
         L("Strand met bar. Amos stond ook bij de strandfeesten.",
           "Strand mit Bar. Amos stand auch bei den Strandpartys.",
           "Beach with a bar. Amos was also listed with the beach parties.",
           "Spiaggia con bar. Amos era anche tra le feste in spiaggia.",
           "Barlı plaj. Amos plaj partilerinde de vardı.",
           "Playa con bar. Amos estaba también en las fiestas de playa.")),
        ("strand-agios-fokas.html", "Agios Fokas",
         L("Strand ten oosten van Kos-stad, op weg naar de warmwaterbron van Therma.",
           "Strand östlich von Kos-Stadt, auf dem Weg zur heißen Quelle von Therma.",
           "Beach east of Kos town, on the way to the Therma hot spring.",
           "Spiaggia a est della città, sulla strada per la sorgente di Therma.",
           "Kos şehrinin doğusunda, Therma sıcak suyuna giderken plaj.",
           "Playa al este de la ciudad, de camino a la fuente de Therma.")),
        ("strand-tam-tam-beach.html", "Tam Tam",
         L("Strand dat de gids bij de noordkust zette, bij Tigaki.",
           "Strand, den der Guide an die Nordküste setzte, bei Tigaki.",
           "A beach the guide placed on the north coast, by Tigaki.",
           "Spiaggia che la guida metteva sulla costa nord, verso Tigaki.",
           "Rehberin kuzey kıyıya, Tigaki tarafına koyduğu plaj.",
           "Playa que la guía ponía en la costa norte, hacia Tigaki.")),
        ("strand-naaktstrand-tigaki.html", "Naaktstrand Tigaki",
         L("Rustiger stuk bij Tigaki waar mensen soms zonder kleding zwemmen. Het is niet overal een officieel naaktstrand. Wees netjes tegen wie dat niet wil.",
           "Ruhigerer Abschnitt bei Tigaki, wo Leute manchmal ohne Kleidung schwimmen. Es ist nicht überall ein offizieller FKK-Strand. Sei höflich zu denen, die das nicht wollen.",
           "A quieter stretch by Tigaki where people sometimes swim without clothes. It is not an official naturist beach everywhere. Be polite to people who do not want that.",
           "Tratto più quieto verso Tigaki dove a volte si nuota senza costume. Non è ovunque una spiaggia nudista ufficiale. Sii gentile con chi non lo vuole.",
           "Tigaki tarafında insanların bazen kıyafetsiz yüzdüğü sakin bir kısım. Her yerde resmi bir çıplak plaj değil. İstemeyenlere karşı nazik ol.",
           "Tramo más quieto hacia Tigaki donde a veces se nada sin ropa. No es en todas partes una playa nudista oficial. Sé correcto con quien no quiere eso.")),
        ("strand-marmari-beach.html", "Marmari Beach",
         L("Zandstrand van het dorp Marmari, tussen Tigaki en Mastichari.",
           "Sandstrand des Dorfs Marmari, zwischen Tigaki und Mastichari.",
           "Sandy beach of the village of Marmari, between Tigaki and Mastichari.",
           "Spiaggia di sabbia del villaggio di Marmari, tra Tigaki e Mastichari.",
           "Tigaki ile Mastichari arasında Marmari köyünün kumsalı.",
           "Playa de arena del pueblo de Marmari, entre Tigaki y Mastichari.")),
        ("strand-mastichari-beach.html", "Mastichari Beach",
         L("Lang strand bij de veerboot naar Kalymnos. De gids noemde een Blauwe Vlag. Wind voor wind- en kitesurfen.",
           "Langer Strand bei der Fähre nach Kalymnos. Der Guide nannte eine Blaue Flagge. Wind zum Wind- und Kitesurfen.",
           "Long beach by the ferry to Kalymnos. The guide mentioned a Blue Flag. Wind for windsurfing and kitesurfing.",
           "Lunga spiaggia vicino al traghetto per Kalymnos. La guida citava una Bandiera Blu. Vento per windsurf e kitesurf.",
           "Kalymnos feribotunun yanında uzun plaj. Rehber Mavi Bayrak’tan söz etti. Rüzgar sörfü ve kite için rüzgar.",
           "Playa larga junto al ferry a Kálimnos. La guía citaba una Bandera Azul. Viento para windsurf y kitesurf.")),
        ("strand-kavo-parediso.html", "Kavo Parediso",
         L("Strand aan de westpunt. Het laatste stuk weg is onverhard. Een klein barretje, parasols, kliffen en helder water.",
           "Strand an der Westspitze. Das letzte Wegstück ist unbefestigt. Eine kleine Bar, Schirme, Klippen und klares Wasser.",
           "Beach at the western tip. The last bit of road is unpaved. A small bar, umbrellas, cliffs and clear water.",
           "Spiaggia sulla punta ovest. L’ultimo pezzo di strada è sterrato. Un piccolo bar, ombrelloni, scogliere e acqua limpida.",
           "Batı uçtaki plaj. Yolun son parçası toprak. Küçük bir bar, şemsiye, uçurum ve berrak su.",
           "Playa en la punta oeste. El último tramo de camino es de tierra. Un bar pequeño, sombrillas, acantilados y agua clara.")),
        ("strand-exotic-beach.html", "Exotic Beach",
         L("De gids zette Exotic bij de stillere stranden waar mensen soms zonder kleding zijn. Niet overal officieel. Houd afstand als iemand dat niet wil.",
           "Der Guide setzte Exotic zu den ruhigeren Stränden, wo Leute manchmal ohne Kleidung sind. Nicht überall offiziell. Halt Abstand, wenn jemand das nicht will.",
           "The guide put Exotic with the quieter beaches where people are sometimes without clothes. Not official everywhere. Keep your distance if someone does not want that.",
           "La guida metteva Exotic tra le spiagge più quiete dove a volte si sta senza costume. Non ovunque ufficiale. Tieni le distanze se qualcuno non lo vuole.",
           "Rehber Exotic’i insanların bazen kıyafetsiz olduğu sakin plajlara koydu. Her yerde resmi değil. Biri istemezse mesafe bırak.",
           "La guía ponía Exotic entre las playas más quietas donde a veces se está sin ropa. No es oficial en todas partes. Guarda distancia si alguien no quiere eso.")),
        ("strand-naaktstrand-kardamena.html", "Naaktstrand Kardamena",
         L("Stillere hoek bij Kardamena die de gids als naaktstrand noemde. Het is geen grote georganiseerde beachclub. Wees respectvol.",
           "Ruhigere Ecke bei Kardamena, die der Guide als FKK-Strand nannte. Es ist kein großer Beachclub. Sei respektvoll.",
           "A quieter corner by Kardamena that the guide called a naturist beach. It is not a big organised beach club. Be respectful.",
           "Angolo più quieto verso Kardamena che la guida chiamava spiaggia nudista. Non è un grande beach club. Sii rispettoso.",
           "Rehberin çıplak plaj dediği Kardamena tarafında sakin bir köşe. Büyük bir beach club değil. Saygılı ol.",
           "Rincón más quieto hacia Kardamena que la guía llamaba playa nudista. No es un gran beach club. Sé respetuoso.")),
    ]
    for fn, name, lead in rows:
        title = L(name, name, name, name, name, name)
        img = ensure_hero(fn, "stranden.jpg")
        page(fn, title, lead,
             [(L("Voorzieningen", "Ausstattung", "Facilities", "Servizi", "Olanaklar", "Servicios"),
               L("Ligbedden, eten en een reddingspost zijn niet op elk stuk hetzelfde. De prijs van een bed staat hier niet.",
                 "Liegen, Essen und eine Rettungsstation sind nicht auf jedem Abschnitt gleich. Der Preis für eine Liege steht hier nicht.",
                 "Sunbeds, food and a lifeguard are not the same on every stretch. The price of a bed is not written here.",
                 "Lettini, cibo e un bagnino non sono uguali su ogni tratto. Il prezzo di un lettino non è scritto qui.",
                 "Şezlong, yemek ve cankurtaran her kesimde aynı değil. Yatak fiyatı burada yok.",
                 "Hamacas, comida y socorrista no son iguales en cada tramo. El precio de una hamaca no está aquí."))],
             [L("Strand", "Strand", "Beach", "Spiaggia", "Plaj", "Playa"), BADGE_CHECK],
             img, "stranden.html", BACK_BEACH, name + " Kos", NOTE_PRICE)


def write_excursions():
    # overwrite excursies hub with translations, same 12 links
    cards = []
    items = [
        ("excursie-3-eilanden.html", "3 eilanden", "3 Inseln", "3 islands", "3 isole", "3 ada", "3 islas"),
        ("excursie-bodrum.html", "Veerboot Bodrum", "Fähre Bodrum", "Bodrum ferry", "Traghetto Bodrum", "Bodrum feribotu", "Ferry a Bodrum"),
        ("excursie-glazenboot.html", "Glazen boot", "Glasbodenboot", "Glass-bottom boat", "Barca con fondo di vetro", "Cam tabanlı tekne", "Barco de fondo de cristal"),
        ("excursie-duiken.html", "Duiken", "Tauchen", "Diving", "Immersioni", "Dalış", "Buceo"),
        ("excursie-waterpark.html", "Waterpark Lido", "Wasserpark Lido", "Lido water park", "Parco acquatico Lido", "Lido su parkı", "Parque acuático Lido"),
        ("excursie-zeevissen.html", "Zeevissen", "Hochseefischen", "Sea fishing", "Pesca in mare", "Deniz balıkçılığı", "Pesca en el mar"),
        ("excursie-griekse-avond.html", "Griekse avond", "Griechischer Abend", "Greek evening", "Serata greca", "Yunan gecesi", "Noche griega"),
        ("excursie-zia-nacht.html", "Zia in de avond", "Zia am Abend", "Zia at night", "Zia di sera", "Akşam Zia", "Zia de noche"),
        ("excursie-massage.html", "Massage", "Massage", "Massage", "Massaggio", "Masaj", "Masaje"),
        ("excursie-therma.html", "Therma", "Therma", "Therma", "Therma", "Therma", "Therma"),
        ("excursie-paard.html", "Paardrijden", "Reiten", "Horse riding", "Equitazione", "At binme", "Paseo a caballo"),
        ("excursie-karten.html", "Karten", "Kartbahn", "Go-karting", "Kart", "Karting", "Karting"),
    ]
    for fn, nl, de, en, it, tr, es in items:
        cards.append((fn, "excursies.jpg", L(nl, de, en, it, tr, es)))
    hub("excursies.html",
        L("Excursies & activiteiten", "Ausflüge & Aktivitäten", "Excursions & activities", "Escursioni e attività", "Turlar ve aktiviteler", "Excursiones y actividades"),
        L("Kies een uitje. Prijzen in de tekst komen uit de oude gids en kunnen veranderd zijn.",
          "Wähl einen Ausflug. Preise im Text kommen aus dem alten Guide und können sich geändert haben.",
          "Pick a trip. Prices in the text come from the old guide and may have changed.",
          "Scegli un’uscita. I prezzi nel testo vengono dalla vecchia guida e possono essere cambiati.",
          "Bir gezi seç. Metindeki fiyatlar eski rehberden, değişmiş olabilir.",
          "Elige una salida. Los precios del texto vienen de la guía antigua y pueden haber cambiado."),
        cards, "index.html", BACK_HOME, "excursies.jpg")

    page("excursie-3-eilanden.html",
         L("Drie eilanden", "Drei Inseln", "Three islands", "Tre isole", "Üç ada", "Tres islas"),
         L("Boottocht die vaak Pserimos, Kalymnos en Plati aandoet. Pserimos is klein en rustig. Kalymnos staat bekend om de sponzenvisserij. Bij Plati is het water helder om te zwemmen.",
           "Bootsausflug, der oft Pserimos, Kalymnos und Plati anläuft. Pserimos ist klein und ruhig. Kalymnos ist bekannt für die Schwammfischerei. Bei Plati ist das Wasser klar zum Schwimmen.",
           "A boat trip that often calls at Pserimos, Kalymnos and Plati. Pserimos is small and quiet. Kalymnos is known for sponge fishing. At Plati the water is clear for swimming.",
           "Giro in barca che spesso tocca Pserimos, Kalymnos e Plati. Pserimos è piccola e quieta. Kalymnos è nota per la pesca delle spugne. A Plati l’acqua è limpida per nuotare.",
           "Çoğu zaman Pserimos, Kalymnos ve Plati’ye uğrayan tekne turu. Pserimos küçük ve sakin. Kalymnos sünger avıyla bilinir. Plati’de su yüzmek için berrak.",
           "Paseo en barco que suele tocar Pserimos, Kálimnos y Plati. Pserimos es pequeña y tranquila. Kálimnos es conocida por la pesca de esponjas. En Plati el agua es clara para nadar."),
         [(L("Meenemen", "Mitnehmen", "Bring", "Porta", "Götür", "Lleva"),
           L("De gids zei: drank is vaak voor eigen rekening, neem zonnebrand mee, en eigen drinken mee aan boord mag soms niet. Welke boot vaart, wisselt.",
             "Der Guide sagte: Getränke sind oft selbst zu zahlen, nimm Sonnencreme mit, und eigene Getränke an Bord sind manchmal verboten. Welches Boot fährt, wechselt.",
             "The guide said: drinks are often extra, bring sunscreen, and your own drinks may not be allowed on board. Which boat sails changes.",
             "La guida diceva: le bevande sono spesso a parte, porta la crema solare, e le tue bevande a bordo a volte non sono ammesse. Quale barca parte cambia.",
             "Rehber diyordu: içecek çoğu zaman ayrıca, güneş kremi götür, kendi içeceğin bazen güvertede yasak. Hangi tekne kalktığı değişir.",
             "La guía decía: la bebida suele ir aparte, lleva protector solar, y tu propia bebida a bordo a veces no se permite. Qué barco sale cambia."))],
         [BADGE_CHECK, L("Boot", "Boot", "Boat", "Barca", "Tekne", "Barco")],
         ensure_hero("excursie-3-eilanden.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "Kos harbour boat trip", NOTE_PRICE)

    page("excursie-bodrum.html",
         L("Veerboot naar Bodrum", "Fähre nach Bodrum", "Ferry to Bodrum", "Traghetto per Bodrum", "Bodrum feribotu", "Ferry a Bodrum"),
         L("Bodrum ligt in Turkije, aan de overkant. De gids noemde een vaart van ongeveer 30 minuten naar het centrum, met Sea Star en Apollon 2. Een enkeltje stond op €35 (12 jaar en ouder), €24 (6–12) en €10 (0–5), belastingen inbegrepen. Vertrek rond 9:00 of 9:30, terug in de middag. Er was soms een extra afvaart.",
           "Bodrum liegt in der Türkei gegenüber. Der Guide nannte etwa 30 Minuten ins Zentrum, mit Sea Star und Apollon 2. Einzelticket €35 (ab 12), €24 (6–12) und €10 (0–5), Steuern inklusive. Abfahrt um 9:00 oder 9:30, zurück am Nachmittag. Manchmal gab es eine Extrafahrt.",
           "Bodrum is in Turkey, across the water. The guide named a crossing of about 30 minutes to the centre, with Sea Star and Apollon 2. A single was listed at €35 (12 and over), €24 (6–12) and €10 (0–5), tax included. Departure around 9:00 or 9:30, back in the afternoon. There was sometimes an extra sailing.",
           "Bodrum è in Turchia, di fronte. La guida indicava circa 30 minuti fino al centro, con Sea Star e Apollon 2. Un solo andata a €35 (dai 12 anni), €24 (6–12) e €10 (0–5), tasse incluse. Partenza verso le 9:00 o le 9:30, ritorno nel pomeriggio. A volte c’era una corsa in più.",
           "Bodrum karşıda, Türkiye’de. Rehber merkeze yaklaşık 30 dakika diyordu, Sea Star ve Apollon 2 ile. Tek yön 12 yaş ve üstü €35, 6–12 €24, 0–5 €10, vergiler dahil. Kalkış 9:00 veya 9:30 civarı, dönüş öğleden sonra. Bazen ek sefer vardı.",
           "Bodrum está en Turquía, enfrente. La guía citaba unos 30 minutos hasta el centro, con Sea Star y Apollon 2. Un solo ida a 35 € (desde 12 años), 24 € (6–12) y 10 € (0–5), impuestos incluidos. Salida hacia las 9:00 o las 9:30, vuelta por la tarde. A veces había una salida extra."),
         [(L("Paspoort", "Reisepass", "Passport", "Passaporto", "Pasaport", "Pasaporte"),
           L("Je gaat een ander land in. Lees de pagina over het visum voor Bodrum en de pagina over shoppen en de douane. De dienstregeling verandert.",
             "Du fährst in ein anderes Land. Lies die Seite zum Visum für Bodrum und die Seite über Shopping und Zoll. Der Fahrplan ändert sich.",
             "You enter another country. Read the page about the Bodrum visa and the page about shopping and customs. The timetable changes.",
             "Entri in un altro paese. Leggi la pagina sul visto per Bodrum e quella su shopping e dogana. L’orario cambia.",
             "Başka bir ülkeye girersin. Bodrum vizesi sayfasını ve alışveriş ile gümrük sayfasını oku. Tarife değişir.",
             "Entras en otro país. Lee la página del visado de Bodrum y la de compras y aduana. El horario cambia."))],
         [BADGE_CHECK, L("Turkije", "Türkei", "Turkey", "Turchia", "Türkiye", "Turquía")],
         ensure_hero("excursie-bodrum.html", "wjd-bodrum-vliegtuig.jpg"),
         "excursies.html", BACK_EX, "Kos Bodrum ferry", NOTE_PRICE)

    page("excursie-glazenboot.html",
         L("Boot met glazen bodem", "Glasbodenboot", "Glass-bottom boat", "Barca dal fondo di vetro", "Cam tabanlı tekne", "Barco de fondo de cristal"),
         L("Korte tocht vanuit Kos-stad: onderwatercabine, vissen kijken en een zwemstop. De gids noemde twee boten. Yellow: 12:00–13:30, 14:00–15:30 en 16:00–17:30. Kinderen 0–3 gratis, 4–12 €12, vanaf 13 jaar €23. Dory: 11:00–13:30 en 13:30–16:00, langs een wrak van ongeveer 40 jaar en de Blue Lagoon. 0–4 gratis, 5–12 €10, vanaf 13 €20. Op vrijdag was er een zonsondergang van 19:00 tot 20:45 voor 13+, €30 met mezze en salade.",
           "Kurze Fahrt ab Kos-Stadt: Unterwasserkabine, Fische und eine Schwimmstopps. Der Guide nannte zwei Boote. Yellow: 12:00–13:30, 14:00–15:30 und 16:00–17:30. Kinder 0–3 gratis, 4–12 €12, ab 13 €23. Dory: 11:00–13:30 und 13:30–16:00, an einem etwa 40 Jahre alten Wrack und der Blue Lagoon vorbei. 0–4 gratis, 5–12 €10, ab 13 €20. Freitags gab es einen Sonnenuntergang 19:00–20:45 ab 13, €30 mit Mezze und Salat.",
           "A short trip from Kos town: underwater cabin, watching fish and a swim stop. The guide named two boats. Yellow: 12:00–13:30, 14:00–15:30 and 16:00–17:30. Children 0–3 free, 4–12 €12, from 13 €23. Dory: 11:00–13:30 and 13:30–16:00, past a wreck about 40 years old and the Blue Lagoon. 0–4 free, 5–12 €10, from 13 €20. On Friday there was a sunset from 19:00 to 20:45 for ages 13+, €30 with mezze and salad.",
           "Giro breve da Kos città: cabina sott’acqua, pesci e una sosta per nuotare. La guida citava due barche. Yellow: 12:00–13:30, 14:00–15:30 e 16:00–17:30. Bambini 0–3 gratis, 4–12 €12, dai 13 €23. Dory: 11:00–13:30 e 13:30–16:00, lungo un relitto di circa 40 anni e la Blue Lagoon. 0–4 gratis, 5–12 €10, dai 13 €20. Il venerdì c’era un tramonto 19:00–20:45 dai 13 anni, €30 con mezze e insalata.",
           "Kos şehrinden kısa tur: su altı kabin, balık ve yüzme molası. Rehber iki tekne saydı. Yellow: 12:00–13:30, 14:00–15:30 ve 16:00–17:30. 0–3 ücretsiz, 4–12 €12, 13 yaştan €23. Dory: 11:00–13:30 ve 13:30–16:00, yaklaşık 40 yıllık batık ve Blue Lagoon. 0–4 ücretsiz, 5–12 €10, 13’ten €20. Cuma 19:00–20:45, 13+, €30 meze ve salata ile gün batımı vardı.",
           "Paseo corto desde la ciudad: cabina bajo el agua, peces y una parada para nadar. La guía citaba dos barcos. Yellow: 12:00–13:30, 14:00–15:30 y 16:00–17:30. Niños de 0–3 gratis, 4–12 12 €, desde 13 23 €. Dory: 11:00–13:30 y 13:30–16:00, junto a un pecio de unos 40 años y la Blue Lagoon. 0–4 gratis, 5–12 10 €, desde 13 20 €. El viernes había un atardecer de 19:00 a 20:45 para mayores de 13, 30 € con mezze y ensalada."),
         [(L("Meenemen", "Mitnehmen", "Bring", "Porta", "Götür", "Lleva"),
          L("Neem zwemkleding mee. Dit zijn de prijzen uit de oude gids.",
            "Nimm Badesachen mit. Das sind die Preise aus dem alten Guide.",
            "Bring swimwear. These are the prices from the old guide.",
            "Porta il costume. Questi sono i prezzi della vecchia guida.",
            "Mayo götür. Bunlar eski rehberin fiyatları.",
            "Lleva bañador. Estos son los precios de la guía antigua."))],
         [BADGE_CHECK, BADGE_TOWN],
         ensure_hero("excursie-glazenboot.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "glass bottom boat Kos", NOTE_PRICE)

    page("excursie-duiken.html",
         L("Duiken en snorkelen", "Tauchen und Schnorcheln", "Diving and snorkelling", "Immersioni e snorkeling", "Dalış ve şnorkel", "Buceo y esnórquel"),
         L("Meerdere centra. De gids noemde: Liamis in de haven van Kos-stad (PADI, ook naar Pserimos), Kos Divers in Psalidi, Sea World op het strand van Agios Stefanos in Kefalos, Arian in Kardamena (SSI en ANDI), Silent Explorers in Mastichari, en Volcano Bubbles op Nisyros.",
           "Mehrere Zentren. Der Guide nannte: Liamis im Hafen von Kos-Stadt (PADI, auch nach Pserimos), Kos Divers in Psalidi, Sea World am Strand von Agios Stefanos in Kefalos, Arian in Kardamena (SSI und ANDI), Silent Explorers in Mastichari und Volcano Bubbles auf Nisyros.",
           "Several centres. The guide named: Liamis in Kos town harbour (PADI, also to Pserimos), Kos Divers in Psalidi, Sea World on Agios Stefanos beach in Kefalos, Arian in Kardamena (SSI and ANDI), Silent Explorers in Mastichari, and Volcano Bubbles on Nisyros.",
           "Più centri. La guida citava: Liamis nel porto di Kos città (PADI, anche verso Pserimos), Kos Divers a Psalidi, Sea World sulla spiaggia di Agios Stefanos a Kefalos, Arian a Kardamena (SSI e ANDI), Silent Explorers a Mastichari e Volcano Bubbles a Nisyros.",
           "Birkaç merkez. Rehber saydı: Kos limanında Liamis (PADI, Pserimos’a da), Psalidi’de Kos Divers, Kefalos Agios Stefanos plajında Sea World, Kardamena’da Arian (SSI ve ANDI), Mastichari’de Silent Explorers ve Nisyros’ta Volcano Bubbles.",
           "Varios centros. La guía citaba: Liamis en el puerto de la ciudad (PADI, también a Pserimos), Kos Divers en Psalidi, Sea World en la playa de Agios Stefanos en Kéfalos, Arian en Kardamena (SSI y ANDI), Silent Explorers en Mastichari y Volcano Bubbles en Nísiros."),
         [(L("Eerste keer", "Erstes Mal", "First time", "Prima volta", "İlk kez", "Primera vez"),
          L("Een introductieduik kan zonder brevet. Een medische verklaring vragen ze vaak. De prijs staat hier niet.",
            "Ein Schnuppertauchgang geht ohne Schein. Eine ärztliche Erklärung wird oft verlangt. Der Preis steht hier nicht.",
            "A try-dive can be done without a certificate. They often ask for a medical form. The price is not written here.",
            "Un battesimo può farsi senza brevetto. Spesso chiedono un modulo medico. Il prezzo non è scritto qui.",
            "Deneme dalışı belgesiz yapılabilir. Çoğu zaman sağlık formu isterler. Fiyat burada yok.",
            "Un bautizo puede hacerse sin título. A menudo piden un formulario médico. El precio no está aquí."))],
         [BADGE_CHECK], ensure_hero("excursie-duiken.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "diving Kos", NOTE_PRICE)

    page("excursie-waterpark.html",
         L("Lido Waterpark", "Lido Waterpark", "Lido Waterpark", "Lido Waterpark", "Lido Waterpark", "Lido Waterpark"),
         L("Waterpark bij Mastichari. De gids noemde het een van de grotere van de Dodekanesos, met meer dan 18 onderdelen, zwembaden, schaduw, een EHBO-post en badmeesters. Eten en drinken meenemen was verboden. Als seizoensstart stond 12 juni 2026.",
           "Wasserpark bei Mastichari. Der Guide nannte ihn einen der größeren des Dodekanes, mit mehr als 18 Anlagen, Becken, Schatten, einer Erste-Hilfe-Stelle und Rettungsschwimmern. Essen und Trinken mitbringen war verboten. Als Saisonstart stand der 12. Juni 2026.",
           "Water park near Mastichari. The guide called it one of the larger ones in the Dodecanese, with more than 18 features, pools, shade, a first-aid post and lifeguards. Bringing food and drink was forbidden. 12 June 2026 was listed as the season start.",
           "Parco acquatico vicino a Mastichari. La guida lo chiamava uno dei più grandi del Dodecaneso, con più di 18 attrazioni, piscine, ombra, un pronto soccorso e bagnini. Portare cibo e bevande era vietato. Come inizio stagione c’era il 12 giugno 2026.",
           "Mastichari yakınında su parkı. Rehber onu On İki Ada’nın büyüklerinden saydı: 18’den fazla ünite, havuz, gölge, ilk yardım ve cankurtaran. Yiyecek ve içecek getirmek yasaktı. Sezon başlangıcı olarak 12 Haziran 2026 yazıyordu.",
           "Parque acuático cerca de Mastichari. La guía lo llamaba uno de los grandes del Dodecaneso, con más de 18 atracciones, piscinas, sombra, un puesto de primeros auxilios y socorristas. Llevar comida y bebida estaba prohibido. El 12 de junio de 2026 figuraba como inicio de temporada."),
         [(L("Nu", "Jetzt", "Now", "Ora", "Şimdi", "Ahora"),
          L("Of het park vandaag open is en wat een ticket kost, moet je ter plaatse of bij het park nakijken.",
            "Ob der Park heute offen ist und was ein Ticket kostet, musst du vor Ort oder beim Park prüfen.",
            "Whether the park is open today and what a ticket costs, check on site or with the park.",
            "Se il parco è aperto oggi e quanto costa il biglietto, controlla sul posto o con il parco.",
            "Parkın bugün açık olup olmadığını ve biletin fiyatını yerinde veya parktan kontrol et.",
            "Si el parque está abierto hoy y cuánto cuesta la entrada, míralo en el sitio o con el parque."))],
         [BADGE_FEE, L("Mastichari", "Mastichari", "Mastichari", "Mastichari", "Mastichari", "Mastichari")],
         ensure_hero("excursie-waterpark.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "Lido Waterpark Kos", NOTE_PRICE)

    page("excursie-zeevissen.html",
         L("Vissen op zee", "Angeln auf See", "Fishing at sea", "Pesca in mare", "Denizde balık", "Pesca en el mar"),
         L("De gids noemde Captain Tasos: een houten vissersboot vanuit de haven van Kos-stad, hooguit ongeveer 12 personen. Verder SaltyLife en Kardamena Fishing. Vissen zonder vergunning mocht volgens de gids, maar er zijn regels.",
           "Der Guide nannte Captain Tasos: ein hölzernes Fischerboot ab dem Hafen von Kos-Stadt, höchstens etwa 12 Personen. Dazu SaltyLife und Kardamena Fishing. Angeln ohne Lizenz war laut Guide erlaubt, aber es gibt Regeln.",
           "The guide named Captain Tasos: a wooden fishing boat from Kos town harbour, about 12 people at most. Also SaltyLife and Kardamena Fishing. Fishing without a licence was allowed according to the guide, but there are rules.",
           "La guida citava Captain Tasos: una barca di legno dal porto di Kos città, al massimo circa 12 persone. Anche SaltyLife e Kardamena Fishing. Pescare senza licenza era permesso secondo la guida, ma ci sono regole.",
           "Rehber Captain Tasos’u saydı: Kos limanından ahşap balıkçı teknesi, en fazla yaklaşık 12 kişi. Ayrıca SaltyLife ve Kardamena Fishing. Rehbere göre izinsiz balık serbestti, ama kurallar var.",
           "La guía citaba a Captain Tasos: un barco de madera desde el puerto de la ciudad, unas 12 personas como máximo. También SaltyLife y Kardamena Fishing. Pescar sin licencia estaba permitido según la guía, pero hay normas."),
         [(L("Regels", "Regeln", "Rules", "Regole", "Kurallar", "Normas"),
          L("De precieze regels en de prijs van een tocht staan hier niet. Vraag de schipper.",
            "Die genauen Regeln und der Preis einer Fahrt stehen hier nicht. Frag den Skipper.",
            "The exact rules and the price of a trip are not written here. Ask the skipper.",
            "Le regole precise e il prezzo di un giro non sono scritti qui. Chiedi allo skipper.",
            "Kesin kurallar ve tur fiyatı burada yok. Kaptana sor.",
            "Las normas exactas y el precio de una salida no están aquí. Pregunta al patrón."))],
         [BADGE_CHECK], ensure_hero("excursie-zeevissen.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "fishing boat Kos harbour", NOTE_PRICE)

    page("excursie-griekse-avond.html",
         L("Griekse avond", "Griechischer Abend", "Greek evening", "Serata greca", "Yunan gecesi", "Noche griega"),
         L("Bus naar Zia, diner buiten, wijn onbeperkt, andere drank tegen betaling, muziek en dans, en de bus terug. Zo stond het in de gids.",
           "Bus nach Zia, Abendessen draußen, Wein unbegrenzt, andere Getränke gegen Bezahlung, Musik und Tanz, und der Bus zurück. So stand es im Guide.",
           "A bus to Zia, dinner outside, unlimited wine, other drinks paid, music and dance, and the bus back. That is how the guide described it.",
           "Bus per Zia, cena all’aperto, vino illimitato, altre bevande a pagamento, musica e danza, e il bus di ritorno. Così lo descriveva la guida.",
           "Zia’ya otobüs, dışarıda akşam yemeği, sınırsız şarap, diğer içkiler ücretli, müzik ve dans, dönüş otobüsü. Rehber böyle anlatıyordu.",
           "Autobús a Zia, cena fuera, vino ilimitado, otras bebidas de pago, música y baile, y el autobús de vuelta. Así lo describía la guía."),
         [(L("Prijs", "Preis", "Price", "Prezzo", "Fiyat", "Precio"),
          L("Het bedrag per persoon staat niet in deze pagina. Vraag het bij de organisatie.",
            "Der Betrag pro Person steht nicht auf dieser Seite. Frag bei der Organisation.",
            "The price per person is not on this page. Ask the organiser.",
            "L’importo a persona non è in questa pagina. Chiedi all’organizzazione.",
            "Kişi başı tutar bu sayfada yok. Organizatöre sor.",
            "El importe por persona no está en esta página. Pregunta a la organización."))],
         [BADGE_CHECK, L("Zia", "Zia", "Zia", "Zia", "Zia", "Zia")],
         ensure_hero("excursie-griekse-avond.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "Zia Kos Greek night", NOTE_PRICE)

    page("excursie-zia-nacht.html",
         L("Zia in de avond", "Zia am Abend", "Zia in the evening", "Zia di sera", "Akşam Zia", "Zia por la tarde"),
         L("Rit naar Zia voor de zonsondergang, zonder het grote diner van de Griekse avond. De gids noemde gedeelde ritten van 18:00 tot 21:30: €15 per persoon vanuit een deel van het eiland en €18 vanuit Psalidi. Privé vanuit Kos-stad: €90 voor 4 personen en €130 voor 8, op een zelfgekozen tijd.",
           "Fahrt nach Zia zum Sonnenuntergang, ohne das große Essen des griechischen Abends. Der Guide nannte geteilte Fahrten von 18:00 bis 21:30: €15 pro Person aus einem Teil der Insel und €18 aus Psalidi. Privat ab Kos-Stadt: €90 für 4 Personen und €130 für 8, zur selbst gewählten Zeit.",
           "A ride to Zia for the sunset, without the big dinner of the Greek evening. The guide listed shared rides from 18:00 to 21:30: €15 per person from part of the island and €18 from Psalidi. Private from Kos town: €90 for 4 people and €130 for 8, at a time you choose.",
           "Corsa per Zia al tramonto, senza la grande cena della serata greca. La guida indicava corse condivise dalle 18:00 alle 21:30: €15 a persona da una parte dell’isola e €18 da Psalidi. Privato da Kos città: €90 per 4 persone e €130 per 8, all’ora che scegli.",
           "Yunan gecesinin büyük yemeği olmadan, gün batımı için Zia’ya gidiş. Rehber 18:00–21:30 paylaşımlı sefer yazdı: adanın bir kısmından kişi başı €15, Psalidi’den €18. Kos şehrinden özel: 4 kişi €90, 8 kişi €130, seçtiğin saatte.",
           "Trayecto a Zia para el atardecer, sin la gran cena de la noche griega. La guía citaba viajes compartidos de 18:00 a 21:30: 15 € por persona desde una parte de la isla y 18 € desde Psalidi. Privado desde la ciudad: 90 € para 4 personas y 130 € para 8, a la hora que elijas."),
         [(L("Druk", "Voll", "Busy", "Pieno", "Kalabalık", "Lleno"),
          L("De weg is rond zonsondergang vol. Deze bedragen komen uit de oude gids.",
            "Die Straße ist zum Sonnenuntergang voll. Diese Beträge kommen aus dem alten Guide.",
            "The road is full around sunset. These amounts come from the old guide.",
            "La strada è piena al tramonto. Queste cifre vengono dalla vecchia guida.",
            "Yol gün batımında dolar. Bu tutarlar eski rehberden.",
            "La carretera se llena al atardecer. Estas cifras vienen de la guía antigua."))],
         [BADGE_CHECK], ensure_hero("excursie-zia-nacht.html", "wjd-zonsondergang.jpg"),
         "excursies.html", BACK_EX, "Zia Kos sunset", NOTE_PRICE)

    page("excursie-massage.html",
         L("Massage", "Massage", "Massage", "Massaggio", "Masaj", "Masaje"),
         L("De gids noemde Afrodite bij de bron van Therma, strandmassage bij Mylos, Euphoria (hamam) in Kardamena, een studio in Marmari, Mastichari Massage van Konstantinos Fessaras, en Natural Malaxis in Kos-stad.",
           "Der Guide nannte Afrodite an der Quelle von Therma, Strandmassage bei Mylos, Euphoria (Hamam) in Kardamena, ein Studio in Marmari, Mastichari Massage von Konstantinos Fessaras und Natural Malaxis in Kos-Stadt.",
           "The guide named Afrodite by the Therma spring, a beach massage at Mylos, Euphoria (hamam) in Kardamena, a studio in Marmari, Mastichari Massage by Konstantinos Fessaras, and Natural Malaxis in Kos town.",
           "La guida citava Afrodite alla sorgente di Therma, massaggio in spiaggia a Mylos, Euphoria (hamam) a Kardamena, uno studio a Marmari, Mastichari Massage di Konstantinos Fessaras e Natural Malaxis in città.",
           "Rehber saydı: Therma kaynağında Afrodite, Mylos’ta plaj masajı, Kardamena’da Euphoria (hamam), Marmari’de bir stüdyo, Konstantinos Fessaras’ın Mastichari Massage’ı ve Kos şehrinde Natural Malaxis.",
           "La guía citaba Afrodita junto a la fuente de Therma, masaje en la playa en Mylos, Euphoria (hamam) en Kardamena, un estudio en Marmari, Mastichari Massage de Konstantinos Fessaras y Natural Malaxis en la ciudad."),
         [(L("Afspraak", "Termin", "Booking", "Prenotazione", "Randevu", "Reserva"),
          L("Duur en prijs verschillen per behandeling. Die staan hier niet.",
            "Dauer und Preis unterscheiden sich je Behandlung. Sie stehen hier nicht.",
            "Length and price differ by treatment. They are not written here.",
            "Durata e prezzo cambiano secondo il trattamento. Non sono scritti qui.",
            "Süre ve fiyat işleme göre değişir. Burada yok.",
            "Duración y precio cambian según el tratamiento. No están aquí."))],
         [BADGE_CHECK], ensure_hero("excursie-massage.html", "wellness.jpg"),
         "excursies.html", BACK_EX, "massage Kos", NOTE_PRICE)

    page("excursie-therma.html",
         L("Therma", "Therma", "Therma", "Therma", "Therma", "Therma"),
         L("De warmwaterbron is gratis en geen georganiseerde excursie. Je kunt er zelf naartoe. De uitleg staat bij de bezienswaardigheid Therma. Een transfer regel je apart.",
           "Die heiße Quelle ist kostenlos und keine organisierte Tour. Du kannst selbst hinfahren. Die Erklärung steht bei der Sehenswürdigkeit Therma. Einen Transfer buchst du extra.",
           "The hot spring is free and not an organised excursion. You can go yourself. The explanation is on the Therma sight page. You arrange a transfer separately.",
           "La sorgente calda è gratuita e non è un’escursione organizzata. Puoi andarci da solo. La spiegazione è nella pagina Therma. Il transfer lo organizzi a parte.",
           "Sıcak su ücretsizdir ve organize bir tur değildir. Kendin gidebilirsin. Anlatım Therma sayfasında. Transferi ayrıca ayarlarsın.",
           "La fuente caliente es gratis y no es una excursión organizada. Puedes ir por tu cuenta. La explicación está en la página de Therma. El transfer lo arreglas aparte."),
         [(L("Route", "Route", "Route", "Percorso", "Rota", "Ruta"),
          L("De laatste klim is steil. Met de fiets alleen als je dat aankunt.",
            "Die letzte Steigung ist steil. Mit dem Rad nur, wenn du das schaffst.",
            "The last climb is steep. By bike only if you can manage it.",
            "L’ultima salita è ripida. In bici solo se ce la fai.",
            "Son tırmanış dik. Bisikletle ancak kaldırabiliyorsan.",
            "La última cuesta es fuerte. En bici solo si puedes."))],
         [BADGE_FREE], scrape_img("therma", "excursie-therma.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "Embros Thermes Kos", None)

    page("excursie-paard.html",
         L("Paardrijden", "Reiten", "Horse riding", "Equitazione", "At binme", "Paseo a caballo"),
         L("De gids noemde Paradise Ranch bij Zia, Salt Lake Stables, Erika’s Horse Farm en Veroutas tussen Tigaki en Marmari, en een stal bij Kardamena. Ritten gaan over het strand, rond het zoutmeer of de bergen in. Er zijn pony’s voor kinderen.",
           "Der Guide nannte Paradise Ranch bei Zia, Salt Lake Stables, Erika’s Horse Farm und Veroutas zwischen Tigaki und Marmari und einen Stall bei Kardamena. Ausritte gehen über den Strand, um den Salzsee oder in die Berge. Es gibt Ponys für Kinder.",
           "The guide named Paradise Ranch near Zia, Salt Lake Stables, Erika’s Horse Farm and Veroutas between Tigaki and Marmari, and a stable near Kardamena. Rides go on the beach, around the salt lake or into the hills. There are ponies for children.",
           "La guida citava Paradise Ranch verso Zia, Salt Lake Stables, Erika’s Horse Farm e Veroutas tra Tigaki e Marmari, e una scuderia verso Kardamena. Le uscite vanno sulla spiaggia, intorno al lago salato o sulle colline. Ci sono pony per i bambini.",
           "Rehber saydı: Zia tarafında Paradise Ranch, Salt Lake Stables, Erika’s Horse Farm ve Tigaki ile Marmari arasında Veroutas, Kardamena yakınında bir ahır. Turlar plajda, tuz gölü çevresinde veya tepelerde. Çocuklar için midilli var.",
           "La guía citaba Paradise Ranch hacia Zia, Salt Lake Stables, Erika’s Horse Farm y Veroutas entre Tigaki y Mastichari, y un establo cerca de Kardamena. Los paseos van por la playa, el lago salado o las colinas. Hay ponis para niños."),
         [(L("Kleding", "Kleidung", "Clothes", "Vestiti", "Giysi", "Ropa"),
          L("Dichte schoenen zijn handiger dan slippers. Gewichtslimiet en prijs vraag je bij de stal.",
            "Geschlossene Schuhe sind besser als Schlappen. Gewichtslimit und Preis fragst du im Stall.",
            "Closed shoes are better than flip-flops. Ask the stable about the weight limit and the price.",
            "Scarpe chiuse sono meglio delle ciabatte. Limite di peso e prezzo li chiedi alla scuderia.",
            "Kapalı ayakkabı terlikten iyidir. Kilo sınırı ve fiyatı ahıra sor.",
            "Zapatos cerrados van mejor que las chanclas. El límite de peso y el precio se preguntan en el establo."))],
         [BADGE_CHECK], ensure_hero("excursie-paard.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "horse riding Kos", NOTE_PRICE)

    page("excursie-karten.html",
         L("Karten", "Kartbahn", "Go-karting", "Kart", "Karting", "Karting"),
         L("De gids noemde twee banen: Go Kart Kos Pro Track bij Kardamena en Go Kart Centre bij Marmari.",
           "Der Guide nannte zwei Bahnen: Go Kart Kos Pro Track bei Kardamena und Go Kart Centre bei Marmari.",
           "The guide named two tracks: Go Kart Kos Pro Track near Kardamena and Go Kart Centre near Marmari.",
           "La guida citava due piste: Go Kart Kos Pro Track verso Kardamena e Go Kart Centre verso Marmari.",
           "Rehber iki pist saydı: Kardamena yakınında Go Kart Kos Pro Track ve Marmari yakınında Go Kart Centre.",
           "La guía citaba dos pistas: Go Kart Kos Pro Track cerca de Kardamena y Go Kart Centre cerca de Marmari."),
         [(L("Leeftijd", "Alter", "Age", "Età", "Yaş", "Edad"),
          L("Een minimumleeftijd en de prijs per sessie staan hier niet. Vraag het bij de baan.",
            "Ein Mindestalter und der Preis pro Session stehen hier nicht. Frag an der Bahn.",
            "A minimum age and the price per session are not written here. Ask at the track.",
            "Età minima e prezzo a sessione non sono scritti qui. Chiedi in pista.",
            "Asgari yaş ve seans fiyatı burada yok. Pistte sor.",
            "La edad mínima y el precio por sesión no están aquí. Pregunta en la pista."))],
         [BADGE_CHECK], ensure_hero("excursie-karten.html", "excursies.jpg"),
         "excursies.html", BACK_EX, "go kart Kos", NOTE_PRICE)


def write_help():
    page("hulp-politie.html",
         L("Politie", "Polizei", "Police", "Polizia", "Polis", "Policía"),
         L("Bij nood bel je 112. Dat nummer staat ook op de pagina Noodgevallen. Het dekt politie, ambulance en brandweer.",
           "Im Notfall rufst du 112. Die Nummer steht auch auf der Seite Notfälle. Sie gilt für Polizei, Rettung und Feuerwehr.",
           "In an emergency call 112. That number is also on the Emergencies page. It covers police, ambulance and the fire service.",
           "In emergenza chiami il 112. Il numero è anche nella pagina Emergenze. Vale per polizia, ambulanza e vigili del fuoco.",
           "Acilde 112’yi ara. Numara Acil durum sayfasında da var. Polis, ambulans ve itfaiyeyi kapsar.",
           "En una emergencia llama al 112. Ese número está también en Emergencias. Cubre policía, ambulancia y bomberos."),
         [(L("Bureaus", "Wachen", "Stations", "Commissariati", "Karakollar", "Comisarías"),
          L("Er zijn bureaus op het eiland, onder meer in Kos-stad. Het adres en het lokale nummer zijn hier nog niet ingevuld. De fabel dat er geen politie zou zijn, klopt niet.",
            "Es gibt Wachen auf der Insel, unter anderem in Kos-Stadt. Adresse und lokale Nummer fehlen hier noch. Die Fabel, es gäbe keine Polizei, stimmt nicht.",
            "There are stations on the island, including in Kos town. The address and the local number are not filled in here yet. The myth that there is no police is wrong.",
            "Ci sono commissariati sull’isola, anche in città. Indirizzo e numero locale non sono ancora qui. La favola che non ci sia polizia è falsa.",
            "Adada karakollar var, Kos şehri dahil. Adres ve yerel numara burada henüz yok. Polis olmadığı efsanesi yanlış.",
            "Hay comisarías en la isla, también en la ciudad. La dirección y el número local aún no están. El mito de que no hay policía es falso."))],
         [L("112", "112", "112", "112", "112", "112")],
         ensure_hero("hulp-politie.html", "noodgevallen.jpg"),
         "noodgevallen.html", BACK_HELP, "police Kos town", NOTE_PHONE)

    page("hulp-brandweer.html",
         L("Brandweer", "Feuerwehr", "Fire service", "Vigili del fuoco", "İtfaiye", "Bomberos"),
         L("Bel 112 bij brand. In het droge seizoen zet de brandweer extra ploegen in, onder meer bij Kefalos en Kardamena. Bij grote branden komt er hulp uit de lucht.",
           "Ruf 112 bei Feuer. In der trockenen Saison setzt die Feuerwehr Extra-Teams ein, unter anderem bei Kefalos und Kardamena. Bei großen Bränden kommt Hilfe aus der Luft.",
           "Call 112 if there is a fire. In the dry season the fire service adds crews, including near Kefalos and Kardamena. Big fires get help from the air.",
           "Chiama il 112 in caso di incendio. Nella stagione secca i vigili del fuoco aggiungono squadre, anche verso Kefalos e Kardamena. I grandi incendi ricevono aiuto dall’aria.",
           "Yangında 112’yi ara. Kurak sezonda itfaiye ek ekip koyar, Kefalos ve Kardamena tarafı dahil. Büyük yangınlara havadan yardım gelir.",
           "Llama al 112 si hay fuego. En la temporada seca los bomberos añaden equipos, también hacia Kéfalos y Kardamena. Los incendios grandes reciben ayuda desde el aire."),
         [(L("Zelf", "Selbst", "Yourself", "Da solo", "Kendin", "Tú mismo"),
          L("Een wegwerpbarbecue in droog gras is een slecht idee. Het kazernenummer staat hier niet.",
            "Ein Einweggrill in trockenem Gras ist eine schlechte Idee. Die Wachnummer steht hier nicht.",
            "A disposable barbecue in dry grass is a bad idea. The station number is not written here.",
            "Un barbecue usa e getta nell’erba secca è una cattiva idea. Il numero della caserma non è scritto qui.",
            "Kuru otta tek kullanımlık mangal kötü fikirdir. İstasyon numarası burada yok.",
            "Una barbacoa desechable en hierba seca es mala idea. El número del parque no está aquí."))],
         [L("112", "112", "112", "112", "112", "112")],
         ensure_hero("hulp-brandweer.html", "noodgevallen.jpg"),
         "noodgevallen.html", BACK_HELP, "fire station Kos", NOTE_PHONE)

    page("hulp-huisartsen.html",
         L("Huisartsen", "Hausärzte", "General practitioners", "Medici di base", "Aile hekimleri", "Médicos de cabecera"),
         L("De gids deelde huisartsen in per streek: Kos-stad, Tigaki en Psalidi. De namen, telefoons en adressen zijn op deze pagina nog niet ingevuld.",
           "Der Guide teilte Hausärzte nach Gegend: Kos-Stadt, Tigaki und Psalidi. Namen, Telefone und Adressen fehlen auf dieser Seite noch.",
           "The guide split general practitioners by area: Kos town, Tigaki and Psalidi. Names, phones and addresses are not filled in on this page yet.",
           "La guida divideva i medici per zona: città di Kos, Tigaki e Psalidi. Nomi, telefoni e indirizzi non sono ancora in questa pagina.",
           "Rehber aile hekimlerini yöreye göre ayırdı: Kos şehri, Tigaki ve Psalidi. İsim, telefon ve adres bu sayfada henüz yok.",
           "La guía repartía los médicos por zona: ciudad de Kos, Tigaki y Psalidi. Nombres, teléfonos y direcciones aún no están en esta página."),
         [(L("Spoed", "Notfall", "Emergency", "Urgenza", "Acil", "Urgencia"),
          L("Voor een noodgeval ga je niet wachten op een afspraak. Bel 112 of 166 (ambulance) of ga naar het ziekenhuis.",
            "Im Notfall wartest du nicht auf einen Termin. Ruf 112 oder 166 (Rettung) oder geh ins Krankenhaus.",
            "In an emergency do not wait for an appointment. Call 112 or 166 (ambulance) or go to the hospital.",
            "In emergenza non aspetti un appuntamento. Chiama il 112 o il 166 (ambulanza) o vai in ospedale.",
            "Acilde randevu bekleme. 112 veya 166’yı (ambulans) ara ya da hastaneye git.",
            "En una urgencia no esperes una cita. Llama al 112 o al 166 (ambulancia) o ve al hospital."))],
         [L("Per streek", "Nach Gegend", "By area", "Per zona", "Yöreye göre", "Por zona")],
         ensure_hero("hulp-huisartsen.html", "noodgevallen.jpg"),
         "noodgevallen.html", BACK_HELP, "doctor Kos", NOTE_PHONE)

    page("hulp-tandarts.html",
         L("Tandarts", "Zahnarzt", "Dentist", "Dentista", "Diş hekimi", "Dentista"),
         L("De gids noemde praktijken voor een afgebroken tand of een spoed, onder meer Georgios & Koutsouradis en George Hatzinikitas, en ook een praktijk bij Bar Street en een bij de rotonde. Telefoon en adres staan hier niet.",
           "Der Guide nannte Praxen für einen abgebrochenen Zahn oder einen Notfall, unter anderem Georgios & Koutsouradis und George Hatzinikitas, und auch eine Praxis bei Bar Street und eine am Kreisverkehr. Telefon und Adresse stehen hier nicht.",
           "The guide named practices for a broken tooth or an emergency, including Georgios & Koutsouradis and George Hatzinikitas, and also a practice by Bar Street and one by the roundabout. Phone and address are not written here.",
           "La guida citava studi per un dente rotto o un’urgenza, tra cui Georgios & Koutsouradis e George Hatzinikitas, e anche uno studio verso Bar Street e uno alla rotonda. Telefono e indirizzo non sono scritti qui.",
           "Rehber kırık diş veya acil için muayenehaneler saydı, Georgios & Koutsouradis ve George Hatzinikitas dahil, ayrıca Bar Street tarafında ve kavşakta bir muayenehane. Telefon ve adres burada yok.",
           "La guía citaba consultas para un diente roto o una urgencia, entre ellas Georgios & Koutsouradis y George Hatzinikitas, y también una hacia Bar Street y una en la rotonda. Teléfono y dirección no están aquí."),
         [(L("Pijn", "Schmerz", "Pain", "Dolore", "Ağrı", "Dolor"),
          L("Apotheken kunnen soms helpen tot je een tandarts ziet. Het ziekenhuis is voor echte spoed.",
            "Apotheken können manchmal helfen, bis du einen Zahnarzt siehst. Das Krankenhaus ist für echte Notfälle.",
            "A pharmacy can sometimes help until you see a dentist. The hospital is for a real emergency.",
            "Una farmacia a volte aiuta finché non vedi un dentista. L’ospedale è per una vera urgenza.",
            "Diş hekimini görene kadar eczane bazen yardım eder. Hastane gerçek acil içindir.",
            "Una farmacia a veces ayuda hasta que ves al dentista. El hospital es para una urgencia de verdad."))],
         [BADGE_CHECK], ensure_hero("hulp-tandarts.html", "noodgevallen.jpg"),
         "noodgevallen.html", BACK_HELP, "dentist Kos town", NOTE_PHONE)

    page("hulp-waterbedrijf.html",
         L("Waterbedrijf", "Wasserwerk", "Water company", "Acquedotto", "Su idaresi", "Compañía del agua"),
         L("Het waterbedrijf van de gemeente Kos heet Δ.Ε.Υ.Α. Δήμου Κω (DEYAK). Het telefoonnummer voor een storing staat op deze pagina nog niet.",
           "Das Wasserwerk der Gemeinde Kos heißt Δ.Ε.Υ.Α. Δήμου Κω (DEYAK). Die Telefonnummer bei einer Störung steht auf dieser Seite noch nicht.",
           "The water company of the municipality of Kos is called Δ.Ε.Υ.Α. Δήμου Κω (DEYAK). The phone number for a fault is not on this page yet.",
           "L’acquedotto del comune di Kos si chiama Δ.Ε.Υ.Α. Δήμου Κω (DEYAK). Il numero per un guasto non è ancora in questa pagina.",
           "Kos belediyesinin su idaresi Δ.Ε.Υ.Α. Δήμου Κω (DEYAK) adını taşır. Arıza telefonu bu sayfada henüz yok.",
           "La compañía de agua del municipio de Kos se llama Δ.Ε.Υ.Α. Δήμου Κω (DEYAK). El teléfono de una avería aún no está en esta página."),
         [(L("Kraan", "Hahn", "Tap", "Rubinetto", "Musluk", "Grifo"),
          L("Of je het kraanwater drinkt, staat bij Water en ijsklontjes. Een lege kraan in één huis is iets anders dan een storing in de wijk.",
            "Ob du das Leitungswasser trinkst, steht bei Wasser und Eiswürfel. Ein leerer Hahn in einem Haus ist etwas anderes als eine Störung im Viertel.",
            "Whether you drink the tap water is under Water and ice cubes. An empty tap in one house is different from a fault in the neighbourhood.",
            "Se bevi l’acqua del rubinetto è sotto Acqua e ghiaccio. Un rubinetto vuoto in una casa è diverso da un guasto nel quartiere.",
            "Musluk suyunu içip içmeyeceğin Su ve buz küpleri altında. Tek evde boş musluk, mahalle arızasından farklıdır.",
            "Si bebes el agua del grifo está en Agua y hielo. Un grifo vacío en una casa no es lo mismo que una avería en el barrio."))],
         [L("DEYAK", "DEYAK", "DEYAK", "DEYAK", "DEYAK", "DEYAK")],
         ensure_hero("hulp-waterbedrijf.html", "wjd-water.jpg"),
         "noodgevallen.html", BACK_HELP, "DEYAK Kos water", NOTE_PHONE)

    page("hulp-stroomuitval.html",
         L("Stroomuitval", "Stromausfall", "Power cut", "Blackout", "Elektrik kesintisi", "Corte de luz"),
         L("Het netbeheer heet ΔΕΔΔΗΕ (HEDNO). Geplande onderbrekingen komen voor. Zonder stroom werken pinapparaten niet. Het storingsnummer staat hier nog niet.",
           "Der Netzbetreiber heißt ΔΕΔΔΗΕ (HEDNO). Geplante Abschaltungen kommen vor. Ohne Strom funktionieren Kartengeräte nicht. Die Störungsnummer steht hier noch nicht.",
           "The grid operator is called ΔΕΔΔΗΕ (HEDNO). Planned cuts happen. Without power, card machines do not work. The fault number is not written here yet.",
           "Il gestore della rete si chiama ΔΕΔΔΗΕ (HEDNO). Le interruzioni programmate capitano. Senza corrente i POS non funzionano. Il numero guasti non è ancora scritto qui.",
           "Şebeke işletmecisi ΔΕΔΔΗΕ (HEDNO) adını taşır. Planlı kesintiler olur. Elektrik yokken kart cihazları çalışmaz. Arıza numarası burada henüz yok.",
           "El operador de la red se llama ΔΕΔΔΗΕ (HEDNO). Hay cortes previstos. Sin luz, los datáfonos no funcionan. El número de averías aún no está aquí."),
         [(L("Wat jij kunt doen", "Was du tun kannst", "What you can do", "Cosa puoi fare", "Ne yapabilirsin", "Qué puedes hacer"),
          L("Kijk of alleen jouw huis donker is of de hele straat. Een zaklamp op je telefoon helpt. Lift niet gebruiken als het licht uitgaat. Neem wat contant geld mee, juist omdat pinnen dan stopt.",
            "Schau, ob nur dein Haus dunkel ist oder die ganze Straße. Eine Taschenlampe am Telefon hilft. Fahrstuhl nicht benutzen, wenn das Licht ausgeht. Nimm etwas Bargeld mit, gerade weil Kartenzahlung dann stoppt.",
            "See if only your house is dark or the whole street. A phone torch helps. Do not use the lift if the lights go out. Carry some cash, because card payments stop.",
            "Guarda se è buia solo casa tua o tutta la via. La torcia del telefono aiuta. Non usare l’ascensore se si spegne la luce. Porta dei contanti, perché il bancomat si ferma.",
            "Yalnız evin mi karanlık yoksa bütün sokak mı bak. Telefon feneri işe yarar. Işık gidince asansöre binme. Kart çalışmadığı için biraz nakit taşı.",
            "Mira si solo tu casa está a oscuras o toda la calle. La linterna del teléfono ayuda. No uses el ascensor si se va la luz. Lleva algo de efectivo, porque el pago con tarjeta se para."))],
         [L("ΔΕΔΔΗΕ", "ΔΕΔΔΗΕ", "HEDNO", "HEDNO", "HEDNO", "HEDNO")],
         ensure_hero("hulp-stroomuitval.html", "noodgevallen.jpg"),
         "noodgevallen.html", BACK_HELP, "HEDNO Kos power", NOTE_PHONE)

    page("transfer.html",
         L("Transfer", "Transfer", "Transfer", "Transfer", "Transfer", "Transfer"),
         L("Een transfer is een afgesproken rit, vaak vanaf het vliegveld of de haven naar je hotel. Hello Kos rijdt zelf niet. De chauffeur is de vervoerder. Een aanvraag is pas een rit als die vervoerder bevestigt.",
           "Ein Transfer ist eine verabredete Fahrt, oft vom Flughafen oder Hafen zum Hotel. Hello Kos fährt nicht selbst. Der Fahrer ist der Beförderer. Eine Anfrage ist erst eine Fahrt, wenn dieser Beförderer bestätigt.",
           "A transfer is an agreed ride, often from the airport or the port to your hotel. Hello Kos does not drive itself. The driver is the carrier. A request is only a ride when that carrier confirms.",
           "Un transfer è una corsa concordata, spesso dall’aeroporto o dal porto all’hotel. Hello Kos non guida. L’autista è il vettore. Una richiesta è una corsa solo quando quel vettore conferma.",
           "Transfer, çoğu zaman havalimanı veya limandan otele kararlaştırılmış bir yoldur. Hello Kos kendisi sürmez. Sürücü taşıyıcıdır. Talep, taşıyıcı onaylarsa yolculuk olur.",
           "Un transfer es un trayecto acordado, a menudo del aeropuerto o del puerto al hotel. Hello Kos no conduce. El conductor es el transportista. Una solicitud es un viaje solo cuando ese transportista confirma."),
         [(L("Prijs", "Preis", "Price", "Prezzo", "Fiyat", "Precio"),
          L("Spreek de prijs af vóór je instapt. Op Kos is de meter wettelijk verplicht, maar in de praktijk hoor je vaak een vaste prijs, zeker vanaf het vliegveld. Vraag: meter of vaste prijs? Stand 1 is dag, stand 2 is nacht.",
            "Vereinbare den Preis, bevor du einsteigst. Auf Kos ist der Taxameter gesetzlich Pflicht, in der Praxis hörst du oft einen Festpreis, sicher ab dem Flughafen. Frag: Taxameter oder Festpreis? Stufe 1 ist Tag, Stufe 2 ist Nacht.",
            "Agree the price before you get in. On Kos the meter is required by law, but in practice you often hear a fixed price, especially from the airport. Ask: meter or fixed price? Tariff 1 is day, tariff 2 is night.",
            "Accorda il prezzo prima di salire. A Kos il tassametro è obbligatorio per legge, ma in pratica senti spesso un prezzo fisso, soprattutto dall’aeroporto. Chiedi: tassametro o prezzo fisso? Tariffa 1 è giorno, tariffa 2 è notte.",
            "Binmeden fiyatı konuş. Kos’ta taksimetre yasal olarak zorunlu, ama pratikte özellikle havalimanından sabit fiyat duyarsın. Sor: taksimetre mi sabit fiyat mı? Kademe 1 gündüz, kademe 2 gece.",
            "Acuerda el precio antes de subir. En Kos el taxímetro es obligatorio por ley, pero en la práctica oyes a menudo un precio fijo, sobre todo desde el aeropuerto. Pregunta: ¿taxímetro o precio fijo? Tarifa 1 es de día, tarifa 2 de noche.")),
         (L("Bus", "Bus", "Bus", "Bus", "Otobüs", "Bus"),
          L("De lokale bus is goedkoper en staat op de pagina Openbaar vervoer. Een taxi of transfer is handig met koffers of laat op de avond.",
            "Der lokale Bus ist günstiger und steht auf der Seite Öffentliche Verkehrsmittel. Taxi oder Transfer ist praktisch mit Koffern oder spätabends.",
            "The local bus is cheaper and is on the Public transport page. A taxi or transfer is useful with suitcases or late at night.",
            "Il bus locale è più economico ed è nella pagina Trasporto pubblico. Taxi o transfer è comodo con le valigie o a tarda sera.",
            "Yerel otobüs daha ucuzdur ve Toplu taşıma sayfasındadır. Bavulla veya geç saatte taksi ya da transfer işe yarar.",
            "El bus local es más barato y está en Transporte público. Un taxi o transfer viene bien con maletas o tarde por la noche."))],
         [L("Vliegveld", "Flughafen", "Airport", "Aeroporto", "Havalimanı", "Aeropuerto"), BADGE_CHECK],
         "taxi-bussen.jpg", "taxi-bussen.html", BACK_TAXI, "Kos airport transfer", NOTE_PRICE)


def write_wjd():
    page("fooien.html",
         L("Fooien", "Trinkgeld", "Tipping", "Mance", "Bahşiş", "Propinas"),
         L("Een fooi is vrijwillig. De gids zei: onder de €1 kan bot overkomen, behalve bij een koffie of een heel kleine bestelling.",
           "Trinkgeld ist freiwillig. Der Guide sagte: unter €1 kann unhöflich wirken, außer bei einem Kaffee oder einer sehr kleinen Bestellung.",
           "A tip is voluntary. The guide said: under €1 can feel rude, except for a coffee or a very small order.",
           "La mancia è volontaria. La guida diceva: sotto €1 può sembrare scortese, tranne per un caffè o un ordine molto piccolo.",
           "Bahşiş isteğe bağlıdır. Rehber diyordu: 1 € altı kaba gelebilir, kahve veya çok küçük bir sipariş hariç.",
           "La propina es voluntaria. La guía decía: menos de 1 € puede parecer grosero, salvo un café o un pedido muy pequeño."),
         [(L("Hoeveel", "Wie viel", "How much", "Quanto", "Ne kadar", "Cuánto"),
          L("In een restaurant of taverne is 5 tot 10 procent gebruikelijk. In een café vaak een euro of een paar euro. Bij een taxi rond je naar boven af, iets meer als de chauffeur met koffers helpt. In een hotel een paar euro per dag voor de kamer, of aan het eind van het verblijf. Bij een excursie vaak 2 tot 5 euro per persoon.",
            "Im Restaurant oder in der Taverne sind 5 bis 10 Prozent üblich. Im Café oft ein Euro oder ein paar Euro. Beim Taxi rundest du auf, etwas mehr, wenn der Fahrer mit Koffern hilft. Im Hotel ein paar Euro pro Tag fürs Zimmer oder am Ende. Bei einer Tour oft 2 bis 5 Euro pro Person.",
            "In a restaurant or taverna 5 to 10 percent is usual. In a café often one euro or a few euros. For a taxi you round up, a bit more if the driver helps with bags. In a hotel a few euros a day for the room, or at the end of the stay. On an excursion often 2 to 5 euros per person.",
            "In un ristorante o in taverna è normale il 5–10 percento. In un caffè spesso un euro o pochi euro. In taxi arrotondi per eccesso, un po’ di più se l’autista aiuta con le valigie. In hotel pochi euro al giorno per la camera, o alla fine. In un’escursione spesso 2–5 euro a persona.",
            "Restoran veya tavernada yüzde 5–10 normaldir. Kafede çoğu zaman bir veya birkaç euro. Taksinde yukarı yuvarlarsın, şoför bavula yardım ederse biraz daha. Otelde oda için günde birkaç euro ya da çıkışta. Turda çoğu zaman kişi başı 2–5 euro.",
            "En un restaurante o taberna es habitual del 5 al 10 por ciento. En un café a menudo un euro o unos euros. En un taxi redondeas hacia arriba, un poco más si el conductor ayuda con las maletas. En un hotel unos euros al día por la habitación, o al final. En una excursión a menudo de 2 a 5 euros por persona.")),
         (L("Contant", "Bar", "Cash", "Contanti", "Nakit", "Efectivo"),
          L("Geef de fooi contant. Via de pin komt het geld niet altijd bij het personeel, en het kan als omzet worden gezien.",
            "Gib das Trinkgeld bar. Über die Karte kommt das Geld nicht immer beim Personal an und kann als Umsatz gelten.",
            "Give the tip in cash. By card the money does not always reach the staff, and it can be treated as turnover.",
            "Dai la mancia in contanti. Con la carta i soldi non arrivano sempre al personale e possono contare come incasso.",
            "Bahşişi nakit ver. Kartla para her zaman personele ulaşmaz ve ciro sayılabilir.",
            "Da la propina en efectivo. Con tarjeta el dinero no siempre llega al personal y puede contar como ingreso."))],
         [L("Vrijwillig", "Freiwillig", "Voluntary", "Volontaria", "İsteğe bağlı", "Voluntaria")],
         "wjd-fooien.jpg", "wist-je-dat.html", BACK_WJD, None, None)

    page("afgeknipte-oren.html",
         L("Katten met een geknipt oor", "Katzen mit gekipptem Ohr", "Cats with a tipped ear", "Gatti con l’orecchio tagliato", "Kulağı kesik kediler", "Gatos con la oreja cortada"),
         L("Een recht afgeknipt puntje aan het oor is een teken uit een TNR-programma: de kat is gevangen, gecastreerd of gesteriliseerd, nagekeken en weer vrijgelaten. Het is geen mishandeling.",
           "Eine gerade gekappte Ohrspitze ist ein Zeichen aus einem TNR-Programm: die Katze wurde gefangen, kastriert, untersucht und wieder freigelassen. Es ist keine Misshandlung.",
           "A straight cut tip on the ear is a sign from a TNR programme: the cat was trapped, neutered or spayed, checked and released. It is not abuse.",
           "Una punta d’orecchio tagliata dritta è un segno di un programma TNR: il gatto è stato catturato, sterilizzato, controllato e liberato. Non è maltrattamento.",
           "Kulağın düz kesilmiş ucu bir TNR programının işaretidir: kedi yakalanmış, kısırlaştırılmış, kontrol edilmiş ve bırakılmıştır. Bu kötü muamele değildir.",
           "Una punta de oreja cortada recta es una señal de un programa TNR: el gato fue capturado, esterilizado, revisado y soltado. No es maltrato."),
         [(L("Wat jij doet", "Was du tust", "What you do", "Cosa fai", "Ne yaparsın", "Qué haces"),
          L("Je hoeft niet te schrikken. De gids noemde N-Joy in Kos-stad: een zaak van de Nederlandse Nicolle die katten laat castreren. Meer over zwerfkatten staat op de eigen pagina.",
            "Du musst nicht erschrecken. Der Guide nannte N-Joy in Kos-Stadt: ein Lokal der Niederländerin Nicolle, das Katzen kastrieren lässt. Mehr über Streuner steht auf der eigenen Seite.",
            "You do not need to be alarmed. The guide named N-Joy in Kos town: a place run by the Dutch owner Nicolle that has cats neutered. More about strays is on its own page.",
            "Non devi spaventarti. La guida citava N-Joy in città: un locale della olandese Nicolle che fa sterilizzare i gatti. Altro sui randagi è nella pagina dedicata.",
            "Korkmana gerek yok. Rehber Kos şehrinde N-Joy’u saydı: Hollandalı Nicolle’in işlettiği, kedileri kısırlaştıran bir yer. Sokak kedileri kendi sayfasında.",
            "No hace falta asustarse. La guía citaba N-Joy en la ciudad: un local de la holandesa Nicolle que esteriliza gatos. Más sobre callejeros está en su página."))],
         [L("TNR", "TNR", "TNR", "TNR", "TNR", "TNR")],
         "wjd-afgeknipte-oren.jpg", "wist-je-dat.html", BACK_WJD, None, None)

    page("cash-of-card.html",
         L("Contant of pin", "Bar oder Karte", "Cash or card", "Contanti o carta", "Nakit veya kart", "Efectivo o tarjeta"),
         L("Winkels en horeca moeten pin kunnen aannemen, maar contant is nog geliefd. Pinnen kost de ondernemer geld. Een storing legt de betaalautomaat stil.",
           "Läden und Lokale müssen Karte annehmen können, aber bar ist noch beliebt. Kartenzahlung kostet den Betrieb Geld. Eine Störung legt das Gerät lahm.",
           "Shops and restaurants must be able to take cards, but cash is still preferred. Card payments cost the owner money. A power cut stops the terminal.",
           "Negozi e locali devono poter accettare la carta, ma il contante è ancora gradito. La carta costa soldi al gestore. Un blackout ferma il POS.",
           "Dükkan ve lokantalar kart kabul edebilmeli, ama nakit hâlâ sevilir. Kart işletmeye paraya mal olur. Kesinti terminali durdurur.",
           "Tiendas y bares deben poder cobrar con tarjeta, pero el efectivo sigue gustando. La tarjeta le cuesta dinero al dueño. Un corte para el datáfono."),
         [(L("Geldautomaat", "Geldautomat", "Cash machine", "Bancomat", "Bankamatik", "Cajero"),
          L("De automaat zelf kan een paar euro rekenen. De gids noemde ongeveer €2,50 tot soms €6, bovenop je eigen bank. Lees het scherm vóór je bevestigt. Fooi geef je liever contant.",
            "Der Automat selbst kann ein paar Euro verlangen. Der Guide nannte etwa €2,50 bis manchmal €6, zusätzlich zu deiner Bank. Lies den Bildschirm, bevor du bestätigst. Trinkgeld gibst du lieber bar.",
            "The machine itself can charge a few euros. The guide mentioned about €2.50 up to sometimes €6, on top of your own bank. Read the screen before you confirm. Give tips in cash.",
            "Il bancomat stesso può chiedere qualche euro. La guida indicava circa €2,50 fino a volte €6, oltre alla tua banca. Leggi lo schermo prima di confermare. La mancia meglio in contanti.",
            "Makinenin kendisi birkaç euro kesebilir. Rehber yaklaşık 2,50 € ile bazen 6 € diyordu, kendi bankana ek. Onaylamadan ekranı oku. Bahşişi nakit ver.",
            "El cajero mismo puede cobrar unos euros. La guía citaba unos 2,50 € y a veces hasta 6 €, además de tu banco. Lee la pantalla antes de confirmar. La propina mejor en efectivo."))],
         [L("Pin en cash", "Karte und bar", "Card and cash", "Carta e contanti", "Kart ve nakit", "Tarjeta y efectivo")],
         "wjd-cash-card.jpg", "wist-je-dat.html", BACK_WJD, "ATM Kos town", None)

    page("eenoudertoestemming.html",
         L("Toestemming van één ouder", "Einverständnis eines Elternteils", "Consent of one parent", "Consenso di un genitore", "Tek ebeveyn onayı", "Consentimiento de un progenitor"),
         L("Reis je met een kind en de andere ouder is er niet bij, dan vragen luchtvaartmaatschappijen en sommige landen een toestemmingsbrief. De gids raadde een brief in het Engels aan, soms bij de notaris, plus een kopie van de geboorteakte.",
           "Reist du mit einem Kind und der andere Elternteil ist nicht dabei, verlangen Fluggesellschaften und manche Länder eine Einverständniserklärung. Der Guide riet zu einem Brief auf Englisch, manchmal beim Notar, plus einer Kopie der Geburtsurkunde.",
           "If you travel with a child and the other parent is not there, airlines and some countries ask for a consent letter. The guide advised a letter in English, sometimes notarised, plus a copy of the birth certificate.",
           "Se viaggi con un bambino e l’altro genitore non c’è, le compagnie e alcuni paesi chiedono una lettera di consenso. La guida consigliava una lettera in inglese, a volte dal notaio, più una copia dell’atto di nascita.",
           "Çocukla seyahat ediyorsan ve diğer ebeveyn yoksa, havayolları ve bazı ülkeler onay mektubu ister. Rehber İngilizce bir mektup, bazen noterli, ve doğum belgesinin kopyasını önerdi.",
           "Si viajas con un niño y el otro progenitor no está, las aerolíneas y algunos países piden una carta de consentimiento. La guía aconsejaba una carta en inglés, a veces ante notario, más una copia del acta de nacimiento."),
         [(L("Regels verschillen", "Regeln unterscheiden sich", "Rules differ", "Le regole cambiano", "Kurallar değişir", "Las normas cambian"),
          L("Dit is geen wetstekst. Vraag het na bij je airline en, voor een dagtocht naar Bodrum, bij de Turkse regels. Een printwinkel op Kos kan een brief printen als je die nog per mail krijgt. Het adres van die winkel is hier nog niet ingevuld.",
            "Das ist kein Gesetzestext. Frag bei deiner Airline und, für einen Tagesausflug nach Bodrum, bei den türkischen Regeln nach. Ein Copyshop auf Kos kann einen Brief drucken, wenn du ihn noch per Mail bekommst. Die Adresse dieses Ladens fehlt hier noch.",
            "This is not a statute. Check with your airline and, for a day trip to Bodrum, with the Turkish rules. A print shop on Kos can print a letter if it is still emailed to you. That shop’s address is not filled in here yet.",
            "Questo non è un testo di legge. Verifica con la compagnia e, per una gita a Bodrum, con le regole turche. Un negozio di stampe a Kos può stampare una lettera se te la mandano ancora per mail. L’indirizzo di quel negozio non è ancora qui.",
            "Bu bir kanun metni değil. Havayoluna ve Bodrum günübirlik için Türk kurallarına sor. Mektup hâlâ e-postayla gelirse Kos’ta bir baskı dükkanı basabilir. O dükkanın adresi burada henüz yok.",
            "Esto no es un texto legal. Consúltalo con tu aerolínea y, para un día a Bodrum, con las normas turcas. Una copistería en Kos puede imprimir una carta si aún te la envían por correo. La dirección de esa tienda aún no está aquí."))],
         [L("Kinderen", "Kinder", "Children", "Bambini", "Çocuklar", "Niños")],
         "wjd-eenoudertoestemming.jpg", "wist-je-dat.html", BACK_WJD, None,
         L("Het adres van de printwinkel is nog niet ingevuld.",
           "Die Adresse des Copyshops ist noch nicht eingetragen.",
           "The print shop address is not filled in yet.",
           "L’indirizzo del negozio di stampe non è ancora inserito.",
           "Baskı dükkanının adresi henüz yok.",
           "La dirección de la copistería aún no está.",
           ))

    page("kinderserie.html",
         L("Kinderserie Nikos & Eleni", "Kinderserie Nikos & Eleni", "Kids’ series Nikos & Eleni", "Serie per bambini Nikos & Eleni", "Çocuk dizisi Nikos & Eleni", "Serie infantil Nikos y Eleni"),
         L("Hello Kos heeft een kinderserie over Nikos en Eleni. De afleveringen staan nog niet op deze site.",
           "Hello Kos hat eine Kinderserie über Nikos und Eleni. Die Folgen stehen noch nicht auf dieser Website.",
           "Hello Kos has a children’s series about Nikos and Eleni. The episodes are not on this site yet.",
           "Hello Kos ha una serie per bambini su Nikos ed Eleni. Gli episodi non sono ancora su questo sito.",
           "Hello Kos’un Nikos ve Eleni hakkında bir çocuk dizisi var. Bölümler bu sitede henüz yok.",
           "Hello Kos tiene una serie infantil sobre Nikos y Eleni. Los episodios aún no están en este sitio."),
         [(L("Taal", "Sprache", "Language", "Lingua", "Dil", "Idioma"),
          L("De oude site had een Nederlandse versie. Die films zijn hier nog niet geplaatst, zodat er geen dode link ontstaat.",
            "Die alte Website hatte eine niederländische Fassung. Die Filme sind hier noch nicht eingebunden, damit kein toter Link entsteht.",
            "The old site had a Dutch version. Those films are not placed here yet, so there is no dead link.",
            "Il vecchio sito aveva una versione olandese. Quei filmati non sono ancora messi qui, così non c’è un link morto.",
            "Eski sitede Hollandaca bir sürüm vardı. O filmler burada henüz yok, böylece ölü bağlantı olmaz.",
            "El sitio antiguo tenía una versión en neerlandés. Esos vídeos aún no están aquí, para que no haya un enlace muerto."))],
         [L("Kinderen", "Kinder", "Children", "Bambini", "Çocuklar", "Niños")],
         "wjd-kinderserie.jpg", "wist-je-dat.html", BACK_WJD, None,
         L("De afleveringen zelf zijn nog niet ingevuld.",
           "Die Folgen selbst sind noch nicht eingetragen.",
           "The episodes themselves are not filled in yet.",
           "Gli episodi stessi non sono ancora inseriti.",
           "Bölümlerin kendisi henüz yok.",
           "Los episodios en sí aún no están.",
           ))


def write_walk():
    stops = [
        ("sight-neratzia.html", L("1. Kasteel Neratzia", "1. Burg Neratzia", "1. Neratzia castle", "1. Castello di Neratzia", "1. Neratzia kalesi", "1. Castillo de Neratzia")),
        ("sight-palm-tree-lane.html", L("2. Palm Tree Lane", "2. Palm Tree Lane", "2. Palm Tree Lane", "2. Palm Tree Lane", "2. Palm Tree Lane", "2. Palm Tree Lane")),
        ("sight-i-love-kos.html", L("3. I love Kos", "3. I love Kos", "3. I love Kos", "3. I love Kos", "3. I love Kos", "3. I love Kos")),
        ("sight-witte-trappen.html", L("4. Witte trappen", "4. Weiße Treppe", "4. White steps", "4. Scale bianche", "4. Beyaz merdiven", "4. Escaleras blancas")),
        ("sight-old-town.html", L("5. Oude stad", "5. Altstadt", "5. Old town", "5. Città vecchia", "5. Eski şehir", "5. Casco antiguo")),
        ("sight-agora.html", L("6. Agora", "6. Agora", "6. Agora", "6. Agorà", "6. Agora", "6. Ágora")),
        ("sight-paraskevi.html", L("7. Agia Paraskevi", "7. Agia Paraskevi", "7. Agia Paraskevi", "7. Agia Paraskevi", "7. Agia Paraskevi", "7. Agia Paraskevi")),
        ("sight-odeon.html", L("8. Odeon", "8. Odeon", "8. Odeon", "8. Odeon", "8. Odeon", "8. Odeón")),
        ("sight-boom-hippocrates.html", L("9. Boom van Hippocrates", "9. Baum des Hippokrates", "9. Hippocrates’ tree", "9. Albero di Ippocrate", "9. Hipokrat ağacı", "9. Árbol de Hipócrates")),
        ("sight-asklepion.html", L("10. Asklepion (buiten de stad)", "10. Asklepion (außerhalb)", "10. Asklepion (outside town)", "10. Asklepion (fuori città)", "10. Asklepion (şehir dışı)", "10. Asklepion (fuera)")),
    ]
    # Build as article with HTML links inside paragraphs would be heavy.
    # Use hub-like list by writing a custom page: reuse page() sections as text and add a link list via note? 
    # I'll write sections as short and then a links block by using innerHTML in one paragraph.
    links_nl = "<br>".join('<a href="%s">%s</a>' % (h, lab["nl"]) for h, lab in stops)
    # For other languages, build per lang inside L by doing it in the paragraph dict.
    paras = {}
    for lang in LANGS:
        paras[lang] = "<br>".join('<a href="%s">%s</a>' % (h, lab[lang]) for h, lab in stops)
    # page() will put paragraph in HTML and in JSON. The Dutch default is paras['nl']. Good if I pass L via a dict already.
    lead = L(
        "Een wandeling door Kos-stad, van de haven naar het centrum. Het Asklepion ligt buiten de stad en is een stuk verder. Doe het in de ochtend of laat op de dag, niet in de volle zon.",
        "Ein Spaziergang durch Kos-Stadt, vom Hafen ins Zentrum. Das Asklepion liegt außerhalb und ist ein Stück weiter. Mach es morgens oder spät am Tag, nicht in der prallen Sonne.",
        "A walk through Kos town, from the harbour to the centre. The Asklepion is outside town and a good bit further. Do it in the morning or late in the day, not in full sun.",
        "Una passeggiata per la città, dal porto al centro. L’Asklepion è fuori città ed è più lontano. Fallo al mattino o a fine giornata, non sotto il sole pieno.",
        "Kos şehrinde limandan merkeze bir yürüyüş. Asklepion şehir dışındadır ve daha uzaktır. Sabah ya da günün sonunda yap, tam güneşte değil.",
        "Un paseo por la ciudad, del puerto al centro. El Asklepion está fuera y queda más lejos. Hazlo por la mañana o al final del día, no a pleno sol.",
    )
    heading = L("De haltepunten", "Die Stopps", "The stops", "Le tappe", "Duraklar", "Las paradas")
    body = {"nl": paras["nl"], "de": paras["de"], "en": paras["en"], "it": paras["it"], "tr": paras["tr"], "es": paras["es"]}
    img = ensure_hero("route-wandel.html", "bezienswaardigheden.jpg")
    # download a real photo if possible from witte trappen page later via fix. 
    page("route-wandel.html",
         L("Wandelroute Kos-stad", "Spaziergang Kos-Stadt", "Kos town walk", "Passeggiata Kos città", "Kos şehri yürüyüşü", "Paseo por la ciudad de Kos"),
         lead,
         [(heading, body),
          (L("Zelf kiezen", "Selbst wählen", "Choose yourself", "Scegli tu", "Kendin seç", "Elige tú"),
           L("Op de pagina Radar Kos-stad (vrije route) staan dezelfde plekken als losse punten. Met de auto is er een route van 1 dag en van 2 dagen.",
             "Auf der Seite Radar Kos-Stadt (freie Route) stehen dieselben Orte als einzelne Punkte. Mit dem Auto gibt es eine Route für 1 Tag und für 2 Tage.",
             "On the Kos town radar page (free route) the same places are separate points. By car there is a 1-day route and a 2-day route.",
             "Nella pagina radar di Kos città (percorso libero) gli stessi luoghi sono punti separati. In auto c’è un percorso di 1 giorno e uno di 2.",
             "Kos şehri radar sayfasında (serbest rota) aynı yerler ayrı noktalar. Arabayla 1 günlük ve 2 günlük rota var.",
             "En la página radar de la ciudad (ruta libre) los mismos sitios son puntos sueltos. En coche hay una ruta de 1 día y una de 2."))],
         [BADGE_FREE, BADGE_TOWN], img, "bezienswaardigheden.html", BACK_SIGHT, "Kos town harbour", None)


if __name__ == "__main__":
    build()
