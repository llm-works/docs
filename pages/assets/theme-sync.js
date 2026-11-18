// The main site's theme switch, driving Zensical's color scheme as well.
(function () {
  function sync() {
    var toggle = document.getElementById("theme-switch");
    if (toggle) toggle.checked = document.documentElement.classList.contains("light-mode");
  }

  document.addEventListener("change", function (e) {
    if (!e.target || e.target.id !== "theme-switch") return;
    var light = e.target.checked;
    document.documentElement.classList.toggle("light-mode", light);
    document.body.setAttribute("data-md-color-scheme", light ? "default" : "slate");
    try { localStorage.setItem("theme", light ? "light" : "dark"); } catch (err) {}
  });

  sync();
  document.addEventListener("DOMContentLoaded", sync);
})();
