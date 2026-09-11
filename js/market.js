(function () {
  var KEY = "pkdl-market-v1";

  function load() {
    try {
      var raw = JSON.parse(localStorage.getItem(KEY) || "{}");
      return {
        watch: Array.isArray(raw.watch) ? raw.watch : [],
        binder: Array.isArray(raw.binder) ? raw.binder : [],
        alerts: Array.isArray(raw.alerts) ? raw.alerts : [],
      };
    } catch (err) {
      return { watch: [], binder: [], alerts: [] };
    }
  }

  function save(state) {
    localStorage.setItem(KEY, JSON.stringify(state));
  }

  function money(n) {
    if (n == null || isNaN(n)) return "—";
    return "$" + Number(n).toFixed(2);
  }

  function catalog() {
    var blob = document.getElementById("market-data");
    if (!blob) return [];
    try {
      return JSON.parse(blob.textContent || "[]");
    } catch (err) {
      return [];
    }
  }

  function byHref(href) {
    href = href || "";
    return catalog().find(function (row) {
      return row.href === href || row.key === href;
    });
  }

  function payloadFromEl(el) {
    var root = el.closest("[data-href]") || el;
    return {
      href: root.getAttribute("data-href") || "",
      name: root.getAttribute("data-name") || "",
      image: root.getAttribute("data-image") || "",
      set: root.getAttribute("data-set") || "",
      number: root.getAttribute("data-number") || "",
      spot: Number(root.getAttribute("data-spot") || 0),
      buy: root.getAttribute("data-buy") || "",
    };
  }

  function upsert(list, item, key) {
    key = key || "href";
    var next = list.filter(function (row) {
      return row[key] !== item[key];
    });
    next.unshift(item);
    return next;
  }

  function remove(list, href) {
    return list.filter(function (row) {
      return row.href !== href;
    });
  }

  function watched(state, href) {
    return state.watch.some(function (row) {
      return row.href === href;
    });
  }

  function labelWatch(btn, on) {
    btn.textContent = on ? "Watching" : "Watch";
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  }

  function renderWatch() {
    var root = document.getElementById("watch-list");
    if (!root) return;
    var state = load();
    if (!state.watch.length) {
      root.innerHTML = '<p class="muted">Nothing watched yet. Open a collectible card and tap Watch — it stays in this browser.</p>';
      return;
    }
    root.innerHTML = state.watch
      .map(function (row) {
        var live = byHref(row.href) || row;
        var spot = live.spot != null ? live.spot : row.spot;
        var ch = live.change7;
        var cls = ch == null ? "" : ch >= 0 ? "up" : "down";
        var chs = ch == null ? "" : (ch >= 0 ? "+" : "") + Number(ch).toFixed(1) + "% 7d";
        return (
          '<article class="collect-card market-tile">' +
          '<a href="' +
          row.href +
          '"><img src="' +
          (row.image || "") +
          '" alt="' +
          row.name +
          '" width="245" height="342"></a>' +
          '<div class="collect-card-copy"><strong>' +
          row.name +
          "</strong>" +
          '<div class="muted">' +
          (row.set || "") +
          " · " +
          (row.number || "") +
          "</div>" +
          '<div class="collect-price">' +
          money(spot) +
          "</div>" +
          (chs ? '<div class="' + cls + '">' + chs + "</div>" : "") +
          '<div class="market-row-actions">' +
          '<a class="buy-tcg" href="' +
          (live.buy || row.buy || "#") +
          '" target="_blank" rel="noopener nofollow sponsored">Buy</a>' +
          '<button type="button" class="home-ghost" data-unwatch="' +
          row.href +
          '">Remove</button></div></div></article>'
        );
      })
      .join("");
  }

  function renderBinder() {
    var root = document.getElementById("binder-list");
    var sum = document.getElementById("binder-sum");
    if (!root) return;
    var state = load();
    if (!state.binder.length) {
      root.innerHTML = '<p class="muted">Your binder is empty. Add a print from a card page. Qty and paid price stay on this device.</p>';
      if (sum) sum.hidden = true;
      return;
    }
    var market = 0;
    var cost = 0;
    root.innerHTML = state.binder
      .map(function (row, i) {
        var live = byHref(row.href) || row;
        var qty = Number(row.qty || 1);
        var paid = Number(row.paid || 0);
        var spot = Number(live.spot || row.spot || 0);
        market += spot * qty;
        cost += paid * qty;
        var pnl = (spot - paid) * qty;
        var cls = pnl >= 0 ? "up" : "down";
        return (
          '<article class="binder-row">' +
          '<img src="' +
          (row.image || "") +
          '" alt="' +
          row.name +
          '" width="54" height="76">' +
          "<div><a href=\"" +
          row.href +
          '"><strong>' +
          row.name +
          "</strong></a>" +
          '<div class="muted">' +
          (row.set || "") +
          " " +
          (row.number || "") +
          " · now " +
          money(spot) +
          '</div></div>' +
          '<label class="binder-qty">Qty <input type="number" min="1" data-binder-qty="' +
          i +
          '" value="' +
          qty +
          '"></label>' +
          '<label class="binder-qty">Paid <input type="number" min="0" step="0.01" data-binder-paid="' +
          i +
          '" value="' +
          paid +
          '"></label>' +
          '<div class="' +
          cls +
          '">' +
          (pnl >= 0 ? "+" : "") +
          money(Math.abs(pnl)).replace("$", (pnl < 0 ? "−$" : "$")) +
          "</div>" +
          '<button type="button" class="home-ghost" data-binder-del="' +
          i +
          '">Remove</button></article>'
        );
      })
      .join("");
    if (sum) {
      sum.hidden = false;
      var diff = market - cost;
      sum.innerHTML =
        "<strong>" +
        money(market) +
        "</strong> market · " +
        money(cost) +
        " paid · <span class=\"" +
        (diff >= 0 ? "up" : "down") +
        '">' +
        (diff >= 0 ? "+" : "−") +
        money(Math.abs(diff)) +
        "</span>";
    }
  }

  function renderAlerts() {
    var root = document.getElementById("alert-list");
    var hits = document.getElementById("alert-hits");
    if (!root) return;
    var state = load();
    var fired = [];
    root.innerHTML = (state.watch.length
      ? state.watch
          .map(function (row) {
            var live = byHref(row.href) || row;
            var alert = state.alerts.find(function (a) {
              return a.href === row.href;
            }) || { href: row.href, below: "", above: "" };
            var spot = Number(live.spot || 0);
            if (alert.below && spot && spot <= Number(alert.below)) {
              fired.push(row.name + " is at " + money(spot) + " (below " + money(alert.below) + ")");
            }
            if (alert.above && spot && spot >= Number(alert.above)) {
              fired.push(row.name + " is at " + money(spot) + " (above " + money(alert.above) + ")");
            }
            return (
              '<article class="alert-row"><img src="' +
              (row.image || "") +
              '" alt="">' +
              "<div><a href=\"" +
              row.href +
              '"><strong>' +
              row.name +
              "</strong></a><div class=\"muted\">Now " +
              money(spot) +
              "</div></div>" +
              '<label>Alert below <input type="number" min="0" step="0.01" data-alert-below="' +
              row.href +
              '" value="' +
              (alert.below || "") +
              '"></label>' +
              '<label>Alert above <input type="number" min="0" step="0.01" data-alert-above="' +
              row.href +
              '" value="' +
              (alert.above || "") +
              '"></label></article>'
            );
          })
          .join("")
      : '<p class="muted">Watch cards first, then set a below / above price. Checks run when you open this page.</p>');
    if (hits) {
      if (!fired.length) {
        hits.hidden = true;
      } else {
        hits.hidden = false;
        hits.innerHTML = "<strong>Triggered now</strong><ul>" + fired.map(function (t) {
          return "<li>" + t + "</li>";
        }).join("") + "</ul>";
      }
    }
  }

  function fillCompare() {
    var a = document.getElementById("compare-a");
    var b = document.getElementById("compare-b");
    if (!a || !b) return;
    var rows = catalog();
    var opts = rows
      .map(function (row) {
        return '<option value="' + row.href + '">' + row.name + " (" + row.set + " " + row.number + ")</option>";
      })
      .join("");
    a.innerHTML = '<option value="">Pick a card</option>' + opts;
    b.innerHTML = a.innerHTML;
    var params = new URLSearchParams(window.location.search);
    if (params.get("a")) a.value = params.get("a");
    if (params.get("b")) b.value = params.get("b");
    function paint() {
      var left = byHref(a.value);
      var right = byHref(b.value);
      var out = document.getElementById("compare-out");
      if (!out) return;
      function col(row) {
        if (!row) return "<div class=\"muted\">Choose a print.</div>";
        var ch = row.change7;
        return (
          '<div class="compare-pane"><a class="compare-col" href="' +
          row.href +
          '"><img src="' +
          (row.image || "") +
          '" alt="' +
          row.name +
          '"><strong>' +
          row.name +
          "</strong><div class=\"muted\">" +
          row.set +
          " · " +
          row.number +
          '</div><div class="big-price">' +
          money(row.spot) +
          "</div><div class=\"" +
          (ch == null ? "" : ch >= 0 ? "up" : "down") +
          '">' +
          (ch == null ? "—" : (ch >= 0 ? "+" : "") + Number(ch).toFixed(1) + "% 7d") +
          "</div></a>" +
          '<a class="shop-buy" href="' +
          row.buy +
          '" target="_blank" rel="noopener nofollow sponsored">Buy on TCGplayer</a></div>'
        );
      }
      out.innerHTML = '<div class="compare-grid">' + col(left) + col(right) + "</div>";
      if (a.value && b.value) {
        history.replaceState(null, "", "?a=" + encodeURIComponent(a.value) + "&b=" + encodeURIComponent(b.value));
      }
    }
    a.addEventListener("change", paint);
    b.addEventListener("change", paint);
    paint();
  }

  function initButtons() {
    document.querySelectorAll("[data-watch]").forEach(function (btn) {
      var item = payloadFromEl(btn);
      if (!item.href) return;
      var state = load();
      labelWatch(btn, watched(state, item.href));
      btn.addEventListener("click", function () {
        var next = load();
        if (watched(next, item.href)) next.watch = remove(next.watch, item.href);
        else next.watch = upsert(next.watch, item).slice(0, 80);
        save(next);
        labelWatch(btn, watched(next, item.href));
      });
    });
    document.querySelectorAll("[data-binder-add]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var item = payloadFromEl(btn);
        var next = load();
        var existing = next.binder.find(function (row) {
          return row.href === item.href;
        });
        if (existing) existing.qty = Number(existing.qty || 1) + 1;
        else next.binder.push({ href: item.href, name: item.name, image: item.image, set: item.set, number: item.number, spot: item.spot, qty: 1, paid: item.spot || 0 });
        save(next);
        btn.textContent = "Added to binder";
        setTimeout(function () {
          btn.textContent = "Add to binder";
        }, 1400);
      });
    });
  }

  function initLists() {
    document.addEventListener("click", function (ev) {
      var un = ev.target.closest("[data-unwatch]");
      if (un) {
        var next = load();
        next.watch = remove(next.watch, un.getAttribute("data-unwatch"));
        next.alerts = next.alerts.filter(function (a) {
          return a.href !== un.getAttribute("data-unwatch");
        });
        save(next);
        renderWatch();
        renderAlerts();
      }
      var del = ev.target.closest("[data-binder-del]");
      if (del) {
        var nextb = load();
        nextb.binder.splice(Number(del.getAttribute("data-binder-del")), 1);
        save(nextb);
        renderBinder();
      }
    });
    document.addEventListener("change", function (ev) {
      var qty = ev.target.getAttribute("data-binder-qty");
      var paid = ev.target.getAttribute("data-binder-paid");
      if (qty != null) {
        var s = load();
        if (s.binder[qty]) s.binder[qty].qty = Math.max(1, Number(ev.target.value || 1));
        save(s);
        renderBinder();
      }
      if (paid != null) {
        var s2 = load();
        if (s2.binder[paid]) s2.binder[paid].paid = Math.max(0, Number(ev.target.value || 0));
        save(s2);
        renderBinder();
      }
      var below = ev.target.getAttribute("data-alert-below");
      var above = ev.target.getAttribute("data-alert-above");
      if (below || above) {
        var href = below || above;
        var st = load();
        var rec = st.alerts.find(function (a) {
          return a.href === href;
        });
        if (!rec) {
          rec = { href: href, below: "", above: "" };
          st.alerts.push(rec);
        }
        if (below) rec.below = ev.target.value;
        if (above) rec.above = ev.target.value;
        save(st);
        renderAlerts();
      }
    });
  }

  function deskNote() {
    var el = document.getElementById("market-desk-note");
    if (!el) return;
    var s = load();
    el.textContent =
      s.watch.length +
      " watched · " +
      s.binder.length +
      " binder prints · " +
      s.alerts.length +
      " alerts. Stored in this browser only.";
  }

  function ready() {
    initButtons();
    initLists();
    renderWatch();
    renderBinder();
    renderAlerts();
    fillCompare();
    deskNote();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready);
  else ready();
})();
