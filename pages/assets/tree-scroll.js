// Keep the tree still when the reader clicks an item in it: the clicked item stays exactly where
// it was on screen.
//
// On a page change (instant navigation), the new page's tree comes in scrolled to the top, and
// the theme then scrolls it so the active item sits in the middle of the pane. Both positions get
// painted, so the tree flickers or jumps. Instead, on the click, remember how far below the
// pane's top the item is; when the new tree is inserted (a mutation callback runs before the
// browser paints) scroll it so its active item (the clicked one) is at that distance again, and
// do the same in place of the theme's centering. Sections may have opened or closed above the
// item, so it is the item's place that is kept, not the scroll offset.
//
// The new pane only becomes a scroll container when the theme sizes it, a frame after it is
// inserted; it gets the old pane's height (same layout) at once, so the position takes before
// first paint.
(function () {
  var PANE = ".md-sidebar--primary .md-sidebar__scrollwrap";
  var HOLD_MS = 1500;
  var hold = null; // {href, offset, height} while a click's page change is in progress
  var timer = null;

  function isPane(el) {
    return hold !== null && el && el.matches && el.matches(PANE);
  }

  // The pane's active item, once it is the clicked one (not the page being left).
  function clicked(pane) {
    var active = pane.querySelector(".md-nav__link--active[href]");
    return active && active.href === hold.href ? active : null;
  }

  function release() {
    hold = null;
    if (timer) clearTimeout(timer);
    timer = null;
  }

  // Scroll `pane` so the clicked item sits `hold.offset` below the pane's top again.
  function place(pane, item) {
    var delta = item.getBoundingClientRect().top - pane.getBoundingClientRect().top - hold.offset;
    if (Math.abs(delta) >= 1) pane.scrollTop += delta;
  }

  document.addEventListener("click", function (e) {
    var pane = document.querySelector(PANE);
    var link = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!pane || !link || !pane.contains(link)) return;
    hold = {
      href: link.href,
      offset: link.getBoundingClientRect().top - pane.getBoundingClientRect().top,
      height: pane.style.height,
    };
    // A click that does not navigate, or a slow page, must not hold forever.
    if (timer) clearTimeout(timer);
    timer = setTimeout(release, HOLD_MS);
  }, true);

  // The new page's tree: size it as the old one was and place it, before first paint.
  new MutationObserver(function () {
    var pane = document.querySelector(PANE);
    var item = isPane(pane) ? clicked(pane) : null;
    if (!item) return;
    if (!pane.style.height && hold.height) pane.style.height = hold.height;
    place(pane, item);
  }).observe(document.documentElement, { childList: true, subtree: true });

  // The theme's centering of the active item: place it instead, and the page change is done.
  var nativeScrollTo = Element.prototype.scrollTo;
  Element.prototype.scrollTo = function () {
    var item = isPane(this) ? clicked(this) : null;
    if (item) {
      place(this, item);
      release();
      return;
    }
    return nativeScrollTo.apply(this, arguments);
  };
})();
