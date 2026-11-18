// Full text on hover for tree and "On this page" items that one line cuts short ("…").
// Checked when the pointer enters an item, so it stays right as sections open or the window
// resizes; items that fit get no tooltip.
(function () {
  document.addEventListener("mouseover", function (e) {
    var el = e.target && e.target.closest ? e.target.closest(".md-nav .md-ellipsis") : null;
    if (!el) return;
    if (el.scrollWidth > el.clientWidth) {
      el.title = el.textContent.replace(/\s+/g, " ").trim();
    } else {
      el.removeAttribute("title");
    }
  });
})();
