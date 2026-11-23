/* Choice screen on route-wandel.html: walk, drive, or build your own. */
(function () {
  var PICK_KEY = "hk-route-picks";
  /* Fixed app order. The wishlist follows these lists and never sorts by distance. */
  var WALKL = ["sight-witte-trappen","sight-i-love-kos","sight-palm-tree-lane","vlag-hijsen","sight-palazzo-giustizia","sight-turks-badhuis","sight-boom-hippocrates","sight-gazi-hasan","sight-neratzia","sight-albergo-gelsomino","sight-kathedraal","sight-hatzi-pasha","sight-agora","sight-belastingpoort","sight-archeologisch-museum","sight-casa-del-fascio","sight-defterdar","sight-markthal","sight-paraskevi","sight-old-town","sight-morouk","sight-eski-tzami","sight-katholieke-kerk","sight-odeon","sight-westelijke-opgraving","sight-casa-romana","sight-altaar-dionysos"];
  var WALKS = ["sight-witte-trappen","sight-i-love-kos","sight-palm-tree-lane","sight-palazzo-giustizia","sight-turks-badhuis","sight-boom-hippocrates","sight-gazi-hasan","sight-neratzia"];
  var DRIVES = ["sight-therma","sight-asklepion","sight-zia","sight-zoutmeer-tigaki","sight-kasteel-antimachia","sight-molen-antimachia","sight-agios-stefanos-kefalos","sight-limnionas"];
  var DRIVEL = ["sight-therma","sight-platani","sight-asklepion","sight-waterval-platani","sight-haihoutes","sight-hippocratic-foundation","sight-zia","sight-palio-pyli","sight-kasteel-palio-pyli","sight-tigaki","sight-zoutmeer-tigaki","sight-aquaduct-linopotas","sight-marmari","sight-mastichari","sight-kasteel-antimachia","sight-kardamena","sight-traditioneel-huis-antimachia","sight-molen-antimachia","sight-hippocrates-garden","sight-plaka","sight-kapel-agios-nikolaos","sight-agios-stefanos-kefalos","sight-cavo-paradiso","sight-limnionas"];
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
  function hav(a, b) {
    var R = 6371, p = Math.PI / 180;
    var dLa = (b.lat - a.lat) * p, dLo = (b.lon - a.lon) * p;
    var x = Math.sin(dLa / 2) * Math.sin(dLa / 2) + Math.cos(a.lat * p) * Math.cos(b.lat * p) * Math.sin(dLo / 2) * Math.sin(dLo / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(x)));
  }
  function crow(stops) {
    var sum = 0;
    for (var i = 1; i < stops.length; i++) sum += hav(stops[i - 1], stops[i]);
    return Math.round(sum * 10) / 10;
  }
  function kmStr(n) {
    var s = n.toFixed(1);
    return lang() === "en" ? s : s.replace(".", ",");
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
  function dirUrl(stops, tm, cap) {
    if (stops.length < 2) return null;
    var mid = stops.slice(1, -1);
    var trimmed = false;
    var limit = cap == null ? 9 : cap;
    if (limit && mid.length > limit) {
      mid = mid.slice(0, limit);
      trimmed = true;
    }
    var url = "https://www.google.com/maps/dir/?api=1&origin=" + encodeURIComponent(stops[0].lat + "," + stops[0].lon) + "&destination=" + encodeURIComponent(stops[stops.length - 1].lat + "," + stops[stops.length - 1].lon) + "&travelmode=" + (tm === "drive" ? "driving" : "walking");
    if (mid.length) {
      url += "&waypoints=" + mid.map(function (p) { return encodeURIComponent(p.lat + "," + p.lon); }).join("%7C");
    }
    return { url: url, trimmed: trimmed };
  }
  function appleDir(stops, tm) {
    if (!stops.length) return "";
    if (stops.length === 1) return aPoint(stops[0].lat, stops[0].lon, stops[0].name);
    var rest = stops.slice(1).map(function (p) { return encodeURIComponent(p.lat + "," + p.lon); }).join("+to:");
    return "https://maps.apple.com/?saddr=" + encodeURIComponent(stops[0].lat + "," + stops[0].lon) + "&daddr=" + rest + "&dirflg=" + (tm === "drive" ? "d" : "w");
  }
  function buttons(p) {
    var g = typeof p.lat === "number" ? gPoint(p.lat, p.lon) : gName(p.name);
    var a = typeof p.lat === "number" ? aPoint(p.lat, p.lon, placeName(p)) : aName(p.name);
    return '<div class="map-row"><a href="' + esc(g) + '" target="_blank" rel="noopener">' + PIN + esc(T("gmaps")) + '</a><a href="' + esc(a) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + '</a></div>';
  }
  function openBtn(p) {
    if (!p.link) return "";
    return '<a class="open-btn" href="' + esc(p.link) + '">' + BOOK + "<span>" + esc(T("open")) + "</span></a>";
  }
  function estLine(stops, withKind) {
    var line = T("est").replace("{n}", String(stops.length)).replace("{km}", kmStr(crow(stops)));
    if (withKind) {
      var kind = (stops.length <= 8 && crow(stops) < 8) ? T("estShort") : T("estLong");
      line += " " + T("estKind").replace("{kind}", kind);
    }
    return line;
  }
  function renderWalk() {
    showRoute(WALKL, "walkOnlyNote", "walk");
  }
  function showRoute(ids, noteKey, tm) {
    var custom = document.getElementById("customView");
    if (custom) custom.hidden = true;
    var stops = ids.map(byId).filter(Boolean);
    var mapped = stops.filter(function (p) { return typeof p.lat === "number"; });
    var html = "";
    stops.forEach(function (p, i) {
      html += '<article class="stop">';
      if (p.photo) html += '<img src="' + esc(p.photo) + '" alt="">';
      html += '<h2>' + (i + 1) + ". " + esc(placeName(p)) + "</h2>";
      html += '<div class="body"><p>' + esc(stopText(p.id)) + "</p>";
      html += openBtn(p);
      html += buttons(p);
      html += "</div></article>";
    });
    var info = dirUrl(mapped, tm);
    if (info) {
      html += '<div class="map-row"><a id="routeGoogle" href="' + esc(info.url) + '" target="_blank" rel="noopener">' + PIN + esc(T("openG")) + '</a><a id="routeApple" href="' + esc(appleDir(mapped, tm)) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + "</a></div>";
      if (info.trimmed) html += '<p class="est">' + esc(T("trim")) + "</p>";
    }
    var view = document.getElementById("routeView");
    view.innerHTML = html;
    view.setAttribute("data-stops", String(stops.length));
    document.getElementById("blurb").textContent = T(noteKey);
    document.getElementById("est").textContent = mapped.length > 1 ? estLine(mapped, false) : "";
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
  function currentTravel() {
    return document.getElementById("cDrive").classList.contains("on") ? "drive" : "walk";
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
    var trim = document.getElementById("cTrim");
    if (stops.length < 2) {
      box.hidden = true;
      if (trim) trim.hidden = true;
      document.getElementById("cest").textContent = stops.length ? T("need2") : "";
      return;
    }
    var tm = currentTravel();
    document.getElementById("cest").textContent = estLine(stops, true);
    var info = dirUrl(stops, tm);
    box.hidden = false;
    box.innerHTML = '<a id="customGoogle" href="' + esc(info.url) + '" target="_blank" rel="noopener">' + PIN + esc(T("openG")) + '</a><a id="customApple" href="' + esc(appleDir(stops, tm)) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + "</a>";
    if (trim) {
      trim.hidden = !info.trimmed;
      trim.textContent = info.trimmed ? T("trim") : "";
    }
  }
  function openCustom() {
    mode = "custom";
    len = null;
    var step2 = document.getElementById("step2");
    if (step2) step2.hidden = true;
    var routeView = document.getElementById("routeView");
    if (routeView) routeView.innerHTML = "";
    var blurb = document.getElementById("blurb");
    if (blurb) blurb.textContent = T("customNote");
    var est = document.getElementById("est");
    if (est) est.textContent = "";
    document.getElementById("customView").hidden = false;
    renderChecks();
  }
  function applyPreset() {
    if (!mode || mode === "custom" || !len) return;
    var ids = mode === "walk" ? (len === "short" ? WALKS : WALKL) : (len === "short" ? DRIVES : DRIVEL);
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
    var html = '<p class="est">' + esc(T("wishCount").replace("{n}", String(stops.length))) + "</p>";
    stops.forEach(function (p, i) {
      html += '<article class="stop">';
      html += '<div class="stop-top">';
      if (p.photo) html += '<img src="' + esc(p.photo) + '" alt="">';
      else html += '<div class="ph"></div>';
      html += '<button type="button" class="drop" data-drop="' + esc(p.id) + '" aria-label="' + esc(T("wishRemove")) + '">' + TRASH + "</button>";
      html += "</div>";
      html += "<h2>" + (i + 1) + ". " + esc(placeName(p)) + "</h2>";
      html += '<div class="body"><p>' + esc(stopText(p.id)) + "</p>";
      html += openBtn(p);
      html += buttons(p);
      html += "</div></article>";
    });
    var mapped = stops.filter(function (p) { return typeof p.lat === "number"; });
    var tm = town ? "walk" : "drive";
    var info = dirUrl(mapped, tm);
    if (info) {
      html += '<div class="map-row route-all"><a id="routeGoogle" href="' + esc(info.url) + '" target="_blank" rel="noopener">' + PIN + esc(T("openG")) + '</a><a id="routeApple" href="' + esc(appleDir(mapped, tm)) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + "</a></div>";
      if (info.trimmed) html += '<p class="est">' + esc(T("trim")) + "</p>";
    }
    view.innerHTML = html;
    view.setAttribute("data-stops", String(stops.length));
    view.setAttribute("data-mode", wishMode);
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
    var step2 = document.getElementById("step2");
    if (step2) {
      step2.hidden = false;
      step2.addEventListener("click", function (e) {
        var b = e.target.closest("[data-len]");
        if (!b) return;
        len = b.getAttribute("data-len");
        document.querySelectorAll("#step2 .pick").forEach(function (el) { el.classList.toggle("on", el === b); });
        applyPreset();
      });
    }
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
