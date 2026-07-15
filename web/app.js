/* Gallery rendering, search and pagination. All data is baked into the page
   at build time (window.__THEMES__) — no network calls, no GitHub API. */
(function () {
  "use strict";

  var THEMES = window.__THEMES__ || [];
  var PER_PAGE = 9;

  var grid = document.getElementById("grid");
  var pager = document.getElementById("pagination");
  var search = document.getElementById("search");
  var countEl = document.getElementById("count");

  var state = { page: 1, query: "" };

  function filtered() {
    var q = state.query.trim().toLowerCase();
    if (!q) return THEMES;
    return THEMES.filter(function (t) {
      return (
        t.name.toLowerCase().indexOf(q) !== -1 ||
        (t.author || "").toLowerCase().indexOf(q) !== -1 ||
        (t.description || "").toLowerCase().indexOf(q) !== -1
      );
    });
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function card(t) {
    var c = el("article", "card");

    var preview = el("div", "preview");
    if (t.preview) {
      var img = el("img");
      img.src = t.preview;
      img.alt = t.name + " preview";
      img.loading = "lazy";
      preview.appendChild(img);
    } else {
      var ph = el("div", "placeholder");
      ph.appendChild(el("span", null, "No preview"));
      preview.appendChild(ph);
    }
    c.appendChild(preview);

    var body = el("div", "body");
    body.appendChild(el("h3", null, t.name));
    if (t.description) body.appendChild(el("p", "desc", t.description));

    var meta = el("div", "meta");
    meta.appendChild(el("span", "badge base-" + (t.base || "dark"), t.base || "dark"));
    if (t.author) meta.appendChild(el("span", "badge", "by " + t.author));
    if (t.version) meta.appendChild(el("span", "badge", "v" + t.version));
    if (t.peltonMin) meta.appendChild(el("span", "badge", "Pelton " + t.peltonMin + "+"));
    body.appendChild(meta);

    var actions = el("div", "actions");
    var folder = el("a", "btn btn-ghost", "View folder");
    folder.href = t.folder;
    folder.target = "_blank";
    folder.rel = "noreferrer noopener";
    actions.appendChild(folder);

    var dl = el("button", "btn btn-primary", "Download");
    dl.type = "button";
    dl.addEventListener("click", function () {
      openModal(t);
    });
    actions.appendChild(dl);
    body.appendChild(actions);

    c.appendChild(body);
    return c;
  }

  function pageButton(label, page, opts) {
    opts = opts || {};
    var b = el("button", null, label);
    b.type = "button";
    if (opts.current) b.setAttribute("aria-current", "true");
    if (opts.disabled) b.disabled = true;
    else
      b.addEventListener("click", function () {
        state.page = page;
        render();
        window.scrollTo({ top: grid.offsetTop - 90, behavior: "smooth" });
      });
    return b;
  }

  function renderPagination(total) {
    pager.innerHTML = "";
    var pages = Math.ceil(total / PER_PAGE);
    if (pages <= 1) return;

    pager.appendChild(pageButton("‹", state.page - 1, { disabled: state.page === 1 }));

    var shown = [];
    for (var i = 1; i <= pages; i++) {
      if (i === 1 || i === pages || Math.abs(i - state.page) <= 1) shown.push(i);
    }
    var last = 0;
    shown.forEach(function (p) {
      if (last && p - last > 1) pager.appendChild(el("span", "ellipsis", "…"));
      pager.appendChild(pageButton(String(p), p, { current: p === state.page }));
      last = p;
    });

    pager.appendChild(pageButton("›", state.page + 1, { disabled: state.page === pages }));
  }

  function render() {
    var items = filtered();
    var pages = Math.max(1, Math.ceil(items.length / PER_PAGE));
    if (state.page > pages) state.page = pages;

    countEl.textContent =
      items.length + (items.length === 1 ? " theme" : " themes");

    grid.innerHTML = "";
    if (items.length === 0) {
      var empty = el("p", "empty", "No themes match your search.");
      grid.appendChild(empty);
      pager.innerHTML = "";
      return;
    }

    var start = (state.page - 1) * PER_PAGE;
    items.slice(start, start + PER_PAGE).forEach(function (t) {
      grid.appendChild(card(t));
    });
    renderPagination(items.length);
  }

  /* --- Trust modal ------------------------------------------------------ */
  var backdrop = document.getElementById("modal-backdrop");
  var modalTheme = document.getElementById("modal-theme");
  var modalConfirm = document.getElementById("modal-confirm");
  var modalCancel = document.getElementById("modal-cancel");
  var pending = null;

  function openModal(t) {
    pending = t;
    modalTheme.textContent = t.name + " · " + t.file;
    backdrop.classList.add("open");
    modalConfirm.focus();
  }
  function closeModal() {
    backdrop.classList.remove("open");
    pending = null;
  }
  modalCancel.addEventListener("click", closeModal);
  backdrop.addEventListener("click", function (e) {
    if (e.target === backdrop) closeModal();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });
  modalConfirm.addEventListener("click", function () {
    if (!pending) return;
    var a = document.createElement("a");
    a.href = pending.download;
    a.download = pending.file;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    closeModal();
  });

  if (search) {
    search.addEventListener("input", function () {
      state.query = search.value;
      state.page = 1;
      render();
    });
  }

  render();
})();
