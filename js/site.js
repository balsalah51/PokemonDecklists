(function () {
  var COPY_LABEL = "Copy list";

  function textList(root) {
    return Array.prototype.map.call(root.querySelectorAll(".text-line"), function (line) {
      var qty = (line.querySelector(".qty") || {}).textContent || "";
      var name = (line.querySelector(".card-title") || {}).textContent || "";
      var id = (line.querySelector(".card-id") || {}).textContent || "";
      qty = qty.replace(/\s+/g, "");
      name = (name || "").trim();
      id = id.trim();
      if (!qty || !name) return "";
      if (qty.slice(-1) !== "x") qty += "x";
      return qty + " " + name + (id ? " " + id : "");
    }).filter(Boolean).join("\n");
  }

  function initCopy() {
    document.querySelectorAll("[data-copy-sim]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var root = btn.closest(".text-deck") || document;
        var text = textList(root);
        if (!text) return;
        var done = function () {
          var prev = btn.textContent;
          btn.textContent = "Copied";
          setTimeout(function () { btn.textContent = prev; }, 1400);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done).catch(function () {
            window.prompt("Copy this 60-card list", text);
          });
        } else {
          window.prompt("Copy this 60-card list", text);
        }
      });
    });
  }

  function ensureCopyButtons() {
    document.querySelectorAll(".text-deck .section-title").forEach(function (title) {
      if (title.querySelector("[data-copy-sim]")) return;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy-sim";
      btn.setAttribute("data-copy-sim", "");
      btn.textContent = COPY_LABEL;
      title.appendChild(btn);
    });
  }

  function initFilters() {
    document.querySelectorAll("[data-hub-filters]").forEach(function (bar) {
      if (bar.dataset.bound) return;
      bar.dataset.bound = "1";
      var section = bar.closest(".deck-index");
      if (!section) return;
      var items = section.querySelectorAll("ul.list > li");
      var countEl = section.querySelector(".section-title .muted");
      var total = items.length;
      function apply() {
        var q = ((bar.querySelector("[data-filter=q]") || {}).value || "").toLowerCase();
        var when = (bar.querySelector("[data-filter=when]") || {}).value || "";
        var place = (bar.querySelector("[data-filter=place]") || {}).value || "";
        var shown = 0;
        items.forEach(function (li) {
          var hay = (li.textContent || "").toLowerCase();
          var date = li.getAttribute("data-date") || "";
          var placing = parseInt(li.getAttribute("data-placing") || "9999", 10);
          var ok = true;
          if (q && hay.indexOf(q) < 0) ok = false;
          if (when === "sep" && (date < "2026-09-01" || date > "2026-09-30")) ok = false;
          if (when === "aug" && (date < "2026-08-01" || date > "2026-08-31")) ok = false;
          if (place === "top8" && placing > 8) ok = false;
          if (place === "win" && placing !== 1) ok = false;
          li.hidden = !ok;
          if (ok) shown += 1;
        });
        if (countEl) countEl.textContent = shown === total ? total + " lists" : shown + " of " + total;
      }
      bar.addEventListener("input", apply);
      bar.addEventListener("change", apply);
    });
  }

  function initSiteSearch() {
    var params = new URLSearchParams(window.location.search);
    var q = (params.get("q") || "").trim();
    document.querySelectorAll('form.site-search input[name="q"]').forEach(function (input) {
      if (!input.value) input.value = q;
    });
    if (!document.querySelector("[data-search-group]")) return;
    var needle = q.toLowerCase();
    var status = document.getElementById("search-status");
    var shown = 0;
    document.querySelectorAll("[data-search-group]").forEach(function (group) {
      var any = 0;
      group.querySelectorAll("li[data-q]").forEach(function (li) {
        var hay = ((li.getAttribute("data-q") || "") + " " + (li.textContent || "")).toLowerCase();
        var ok = !needle || hay.indexOf(needle) >= 0;
        li.hidden = !ok;
        if (ok) {
          any += 1;
          shown += 1;
        }
      });
      group.hidden = !any;
    });
    if (status) {
      if (!needle) status.hidden = true;
      else {
        status.hidden = false;
        status.textContent = "Showing " + shown + " matches for “" + q + "”.";
      }
    }
  }

  function ready() {
    var y = document.getElementById("year");
    if (y) y.textContent = new Date().getFullYear();
    ensureCopyButtons();
    initCopy();
    initFilters();
    initSiteSearch();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready);
  else ready();
})();
