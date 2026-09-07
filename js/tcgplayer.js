(function () {
  var PARTNER = (window.PKDL_TCGPLAYER && window.PKDL_TCGPLAYER.partnerLink) ||
    "https://partner.tcgplayer.com/c/7670706/1780961/21018";
  var REL = "noopener nofollow sponsored";

  function affiliate(dest) {
    if (!dest) return dest;
    if (dest.indexOf("partner.tcgplayer.com") >= 0) return dest;
    return PARTNER + (PARTNER.indexOf("?") >= 0 ? "&" : "?") + "u=" + encodeURIComponent(dest);
  }

  function searchUrl(name, setCode, number) {
    var q = [name, setCode, number].filter(Boolean).join(" ");
    return "https://www.tcgplayer.com/search/pokemon/product?q=" + encodeURIComponent(q) +
      "&productLineName=pokemon";
  }

  function productUrl(pid, name, setCode, number) {
    if (pid) return "https://www.tcgplayer.com/product/" + pid;
    return searchUrl(name, setCode, number);
  }

  function addBuy(el, href, label) {
    if (el.querySelector(".buy-tcg-inline")) return;
    var a = document.createElement("a");
    a.className = "buy-tcg-inline";
    a.href = affiliate(href);
    a.target = "_blank";
    a.rel = REL;
    a.textContent = label || "Buy";
    el.appendChild(a);
  }

  function init() {
    document.querySelectorAll(".text-line").forEach(function (line) {
      var name = ((line.querySelector(".card-title") || {}).textContent || "").trim();
      var id = ((line.querySelector(".card-id") || {}).textContent || "").trim();
      var parts = id.split("-");
      var setCode = parts.length > 1 ? parts[0] : "";
      var number = parts.length > 1 ? parts.slice(1).join("-") : "";
      var pid = line.getAttribute("data-tcg-id");
      if (!name) return;
      addBuy(line, productUrl(pid, name, setCode, number));
    });
    document.querySelectorAll(".card-entry").forEach(function (entry) {
      var name = ((entry.querySelector("h4") || {}).textContent || "").trim();
      var id = ((entry.querySelector(".id") || {}).textContent || "").replace(/^\d+x\s*/, "").trim();
      var parts = id.split("·")[0].trim().split("-");
      var setCode = parts.length > 1 ? parts[0] : "";
      var number = parts.length > 1 ? parts.slice(1).join("-") : "";
      if (!name) return;
      addBuy(entry, searchUrl(name, setCode, number), "TCGplayer");
    });
    document.querySelectorAll("[data-buy-list]").forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      var dest = btn.getAttribute("data-buy-list") || "https://www.tcgplayer.com/massentry?productLineName=pokemon";
      btn.href = affiliate(dest);
      btn.rel = REL;
      btn.target = "_blank";
    });
    document.querySelectorAll("a[data-aff]").forEach(function (a) {
      var dest = a.getAttribute("data-aff") || a.href;
      a.href = affiliate(dest);
      a.rel = REL;
      a.target = "_blank";
    });
  }

  window.pkdlAffiliate = affiliate;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
