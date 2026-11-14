#!/usr/bin/env node
/* Rebuild the site search index.
   Run from the repo root after page text changes:
     node build-search-index.js
   It reads every HTML file and writes search-index.js. */
const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const LANGS = ["nl", "de", "en", "it", "tr", "es"];
const OUT = path.join(ROOT, "search-index.js");

function sliceBalanced(src, start) {
  let depth = 0;
  let quote = null;
  for (let i = start; i < src.length; i++) {
    const c = src[i];
    if (quote) {
      if (c === "\\") { i++; continue; }
      if (c === quote) quote = null;
      continue;
    }
    if (c === '"' || c === "'" || c === "`") { quote = c; continue; }
    if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return src.slice(start, i + 1);
    }
  }
  return null;
}

function objectsMatching(src, re) {
  const found = [];
  const flags = new RegExp(re.source, "g");
  let m;
  while ((m = flags.exec(src))) {
    const brace = src.indexOf("{", m.index);
    if (brace < 0 || brace - m.index > 30) continue;
    const raw = sliceBalanced(src, brace);
    if (!raw) continue;
    try {
      const val = Function("return (" + raw + ")")();
      if (val && typeof val === "object") found.push(val);
    } catch (err) { /* skip blocks that are not plain data */ }
  }
  return found;
}

function plain(s) {
  return String(s || "")
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\s+/g, " ")
    .trim();
}

function collectStrings(value, out) {
  if (typeof value === "string") {
    const t = plain(value);
    if (t) out.push(t);
  } else if (value && typeof value === "object") {
    Object.keys(value).forEach(function (k) { collectStrings(value[k], out); });
  }
  return out;
}

function visibleText(html) {
  return plain(html.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " "));
}

function langBlockText(html) {
  const re = /data-lang-block="([a-z]{2})"/gi;
  const marks = [];
  let m;
  while ((m = re.exec(html))) marks.push({ lang: m[1], i: m.index });
  const map = {};
  marks.forEach(function (mark, idx) {
    if (map[mark.lang]) return;
    const start = html.indexOf(">", mark.i) + 1;
    let end = html.length;
    if (idx + 1 < marks.length) end = html.lastIndexOf("<", marks[idx + 1].i);
    if (end < start) end = html.length;
    const slice = html.slice(start, end);
    const h1 = plain((slice.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) || [])[1] || "");
    map[mark.lang] = { text: visibleText(slice), h1: h1 };
  });
  return map;
}

function pick(block, keys) {
  if (!block) return "";
  for (let i = 0; i < keys.length; i++) {
    const v = block[keys[i]];
    if (typeof v === "string" && plain(v)) return plain(v);
  }
  return "";
}

function pageRecord(file, html) {
  const blocks = []
    .concat(objectsMatching(html, /HK_DICT\s*=/))
    .concat(objectsMatching(html, /I18N\s*=/))
    .concat(objectsMatching(html, /var\s+dict\s*=/));
  const byLang = {};
  LANGS.forEach(function (lang) { byLang[lang] = []; });
  blocks.forEach(function (obj) {
    LANGS.forEach(function (lang) {
      if (obj[lang] && typeof obj[lang] === "object") collectStrings(obj[lang], byLang[lang]);
    });
  });
  const blocksByLang = langBlockText(html);
  const langAttr = (html.match(/<html[^>]*\slang="([a-z]{2})"/i) || [])[1] || "nl";
  if (Object.keys(blocksByLang).length) {
    LANGS.forEach(function (lang) {
      if (blocksByLang[lang] && blocksByLang[lang].text) byLang[lang].push(blocksByLang[lang].text);
    });
  } else {
    const visible = visibleText(html);
    if (byLang[langAttr]) byLang[langAttr].push(visible);
    else byLang.nl.push(visible);
  }

  const titleTag = plain((html.match(/<title>([\s\S]*?)<\/title>/i) || [])[1] || "").replace(/\s+[–|-]\s+Hello Kos.*$/i, "");
  const h1 = plain((html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) || [])[1] || "");
  const title = {};
  const blurb = {};
  const text = {};
  LANGS.forEach(function (lang) {
    const block = blocks.map(function (o) { return o[lang]; }).filter(Boolean);
    let t = "";
    let b = "";
    block.forEach(function (one) {
      if (!t) t = pick(one, ["title", "heroTitle", "name", "h1"]);
      if (!b) b = pick(one, ["lead", "sub", "heroSub", "intro"]);
    });
    if (!t && blocksByLang[lang] && blocksByLang[lang].h1) t = blocksByLang[lang].h1;
    if (!t) t = h1 || titleTag || file.replace(/\.html$/, "");
    const body = Array.from(new Set(byLang[lang])).join(" ");
    if (!b) b = body.slice(0, 180);
    title[lang] = t;
    blurb[lang] = b;
    text[lang] = (t + " " + body).replace(/\s+/g, " ").trim();
  });
  return { url: file, title: title, blurb: blurb, text: text };
}

const files = fs.readdirSync(ROOT).filter(function (name) {
  return name.endsWith(".html") && name !== "index.html";
}).sort();

const pages = [];
files.forEach(function (name) {
  const html = fs.readFileSync(path.join(ROOT, name), "utf8");
  pages.push(pageRecord(name, html));
});

const body = "window.HK_SEARCH = " + JSON.stringify(pages) + ";\n";
fs.writeFileSync(OUT, body);
const kb = Math.round(body.length / 1024);
console.log("pages " + pages.length + "  search-index.js " + kb + " KB");
