/* Homepage search over search-index.js. Rebuild the index with: node build-search-index.js */
(function () {
  var LANGS = ["nl", "de", "en", "it", "tr", "es"];
  var lang = localStorage.getItem("hk-lang") || "nl";
  if (LANGS.indexOf(lang) < 0) lang = "nl";

  function fold(s) {
    return String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/ß/g, "ss").toLowerCase();
  }

  function analyze(s) {
    var chars = Array.from(s);
    var folded = "";
    var starts = [];
    chars.forEach(function (ch, i) {
      var f = fold(ch);
      for (var k = 0; k < f.length; k++) {
        starts.push(i);
        folded += f[k];
      }
    });
    return { chars: chars, folded: folded, starts: starts };
  }

  function esc(s) {
    return String(s || "").replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function snippet(text, query) {
    var info = analyze(text);
    var nq = fold(query);
    var at = info.folded.indexOf(nq);
    if (at < 0) return "";
    var from = info.starts[at];
    var to = info.starts[at + nq.length - 1] + 1;
    var winStart = Math.max(0, from - 42);
    var winEnd = Math.min(info.chars.length, to + 72);
    var before = esc(info.chars.slice(winStart, from).join(""));
    var mid = esc(info.chars.slice(from, to).join(""));
    var after = esc(info.chars.slice(to, winEnd).join(""));
    return (winStart > 0 ? "…" : "") + before + "<mark>" + mid + "</mark>" + after + (winEnd < info.chars.length ? "…" : "");
  }

  function find(page, query) {
    var nq = fold(query);
    var order = [lang].concat(LANGS.filter(function (l) { return l !== lang; }));
    for (var i = 0; i < order.length; i++) {
      var l = order[i];
      var blob = (page.text && page.text[l]) || "";
      if (blob && fold(blob).indexOf(nq) !== -1) return l;
    }
    return "";
  }

  function render(query) {
    var box = document.getElementById("searchResults");
    var empty = document.getElementById("searchEmpty");
    var grid = document.getElementById("tileGrid");
    if (!box || !grid) return;
    var q = String(query || "").trim();
    if (fold(q).length < 2) {
      box.hidden = true;
      box.innerHTML = "";
      grid.hidden = false;
      if (empty) empty.classList.remove("show");
      return;
    }
    var pages = window.HK_SEARCH || [];
    var hits = [];
    pages.forEach(function (page) {
      var used = find(page, q);
      if (!used) return;
      var title = (page.title && (page.title[lang] || page.title[used] || page.title.nl)) || page.url;
      var text = (page.text && page.text[used]) || "";
      var snip = snippet(text, q);
      if (!snip && page.blurb) snip = esc((page.blurb[lang] || page.blurb[used] || "").slice(0, 140));
      hits.push({ url: page.url, title: title, snip: snip, titleHit: fold(title).indexOf(fold(q)) !== -1 });
    });
    hits.sort(function (a, b) { return (b.titleHit - a.titleHit); });
    grid.hidden = true;
    if (!hits.length) {
      box.hidden = true;
      box.innerHTML = "";
      if (empty) empty.classList.add("show");
      return;
    }
    if (empty) empty.classList.remove("show");
    box.hidden = false;
    box.innerHTML = hits.map(function (hit) {
      return '<a class="search-hit" href="' + esc(hit.url) + '"><strong>' + esc(hit.title) + "</strong><span>" + hit.snip + "</span></a>";
    }).join("");
  }

  var input = document.getElementById("searchInput");
  if (input) {
    input.addEventListener("input", function () { render(input.value); });
  }
  document.addEventListener("hk-lang", function (e) {
    if (e && e.detail) lang = e.detail;
    if (input) render(input.value);
  });
  window.HKSearch = {
    setLang: function (l) { lang = l; if (input) render(input.value); },
    render: render
  };
})();
