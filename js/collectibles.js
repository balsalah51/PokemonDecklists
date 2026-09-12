(function () {
  function money(n) {
    if (n == null || isNaN(n)) return "-";
    return "$" + Number(n).toFixed(2);
  }

  function initCatalog() {
    var blob = document.getElementById("collect-data");
    var q = document.getElementById("collect-q");
    var setf = document.getElementById("collect-set");
    var grid = document.getElementById("collect-grid");
    var status = document.getElementById("collect-status");
    if (!blob || !grid) return;
    var rows = [];
    try { rows = JSON.parse(blob.textContent || "[]"); } catch (e) { rows = []; }

    function render() {
      var needle = ((q && q.value) || "").toLowerCase();
      var setv = (setf && setf.value) || "";
      grid.innerHTML = "";
      var n = 0;
      rows.forEach(function (row) {
        var hay = (row.name + " " + row.set + " " + row.number + " " + (row.artist || "") + " " + (row.kind || "")).toLowerCase();
        if (needle && hay.indexOf(needle) < 0) return;
        if (setv && row.set !== setv) return;
        n += 1;
        var a = document.createElement("a");
        a.className = "collect-card";
        a.href = row.href;
        a.innerHTML =
          "<img src=\"" + (row.image || "") + "\" alt=\"" + String(row.name || "").replace(/"/g, "&quot;") + "\" width=\"245\" height=\"342\" loading=\"lazy\">" +
          "<div class=\"collect-card-copy\">" +
          "<strong>" + row.name + "</strong>" +
          "<div class=\"muted\">" + row.set + " · " + row.number + (row.artist ? " · " + row.artist : "") + "</div>" +
          "<div class=\"collect-price\">" + money(row.spot) + "</div>" +
          (row.change7 == null ? "" : "<div class=\"" + (row.change7 >= 0 ? "up" : "down") + "\">" + (row.change7 >= 0 ? "+" : "") + row.change7.toFixed(1) + "% 7d</div>") +
          "</div>";
        grid.appendChild(a);
      });
      if (status) status.textContent = n + " cards";
    }

    if (q) q.addEventListener("input", render);
    if (setf) setf.addEventListener("change", render);
    render();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCatalog);
  else initCatalog();
})();
