// Tree sections stay open until the reader closes them. Each page comes with its own tree, in
// which only the path to that page is open, so opening one section and then moving to another
// page closed every other section. Remember the open sections for the tab, by their toggle's id
// (the same on every page, since every page has the same tree), and reopen them in each new
// page's tree.
//
// A section opens or closes on its own page, by its toggle. The sections a page opens because it
// lies inside them count as opened too. A click on a section's row that opens its page and
// flips it (tree-toggle.js) asks for that state with window.lwTreeOpen(id, open, href): the
// tree of the page at `href` gets it, even where that page would open the section itself (it is
// the section's own page), however long the page takes to arrive.
//
// The new tree is reopened in a mutation callback, before the browser paints it. The theme may
// already have computed its styles by then (with those sections closed), so reopening would play
// the open animation: the reopened sections get .lw-tree-restore, which turns transitions off,
// until two frames later. This must run before tree-scroll.js, which measures the new tree to keep
// the clicked item in place: load it first.
(function () {
  var KEY = "lw-tree-open";
  var TOGGLE = ".md-nav--primary .md-nav__toggle[id]";
  var open = load();
  var tree = null;
  var request = null; // {id, open, path}: the state the tree of page `path` gives section `id`

  function load() {
    try {
      return new Set(JSON.parse(sessionStorage.getItem(KEY) || "[]"));
    } catch (e) {
      return new Set();
    }
  }

  function save() {
    try {
      sessionStorage.setItem(KEY, JSON.stringify(Array.from(open)));
    } catch (e) {
      // Without storage the sections stay open while the tab does not reload.
    }
  }

  // Give a new tree the remembered sections and the requested state; remember the sections it
  // opened itself.
  function sync(nav) {
    // A request is for the page its click opens. Any other page's tree drops it: another click
    // came first, or the click opened no page.
    var asked = request && request.path === location.pathname ? request : null;
    request = null;
    var changed = [];
    nav.querySelectorAll(".md-nav__toggle[id]").forEach(function (toggle) {
      var want = asked && toggle.id === asked.id ? asked.open : open.has(toggle.id) || toggle.checked;
      if (toggle.checked !== want) {
        toggle.parentElement.classList.add("lw-tree-restore");
        changed.push(toggle.parentElement);
        toggle.checked = want;
      }
      if (want) open.add(toggle.id);
    });
    save();
    if (changed.length) {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          changed.forEach(function (item) { item.classList.remove("lw-tree-restore"); });
        });
      });
    }
  }

  window.lwTreeOpen = function (id, isOpen, href) {
    if (isOpen) open.add(id);
    else open.delete(id);
    save();
    request = { id: id, open: isOpen, path: new URL(href, location.href).pathname };
  };

  function check() {
    var nav = document.querySelector(".md-nav--primary");
    if (nav && nav !== tree) {
      tree = nav;
      sync(nav);
    }
  }

  document.addEventListener("change", function (e) {
    var toggle = e.target;
    if (!toggle.matches || !toggle.matches(TOGGLE)) return;
    if (toggle.checked) open.add(toggle.id);
    else open.delete(toggle.id);
    save();
  });

  check();
  new MutationObserver(check).observe(document.documentElement, { childList: true, subtree: true });
})();
