/* Saved sights. localStorage key hk-favorites.
   Each item: id, name, photo, link, and lat/lon only when the catalog has them. */
(function () {
  var KEY = "hk-favorites";
  var UI = {
    nl: { save: "Bewaren", saved: "Bewaard", count: "{n} bewaard" },
    de: { save: "Merken", saved: "Gemerkt", count: "{n} gemerkt" },
    en: { save: "Save", saved: "Saved", count: "{n} saved" },
    it: { save: "Salva", saved: "Salvato", count: "{n} salvati" },
    tr: { save: "Kaydet", saved: "Kayıtlı", count: "{n} kayıtlı" },
    es: { save: "Guardar", saved: "Guardado", count: "{n} guardados" }
  };

  function lang() {
    var l = localStorage.getItem("hk-lang") || document.documentElement.lang || "nl";
    return UI[l] ? l : "nl";
  }
  function t(key) {
    return (UI[lang()] && UI[lang()][key]) || UI.nl[key] || "";
  }
  function list() {
    try {
      var raw = JSON.parse(localStorage.getItem(KEY) || "[]");
      return Array.isArray(raw) ? raw : [];
    } catch (e) {
      return [];
    }
  }
  function write(items) {
    localStorage.setItem(KEY, JSON.stringify(items));
    document.dispatchEvent(new CustomEvent("hk-fav"));
  }
  function find(id) {
    var items = list();
    for (var i = 0; i < items.length; i++) if (items[i] && items[i].id === id) return items[i];
    return null;
  }
  function placeById(id) {
    var all = window.HK_PLACES || [];
    for (var i = 0; i < all.length; i++) if (all[i].id === id) return all[i];
    return null;
  }
  function clean(item) {
    var out = {
      id: String(item.id || ""),
      name: String(item.name || item.id || ""),
      photo: String(item.photo || ""),
      link: String(item.link || "")
    };
    var cat = placeById(out.id);
    var lat = cat && typeof cat.lat === "number" ? cat.lat : item.lat;
    var lon = cat && typeof cat.lon === "number" ? cat.lon : item.lon;
    if (typeof lat === "number" && typeof lon === "number" && isFinite(lat) && isFinite(lon)) {
      out.lat = lat;
      out.lon = lon;
    }
    if (cat && cat.photo && !out.photo) out.photo = cat.photo;
    if (cat && cat.link && !out.link) out.link = cat.link;
    if (cat && cat.name) out.name = cat.name;
    return out;
  }
  function add(item) {
    var next = clean(item);
    if (!next.id) return;
    var items = list().filter(function (x) { return x.id !== next.id; });
    items.push(next);
    write(items);
  }
  function remove(id) {
    write(list().filter(function (x) { return x.id !== id; }));
  }
  function toggle(item) {
    if (find(item.id)) remove(item.id);
    else add(item);
  }
  function heart(on) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="' + (on ? "currentColor" : "none") + '" stroke="currentColor" stroke-width="1.6"></path></svg>';
  }
  function paintButton(btn, on, withText) {
    btn.classList.toggle("on", !!on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    var label = on ? t("saved") : t("save");
    btn.setAttribute("aria-label", label);
    btn.innerHTML = heart(on) + (withText ? "<span>" + label + "</span>" : "");
  }
  function cardItem(a) {
    var href = a.getAttribute("href") || "";
    var id = href.replace(/\.html$/, "");
    var cat = placeById(id);
    var img = a.querySelector("img");
    var titleEl = a.querySelector(".card-title");
    var name = (cat && cat.name) || "";
    if (!name && titleEl) {
      var node = titleEl.childNodes[0];
      name = (node ? node.textContent : titleEl.textContent).replace(/\s+/g, " ").trim();
    }
    return clean({
      id: id,
      name: name,
      photo: (img && img.getAttribute("src")) || "",
      link: href
    });
  }
  function mountTiles() {
    document.querySelectorAll("a.card").forEach(function (a) {
      var href = a.getAttribute("href") || "";
      if (href.indexOf("sight-") !== 0 && href !== "vlag-hijsen.html") return;
      if (a.dataset.favReady === "1") return;
      a.dataset.favReady = "1";
      var wrap = document.createElement("div");
      wrap.className = "card-slot";
      a.parentNode.insertBefore(wrap, a);
      wrap.appendChild(a);
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "fav-btn";
      var item = cardItem(a);
      btn.setAttribute("data-fav", item.id);
      wrap.appendChild(btn);
      paintButton(btn, !!find(item.id), false);
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        toggle(cardItem(a));
        paintAll();
      });
    });
  }
  function fileName() {
    var path = location.pathname || "";
    var parts = path.split("/");
    return parts[parts.length - 1] || "";
  }
  function mountDetail() {
    var file = fileName();
    if (file.indexOf("sight-") !== 0 && file !== "vlag-hijsen.html") return;
    if (document.getElementById("favSave")) return;
    var main = document.querySelector("main");
    if (!main) return;
    var id = file.replace(/\.html$/, "");
    var h1s = main.querySelectorAll("h1");
    var btn = document.createElement("button");
    btn.type = "button";
    btn.id = "favSave";
    btn.className = "fav-inline";
    btn.setAttribute("data-fav", id);
    if (h1s.length === 1) h1s[0].insertAdjacentElement("afterend", btn);
    else main.insertBefore(btn, main.firstChild);
    btn.addEventListener("click", function () {
      var img = main.querySelector(".hero-wrap img, img");
      var cat = placeById(id);
      toggle(clean({
        id: id,
        name: (cat && cat.name) || (h1s[0] ? h1s[0].textContent.trim() : id),
        photo: (img && img.getAttribute("src")) || "",
        link: file
      }));
      paintAll();
    });
  }
  function paintCount() {
    var el = document.getElementById("wishCount");
    if (!el) return;
    var n = list().length;
    el.textContent = n ? t("count").replace("{n}", String(n)) : "";
  }
  function paintAll() {
    document.querySelectorAll(".fav-btn, #favSave").forEach(function (btn) {
      var id = btn.getAttribute("data-fav");
      paintButton(btn, !!find(id), btn.id === "favSave");
    });
    paintCount();
  }
  function init() {
    mountTiles();
    mountDetail();
    paintAll();
  }
  window.HKFav = { list: list, find: find, add: add, remove: remove, toggle: toggle, clean: clean };
  document.addEventListener("hk-lang", paintAll);
  document.addEventListener("hk-fav", paintAll);
  document.addEventListener("click", function (e) {
    if (e.target && e.target.closest && e.target.closest(".lang-option")) setTimeout(paintAll, 0);
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
