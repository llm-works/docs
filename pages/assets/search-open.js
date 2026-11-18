// Search buttons open the theme's search through its keyboard shortcut (Ctrl+K).
//
// The theme wires its search button once, when the page first loads. The docs search sits in the
// tree's sidebar (overrides/main.html), which instant navigation replaces on every page change,
// so after the first page change the sidebar's button is a fresh, unwired copy and clicking it
// did nothing. The shortcut's handler is global and keeps working across page changes: a click
// on the sidebar's button, or on the search button in the narrow-screen bar, sends it instead.
(function () {
  var BUTTONS = ".md-search__button, .lw-docbar__search";

  document.addEventListener("click", function (e) {
    var button = e.target && e.target.closest ? e.target.closest(BUTTONS) : null;
    if (!button) return;
    // Before the theme's own handler on the first page's button, so search opens once.
    e.preventDefault();
    e.stopPropagation();
    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "k", code: "KeyK", ctrlKey: true, bubbles: true, cancelable: true,
    }));
  }, true);
})();
