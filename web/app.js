(function () {
  "use strict";

  var PER_PAGE = 9;
  var CAROUSEL_MS = 5000;
  var timers = [];

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
    left: '<path d="M15 6l-6 6l6 6"/>',
    right: '<path d="M9 6l6 6l-6 6"/>',
    back: '<path d="M5 12l14 0"/><path d="M5 12l6 6"/><path d="M5 12l6 -6"/>',
    external:
      '<path d="M12 6h-6a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-6"/><path d="M11 13l9 -9"/><path d="M15 4h5v5"/>',
  };

  function icon(name) {
    return (
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' +
      'aria-hidden="true">' + (ICONS[name] || "") + "</svg>"
    );
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function avatarColor(name) {
    var h = 0;
    for (var i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
    return "hsl(" + h + ", 52%, 52%)";
  }

  function avatar(name) {
    var a = el("span", "avatar");
    a.textContent = (name.replace(/[^a-z0-9]/gi, "")[0] || "?").toUpperCase();
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
      row.appendChild(cap("alert", "Makes external requests. Not necessarily unsafe, but not ideal when privacy matters.", true));
    return row;
  }

  function preview(t, opts) {
    opts = opts || {};
    var wrap = el("div", "preview" + (opts.large ? " preview-large" : ""));
    var imgs = t.previews || [];

    if (imgs.length === 0) {
      var ph = el("div", "placeholder");
      ph.innerHTML = icon("palette");
      wrap.appendChild(ph);
    } else {
      var track = el("div", "carousel-track");
      imgs.forEach(function (src, i) {
        var img = el("img");
        img.src = src;
        img.alt = t.name + " preview " + (i + 1);
        img.loading = "lazy";
        if (i !== 0) img.style.display = "none";
        track.appendChild(img);
      });
      wrap.appendChild(track);

      if (imgs.length > 1) {
        var dots = el("div", "carousel-dots");
        var idx = 0;
        function show(n) {
          idx = (n + track.children.length) % track.children.length;
          for (var k = 0; k < track.children.length; k++)
            track.children[k].style.display = k === idx ? "" : "none";
          for (var d = 0; d < dots.children.length; d++)
            dots.children[d].setAttribute("aria-current", d === idx ? "true" : "false");
        }
        var timer = setInterval(function () { show(idx + 1); }, CAROUSEL_MS);
        timers.push(timer);
        function reset() { clearInterval(timer); timer = setInterval(function () { show(idx + 1); }, CAROUSEL_MS); timers.push(timer); }

        imgs.forEach(function (_, i) {
          var dot = el("button", "carousel-dot");
          dot.type = "button";
          dot.setAttribute("aria-label", "Preview " + (i + 1));
          if (i === 0) dot.setAttribute("aria-current", "true");
          if (opts.interactive)
            dot.addEventListener("click", function (e) { e.stopPropagation(); e.preventDefault(); show(i); reset(); });
          else dot.style.pointerEvents = "none";
          dots.appendChild(dot);
        });

        if (opts.interactive) {
          var prev = el("button", "carousel-arrow prev");
          prev.type = "button";
          prev.setAttribute("aria-label", "Previous preview");
          prev.innerHTML = icon("left");
          prev.addEventListener("click", function (e) { e.stopPropagation(); e.preventDefault(); show(idx - 1); reset(); });
          var next = el("button", "carousel-arrow next");
          next.type = "button";
          next.setAttribute("aria-label", "Next preview");
          next.innerHTML = icon("right");
          next.addEventListener("click", function (e) { e.stopPropagation(); e.preventDefault(); show(idx + 1); reset(); });
          wrap.appendChild(prev);
          wrap.appendChild(next);
        }
        wrap.appendChild(dots);
      }
    }

    if (t.version) wrap.appendChild(el("span", "version-tag", "v" + t.version));
    if (t.multi) wrap.appendChild(el("span", "base-tag base-multi", t.flavors.length + " flavors"));
    else if (t.bases && t.bases[0]) wrap.appendChild(el("span", "base-tag base-" + t.bases[0], t.bases[0]));
    return wrap;
  }

  function card(t) {
    var c = el("article", "card");
    c.tabIndex = 0;
    c.setAttribute("role", "link");
    function go() { window.location.href = t.url; }
    c.addEventListener("click", go);
    c.addEventListener("keydown", function (e) { if (e.key === "Enter") go(); });

    c.appendChild(preview(t, { interactive: false }));

    var body = el("div", "body");
    var head = el("div", "card-head");
    head.appendChild(el("h3", null, t.name));
    if (t.peltonMin) head.appendChild(el("span", "made-for", "Pelton " + t.peltonMin + "+"));
    body.appendChild(head);
    if (t.description) body.appendChild(el("p", "desc", t.description));

    if (t.author) {
      var by = el("div", "author");
      by.appendChild(el("span", "by", "by"));
      by.appendChild(avatar(t.author));
      by.appendChild(el("span", "username", t.author + (t.authors && t.authors.length > 1 ? " +" + (t.authors.length - 1) : "")));
      body.appendChild(by);
    }
    body.appendChild(capabilities(t.caps));

    var footer = el("div", "card-foot");
    footer.appendChild(el("span", "view-link", "View theme"));
    footer.innerHTML += icon("right");
    body.appendChild(footer);

    c.appendChild(body);
    return c;
  }

  function runGallery(themes) {
    var grid = document.getElementById("grid");
    var pager = document.getElementById("pagination");
    var search = document.getElementById("search");
    var countEl = document.getElementById("count");
    var state = { page: 1, query: "" };

    function filtered() {
      var q = state.query.trim().toLowerCase();
      if (!q) return themes;
      return themes.filter(function (t) {
        return t.name.toLowerCase().indexOf(q) !== -1 ||
          (t.author || "").toLowerCase().indexOf(q) !== -1 ||
          (t.description || "").toLowerCase().indexOf(q) !== -1;
      });
    }

    function pageButton(label, page, opts) {
      opts = opts || {};
      var b = el("button", null, label);
      b.type = "button";
      if (opts.current) b.setAttribute("aria-current", "true");
      if (opts.disabled) b.disabled = true;
      else b.addEventListener("click", function () {
        state.page = page; render();
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
      for (var i = 1; i <= pages; i++)
        if (i === 1 || i === pages || Math.abs(i - state.page) <= 1) shown.push(i);
      var last = 0;
      shown.forEach(function (p) {
        if (last && p - last > 1) pager.appendChild(el("span", "ellipsis", "…"));
        pager.appendChild(pageButton(String(p), p, { current: p === state.page }));
        last = p;
      });
      pager.appendChild(pageButton("›", state.page + 1, { disabled: state.page === pages }));
    }

    function render() {
      timers.forEach(clearInterval); timers = [];
      var items = filtered();
      var pages = Math.max(1, Math.ceil(items.length / PER_PAGE));
      if (state.page > pages) state.page = pages;
      countEl.textContent = items.length + (items.length === 1 ? " theme" : " themes");
      grid.innerHTML = "";
      if (items.length === 0) { grid.appendChild(el("p", "empty", "No themes match your search.")); pager.innerHTML = ""; return; }
      var start = (state.page - 1) * PER_PAGE;
      items.slice(start, start + PER_PAGE).forEach(function (t) { grid.appendChild(card(t)); });
      renderPagination(items.length);
    }

    if (search) search.addEventListener("input", function () { state.query = search.value; state.page = 1; render(); });
    render();
  }

  function sideBlock(label, valueNode) {
    var b = el("div", "side-block");
    b.appendChild(el("span", "side-label", label));
    if (typeof valueNode === "string") b.appendChild(el("span", "side-value", valueNode));
    else b.appendChild(valueNode);
    return b;
  }

  function runDetail(t) {
    var page = document.getElementById("theme-page");
    document.title = t.name + " · Pelton Themes";

    var back = el("a", "back");
    back.href = "./";
    back.innerHTML = icon("back") + "<span>All themes</span>";
    page.appendChild(back);

    var gridEl = el("div", "detail-grid");

    var main = el("div", "detail-main");
    main.appendChild(preview(t, { interactive: true, large: true }));
    var bodyEl = el("div", "detail-body");
    bodyEl.appendChild(el("h1", null, t.name));
    if (t.description) bodyEl.appendChild(el("p", "detail-desc", t.description));
    main.appendChild(bodyEl);
    gridEl.appendChild(main);

    var side = el("aside", "detail-side");
    var sc = el("div", "side-card");

    var authors = t.authors && t.authors.length ? t.authors : (t.author ? [t.author] : []);
    if (authors.length) {
      var av = el("div", "side-authors");
      authors.forEach(function (a) {
        var one = el("span", "side-author");
        one.appendChild(avatar(a));
        one.appendChild(el("span", null, a));
        av.appendChild(one);
      });
      sc.appendChild(sideBlock(authors.length > 1 ? "Authors" : "Author", av));
    }

    var versions = t.version ? [t.version] : dedupe(t.flavors.map(function (f) { return f.version; }));
    if (versions.filter(Boolean).length) sc.appendChild(sideBlock(versions.length > 1 ? "Versions" : "Version", versions.filter(Boolean).map(function (v) { return "v" + v; }).join(", ")));

    if (t.bases && t.bases.length) sc.appendChild(sideBlock(t.bases.length > 1 ? "Bases" : "Base", t.bases.join(", ")));

    if (t.peltonMin) sc.appendChild(sideBlock("Made for", "Pelton " + t.peltonMin + " or newer"));

    var licenses = t.licenses && t.licenses.length ? t.licenses : (t.license ? [t.license] : []);
    if (licenses.length) sc.appendChild(sideBlock(licenses.length > 1 ? "Licenses" : "License", licenses.join(", ")));

    var capsRow = capabilities(t.caps);
    if (capsRow.children.length) sc.appendChild(sideBlock("Alters", capsRow));

    var dl = el("div", "downloads");
    (t.flavors || []).forEach(function (f) {
      var b = el("button", "btn btn-primary btn-download");
      b.type = "button";
      var label = t.multi ? f.name + " (" + f.base + ")" : "Download";
      b.innerHTML = icon("download") + "<span>" + label + "</span>";
      b.addEventListener("click", function () { openDownload(t.name, f); });
      dl.appendChild(b);
    });
    sc.appendChild(dl);

    var src = el("a", "btn btn-ghost btn-source");
    src.href = t.folder; src.target = "_blank"; src.rel = "noreferrer noopener";
    src.innerHTML = icon("external") + "<span>Source on GitHub</span>";
    sc.appendChild(src);

    side.appendChild(sc);
    gridEl.appendChild(side);
    page.appendChild(gridEl);
  }

  function dedupe(arr) {
    var out = [];
    arr.forEach(function (v) { if (out.indexOf(v) === -1) out.push(v); });
    return out;
  }

  var backdrop = document.getElementById("modal-backdrop");
  var modalTheme = document.getElementById("modal-theme");
  var modalConfirm = document.getElementById("modal-confirm");
  var modalCancel = document.getElementById("modal-cancel");
  var pending = null;

  function openDownload(themeName, flavor) {
    pending = flavor;
    modalTheme.textContent = themeName + " · " + flavor.file;
    backdrop.classList.add("open");
    modalConfirm.focus();
  }
  function closeModal() { backdrop.classList.remove("open"); pending = null; }
  if (modalCancel) modalCancel.addEventListener("click", closeModal);
  if (backdrop) backdrop.addEventListener("click", function (e) { if (e.target === backdrop) closeModal(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeModal(); });
  if (modalConfirm) modalConfirm.addEventListener("click", function () {
    if (!pending) return;
    var a = document.createElement("a");
    a.href = pending.download; a.download = pending.file;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    closeModal();
  });

  if (document.getElementById("grid") && window.__THEMES__) runGallery(window.__THEMES__);
  if (document.getElementById("theme-page") && window.__THEME__) runDetail(window.__THEME__);
})();
