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
    nl: { read: "Voorlezen", stop: "Stop", fill: "Nog aan te vullen.", soundOn: "Afspelen…", soundDone: "Klaar", soundStop: "Gestopt", noSpeech: "Voorlezen wordt door deze browser niet ondersteund." },
    de: { read: "Vorlesen", stop: "Stopp", fill: "Noch auszufüllen.", soundOn: "Wiedergabe…", soundDone: "Fertig", soundStop: "Gestoppt", noSpeech: "Vorlesen wird von diesem Browser nicht unterstützt." },
    en: { read: "Read aloud", stop: "Stop", fill: "Still to be filled in.", soundOn: "Playing…", soundDone: "Done", soundStop: "Stopped", noSpeech: "Read-aloud is not supported in this browser." },
    it: { read: "Leggi ad alta voce", stop: "Stop", fill: "Ancora da completare.", soundOn: "Riproduzione…", soundDone: "Fatto", soundStop: "Interrotto", noSpeech: "La lettura vocale non è supportata da questo browser." },
    tr: { read: "Sesli oku", stop: "Durdur", fill: "Henüz doldurulacak.", soundOn: "Çalıyor…", soundDone: "Bitti", soundStop: "Durdu", noSpeech: "Sesli okuma bu tarayıcıda desteklenmiyor." },
    es: { read: "Leer en voz alta", stop: "Parar", fill: "Aún por completar.", soundOn: "Reproduciendo…", soundDone: "Listo", soundStop: "Parado", noSpeech: "La lectura en voz alta no está disponible en este navegador." }
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
    if (voice) u.voice = voice;
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
      var btnPlay = document.getElementById("btnPlay");
      var btnStop = document.getElementById("btnStop");
      var status = document.getElementById("ttsStatus");
      function setStatus(msg) { if (status) status.textContent = msg; }
      if (btnPlay) {
        btnPlay.addEventListener("click", function () {
          var lang = getLang();
          var source = document.getElementById("readText");
          var text = source ? source.innerText.replace(/\s+/g, " ").trim() : "";
          if (!text) return;
          if (!window.speechSynthesis) { setStatus(textFor(lang, "noSpeech")); return; }
          var u = speak(text, lang);
          if (!u) return;
          btnPlay.classList.add("playing");
          if (btnStop) btnStop.classList.add("show");
          setStatus(textFor(lang, "soundOn") + " " + lang.toUpperCase());
          u.onend = u.onerror = function () {
            btnPlay.classList.remove("playing");
            if (btnStop) btnStop.classList.remove("show");
            setStatus("");
          };
        });
      }
      if (btnStop) {
        btnStop.addEventListener("click", function () {
          if (window.speechSynthesis) speechSynthesis.cancel();
          if (btnPlay) btnPlay.classList.remove("playing");
          btnStop.classList.remove("show");
          setStatus(textFor(getLang(), "soundStop"));
        });
      }
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
  function ensureSpeaker(btn) {
    if (!btn || btn.querySelector(".spk")) return;
    var key = btn.getAttribute("data-i18n");
    var label = (btn.textContent || "").replace(/^🔊\s*/, "").trim();
    if (key) {
      var span = document.createElement("span");
      span.setAttribute("data-i18n", key);
      span.textContent = label;
      btn.removeAttribute("data-i18n");
      btn.textContent = "";
      btn.insertAdjacentHTML("afterbegin", SPEAKER);
      btn.appendChild(span);
    } else {
      btn.insertAdjacentHTML("afterbegin", SPEAKER);
    }
  }
  ensureSpeaker(document.getElementById("btnPlay"));

  window.HK_I18N = { setLang: setLang, getLang: getLang, apply: apply, speak: speak, VOICE: VOICE };
})();
