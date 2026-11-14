/* Choice screen on route-wandel.html: walk, drive, or build your own. */
(function () {
  var PICK_KEY = "hk-route-picks";
  var WALKL = ["sight-witte-trappen","sight-i-love-kos","sight-palm-tree-lane","sight-palazzo-giustizia","sight-turks-badhuis","sight-boom-hippocrates","sight-gazi-hasan","sight-neratzia","sight-albergo-gelsomino","sight-kathedraal","sight-hatzi-pasha","sight-agora","sight-belastingpoort","sight-archeologisch-museum","sight-casa-del-fascio","sight-defterdar","sight-markthal","sight-paraskevi","sight-old-town","sight-morouk","sight-eski-tzami","sight-odeon","sight-westelijke-opgraving","sight-casa-romana","sight-altaar-dionysos"];
  var WALKS = WALKL.slice(0, 8);
  var DRIVES = ["sight-therma","sight-asklepion","sight-zia","sight-zoutmeer-tigaki","sight-kasteel-antimachia","sight-molen-antimachia","sight-agios-stefanos-kefalos","sight-limnionas"];
  var DRIVEL = ["sight-therma","sight-asklepion","sight-hippocratic-foundation","sight-zia","sight-palio-pyli","sight-zoutmeer-tigaki","sight-marmari","sight-mastichari","sight-kasteel-antimachia","sight-molen-antimachia","sight-agios-stefanos-kefalos","sight-limnionas"];
  /* Control coordinates come from the old walking route's map links (maps.app.goo.gl), resolved to the published pin. Named stops use hello-kos-places.js. */
  var CP = {
    c2: { role: "check", lat: 36.89451, lon: 27.288899 },
    c10: { role: "check", lat: 36.894756, lon: 27.292042 },
    inAgora: { role: "in", lat: 36.892962, lon: 27.290238 },
    outAgora: { role: "out", lat: 36.89378, lon: 27.289835 },
    c25: { role: "check", lat: 36.892289, lon: 27.287083 },
    c26: { role: "check", lat: 36.891629, lon: 27.286378 },
    c29: { role: "check", lat: 36.890837, lon: 27.286127 },
    c31: { role: "check", lat: 36.890303, lon: 27.284375 }
  };
  var WALK_STOPS = [
    { id: "sight-witte-trappen", after: ["c2"] },
    { id: "sight-i-love-kos" },
    { id: "sight-palm-tree-lane" },
    { id: "sight-palazzo-giustizia" },
    { id: "sight-turks-badhuis" },
    { id: "sight-boom-hippocrates" },
    { id: "sight-gazi-hasan" },
    { id: "sight-neratzia", after: ["c10"] },
    { id: "sight-albergo-gelsomino" },
    { id: "sight-kathedraal" },
    { id: "sight-hatzi-pasha" },
    { id: "sight-agora", before: ["inAgora"], after: ["outAgora"] },
    { id: "sight-belastingpoort" },
    { id: "sight-archeologisch-museum" },
    { id: "sight-casa-del-fascio" },
    { id: "sight-defterdar" },
    { id: "sight-markthal" },
    { id: "sight-paraskevi" },
    { id: "sight-old-town" },
    { id: "sight-morouk", after: ["c25", "c26"] },
    { id: "sight-eski-tzami", after: ["c29"] },
    { id: "sight-odeon", after: ["c31"] },
    { id: "sight-westelijke-opgraving" },
    { id: "sight-casa-romana" },
    { id: "sight-altaar-dionysos" }
  ];
  var GROUPS = ["kos","psalidi","platani","zia","pyli","tigaki","marmari","mastichari","antimachia","kefalos","limnionas"];
  var mode = null;
  var len = null;
  var PIN = '<svg class="pin" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>';

  function lang() {
    if (window.HK_I18N && HK_I18N.getLang) return HK_I18N.getLang();
    var l = localStorage.getItem("hk-lang") || "nl";
    return l;
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
    return '<div class="map-row"><a href="' + esc(gPoint(p.lat, p.lon)) + '" target="_blank" rel="noopener">' + PIN + esc(T("gmaps")) + '</a><a href="' + esc(aPoint(p.lat, p.lon, p.name)) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + '</a></div>';
  }
  function estLine(stops, withKind) {
    var line = T("est").replace("{n}", String(stops.length)).replace("{km}", kmStr(crow(stops)));
    if (withKind) {
      var kind = (stops.length <= 8 && crow(stops) < 8) ? T("estShort") : T("estLong");
      line += " " + T("estKind").replace("{kind}", kind);
    }
    return line;
  }
  function cpLabel(role) {
    if (role === "in") return T("cpIn");
    if (role === "out") return T("cpOut");
    return T("cpCheck");
  }
  function cpHtml(key) {
    var c = CP[key];
    if (!c) return "";
    var name = cpLabel(c.role);
    var html = '<li class="cp ' + c.role + '"><span class="mark" aria-hidden="true"></span><span>' + esc(name) + "</span>";
    html += '<a href="' + esc(gPoint(c.lat, c.lon)) + '" target="_blank" rel="noopener">' + esc(T("gmaps")) + "</a>";
    html += "</li>";
    return html;
  }
  function walkPoints() {
    var pts = [];
    WALK_STOPS.forEach(function (stop) {
      (stop.before || []).forEach(function (key) {
        var c = CP[key];
        if (c) pts.push({ lat: c.lat, lon: c.lon, name: cpLabel(c.role) });
      });
      var p = byId(stop.id);
      if (p && typeof p.lat === "number") pts.push(p);
      (stop.after || []).forEach(function (key) {
        var c = CP[key];
        if (c) pts.push({ lat: c.lat, lon: c.lon, name: cpLabel(c.role) });
      });
    });
    return pts;
  }
  function renderWalk() {
    var html = "";
    var cpCount = 0;
    WALK_STOPS.forEach(function (stop, i) {
      var p = byId(stop.id);
      html += '<article class="stop">';
      if (p && p.photo) html += '<img src="' + esc(p.photo) + '" alt="">';
      html += "<h2>" + (i + 1) + ". " + esc(p ? p.name : stop.id) + "</h2>";
      html += "<p>" + esc(stopText(stop.id)) + "</p>";
      if (p && p.link) html += '<p class="info"><a href="' + esc(p.link) + '">' + esc(T("info")) + "</a></p>";
      var subs = (stop.before || []).concat(stop.after || []);
      if (subs.length) {
        html += '<ul class="cps">';
        subs.forEach(function (key) { html += cpHtml(key); cpCount++; });
        html += "</ul>";
      }
      if (p && typeof p.lat === "number") html += buttons(p);
      html += "</article>";
    });
    var pts = walkPoints();
    var info = dirUrl(pts, "walk", 0);
    if (info) {
      html += '<div class="map-row"><a id="routeGoogle" href="' + esc(info.url) + '" target="_blank" rel="noopener">' + PIN + esc(T("openG")) + '</a><a id="routeApple" href="' + esc(appleDir(pts, "walk")) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + "</a></div>";
      if (info.trimmed) html += '<p class="est">' + esc(T("trim")) + "</p>";
    }
    var view = document.getElementById("routeView");
    if (view) view.innerHTML = html;
    var blurb = document.getElementById("blurb");
    if (blurb) blurb.textContent = T("walkOnlyNote");
    var est = document.getElementById("est");
    if (est) est.textContent = T("est").replace("{n}", String(WALK_STOPS.length)).replace("{km}", kmStr(crow(pts.filter(function (p) { return typeof p.lat === "number"; }))));
    view.setAttribute("data-stops", String(WALK_STOPS.length));
    view.setAttribute("data-cps", String(cpCount));
  }
  function showRoute(ids, noteKey, tm) {
    var custom = document.getElementById("customView");
    if (custom) custom.hidden = true;
    var stops = ids.map(byId).filter(function (p) { return p && typeof p.lat === "number"; });
    var html = "";
    stops.forEach(function (p, i) {
      html += '<article class="stop">';
      if (p.photo) html += '<img src="' + esc(p.photo) + '" alt="">';
      html += '<h2>' + (i + 1) + ". " + esc(p.name) + "</h2>";
      html += "<p>" + esc(stopText(p.id)) + "</p>";
      html += '<p class="info"><a href="' + esc(p.link) + '">' + esc(T("info")) + "</a></p>";
      html += buttons(p);
      html += "</article>";
    });
    var info = dirUrl(stops, tm);
    if (info) {
      html += '<div class="map-row"><a id="routeGoogle" href="' + esc(info.url) + '" target="_blank" rel="noopener">' + PIN + esc(T("openG")) + '</a><a id="routeApple" href="' + esc(appleDir(stops, tm)) + '" target="_blank" rel="noopener">' + PIN + esc(T("iphone")) + "</a></div>";
      if (info.trimmed) html += '<p class="est">' + esc(T("trim")) + "</p>";
    }
    document.getElementById("routeView").innerHTML = html;
    document.getElementById("blurb").textContent = T(noteKey);
    document.getElementById("est").textContent = stops.length > 1 ? estLine(stops, false) : "";
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
        html += '<label><input type="checkbox" data-id="' + esc(p.id) + '"' + on + "> " + esc(p.name) + "</label>";
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
    openCustom();
    document.getElementById("cWalk").addEventListener("click", function () {
      document.getElementById("cWalk").classList.add("on");
      document.getElementById("cDrive").classList.remove("on");
      savePicks();
      updateCustom();
    });
    document.getElementById("cDrive").addEventListener("click", function () {
      document.getElementById("cDrive").classList.add("on");
      document.getElementById("cWalk").classList.remove("on");
      savePicks();
      updateCustom();
    });
    document.getElementById("checks").addEventListener("change", function () {
      savePicks();
      updateCustom();
    });
    document.getElementById("fromFav").addEventListener("click", fromFav);
  }
  document.addEventListener("hk-lang", function () {
    if (page === "walk") renderWalk();
    else if (page === "custom") {
      savePicks();
      document.getElementById("blurb").textContent = T("customNote");
      renderChecks();
    } else if (page === "drive") applyPreset();
  });
})();
