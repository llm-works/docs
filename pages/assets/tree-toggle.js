// A click on a tree section's row, its title or its arrow, always opens the section's page (every
// section has one) and flips the section: open becomes closed, closed becomes open.
//   - its page already shown: flip it in place.
//   - another page shown: ask tree-open.js to give the next page's tree the flipped state, and
//     let the title's link open the page. A click on the arrow follows the title's link too,
//     instead of only flipping the section as the theme's arrow does.
(function () {
  var ROW = ".md-nav--primary .md-nav__container";

  document.addEventListener("click", function (e) {
    // Clicks with a modifier key (new tab or window) or another button stay the browser's
    if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    var row = e.target && e.target.closest ? e.target.closest(ROW) : null;
    if (!row) return;
    var link = row.querySelector(":scope > a.md-nav__link[href]");
    var toggle = row.parentElement.querySelector(":scope > .md-nav__toggle");
    if (!link || !toggle) return;
    var isOpen = !toggle.checked;
    if (link.href.split("#")[0] === location.href.split("#")[0]) {
      // Before the theme's instant navigation or the arrow's label sees the click.
      e.preventDefault();
      e.stopPropagation();
      toggle.checked = isOpen;
      toggle.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    if (window.lwTreeOpen) window.lwTreeOpen(toggle.id, isOpen, link.href);
    if (e.target.closest("a") !== link) {
      e.preventDefault();
      e.stopPropagation();
      link.click();
    }
  }, true);
})();
