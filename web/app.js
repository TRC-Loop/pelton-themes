/* Gallery rendering, search and pagination. All data is baked into the page
   at build time (window.__THEMES__): no network calls, no GitHub API. */
(function () {
  "use strict";

  var THEMES = window.__THEMES__ || [];
  var PER_PAGE = 9;

  // Inline Tabler icons (self-hosted, no external requests).
  var ICONS = {
    download:
      '<path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2"/><path d="M7 11l5 5l5 -5"/><path d="M12 4l0 12"/>',
    folder:
      '<path d="M5 4h4l3 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2H5a2 2 0 0 1 -2 -2V6a2 2 0 0 1 2 -2"/>',
    palette:
      '<path d="M12 21a9 9 0 0 1 0 -18c4.97 0 9 3.582 9 8c0 1.06 -.474 2.078 -1.318 2.828c-.844 .75 -1.989 1.172 -3.182 1.172h-2.5a2 2 0 0 0 -1 3.75a1.3 1.3 0 0 1 -1 2.25"/><path d="M7.5 10.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"/><path d="M11.5 7.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"/><path d="M15.5 10.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"/>',
    typography:
      '<path d="M4 20h3m7 0h7M6.9 15h6.9m-3.6 -8.7L16 20M5 20l6 -16h2l7 16"/>',
    icons:
      '<path d="M3 6.5a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0 -7 0M2.5 21h8l-4 -7zM14 3l7 7m-7 0l7 -7m-7 11h7v7h-7z"/>',
    code:
      '<path d="M7 8l-4 4l4 4"/><path d="M17 8l4 4l-4 4"/><path d="M14 4l-4 16"/>',
    alert:
      '<path d="M12 9v4"/><path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0"/><path d="M12 16h.01"/>',
  };

  function icon(name) {
    return (
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' +
      'aria-hidden="true">' +
      (ICONS[name] || "") +
      "</svg>"
    );
  }

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

  // Deterministic avatar colour from the author name.
  function avatarColor(name) {
    var h = 0;
    for (var i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
    return "hsl(" + h + ", 52%, 52%)";
  }

  function avatar(name) {
    var a = el("span", "avatar");
    var letter = (name.replace(/[^a-z0-9]/gi, "")[0] || "?").toUpperCase();
    a.textContent = letter;
    a.style.background = avatarColor(name || "?");
    return a;
  }

  function cap(iconName, tip, warn) {
    var s = el("span", "cap" + (warn ? " cap-warn" : ""));
    s.setAttribute("data-tip", tip);
    s.setAttribute("tabindex", "0");
    s.innerHTML = icon(iconName);
    return s;
  }

  function capabilities(caps) {
    var row = el("div", "caps");
    caps = caps || {};
    if (caps.colours) row.appendChild(cap("palette", "Alters colours"));
    if (caps.fonts) row.appendChild(cap("typography", "Changes fonts and typography"));
    if (caps.icons) row.appendChild(cap("icons", "Replaces interface icons"));
    if (caps.css) row.appendChild(cap("code", "Ships custom CSS"));
    if (caps.external)
      row.appendChild(
        cap(
          "alert",
          "Makes external requests. Not necessarily unsafe, but not ideal when privacy matters.",
          true
        )
      );
    return row;
  }

  function card(t) {
    var c = el("article", "card");

    // Preview with a version tag overlaid bottom-right.
    var preview = el("div", "preview");
    if (t.preview) {
      var img = el("img");
      img.src = t.preview;
      img.alt = t.name + " preview";
      img.loading = "lazy";
      preview.appendChild(img);
    } else {
      var ph = el("div", "placeholder");
      ph.innerHTML = icon("palette");
      preview.appendChild(ph);
    }
    if (t.version) {
      var vtag = el("span", "version-tag", "v" + t.version);
      preview.appendChild(vtag);
    }
    var baseTag = el("span", "base-tag base-" + (t.base || "dark"), t.base || "dark");
    preview.appendChild(baseTag);
    c.appendChild(preview);

    var body = el("div", "body");

    var head = el("div", "card-head");
    head.appendChild(el("h3", null, t.name));
    if (t.peltonMin) head.appendChild(el("span", "made-for", "Pelton " + t.peltonMin + "+"));
    body.appendChild(head);

    if (t.description) body.appendChild(el("p", "desc", t.description));

    // by <pfp> Username
    if (t.author) {
      var by = el("div", "author");
      by.appendChild(el("span", "by", "by"));
      by.appendChild(avatar(t.author));
      by.appendChild(el("span", "username", t.author));
      body.appendChild(by);
    }

    body.appendChild(capabilities(t.caps));

    var actions = el("div", "actions");
    var dl = el("button", "btn btn-primary btn-download", null);
    dl.type = "button";
    dl.innerHTML = icon("download") + "<span>Download</span>";
    dl.addEventListener("click", function () {
      openModal(t);
    });
    actions.appendChild(dl);

    var src = el("a", "btn btn-ghost btn-source", null);
    src.href = t.folder;
    src.target = "_blank";
    src.rel = "noreferrer noopener";
    src.title = "View source folder";
    src.innerHTML = icon("folder") + "<span>Source</span>";
    actions.appendChild(src);

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

    countEl.textContent = items.length + (items.length === 1 ? " theme" : " themes");

    grid.innerHTML = "";
    if (items.length === 0) {
      grid.appendChild(el("p", "empty", "No themes match your search."));
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
