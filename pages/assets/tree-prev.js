// The page read before this one is marked in the tree (.lw-tree-prev, a lighter blue than the
// current page), so after a quick look elsewhere the way back is in sight. Going back marks the
// page just left: two pages can be compared by going back and forth.
//
// Pages are told apart by path; an anchor within the page is the same page, and a reload keeps
// the mark. Kept for the tab. Marked in a mutation callback, before the new tree is painted.
(function () {
  var KEY = "lw-tree-trail";
  var MARK = "lw-tree-prev";
  var tree = null;

  function load() {
    try {
      return JSON.parse(sessionStorage.getItem(KEY) || "{}");
    } catch (e) {
      return {};
    }
  }

  function save(trail) {
    try {
      sessionStorage.setItem(KEY, JSON.stringify(trail));
    } catch (e) {
      // Without storage the mark stays until the tab reloads.
    }
  }

  var trail = load(); // {current, previous}: page paths

  function mark(nav) {
    var path = location.pathname;
    if (trail.current !== path) {
      trail = { current: path, previous: trail.current || null };
      save(trail);
    }
    nav.querySelectorAll("a.md-nav__link[href]").forEach(function (link) {
      var prev = trail.previous !== null && link.pathname === trail.previous && !link.hash;
      if (link.classList.contains(MARK) !== prev) link.classList.toggle(MARK, prev);
    });
  }

  function check() {
    var nav = document.querySelector(".md-nav--primary");
    if (nav && nav !== tree) {
      tree = nav;
      mark(nav);
    }
  }

  check();
  new MutationObserver(check).observe(document.documentElement, { childList: true, subtree: true });
})();
