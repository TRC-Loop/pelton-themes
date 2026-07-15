<p align="center">
  <img src="https://raw.githubusercontent.com/TRC-Loop/Pelton/13f56136136bc00b9c8721dc2042fc9c84e1b3a7/.github/pelton-large-bg.png" alt="Pelton">
</p>

<h1 align="center">Pelton Themes</h1>

<p align="center">
  The community gallery of themes for <a href="https://pelton.app">Pelton</a>, the privacy-first email client.<br>
  Browse, download, and share <code>.peltontheme</code> files — no account, no tracking.
</p>

<p align="center">
  <a href="https://github.com/TRC-Loop/pelton-themes/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge" alt="PRs Welcome">
  </a>
  <a href="https://docs.pelton.app/themes/">
    <img src="https://img.shields.io/badge/Theme_docs-docs.pelton.app-blue?style=for-the-badge" alt="Theme docs">
  </a>
  <a href="https://arne.sh/discord">
    <img src="https://img.shields.io/badge/Discord-Join-7289DA?style=for-the-badge&logo=discord&logoColor=white" alt="Discord">
  </a>
  <a href="https://github.com/TRC-Loop/pelton-themes/issues/new/choose">
    <img src="https://img.shields.io/badge/Submit_a-theme-88c0d0?style=for-the-badge" alt="Submit a theme">
  </a>
</p>

***

## <img src="https://api.iconify.design/tabler/palette.svg?color=888888" width="24" align="center"> What is this?

A **theme** overrides Pelton's design tokens — every colour, font, radius and
shadow — plus optional CSS and interface icons. Anything a theme does not
override falls back to the built-in light or dark look, so a theme is always
complete.[^tokens]

Themes ship as single **`.peltontheme`** files (a zip container). This
repository collects them so you can find one, download it, and share your own.

[^tokens]: Full details, the complete token surface, and the security model are in the [theme documentation](https://docs.pelton.app/themes/).

## <img src="https://api.iconify.design/tabler/link.svg?color=888888" width="24" align="center"> Links

| | |
| --- | --- |
| 🌐 **Website** | <https://pelton.app> |
| 📖 **Documentation** | <https://docs.pelton.app> |
| 🎨 **Theme docs** | <https://docs.pelton.app/themes/> · [format spec](https://docs.pelton.app/themes/format/) · [create a theme](https://docs.pelton.app/themes/create/) |
| 💻 **Main app repo** | <https://github.com/TRC-Loop/Pelton> |
| 🖥️ **Website repo** | <https://github.com/TRC-Loop/pelton.app> |
| 🎭 **This repo** | <https://github.com/TRC-Loop/pelton-themes> |
| 💬 **Community** | <https://arne.sh/discord> |

## <img src="https://api.iconify.design/tabler/download.svg?color=888888" width="24" align="center"> Install a theme

1. Open a theme's folder under [`themes/`](themes/) and download its
   `.peltontheme` file.
2. In Pelton, go to **Settings → Themes → Import theme** and pick the file.
3. Review the metadata and raw CSS in the import preview, then click the
   theme's card to apply it.

> [!TIP]
> Sharing a theme with a friend is just sending them the `.peltontheme` file.

## <img src="https://api.iconify.design/tabler/photo.svg?color=888888" width="24" align="center"> Gallery

<!-- Add a row when you contribute a theme. -->

| Theme | Base | Made for | Preview |
| --- | --- | --- | --- |
| [**Nordish**](themes/nordish/) | `dark` | Pelton `1.0.8`+ | An arctic, north-bluish dark theme |

> [!NOTE]
> Each theme's own `README.md` carries a metadata table — version,
> compatibility, author and license — generated automatically from its
> manifest.

## <img src="https://api.iconify.design/tabler/upload.svg?color=888888" width="24" align="center"> Contribute a theme

We accept themes **two ways** — pick whichever suits you:

```mermaid
flowchart LR
    A([You made a theme]) --> B{Comfortable<br/>with git?}
    B -- Yes --> C[Open a Pull Request]
    B -- No --> D[Open a 'Submit a theme' issue]
    C --> E{{CI validates the theme}}
    D --> F[Maintainer opens the PR for you]
    F --> E
    E --> G([Merged into the gallery])
```

<details>
<summary><b>Quick start (pull request)</b></summary>

```sh
# 1. Fork, then copy the template
cp -r themes/_TEMPLATE themes/my-theme

# 2. Edit the source, then zip it into a .peltontheme
cd themes/my-theme/source
zip -r ../my-theme.peltontheme manifest.json tokens css assets

# 3. Add a LICENSE and README, then validate before pushing
cd ../../..
python3 scripts/validate_theme.py themes/my-theme
```

Then open a pull request. Full details are in
**[CONTRIBUTING.md](CONTRIBUTING.md)**.
</details>

### Requirements at a glance

- [x] A `.peltontheme` file in `themes/<your-theme>/`
- [x] A `LICENSE` in the folder
- [x] Passes `scripts/validate_theme.py` (run by CI)
- [x] `version` and `pelton.min` set in the manifest
- [ ] A preview screenshot _(recommended, not required)_
- [ ] A `README.md` describing the theme _(recommended)_

> [!IMPORTANT]
> Themes must **bundle** their fonts and images. A remote `url()` or `@import`
> can be used to track people, so CI rejects them — see the
> [security model](https://docs.pelton.app/themes/#security-model-in-short).

## <img src="https://api.iconify.design/tabler/tools.svg?color=888888" width="24" align="center"> Repository tooling

| Path | What it does |
| --- | --- |
| [`scripts/validate_theme.py`](scripts/validate_theme.py) | Validates every `.peltontheme` (manifest, tokens, CSS, size caps). |
| [`scripts/render_readme.py`](scripts/render_readme.py) | Renders the manifest metadata header into each theme's README. |
| [`.github/workflows/themes.yml`](.github/workflows/themes.yml) | Runs both on every push and pull request. |
| [`themes/_TEMPLATE/`](themes/_TEMPLATE/) | Copyable starting point for a new theme. |

Both scripts use the Python standard library only — no dependencies to install.

## <img src="https://api.iconify.design/tabler/scale.svg?color=888888" width="24" align="center"> Licensing

Each theme is licensed by its own author under the `LICENSE` file in its
folder — check there before reusing one. The repository tooling and
documentation are maintained by the Pelton community.

***

<p align="center">
  <sub>Not affiliated with any brand whose palette a theme may reference. Built by the <a href="https://pelton.app">Pelton</a> community.</sub>
</p>
