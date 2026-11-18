// "On this page" marks the section the reader is at: the last one whose heading is at or above the
// line where a jump to a heading puts it (the theme's scroll margin, 3.6rem below the window top).
//
// The theme marks a heading as reached at the header's height plus 0.9 times the gap above the
// main grid. That gap is zero here: it also sets when the sidebars stick, and a gap makes them
// slide as the page scrolls. So a heading reached by a click landed below the theme's line, and
// the entry before it stayed marked. This sets the marks from the jump's line instead; the theme
// keeps setting its own, so they are set again whenever it changes them (a mutation callback
// runs before the browser paints).
//
// The last sections of a page cannot scroll up to the line. A clicked entry stays marked until
// the reader scrolls (wheel, touch or keys), so clicking one of them marks it, not the last one.
(function () {
  var NAV = ".md-sidebar--secondary .md-nav--secondary";
  var ACTIVE = "md-nav__link--active";
  var PASSED = "md-nav__link--passed";
  var SLACK_PX = 4;
  var nav = null;
  var entries = [];
  var clicked = null; // the clicked entry's index, until the reader scrolls
  var watcher = new MutationObserver(apply);

  function line() {
    var rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
    return 3.6 * rem + SLACK_PX;
  }

  function current() {
    if (clicked !== null) return clicked;
    var root = document.documentElement;
    if (window.scrollY > 0 && window.innerHeight + window.scrollY >= root.scrollHeight - 1) {
      return entries.length - 1;
    }
    var at = line();
    var index = -1;
    entries.forEach(function (entry, i) {
      if (entry.heading.getBoundingClientRect().top <= at) index = i;
    });
    return index;
  }

  function apply() {
    if (!entries.length) return;
    var index = current();
    entries.forEach(function (entry, i) {
      var link = entry.link;
      if (link.classList.contains(ACTIVE) !== (i === index)) link.classList.toggle(ACTIVE, i === index);
      if (link.classList.contains(PASSED) !== (i <= index)) link.classList.toggle(PASSED, i <= index);
    });
  }

  // A new page's "On this page": its entries and their headings.
  function attach() {
    var found = document.querySelector(NAV);
    if (found === nav) return;
    nav = found;
    clicked = null;
    watcher.disconnect();
    entries = [];
    if (!nav) return;
    nav.querySelectorAll("a.md-nav__link[href*='#']").forEach(function (link) {
      var id;
      try {
        id = decodeURIComponent(link.hash.slice(1));
      } catch (e) {
        return; // a malformed %-escape: skip the entry, keep the others
      }
      var heading = id && document.getElementById(id);
      if (heading) entries.push({ link: link, heading: heading });
    });
    watcher.observe(nav, { attributes: true, attributeFilter: ["class"], subtree: true });
    apply();
  }

  document.addEventListener("click", function (e) {
    var link = e.target && e.target.closest ? e.target.closest(NAV + " a.md-nav__link") : null;
    if (!link) return;
    var index = entries.findIndex(function (entry) { return entry.link === link; });
    clicked = index >= 0 ? index : null;
    apply();
  }, true);

  function release() {
    if (clicked === null) return;
    clicked = null;
    apply();
  }

  ["wheel", "touchstart", "keydown"].forEach(function (type) {
    window.addEventListener(type, release, { passive: true });
  });
  window.addEventListener("scroll", apply, { passive: true });
  window.addEventListener("resize", apply);
  attach();
  new MutationObserver(attach).observe(document.documentElement, { childList: true, subtree: true });
})();
