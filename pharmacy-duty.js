/* Today's Kos pharmacy duty from data/pharmacy-duty.json.
   The browser cannot read fs12.gr itself (no CORS).
   A scheduled job refreshes that file from Φαρμακευτικός Σύλλογος Δωδεκανήσου. */
(function () {
  var LOCALES = { nl: "nl-NL", de: "de-DE", en: "en-GB", it: "it-IT", tr: "tr-TR", es: "es-ES" };
  var TEXT = {
    nl: {
      loading: "De dienstlijst wordt geladen…",
      fail: "De dienstlijst kon niet geladen worden. Probeer het later opnieuw.",
      none: "Voor vandaag staat er geen apotheek van dienst in de laatste lijst.",
      checked: "Lijst opgehaald: {time}. Ongeveer elk uur ververst."
    },
    de: {
      loading: "Die Dienstliste wird geladen…",
      fail: "Die Dienstliste konnte nicht geladen werden. Versuch es später noch einmal.",
      none: "Für heute steht keine Dienstapotheke in der letzten Liste.",
      checked: "Liste geholt: {time}. Wird etwa stündlich erneuert."
    },
    en: {
      loading: "Loading the duty list…",
      fail: "The duty list could not be loaded. Try again later.",
      none: "No on-duty pharmacy for today is in the latest list.",
      checked: "List fetched: {time}. Refreshed about once an hour."
    },
    it: {
      loading: "Caricamento dell’elenco di turno…",
      fail: "L’elenco di turno non si è caricato. Riprova più tardi.",
      none: "Per oggi non c’è una farmacia di turno nell’ultimo elenco.",
      checked: "Elenco scaricato: {time}. Si aggiorna circa ogni ora."
    },
    tr: {
      loading: "Nöbet listesi yükleniyor…",
      fail: "Nöbet listesi yüklenemedi. Daha sonra yeniden dene.",
      none: "Bugün için son listede nöbetçi eczane yok.",
      checked: "Liste alındı: {time}. Yaklaşık saatte bir yenilenir."
    },
    es: {
      loading: "Cargando la lista de servicio…",
      fail: "No se pudo cargar la lista de servicio. Prueba más tarde.",
      none: "Para hoy no hay farmacia de servicio en la última lista.",
      checked: "Lista descargada: {time}. Se actualiza más o menos cada hora."
    }
  };

  var data = null;

  function lang() {
    var value = "nl";
    try {
      value = localStorage.getItem("hk-lang") || document.documentElement.lang || "nl";
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

  function athensDay(date) {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Europe/Athens",
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).format(date);
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

  function phoneHtml(number) {
    var digits = String(number).replace(/\D/g, "");
    var href = digits.length === 10 ? "tel:+30" + digits : "tel:" + digits;
    return '<a href="' + esc(href) + '">' + esc(number) + "</a>";
  }

  function mapQuery(row) {
    var parts = [];
    function add(value) {
      var text = String(value || "").replace(/\s+/g, " ").trim();
      if (!text) return;
      var joined = parts.join(", ").toLowerCase();
      if (joined.indexOf(text.toLowerCase()) >= 0) return;
      parts.push(text);
    }
    add(row.name);
    add(row.address);
    add(row.area);
    add("Kos");
    add("Greece");
    return parts.join(", ");
  }

  function mapHtml(row) {
    if (!String(row.address || "").trim()) return "";
    var query = encodeURIComponent(mapQuery(row));
    var google = "https://www.google.com/maps/search/?api=1&query=" + query;
    var apple = "https://maps.apple.com/?q=" + query;
    return '<div class="actions">' +
      '<a class="btn btn-map" href="' + esc(google) + '" target="_blank" rel="noopener">Google Maps</a>' +
      '<a class="btn btn-map" href="' + esc(apple) + '" target="_blank" rel="noopener">Apple Maps</a>' +
      "</div>";
  }

  function itemHtml(row) {
    var meta = esc(row.dutyLabel || "");
    if (row.area) meta += (meta ? " · " : "") + esc(row.area);
    var phones = (row.phones || []).map(phoneHtml).join(" · ");
    return '<article class="duty-item">' +
      "<strong>" + esc(row.name) + "</strong>" +
      (meta ? '<p class="duty-meta">' + meta + "</p>" : "") +
      (row.address ? "<p>" + esc(row.address) + "</p>" : "") +
      (phones ? "<p>" + phones + "</p>" : "") +
      mapHtml(row) +
      "</article>";
  }

  function render() {
    var status = document.getElementById("pharmacyStatus");
    var list = document.getElementById("pharmacyList");
    var checked = document.getElementById("pharmacyChecked");
    if (!status || !list) return;
    if (!data) {
      status.textContent = t("loading");
      list.innerHTML = "";
      if (checked) checked.textContent = "";
      return;
    }
    if (data.error) {
      status.textContent = t("fail");
      list.innerHTML = "";
      if (checked) checked.textContent = "";
      return;
    }
    var today = athensDay(new Date());
    var rows = (data.pharmacies || []).filter(function (row) { return row.date === today; });
    if (!rows.length) {
      status.textContent = t("none");
      list.innerHTML = "";
    } else {
      status.textContent = "";
      list.innerHTML = rows.map(itemHtml).join("");
    }
    if (checked) checked.textContent = t("checked").replace("{time}", formatWhen(data.fetchedAt));
  }

  function load() {
    render();
    fetch("data/pharmacy-duty.json", { cache: "no-cache" })
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
