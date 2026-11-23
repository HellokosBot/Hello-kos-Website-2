/* Choice screen on route-wandel.html: walk, drive, or build your own. */
(function () {
  var PICK_KEY = "hk-route-picks";
  /* Fixed app order. The wishlist follows these lists and never sorts by distance. */
  var WALKL = ["sight-witte-trappen","sight-i-love-kos","sight-palm-tree-lane","vlag-hijsen","sight-palazzo-giustizia","sight-turks-badhuis","sight-boom-hippocrates","sight-gazi-hasan","sight-neratzia","sight-albergo-gelsomino","sight-kathedraal","sight-hatzi-pasha","sight-agora","sight-belastingpoort","sight-archeologisch-museum","sight-casa-del-fascio","sight-defterdar","sight-markthal","sight-paraskevi","sight-old-town","sight-morouk","sight-eski-tzami","sight-katholieke-kerk","sight-odeon","sight-westelijke-opgraving","sight-casa-romana","sight-altaar-dionysos"];
  var WALKS = ["sight-witte-trappen","sight-i-love-kos","sight-palm-tree-lane","sight-palazzo-giustizia","sight-turks-badhuis","sight-boom-hippocrates","sight-gazi-hasan","sight-neratzia"];
  var DRIVES = ["sight-therma","sight-asklepion","sight-zia","sight-zoutmeer-tigaki","sight-kasteel-antimachia","sight-molen-antimachia","sight-agios-stefanos-kefalos","sight-limnionas"];
  var DRIVEL = ["sight-therma","sight-platani","sight-hippocratic-foundation","sight-asklepion","sight-waterval-platani","sight-haihoutes","sight-zia","sight-palio-pyli","sight-kasteel-palio-pyli","sight-tigaki","sight-zoutmeer-tigaki","sight-aquaduct-linopotas","sight-marmari","sight-mastichari","sight-kasteel-antimachia","sight-kardamena","sight-traditioneel-huis-antimachia","sight-molen-antimachia","sight-hippocrates-garden","sight-plaka","sight-kapel-agios-nikolaos","sight-agios-stefanos-kefalos","sight-cavo-paradiso","sight-limnionas"];
  var DRIVE_OPT = { "sight-hippocratic-foundation": 1, "sight-waterval-platani": 1, "sight-haihoutes": 1, "sight-aquaduct-linopotas": 1, "sight-kardamena": 1, "sight-cavo-paradiso": 1 };
  var ZIA_CPS = [{ lat: "36.8750770", lon: "27.2480940" }, { lat: "36.8631110", lon: "27.2376780" }, { lat: "36.8505510", lon: "27.2132630" }];
  var ZIA_KEY = "hk-zia-open";
  try { localStorage.removeItem("hk-zia-via"); } catch (e) {}
  var GROUPS = ["kos","psalidi","platani","zia","pyli","tigaki","marmari","mastichari","antimachia","kefalos","limnionas"];
  var mode = null;
  var len = null;
  var PIN = '<svg class="pin" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>';
  var BOOK = '<svg class="book" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 6.1c-1.5-.9-3.3-1.4-5.3-1.4H4.3A1.3 1.3 0 0 0 3 6v11.1c0 .7.6 1.3 1.3 1.3h2.5c1.7 0 3.3.4 5.2 1.4 1.9-1 3.5-1.4 5.2-1.4h2.5c.7 0 1.3-.6 1.3-1.3V6c0-.7-.6-1.3-1.3-1.3h-2.4c-2 0-3.8.5-5.3 1.4zM5 7.1h1.6c1.4 0 2.8.3 4 1v8.4c-1.1-.5-2.5-.8-4-.8H5V7.1zm14 8.6h-1.4c-1.5 0-2.9.3-4 .8V8.1c1.2-.7 2.6-1 4-1H19v8.6z"/></svg>';

  function lang() {
    if (window.HK_I18N && HK_I18N.getLang) return HK_I18N.getLang();
    var l = localStorage.getItem("hk-lang") || "nl";
    return l;
  }
  function placeName(p) {
    var pack = (window.HK_NAMES && HK_NAMES[lang()]) || {};
    return (p && pack[p.id]) || (p && p.name) || "";
  }
  function driveLongIds() {
    return DRIVEL.filter(function (id) { return !DRIVE_OPT[id]; });
  }
  function savedIds() {
    var set = {};
    var favs = [];
    try { favs = JSON.parse(localStorage.getItem("hk-favorites") || "[]"); } catch (e) { favs = []; }
    if (!Array.isArray(favs)) favs = [];
    favs.forEach(function (f) { if (f && f.id) set[f.id] = true; });
    return set;
  }
  function driveIds(which) {
    var base = which === "short" ? DRIVES : driveLongIds();
    var want = {};
    base.forEach(function (id) { want[id] = true; });
    var saved = savedIds();
    Object.keys(DRIVE_OPT).forEach(function (id) {
      if (saved[id]) want[id] = true;
    });
    var ordered = [];
    DRIVEL.forEach(function (id) {
      if (want[id]) ordered.push(id);
    });
    return ordered;
  }
  function ziaOn() {
    try { return localStorage.getItem(ZIA_KEY) === "1"; } catch (e) { return false; }
  }
  function toggleZia() {
    try { localStorage.setItem(ZIA_KEY, ziaOn() ? "0" : "1"); } catch (e) {}
  }
  function hidesZiaView(stops) {
    for (var i = 0; i < stops.length; i++) {
      if (stops[i] && stops[i].id === "sight-haihoutes") return true;
    }
    return false;
  }
  function ziaGateCard() {
    var on = ziaOn();
    var html = '<article class="stop" data-zia-gate="1">';
    html += '<img src="img/gids/route-zia-uitzicht.jpg" alt="">';
    html += "<h2>" + esc(T("ziaTile")) + "</h2>";
    html += '<div class="body"><p>' + esc(T("ziaTileText")) + "</p>";
    html += '<button type="button" class="open-btn" data-zia="toggle">' + esc(on ? T("ziaRemove") : T("ziaAdd")) + "</button>";
    html += "</div></article>";
    return html;
  }
  function ziaPointCard(num, c, i) {
    var name = T("ziaPoint").replace("{n}", String(i + 1));
    var fake = { lat: c.lat, lon: c.lon, name: name, link: "route-zia-uitzicht.html" };
    var html = '<article class="stop" data-zia-point="' + (i + 1) + '">';
    html += '<img src="img/gids/route-zia-uitzicht.jpg" alt="">';
    html += "<h2>" + (num ? esc(num) + ". " : "") + esc(name) + "</h2>";
    html += '<div class="body"><p>' + esc(T("ziaPointText")) + "</p>";
    html += openBtn(fake);
    html += buttons(fake);
    html += "</div></article>";
    return html;
  }
  function ziaBefore(n) {
    var letters = ["a", "b", "c"];
    var html = '<section class="zia-group" data-zia-group="1">';
    html += '<p class="zia-label">' + esc(T("ziaTile")) + "</p>";
    html += ziaGateCard();
    if (ziaOn()) {
      ZIA_CPS.forEach(function (c, i) {
        html += ziaPointCard(n + letters[i], c, i);
      });
    }
    html += "</section>";
    return html;
  }
  function T(key) {
    var pack = (window.HK_DICT && window.HK_DICT[lang()]) || {};
    if (pack[key]) return pack[key];
    var nl = (window.HK_DICT && window.HK_DICT.nl) || {};
    return nl[key] || "";
  }
  function stopText(id) {
    var all = window.HK_ROUTE_TEXT || {};
    var pack = all[lang()] || {};
    if (pack[id]) return pack[id];
    return (all.nl && all.nl[id]) || "";
  }
  function byId(id) {
    var all = window.HK_PLACES || [];
    for (var i = 0; i < all.length; i++) if (all[i].id === id) return all[i];
    return null;
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }
  function gPoint(lat, lon) {
    return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(lat + "," + lon);
  }
  function aPoint(lat, lon, name) {
    return "https://maps.apple.com/?ll=" + lat + "," + lon + "&q=" + encodeURIComponent(name);
  }
  function gName(name) {
    return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(name + " Kos");
  }
  function aName(name) {
    return "https://maps.apple.com/?q=" + encodeURIComponent(name + " Kos");
  }
  function hasCoord(p) {
    return p && p.lat != null && p.lon != null && p.lat !== "" && !isNaN(Number(p.lat)) && !isNaN(Number(p.lon));
  }
  function buttons(p) {
    var g = hasCoord(p) ? gPoint(p.lat, p.lon) : gName(p.name);
    var a = hasCoord(p) ? aPoint(p.lat, p.lon, placeName(p) || p.name) : aName(p.name);
    return '<div class="map-row"><a href="' + esc(g) + '" target="_blank" rel="noopener">' + PIN + esc(T("gmaps")) + '</a><a href="' + esc(a) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + '</a></div>';
  }
  function openBtn(p) {
    if (!p.link) return "";
    return '<a class="open-btn" href="' + esc(p.link) + '">' + BOOK + "<span>" + esc(T("open")) + "</span></a>";
  }
  function renderWalk() {
    showRoute(WALKL, "walkOnlyNote", "walk");
  }
  function showRoute(ids, noteKey, tm) {
    var custom = document.getElementById("customView");
    if (custom) custom.hidden = true;
    var stops = ids.map(byId).filter(Boolean);
    var html = "";
    var n = 0;
    stops.forEach(function (p) {
      n += 1;
      if (tm === "drive" && p.id === "sight-zia" && !hidesZiaView(stops)) html += ziaBefore(n);
      html += '<article class="stop">';
      if (p.photo) html += '<img src="' + esc(p.photo) + '" alt="">';
      html += '<h2>' + n + ". " + esc(placeName(p)) + "</h2>";
      html += '<div class="body"><p>' + esc(stopText(p.id)) + "</p>";
      html += openBtn(p);
      html += buttons(p);
      html += "</div></article>";
    });
    var view = document.getElementById("routeView");
    view.innerHTML = html;
    view.setAttribute("data-stops", String(stops.length));
    var blurb = document.getElementById("blurb");
    if (blurb) {
      var note = T(noteKey);
      blurb.hidden = !note;
      blurb.textContent = note;
    }
  }
  function loadPicks() {
    try {
      var raw = JSON.parse(localStorage.getItem(PICK_KEY) || "{}");
      return { ids: Array.isArray(raw.ids) ? raw.ids : [], travel: raw.travel === "drive" ? "drive" : "walk" };
    } catch (e) {
      return { ids: [], travel: "walk" };
    }
  }
  function selectedIds() {
    return Array.prototype.map.call(document.querySelectorAll("#checks input:checked"), function (el) {
      return el.getAttribute("data-id");
    });
  }
  function savePicks() {
    var prev = loadPicks();
    var travel = document.getElementById("cDrive").classList.contains("on") ? "drive" : "walk";
    if (!document.getElementById("cDrive").classList.contains("on") && !document.getElementById("cWalk").classList.contains("on")) travel = prev.travel;
    localStorage.setItem(PICK_KEY, JSON.stringify({ ids: selectedIds(), travel: travel }));
  }
  function renderChecks() {
    var picks = loadPicks();
    var byGroup = {};
    (window.HK_PLACES || []).forEach(function (p) {
      if (typeof p.lat !== "number" || typeof p.lon !== "number") return;
      (byGroup[p.group] = byGroup[p.group] || []).push(p);
    });
    var html = "";
    GROUPS.forEach(function (g) {
      var rows = byGroup[g] || [];
      rows.sort(function (a, b) { return (a.order || 0) - (b.order || 0); });
      if (!rows.length) return;
      html += '<div class="group"><h3>' + esc(T("g_" + g)) + "</h3>";
      rows.forEach(function (p) {
        var on = picks.ids.indexOf(p.id) >= 0 ? " checked" : "";
        html += '<label><input type="checkbox" data-id="' + esc(p.id) + '"' + on + "> " + esc(placeName(p)) + "</label>";
      });
      html += "</div>";
    });
    document.getElementById("checks").innerHTML = html;
    document.getElementById("cWalk").classList.toggle("on", picks.travel !== "drive");
    document.getElementById("cDrive").classList.toggle("on", picks.travel === "drive");
    updateCustom();
  }
  function selectedStops() {
    var stops = [];
    document.querySelectorAll("#checks input:checked").forEach(function (el) {
      var p = byId(el.getAttribute("data-id"));
      if (p && typeof p.lat === "number") stops.push(p);
    });
    return stops;
  }
  function updateCustom() {
    var stops = selectedStops();
    var box = document.getElementById("cBtns");
    var note = document.getElementById("favNote");
    if (note && !note.dataset.lock) note.textContent = "";
    if (box) { box.hidden = true; box.innerHTML = ""; }
    var trim = document.getElementById("cTrim");
    if (trim) { trim.hidden = true; trim.textContent = ""; }
    var cest = document.getElementById("cest");
    if (cest) cest.textContent = stops.length === 1 ? T("need2") : "";
  }
  function openCustom() {
    mode = "custom";
    len = null;
    var step2 = document.getElementById("step2");
    if (step2) step2.hidden = true;
    var routeView = document.getElementById("routeView");
    if (routeView) routeView.innerHTML = "";
    var blurb = document.getElementById("blurb");
    if (blurb) {
      var note = T("customNote");
      blurb.hidden = !note;
      blurb.textContent = note;
    }
    document.getElementById("customView").hidden = false;
    renderChecks();
  }
  function applyPreset() {
    if (!mode || mode === "custom" || !len) return;
    var ids = mode === "walk" ? (len === "short" ? WALKS : WALKL) : driveIds(len);
    var note = mode === "walk" ? (len === "short" ? "walkShortNote" : "walkLongNote") : (len === "short" ? "driveShortNote" : "driveLongNote");
    showRoute(ids, note, mode === "drive" ? "drive" : "walk");
  }
  function fromFav() {
    openCustom();
    var favs = (window.HKFav && HKFav.list) ? HKFav.list() : [];
    var picks = loadPicks();
    var have = {};
    picks.ids.forEach(function (id) { have[id] = true; });
    var missing = [];
    favs.forEach(function (f) {
      var p = byId(f.id);
      if (p && typeof p.lat === "number") have[f.id] = true;
      else missing.push(f.name || f.id);
    });
    picks.ids = Object.keys(have);
    localStorage.setItem(PICK_KEY, JSON.stringify({ ids: picks.ids, travel: picks.travel }));
    renderChecks();
    var note = document.getElementById("favNote");
    note.dataset.lock = "1";
    if (!favs.length) note.textContent = T("fromFavEmpty");
    else if (missing.length) note.textContent = T("fromFavMiss").replace("{names}", missing.join(", "));
    else note.textContent = "";
    note.dataset.lock = "";
  }

  var wishMode = null;
  /* Eigen rijroute only. Starts folded and not in the route on every page open. */
  var eigenZia = "shut";
  var TRASH = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h5v2H3V5h5l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM6 9h2v9H6V9zm-1 12h14l1-12H4l1 12z"/></svg>';
  function onList(id, list) {
    for (var i = 0; i < list.length; i++) if (list[i] === id) return true;
    return false;
  }
  function favPlaces(town) {
    var favs = (window.HKFav && HKFav.list) ? HKFav.list() : [];
    var out = [];
    favs.forEach(function (f) {
      var p = byId(f.id);
      if (!p || !p.group) return;
      var walkStop = onList(p.id, WALKL);
      var driveStop = onList(p.id, DRIVEL);
      if (town) {
        if (walkStop || (!driveStop && p.group === "kos")) out.push(p);
      } else if (driveStop || (!walkStop && p.group !== "kos")) out.push(p);
    });
    return out;
  }
  function orderFixed(stops, template, optional) {
    var want = {};
    stops.forEach(function (p) { want[p.id] = p; });
    var ordered = [];
    var used = {};
    var extras = optional || [];
    template.forEach(function (id) {
      extras.forEach(function (opt) {
        if (opt.before === id && want[opt.id] && !used[opt.id]) {
          ordered.push(want[opt.id]);
          used[opt.id] = true;
        }
      });
      if (want[id]) {
        ordered.push(want[id]);
        used[id] = true;
      }
    });
    (window.HK_PLACES || []).forEach(function (p) {
      if (want[p.id] && !used[p.id]) {
        ordered.push(want[p.id]);
        used[p.id] = true;
      }
    });
    return ordered;
  }
  function renderWish() {
    var view = document.getElementById("routeView");
    if (!view || !wishMode) return;
    var town = wishMode === "walk";
    var optional = town ? [] : [{ id: "sight-natuurpark-zia", before: "sight-zia" }];
    var stops = orderFixed(favPlaces(town), town ? WALKL : DRIVEL, optional);
    document.getElementById("ownWalk").classList.toggle("on", town);
    document.getElementById("ownDrive").classList.toggle("on", !town);
    if (!stops.length) {
      view.innerHTML = '<div class="empty-route"><p>' + esc(T(town ? "wishEmptyWalk" : "wishEmptyDrive")) + '</p><a class="wish-go" href="bezienswaardigheden.html">' + esc(T("wishSee")) + "</a></div>";
      view.setAttribute("data-stops", "0");
      return;
    }
    var html = "";
    var n = 0;
    stops.forEach(function (p) {
      n += 1;
      if (!town && p.id === "sight-zia" && !hidesZiaView(stops)) html += ziaEigen(n);
      html += '<article class="stop">';
      html += '<div class="stop-top">';
      if (p.photo) html += '<img src="' + esc(p.photo) + '" alt="">';
      else html += '<div class="ph"></div>';
      html += '<button type="button" class="drop" data-drop="' + esc(p.id) + '" aria-label="' + esc(T("wishRemove")) + '">' + TRASH + "</button>";
      html += "</div>";
      html += "<h2>" + n + ". " + esc(placeName(p)) + "</h2>";
      html += '<div class="body"><p>' + esc(stopText(p.id)) + "</p>";
      html += openBtn(p);
      html += buttons(p);
      html += "</div></article>";
    });
    view.innerHTML = html;
    view.setAttribute("data-stops", String(stops.length));
    view.setAttribute("data-mode", wishMode);
  }
  function ziaFoldCard(open) {
    var html = '<article class="stop zia-fold">';
    html += '<img src="img/gids/route-zia-uitzicht.jpg" alt="">';
    html += "<h2>" + esc(T("ziaTile")) + "</h2>";
    html += '<div class="body"><button type="button" class="open-btn" data-zia="fold">' + esc(open ? T("ziaFold") : T("ziaUnfold")) + "</button></div>";
    html += "</article>";
    return html;
  }
  function ziaEigen(n) {
    if (eigenZia === "shut") return ziaFoldCard(false);
    var letters = ["a", "b", "c"];
    var added = eigenZia === "in";
    var html = '<section class="zia-group" data-zia-group="1"' + (added ? ' data-zia-in="1"' : ' data-zia-preview="1"') + ">";
    if (added) html += '<p class="zia-label">' + esc(T("ziaTile")) + "</p>";
    else html += ziaFoldCard(true) + '<p class="zia-note">' + esc(T("ziaPreview")) + "</p>";
    ZIA_CPS.forEach(function (c, i) {
      html += ziaPointCard(added ? n + letters[i] : "", c, i);
    });
    html += '<button type="button" class="open-btn zia-act" data-zia="' + (added ? "remove" : "add") + '">' + esc(added ? T("ziaRemove") : T("ziaMine")) + "</button>";
    html += "</section>";
    return html;
  }
  function dropWish(id) {
    if (window.HKFav && HKFav.remove) HKFav.remove(id);
    else {
      try {
        var items = JSON.parse(localStorage.getItem("hk-favorites") || "[]");
        localStorage.setItem("hk-favorites", JSON.stringify(items.filter(function (x) { return x && x.id !== id; })));
      } catch (e) {}
    }
    renderWish();
  }

  var page = document.body.getAttribute("data-route") || "";
  if (page === "walk") renderWalk();
  if (page === "drive") {
    mode = "drive";
    len = document.body.getAttribute("data-len");
    if (len !== "short" && len !== "long") len = null;
    var driveView = document.getElementById("routeView");
    if (driveView) driveView.addEventListener("click", function (e) {
      var via = e.target.closest("[data-zia]");
      if (!via) return;
      toggleZia();
      applyPreset();
    });
    if (len) applyPreset();
  }
  if (page === "custom") {
    document.getElementById("ownWalk").addEventListener("click", function () {
      wishMode = "walk";
      renderWish();
    });
    document.getElementById("ownDrive").addEventListener("click", function () {
      wishMode = "drive";
      renderWish();
    });
    document.getElementById("routeView").addEventListener("click", function (e) {
      var via = e.target.closest("[data-zia]");
      if (via) {
        var act = via.getAttribute("data-zia");
        if (act === "fold") eigenZia = eigenZia === "open" ? "shut" : "open";
        else if (act === "add") eigenZia = "in";
        else if (act === "remove") eigenZia = "shut";
        renderWish();
        return;
      }
      var btn = e.target.closest("[data-drop]");
      if (!btn) return;
      dropWish(btn.getAttribute("data-drop"));
    });
  }
  document.addEventListener("hk-lang", function () {
    if (page === "walk") renderWalk();
    else if (page === "custom") renderWish();
    else if (page === "drive") applyPreset();
  });
})();
