(function () {
  function spark(values, w, h) {
    if (!values || values.length < 2) return "";
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    if (max === min) max = min + 1;
    var pts = values.map(function (v, i) {
      var x = (i / (values.length - 1)) * (w - 4) + 2;
      var y = h - 3 - ((v - min) / (max - min)) * (h - 8);
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
    var last = values[values.length - 1];
    var first = values[0];
    var color = last >= first ? "#2e7d32" : "#c62828";
    return '<svg class="spark" viewBox="0 0 ' + w + " " + h + '" width="' + w + '" height="' + h + '" aria-hidden="true"><polyline fill="none" stroke="' + color + '" stroke-width="2" points="' + pts + '"/></svg>';
  }

  function money(n) {
    if (n == null || isNaN(n)) return "-";
    return "$" + Number(n).toFixed(2);
  }

  function init() {
    var blob = document.getElementById("price-data");
    if (!blob) return;
    var rows = [];
    try { rows = JSON.parse(blob.textContent || "[]"); } catch (e) { rows = []; }
    var q = document.getElementById("price-q");
    var body = document.getElementById("price-body");
    var chartWrap = document.getElementById("price-focus");
    if (!body) return;

    function render(filter) {
      var needle = (filter || "").toLowerCase();
      body.innerHTML = "";
      rows.forEach(function (row, idx) {
        var hay = (row.name + " " + row.set + " " + row.number).toLowerCase();
        if (needle && hay.indexOf(needle) < 0) return;
        var tr = document.createElement("tr");
        tr.innerHTML =
          "<td><img src=\"" + (row.image || "") + "\" alt=\"\"></td>" +
        "<td><a href=\"" + (row.href || "#") + "\"><strong>" + row.name + "</strong></a><div class=\"muted\">" + row.set + " " + row.number + "</div></td>" +
          "<td>" + money(row.spot) + "</td>" +
          "<td class=\"" + (row.change7 >= 0 ? "up" : "down") + "\">" + (row.change7 == null ? "-" : ((row.change7 >= 0 ? "+" : "") + row.change7.toFixed(1) + "%")) + "</td>" +
          "<td class=\"" + (row.change30 >= 0 ? "up" : "down") + "\">" + (row.change30 == null ? "-" : ((row.change30 >= 0 ? "+" : "") + row.change30.toFixed(1) + "%")) + "</td>" +
          "<td>" + spark(row.series, 120, 36) + "</td>" +
          "<td><a class=\"buy-tcg\" href=\"" + row.buy + "\" target=\"_blank\" rel=\"noopener nofollow sponsored\">Buy</a></td>";
        tr.addEventListener("click", function () { show(row); });
        body.appendChild(tr);
        if (idx === 0 && !needle) show(row);
      });
    }

    function show(row) {
      if (!chartWrap) return;
      var w = 640, h = 180;
      chartWrap.innerHTML =
        "<div class=\"price-hero\">" +
        "<img src=\"" + (row.image || "") + "\" alt=\"" + row.name + "\">" +
        "<div><div class=\"muted\">" + row.set + " · " + row.number + "</div>" +
        "<h3 style=\"margin:4px 0 8px\"><a href=\"" + (row.href || "#") + "\">" + row.name + "</a></h3>" +
        "<div class=\"big-price\">" + money(row.spot) + "</div>" +
        "<p class=\"muted\">7-day " + (row.change7 == null ? "-" : row.change7.toFixed(1) + "%") +
        " · 30-day " + (row.change30 == null ? "-" : row.change30.toFixed(1) + "%") +
        ". Public TCGPlayer market snapshots via Limitless.</p>" +
        spark(row.series, w, h) +
        "<p style=\"margin-top:10px\"><a class=\"shop-buy\" href=\"" + row.buy + "\" target=\"_blank\" rel=\"noopener nofollow sponsored\">Buy on TCGplayer</a></p></div></div>";
    }

    if (q) q.addEventListener("input", function () { render(q.value); });
    render("");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
