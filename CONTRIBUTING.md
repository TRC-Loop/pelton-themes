# Contributing a theme

Thanks for helping grow the Pelton theme gallery! This guide covers **how to
build a theme**, **how to submit it**, and the **rules** every theme must meet.

> [!TIP]
> Never built one before? The full format spec lives at
> <https://docs.pelton.app/themes/format/>, and there is a complete worked
> example at <https://docs.pelton.app/themes/create/>.

---

## Repository layout

Every theme is one folder under `themes/`:

```text
themes/
└── your-theme/
    ├── README.md            # your description (CI prepends a metadata header)
    ├── LICENSE              # required
    ├── your-theme.peltontheme  # one file, or several if the pack ships variants
    └── preview.png          # recommended, not required
```

- **Folder name** = your theme's slug: lowercase, digits and dashes only
  (`gruvbox-dark`, `catppuccin-mocha`).
- Ship **more than one** `.peltontheme` in the same folder when they belong
  together (for example a matched light and dark pair).
- Folders starting with `_` or `.` are ignored — that is how
  [`themes/_TEMPLATE/`](themes/_TEMPLATE/) stays out of the gallery.

---

## Build a `.peltontheme`

A `.peltontheme` is just a zip with `manifest.json` at its root.

1. **Copy the template.** Duplicate [`themes/_TEMPLATE/`](themes/_TEMPLATE/)
   and rename it.
2. **Edit the source.** Start with `manifest.json` and `tokens/colors.json`.
   Only [allowlisted tokens](https://docs.pelton.app/themes/format/) are
   themeable; an unknown token name fails validation on purpose, so typos
   surface immediately.
3. **Zip it** so the manifest sits at the archive root:

   ```sh
   cd source
   zip -r ../your-theme.peltontheme manifest.json tokens css assets
   ```

4. **Test it.** Open Pelton → **Settings → Themes → Import theme** and pick the
   file. You will see the metadata and raw CSS before anything installs.

> [!TIP]
> Testing a theme against an empty inbox is no fun. Start Pelton with
> `--potatoes-are-nice` to launch it with example mailboxes and placeholder
> content, so you can see your theme against realistic mail. It is temporary:
> nothing is saved and your real accounts are untouched.

> [!NOTE]
> Prefer clicking **Export** in Pelton? That produces a ready `.peltontheme`
> from a theme you built in the app. Either route is fine — the file is the
> same.

---

## The rules

> [!IMPORTANT]
> These are enforced by CI (`scripts/validate_theme.py`) on every pull request.
> Run it locally first: `python3 scripts/validate_theme.py`.

| Rule | Required? | Why |
| --- | --- | --- |
| Folder holds at least one `.peltontheme` | ✅ Yes | It is the theme. |
| Folder holds a `LICENSE` | ✅ Yes | Reuse terms must be clear. |
| `manifest.json` at container root, `manifestVersion: 1` | ✅ Yes | The only fixed file; the engine refuses newer formats. |
| `name` and `base` (`light`/`dark`) set | ✅ Yes | Minimum a theme needs to apply. |
| `id` is a lowercase slug (`a-z`, `0-9`, `-`) | ✅ Yes | Names the install folder and drives update detection. |
| Only allowlisted tokens, with safe values | ✅ Yes | No `;`, `{`, `}`, `@` or `url()` in token values. |
| No remote `url()` or `@import` in CSS | ✅ Yes | Remote references can track users; **bundle** fonts and images instead. |
| Within size caps | ✅ Yes | 20 MB container · 1 MB CSS total · 5 MB per asset. |
| A `preview` screenshot | 🟡 Recommended | Makes your gallery card show the theme, not a plain swatch. |
| A `README.md` describing the theme | 🟡 Recommended | Context, credits, links, socials. |

### State the version and compatibility

Set these in your manifest so users know what your theme was built for:

```json
{
  "version": "1.0.0",
  "pelton": { "min": "1.0.8" }
}
```

- `version` — your theme's own version. Bump it on every release; users get an
  update prompt instead of a duplicate.
- `pelton.min` / `pelton.max` — the Pelton version range you tested against.
  Outside the range shows a warning badge, never a block.

CI reads these straight from your manifest and renders them into the top of
your theme's `README.md`. **Do not write that header yourself** — write your
own content below the `---`, and let CI keep the facts in sync.

---

## Submit it

You can contribute either way. Pull requests are preferred.

### Option A — Pull request _(preferred)_

1. Fork this repository and create a branch.
2. Add your `themes/<your-theme>/` folder.
3. Run `python3 scripts/validate_theme.py` and fix anything it reports.
4. Open a pull request. CI validates your theme; a maintainer reviews and
   merges. The README metadata header is generated automatically after merge.

### Option B — Issue form

Not comfortable with git? Open a
[**Submit a theme**](https://github.com/TRC-Loop/pelton-themes/issues/new/choose)
issue, attach your theme, and a maintainer will turn it into a PR for you.

> [!IMPORTANT]
> GitHub does not allow attaching `.peltontheme` files to issues. Since a
> `.peltontheme` is already a zip, just rename `YourTheme.peltontheme` to
> `YourTheme.zip` (or drop it inside a new `.zip`) before attaching. Once the
> file is in the repo, **CI renames any `.zip` theme container back to
> `.peltontheme` automatically** ([`scripts/normalize_uploads.py`](scripts/normalize_uploads.py)),
> so no one has to rename it by hand. Committing a `.peltontheme` directly in a
> pull request also works fine and skips this entirely.

---

## Quality guidelines

Not enforced, but the difference between a good theme and a great one:

- **Contrast.** Body text must stay readable on every surface. Aim for WCAG AA.
- **Complete accent.** Set both `accent` and `accent-fg` so text on accent
  stays legible.
- **Don't fight density.** Spacing and density are user settings and are not
  themeable — design with that in mind.
- **Bundle everything.** Fonts and images go inside the file, referenced
  relatively (`url("assets/fonts/inter.woff2")`). Bundled references are
  inlined and work offline.
- **Credit your sources.** Porting an existing palette? Name and link the
  original in your README.
- **Add a preview.** One screenshot of an inbox does more than any description.

---

## Code of conduct

Be kind, credit others, and keep it legal — only submit themes you have the
right to share. Themes that impersonate brands you have no rights to, or that
contain anything unlawful, will be removed.
