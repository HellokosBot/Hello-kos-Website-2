/* Lightbox for photos on location pages. Menu tiles are not .hk-zoom. */
(function () {
  if (!document.body || !document.body.classList.contains("hk-guide")) return;
  var box = document.createElement("div");
  box.id = "hk-lightbox";
  box.hidden = true;
  box.innerHTML = '<img alt="">';
  document.body.appendChild(box);
  var img = box.querySelector("img");

  function close() {
    box.hidden = true;
    img.removeAttribute("src");
  }

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    if (!box.hidden && (t === box || t === img)) {
      close();
      return;
    }
    var photo = t.closest("img.hk-zoom");
    if (!photo || photo.closest("a.card, a.tile, .grid")) return;
    if (!photo.getAttribute("src")) return;
    img.src = photo.currentSrc || photo.src;
    box.hidden = false;
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !box.hidden) close();
  });
})();
