# Theme template

Copy this whole folder, rename it to your theme's slug (lowercase, dashes),
and make it yours. Folders starting with `_` are ignored by CI, so this
template is never validated or listed as a real theme.

## What a finished theme folder looks like

```text
themes/
└── your-theme/
    ├── README.md            # your description — CI adds the metadata header
    ├── LICENSE              # required
    ├── your-theme.peltontheme   # one, or several if you ship variants
    └── preview.png          # recommended, not required
```

## Build your `.peltontheme`

1. Edit the files in [`source/`](source/) — start with `manifest.json` and
   `tokens/colors.json`.
2. Zip the **contents** of `source/` so `manifest.json` sits at the archive
   root:

   ```sh
   cd source
   zip -r ../your-theme.peltontheme manifest.json tokens css assets
   ```

3. Delete this instructional text, write your real README below any `---`,
   drop in the `.peltontheme` and a `LICENSE`, and open a pull request.

> [!TIP]
> The full format spec — every themeable token, CSS and icon rules, size caps —
> is at <https://docs.pelton.app/themes/format/>.

> [!NOTE]
> Do not write the metadata header yourself. CI reads your manifest and
> prepends a generated block (version, compatibility, author, license…) above
> a `---`. Everything you write below the marker is kept as-is.
