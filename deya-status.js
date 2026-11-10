/* Water notices from data/deya-outages.json.
   The browser cannot read deyakos.gr itself (no CORS).
   A scheduled job refreshes that file from the official ΔΕΥΑΚ feed. */
(function () {
  var LOCALES = { nl: "nl-NL", de: "de-DE", en: "en-GB", it: "it-IT", tr: "tr-TR", es: "es-ES" };
  var HOUR = 36 * 60 * 60 * 1000;
  var TEXT = {
    nl: {
      loading: "De meldingen van ΔΕΥΑΚ worden geladen…",
      fail: "De meldingen konden niet geladen worden. Probeer het later opnieuw.",
      none: "Geen lopende of komende melding in de laatste aankondigingen.",
      now: "Er is een melding die nu geldt.",
      soon: "Er is een komende melding. Nu staat er niets als lopend.",
      past: "Geen lopende of komende melding. De laatste aankondiging hieronder is al voorbij.",
      planned: "Werkzaamheden",
      fault: "Storing",
      announced: "Aankondiging",
      when: "Van {from} tot {to}",
      until: "Tot {to}",
      official: "Tekst van ΔΕΥΑΚ (Grieks)",
      checked: "Lijst opgehaald: {time}. Ongeveer elk uur ververst.",
      hint: "De meldingen gaan over gebieden, niet over één gebouw."
    },
    de: {
      loading: "Die Meldungen von ΔΕΥΑΚ werden geladen…",
      fail: "Die Meldungen konnten nicht geladen werden. Versuch es später noch einmal.",
      none: "Keine laufende oder kommende Meldung in den letzten Ankündigungen.",
      now: "Es gibt eine Meldung, die jetzt gilt.",
      soon: "Es gibt eine kommende Meldung. Gerade läuft nichts.",
      past: "Keine laufende oder kommende Meldung. Die letzte Ankündigung unten ist schon vorbei.",
      planned: "Arbeiten",
      fault: "Störung",
      announced: "Ankündigung",
      when: "Von {from} bis {to}",
      until: "Bis {to}",
      official: "Text von ΔΕΥΑΚ (Griechisch)",
      checked: "Liste geholt: {time}. Wird etwa stündlich erneuert.",
      hint: "Die Meldungen gelten für Gebiete, nicht für ein einzelnes Gebäude."
    },
    en: {
      loading: "Loading the ΔΕΥΑΚ notices…",
      fail: "The notices could not be loaded. Try again later.",
      none: "No current or upcoming notice in the latest announcements.",
      now: "There is a notice in force now.",
      soon: "There is an upcoming notice. Nothing is listed as happening right now.",
      past: "No current or upcoming notice. The latest announcement below is already over.",
      planned: "Works",
      fault: "Fault",
      announced: "Announcement",
      when: "From {from} until {to}",
      until: "Until {to}",
      official: "Text from ΔΕΥΑΚ (Greek)",
      checked: "List fetched: {time}. Refreshed about once an hour.",
      hint: "The notices are about areas, not about one building."
    },
    it: {
      loading: "Caricamento degli avvisi ΔΕΥΑΚ…",
      fail: "Gli avvisi non si sono caricati. Riprova più tardi.",
      none: "Nessun avviso in corso o in arrivo tra gli ultimi annunci.",
      now: "C’è un avviso che vale adesso.",
      soon: "C’è un avviso in arrivo. Adesso non risulta nulla in corso.",
      past: "Nessun avviso in corso o in arrivo. L’ultimo annuncio sotto è già passato.",
      planned: "Lavori",
      fault: "Guasto",
      announced: "Annuncio",
      when: "Dal {from} al {to}",
      until: "Fino al {to}",
      official: "Testo di ΔΕΥΑΚ (greco)",
      checked: "Elenco scaricato: {time}. Si aggiorna circa ogni ora.",
      hint: "Gli avvisi riguardano zone, non un singolo edificio."
    },
    tr: {
      loading: "ΔΕΥΑΚ duyuruları yükleniyor…",
      fail: "Duyurular yüklenemedi. Daha sonra yeniden dene.",
      none: "Son duyurularda süren veya yaklaşan bir kayıt yok.",
      now: "Şu an geçerli bir duyuru var.",
      soon: "Yaklaşan bir duyuru var. Şu an süren bir kayıt yok.",
      past: "Süren veya yaklaşan duyuru yok. Aşağıdaki son duyurunun süresi geçmiş.",
      planned: "Çalışma",
      fault: "Arıza",
      announced: "Duyuru",
      when: "{from} – {to}",
      until: "{to} kadar",
      official: "ΔΕΥΑΚ metni (Yunanca)",
      checked: "Liste alındı: {time}. Yaklaşık saatte bir yenilenir.",
      hint: "Duyurular bölgeler içindir, tek bir bina için değil."
    },
    es: {
      loading: "Cargando los avisos de ΔΕΥΑΚ…",
      fail: "No se pudieron cargar los avisos. Prueba más tarde.",
      none: "Ningún aviso en curso o próximo entre los últimos anuncios.",
      now: "Hay un aviso que vale ahora.",
      soon: "Hay un aviso próximo. Ahora no figura nada en curso.",
      past: "Ningún aviso en curso o próximo. El último anuncio de abajo ya ha pasado.",
      planned: "Obras",
      fault: "Avería",
      announced: "Aviso",
      when: "Del {from} al {to}",
      until: "Hasta el {to}",
      official: "Texto de ΔΕΥΑΚ (griego)",
      checked: "Lista descargada: {time}. Se actualiza más o menos cada hora.",
      hint: "Los avisos son de zonas, no de un solo edificio."
    }
  };

  var data = null;

  function lang() {
    var value = "nl";
    try {
      if (window.HK_I18N && HK_I18N.getLang) value = HK_I18N.getLang();
      else value = localStorage.getItem("hk-lang") || "nl";
    } catch (e) {}
    return TEXT[value] ? value : "nl";
  }

  function t(key) {
    return TEXT[lang()][key] || TEXT.nl[key] || "";
  }

  function esc(value) {
    return String(value || "").replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function formatWhen(iso) {
    if (!iso) return "";
    var date = new Date(iso);
    if (isNaN(date.getTime())) return "";
    return date.toLocaleString(LOCALES[lang()] || "nl-NL", {
      timeZone: "Europe/Athens",
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function stateOf(row, now) {
    var from = row.from ? new Date(row.from).getTime() : NaN;
    var to = row.to ? new Date(row.to).getTime() : NaN;
    if (!isNaN(from) && !isNaN(to) && now >= from && now <= to) return "now";
    if (!isNaN(from) && now < from) return "soon";
    if (isNaN(from) && !isNaN(to) && now <= to) return "soon";
    return "past";
  }

  function recent(row, now) {
    var marks = [row.to, row.from, row.publishedAt].map(function (iso) {
      return iso ? new Date(iso).getTime() : NaN;
    }).filter(function (n) { return !isNaN(n); });
    if (!marks.length) return false;
    var latest = Math.max.apply(null, marks);
    return latest >= now - HOUR;
  }

  function itemHtml(row, now) {
    var state = stateOf(row, now);
    var from = formatWhen(row.from);
    var to = formatWhen(row.to);
    var when = "";
    if (from && to) when = t("when").replace("{from}", from).replace("{to}", to);
    else if (to) when = t("until").replace("{to}", to);
    return '<article class="outage-item outage-' + state + '">' +
      '<p class="outage-when">' + esc(t(row.kind || "announced")) + (when ? " · " + esc(when) : "") + "</p>" +
      '<p><strong>' + esc(t("official")) + ":</strong> " + esc(row.text) + "</p>" +
      "</article>";
  }

  function render() {
    var box = document.getElementById("waterSummary");
    var list = document.getElementById("waterList");
    var checked = document.getElementById("waterChecked");
    var hint = document.getElementById("waterHint");
    if (!box || !list) return;
    if (hint) hint.textContent = t("hint");
    if (!data) {
      box.textContent = t("loading");
      list.innerHTML = "";
      if (checked) checked.textContent = "";
      return;
    }
    if (data.error) {
      box.textContent = t("fail");
      list.innerHTML = "";
      return;
    }
    var now = Date.now();
    var rows = (data.notices || []).filter(function (row) { return recent(row, now); });
    var states = rows.map(function (row) { return stateOf(row, now); });
    var line = t("none");
    if (states.indexOf("now") >= 0) line = t("now");
    else if (states.indexOf("soon") >= 0) line = t("soon");
    else if (rows.length) line = t("past");
    box.textContent = line;
    list.innerHTML = rows.map(function (row) { return itemHtml(row, now); }).join("");
    if (checked) checked.textContent = t("checked").replace("{time}", formatWhen(data.fetchedAt));
  }

  function load() {
    render();
    fetch("data/deya-outages.json", { cache: "no-cache" })
      .then(function (response) {
        if (!response.ok) throw new Error(String(response.status));
        return response.json();
      })
      .then(function (json) {
        data = json;
        render();
      })
      .catch(function () {
        data = { error: true };
        render();
      });
  }

  document.addEventListener("hk-lang", render);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", load);
  else load();
})();
