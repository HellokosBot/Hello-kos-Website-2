/* Planned power cuts from data/deddie-outages.json.
   The browser cannot read siteapps.deddie.gr itself (no CORS).
   A scheduled job refreshes that file from the official DEDDIE list. */
(function () {
  var LOCALES = { nl: "nl-NL", de: "de-DE", en: "en-GB", it: "it-IT", tr: "tr-TR", es: "es-ES" };
  var PURPOSE = {
    "Κατασκευές": {
      nl: "Werken aan het net", de: "Arbeiten am Netz", en: "Work on the network",
      it: "Lavori sulla rete", tr: "Şebekede çalışma", es: "Trabajos en la red"
    },
    "Λειτουργία": {
      nl: "Werking van het net", de: "Netzbetrieb", en: "Network operation",
      it: "Esercizio della rete", tr: "Şebeke işletmesi", es: "Funcionamiento de la red"
    }
  };
  var TEXT = {
    nl: {
      loading: "De lijst van ΔΕΔΔΗΕ wordt geladen…",
      fail: "De lijst kon niet geladen worden. Probeer het later opnieuw.",
      dodNone: "Dodekanesos: geen geplande onderbreking in de openbare lijst.",
      dodSome: "Dodekanesos: {n} geplande onderbreking(en) in de lijst.",
      kosNone: "Kos: geen geplande onderbreking in de lijst.",
      kosNow: "Kos: er is nu een geplande onderbreking.",
      kosSoon: "Kos: nu geen onderbreking. Er staat wel iets gepland.",
      kosPast: "Kos: de punten in de lijst zijn al voorbij.",
      otherTitle: "Andere eilanden in de Dodekanesos",
      when: "Van {from} tot {to}",
      places: "Gemeente / dorp",
      official: "Tekst van ΔΕΔΔΗΕ (Grieks)",
      reason: "Reden",
      checked: "Lijst opgehaald: {time}. Ongeveer elk uur ververst.",
      hint: "Dit is de openbare lijst van geplande werken, niet een meting of je lamp het nu doet. Een plotselinge storing staat hier niet altijd in."
    },
    de: {
      loading: "Die Liste von ΔΕΔΔΗΕ wird geladen…",
      fail: "Die Liste konnte nicht geladen werden. Versuch es später noch einmal.",
      dodNone: "Dodekanes: keine geplante Abschaltung in der öffentlichen Liste.",
      dodSome: "Dodekanes: {n} geplante Abschaltung(en) in der Liste.",
      kosNone: "Kos: keine geplante Abschaltung in der Liste.",
      kosNow: "Kos: es gibt jetzt eine geplante Abschaltung.",
      kosSoon: "Kos: gerade keine Abschaltung. Es ist aber etwas geplant.",
      kosPast: "Kos: die Einträge in der Liste sind schon vorbei.",
      otherTitle: "Andere Inseln im Dodekanes",
      when: "Von {from} bis {to}",
      places: "Gemeinde / Ort",
      official: "Text von ΔΕΔΔΗΕ (Griechisch)",
      reason: "Grund",
      checked: "Liste geholt: {time}. Wird etwa stündlich erneuert.",
      hint: "Das ist die öffentliche Liste geplanter Arbeiten, keine Messung, ob deine Lampe jetzt an ist. Ein plötzlicher Ausfall steht hier nicht immer."
    },
    en: {
      loading: "Loading the ΔΕΔΔΗΕ list…",
      fail: "The list could not be loaded. Try again later.",
      dodNone: "Dodecanese: no planned cut in the public list.",
      dodSome: "Dodecanese: {n} planned cut(s) in the list.",
      kosNone: "Kos: no planned cut in the list.",
      kosNow: "Kos: a planned cut is happening now.",
      kosSoon: "Kos: no cut right now. One is scheduled.",
      kosPast: "Kos: the items in the list are already over.",
      otherTitle: "Other islands in the Dodecanese",
      when: "From {from} until {to}",
      places: "Municipality / village",
      official: "Text from ΔΕΔΔΗΕ (Greek)",
      reason: "Reason",
      checked: "List fetched: {time}. Refreshed about once an hour.",
      hint: "This is the public list of planned works, not a reading of whether your light is on. A sudden fault is not always listed here."
    },
    it: {
      loading: "Caricamento dell’elenco ΔΕΔΔΗΕ…",
      fail: "L’elenco non si è caricato. Riprova più tardi.",
      dodNone: "Dodecaneso: nessuna interruzione programmata nell’elenco pubblico.",
      dodSome: "Dodecaneso: {n} interruzione/i programmata/e nell’elenco.",
      kosNone: "Kos: nessuna interruzione programmata nell’elenco.",
      kosNow: "Kos: c’è ora un’interruzione programmata.",
      kosSoon: "Kos: nessuna interruzione adesso. Ce n’è una in programma.",
      kosPast: "Kos: le voci dell’elenco sono già passate.",
      otherTitle: "Altre isole del Dodecaneso",
      when: "Dal {from} al {to}",
      places: "Comune / paese",
      official: "Testo di ΔΕΔΔΗΕ (greco)",
      reason: "Motivo",
      checked: "Elenco scaricato: {time}. Si aggiorna circa ogni ora.",
      hint: "È l’elenco pubblico dei lavori programmati, non una misura se la tua luce è accesa. Un guasto improvviso non è sempre in elenco."
    },
    tr: {
      loading: "ΔΕΔΔΗΕ listesi yükleniyor…",
      fail: "Liste yüklenemedi. Daha sonra yeniden dene.",
      dodNone: "On İki Ada: açık listede planlı kesinti yok.",
      dodSome: "On İki Ada: listede {n} planlı kesinti var.",
      kosNone: "Kos: listede planlı kesinti yok.",
      kosNow: "Kos: şu anda planlı bir kesinti var.",
      kosSoon: "Kos: şu an kesinti yok. Planlı bir kesinti var.",
      kosPast: "Kos: listedeki kayıtların süresi geçmiş.",
      otherTitle: "On İki Ada’daki diğer adalar",
      when: "{from} – {to}",
      places: "Belediye / köy",
      official: "ΔΕΔΔΗΕ metni (Yunanca)",
      reason: "Neden",
      checked: "Liste alındı: {time}. Yaklaşık saatte bir yenilenir.",
      hint: "Bu, planlı çalışmaların açık listesidir; lambanın şu an yanıp yanmadığını ölçmez. Ani bir arıza her zaman burada olmaz."
    },
    es: {
      loading: "Cargando la lista de ΔΕΔΔΗΕ…",
      fail: "No se pudo cargar la lista. Prueba más tarde.",
      dodNone: "Dodecaneso: ninguna interrupción prevista en la lista pública.",
      dodSome: "Dodecaneso: {n} interrupción(es) prevista(s) en la lista.",
      kosNone: "Kos: ninguna interrupción prevista en la lista.",
      kosNow: "Kos: hay ahora una interrupción prevista.",
      kosSoon: "Kos: no hay corte ahora. Hay uno previsto.",
      kosPast: "Kos: los avisos de la lista ya han pasado.",
      otherTitle: "Otras islas del Dodecaneso",
      when: "Del {from} al {to}",
      places: "Municipio / pueblo",
      official: "Texto de ΔΕΔΔΗΕ (griego)",
      reason: "Motivo",
      checked: "Lista descargada: {time}. Se actualiza más o menos cada hora.",
      hint: "Es la lista pública de trabajos previstos, no una medición de si tu luz está encendida. Un fallo repentino no siempre está aquí."
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

  function formatWhen(iso, raw) {
    if (!iso) return raw || "";
    var date = new Date(iso);
    if (isNaN(date.getTime())) return raw || "";
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
    return "past";
  }

  function purpose(row) {
    var known = PURPOSE[row.purpose];
    if (known) return known[lang()] || known.en;
    return row.purpose || "";
  }

  function itemHtml(row, now) {
    var state = stateOf(row, now);
    var when = t("when").replace("{from}", formatWhen(row.from, row.fromRaw)).replace("{to}", formatWhen(row.to, row.toRaw));
    return '<article class="outage-item outage-' + state + '">' +
      '<p class="outage-when">' + esc(when) + '</p>' +
      '<p><strong>' + esc(t("places")) + ':</strong> ' + esc((row.places || []).join(" · ")) + '</p>' +
      (purpose(row) ? '<p><strong>' + esc(t("reason")) + ':</strong> ' + esc(purpose(row)) + '</p>' : '') +
      '<p><strong>' + esc(t("official")) + ':</strong> ' + esc(row.area) + '</p>' +
      '</article>';
  }

  function render() {
    var box = document.getElementById("outageSummary");
    var list = document.getElementById("outageList");
    var checked = document.getElementById("outageChecked");
    var hint = document.getElementById("outageHint");
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
    var rows = data.outages || [];
    var now = Date.now();
    var kos = rows.filter(function (row) { return row.onKos; });
    var other = rows.filter(function (row) { return !row.onKos; });
    var kosStates = kos.map(function (row) { return stateOf(row, now); });
    var kosLine = t("kosNone");
    if (kosStates.indexOf("now") >= 0) kosLine = t("kosNow");
    else if (kosStates.indexOf("soon") >= 0) kosLine = t("kosSoon");
    else if (kos.length) kosLine = t("kosPast");
    var dodLine = rows.length ? t("dodSome").replace("{n}", String(rows.length)) : t("dodNone");
    box.textContent = dodLine + " " + kosLine;
    var html = kos.map(function (row) { return itemHtml(row, now); }).join("");
    if (other.length) {
      html += '<h3 class="outage-other">' + esc(t("otherTitle")) + '</h3>' +
        other.map(function (row) { return itemHtml(row, now); }).join("");
    }
    list.innerHTML = html;
    if (checked) {
      checked.textContent = t("checked").replace("{time}", formatWhen(data.fetchedAt, data.fetchedAt));
    }
  }

  function load() {
    render();
    fetch("data/deddie-outages.json", { cache: "no-cache" })
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
