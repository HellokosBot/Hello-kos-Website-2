/* Shared language switch for Hello Kos.
   Stores the choice in localStorage key "hk-lang".
   Pages with their own setLang set <html data-hk-own="1"> and keep that script.
   Other pages put translations in window.HK_DICT and mark text with data-i18n.
   Voorlezen uses the visible text, so it follows the chosen language. */
(function () {
  var LANGS = ["nl", "de", "en", "it", "tr", "es"];
  var VOICE = {
    nl: "nl-NL",
    de: "de-DE",
    en: "en-GB",
    it: "it-IT",
    tr: "tr-TR",
    es: "es-ES"
  };
  var SOUND = {
    nl: "Hallo. Dit is de geluidstest van Hello Kos.",
    de: "Hallo. Das ist der Soundtest von Hello Kos.",
    en: "Hello. This is the Hello Kos sound test.",
    it: "Ciao. Questo è il test audio di Hello Kos.",
    tr: "Merhaba. Bu, Hello Kos ses testidir.",
    es: "Hola. Esta es la prueba de sonido de Hello Kos."
  };
  var UI = {
    nl: { read: "Voorlezen", readStop: "Stop voorlezen", stop: "Stop", fill: "Nog aan te vullen.", soundOn: "Afspelen…", soundDone: "Klaar", soundStop: "Gestopt", noSpeech: "Voorlezen wordt door deze browser niet ondersteund." },
    de: { read: "Vorlesen", readStop: "Vorlesen stoppen", stop: "Stopp", fill: "Noch auszufüllen.", soundOn: "Wiedergabe…", soundDone: "Fertig", soundStop: "Gestoppt", noSpeech: "Vorlesen wird von diesem Browser nicht unterstützt." },
    en: { read: "Read aloud", readStop: "Stop reading", stop: "Stop", fill: "Still to be filled in.", soundOn: "Playing…", soundDone: "Done", soundStop: "Stopped", noSpeech: "Read-aloud is not supported in this browser." },
    it: { read: "Leggi ad alta voce", readStop: "Ferma la lettura", stop: "Stop", fill: "Ancora da completare.", soundOn: "Riproduzione…", soundDone: "Fatto", soundStop: "Interrotto", noSpeech: "La lettura vocale non è supportata da questo browser." },
    tr: { read: "Sesli oku", readStop: "Okumayı durdur", stop: "Durdur", fill: "Henüz doldurulacak.", soundOn: "Çalıyor…", soundDone: "Bitti", soundStop: "Durdu", noSpeech: "Sesli okuma bu tarayıcıda desteklenmiyor." },
    es: { read: "Leer en voz alta", readStop: "Parar la lectura", stop: "Parar", fill: "Aún por completar.", soundOn: "Reproduciendo…", soundDone: "Listo", soundStop: "Parado", noSpeech: "La lectura en voz alta no está disponible en este navegador." }
  };

  function getLang() {
    var l = localStorage.getItem("hk-lang") || "nl";
    return LANGS.indexOf(l) >= 0 ? l : "nl";
  }

  function textFor(lang, key) {
    var page = window.HK_DICT && window.HK_DICT[lang];
    if (page && page[key] != null && page[key] !== "") return page[key];
    var nlPage = window.HK_DICT && window.HK_DICT.nl;
    if (nlPage && nlPage[key] != null) return nlPage[key];
    if (UI[lang] && UI[lang][key] != null) return UI[lang][key];
    if (UI.nl[key] != null) return UI.nl[key];
    return null;
  }

  function apply(lang) {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-lang-block]").forEach(function (el) {
      el.style.display = el.getAttribute("data-lang-block") === lang ? "block" : "none";
    });
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var value = textFor(lang, key);
      if (value == null) return;
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") el.placeholder = value;
      else el.innerHTML = value;
    });
    var heading = document.querySelector("h1[data-i18n]");
    if (heading) {
      var name = heading.textContent.replace(/\s+/g, " ").trim();
      if (name) document.title = name + " – Hello Kos";
    }
    var opt = document.querySelector('.lang-option[data-lang="' + lang + '"]');
    var flag = document.getElementById("flag");
    var code = document.getElementById("code");
    if (opt && flag) flag.textContent = opt.getAttribute("data-flag") || flag.textContent;
    if (code) code.textContent = lang.toUpperCase();
    document.querySelectorAll(".lang-option").forEach(function (o) {
      o.classList.toggle("active", o.getAttribute("data-lang") === lang);
    });
  }

  function closeMenu() {
    var menu = document.getElementById("langMenu");
    var overlay = document.getElementById("overlay");
    var btn = document.getElementById("langBtn");
    if (menu) menu.classList.remove("open");
    if (overlay) overlay.classList.remove("open");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }

  function openMenu() {
    var menu = document.getElementById("langMenu");
    var overlay = document.getElementById("overlay");
    var btn = document.getElementById("langBtn");
    if (menu) menu.classList.add("open");
    if (overlay) overlay.classList.add("open");
    if (btn) btn.setAttribute("aria-expanded", "true");
  }

  function setLang(lang) {
    if (LANGS.indexOf(lang) < 0) lang = "nl";
    localStorage.setItem("hk-lang", lang);
    apply(lang);
    closeMenu();
    document.dispatchEvent(new CustomEvent("hk-lang", { detail: lang }));
  }

  function pickVoice(code) {
    var voices = window.speechSynthesis ? speechSynthesis.getVoices() || [] : [];
    var prefix = code.slice(0, 2).toLowerCase();
    return voices.find(function (v) { return v.lang === code; })
      || voices.find(function (v) { return v.lang && v.lang.toLowerCase().indexOf(prefix) === 0; })
      || null;
  }

  function speak(text, lang) {
    if (!window.speechSynthesis) return false;
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = VOICE[lang] || VOICE.nl;
    u.rate = 0.95;
    var voice = pickVoice(u.lang);
    if (voice) {
      try { u.voice = voice; } catch (err) { /* some browsers reject a voice object */ }
    }
    speechSynthesis.speak(u);
    return u;
  }

  var own = document.documentElement.getAttribute("data-hk-own") === "1";
  if (!own) {
    var langBtn = document.getElementById("langBtn");
    var overlay = document.getElementById("overlay");
    if (langBtn) {
      langBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        var menu = document.getElementById("langMenu");
        if (menu && menu.classList.contains("open")) closeMenu();
        else openMenu();
      });
    }
    if (overlay) overlay.addEventListener("click", closeMenu);
    document.querySelectorAll(".lang-option").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setLang(btn.getAttribute("data-lang"));
      });
    });
    apply(getLang());

    if (document.documentElement.getAttribute("data-hk-tts") !== "1") {
      var btnTest = document.getElementById("btnTestSound");
      var btnTestStop = document.getElementById("btnStopSound");
      if (btnTest) {
        btnTest.addEventListener("click", function () {
          var lang = getLang();
          var u = speak(SOUND[lang] || SOUND.nl, lang);
          var el = document.getElementById("soundStatus");
          if (!u) { if (el) el.textContent = textFor(lang, "noSpeech"); return; }
          if (el) el.textContent = textFor(lang, "soundOn");
          u.onend = function () { if (el) el.textContent = textFor(lang, "soundDone"); };
        });
      }
      if (btnTestStop) {
        btnTestStop.addEventListener("click", function () {
          if (window.speechSynthesis) speechSynthesis.cancel();
          var el = document.getElementById("soundStatus");
          if (el) el.textContent = textFor(getLang(), "soundStop");
        });
      }
    }
  }

  var SPEAKER = '<svg class="spk" viewBox="0 0 24 24" aria-hidden="true"><path fill="#fff" d="M3 10v4h4l5 5V5L7 10H3zm11.5 2a3.5 3.5 0 0 0-2-3.15v6.3a3.5 3.5 0 0 0 2-3.15zM14 4.07v2.02a6 6 0 0 1 0 11.82v2.02a8 8 0 0 0 0-15.86z"/></svg>';
  var STOPICON = '<svg class="spk" viewBox="0 0 24 24" aria-hidden="true"><path fill="#fff" d="M6 6h12v12H6z"/></svg>';
  var hkSpeaking = false;

  function ensureSpeaker(btn) {
    if (!btn || btn.querySelector(".spk")) return;
    var key = btn.getAttribute("data-i18n");
    var label = (btn.textContent || "").replace(/^🔊\s*/, "").trim();
    if (key) {
      var span = document.createElement("span");
      span.setAttribute("data-i18n", key);
      span.setAttribute("data-i18n-idle", key);
      span.textContent = label;
      btn.removeAttribute("data-i18n");
      btn.textContent = "";
      btn.insertAdjacentHTML("afterbegin", SPEAKER);
      btn.appendChild(span);
    } else {
      btn.insertAdjacentHTML("afterbegin", SPEAKER);
    }
  }

  function setStatus(msg) {
    var status = document.getElementById("ttsStatus");
    if (status) status.textContent = msg || "";
  }

  function setSpeakUi(on) {
    hkSpeaking = on;
    var btn = document.getElementById("btnPlay");
    if (!btn) return;
    btn.classList.toggle("playing", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    var icon = btn.querySelector(".spk");
    if (icon) icon.outerHTML = on ? STOPICON : SPEAKER;
    var span = btn.querySelector("[data-i18n]");
    if (span) {
      var idle = span.getAttribute("data-i18n-idle") || span.getAttribute("data-i18n") || "read";
      var key = on ? "readStop" : idle;
      span.setAttribute("data-i18n", key);
      var label = textFor(getLang(), key);
      if (label) span.textContent = label;
    }
    var stop = document.getElementById("btnStop");
    if (stop) stop.style.display = "none";
  }

  function onPlayClick() {
    var lang = getLang();
    if (hkSpeaking || (window.speechSynthesis && speechSynthesis.speaking)) {
      if (window.speechSynthesis) speechSynthesis.cancel();
      setSpeakUi(false);
      setStatus("");
      return;
    }
    var source = document.getElementById("readText");
    var text = source ? source.innerText.replace(/\s+/g, " ").trim() : "";
    if (!text) return;
    if (!window.speechSynthesis) { setStatus(textFor(lang, "noSpeech")); return; }
    var u = speak(text, lang);
    if (!u) return;
    setSpeakUi(true);
    setStatus(textFor(lang, "soundOn"));
    u.onend = u.onerror = function () {
      setSpeakUi(false);
      setStatus("");
    };
  }

  function bindReadAloud() {
    var btn = document.getElementById("btnPlay");
    if (!btn || btn.getAttribute("data-hk-bound") === "1") return;
    if (document.documentElement.getAttribute("data-hk-tts") === "1" || document.documentElement.getAttribute("data-hk-own") === "1") {
      var fresh = btn.cloneNode(true);
      btn.parentNode.replaceChild(fresh, btn);
      btn = fresh;
    }
    btn.setAttribute("data-hk-bound", "1");
    ensureSpeaker(btn);
    var stop = document.getElementById("btnStop");
    if (stop) stop.style.display = "none";
    btn.addEventListener("click", onPlayClick);
  }

  function placeForPage() {
    if (!window.HK_PLACES) return null;
    var file = ((location.pathname || "").split("/").pop() || "").replace(/\.html$/, "");
    for (var i = 0; i < window.HK_PLACES.length; i++) {
      if (window.HK_PLACES[i].id === file) return window.HK_PLACES[i];
    }
    return null;
  }

  function mapsSearch(lat, lon) {
    return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(String(lat) + "," + String(lon));
  }

  function fixMapHrefs() {
    var place = placeForPage();
    document.querySelectorAll("a[href*='google.com/maps']").forEach(function (a) {
      var raw = a.getAttribute("href") || "";
      if (raw.indexOf("/dir") >= 0 || raw.indexOf("destination=") >= 0) return;
      if (!a.getAttribute("target")) a.setAttribute("target", "_blank");
      if (!a.getAttribute("rel")) a.setAttribute("rel", "noopener");
      if (place && place.lat != null && place.lon != null) a.href = mapsSearch(place.lat, place.lon);
      else if (place && place.name) {
        var q = "";
        try { q = new URL(a.href, location.href).searchParams.get("query") || ""; } catch (err) { q = ""; }
        if (!q) a.href = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(place.name + " Kos");
      }
    });
    document.querySelectorAll("a[href*='maps.apple.com']").forEach(function (a) {
      if (!place) return;
      if (!a.getAttribute("target")) a.setAttribute("target", "_blank");
      if (!a.getAttribute("rel")) a.setAttribute("rel", "noopener");
      if (place.lat != null && place.lon != null) {
        a.href = "https://maps.apple.com/?ll=" + place.lat + "," + place.lon + "&q=" + encodeURIComponent(place.name || "Kos");
      }
    });
  }

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var a = t.closest("a[href*='google.com/maps'], a[href*='maps.apple.com']");
    if (!a) return;
    var href = a.href || "";
    if (href.indexOf("http") !== 0) return;
    if (/[?&](?:query|q)=(?:&|$)/.test(href)) return;
    e.preventDefault();
    var opened = null;
    try { opened = window.open(href, "_blank", "noopener"); } catch (err) { opened = null; }
    if (!opened) window.location.href = href;
  }, true);

  bindReadAloud();
  ensureSpeaker(document.getElementById("btnPlay"));
  if (document.readyState !== "complete") document.addEventListener("DOMContentLoaded", fixMapHrefs);
  fixMapHrefs();

  window.HK_I18N = { setLang: setLang, getLang: getLang, apply: apply, speak: speak, VOICE: VOICE };
})();
