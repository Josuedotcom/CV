# CV Generator

Data-driven LaTeX CV generator. Content lives once in `data/*.yaml`
(bilingual, tagged); `profiles/*.yaml` pick which content shows up for a
given kind of role; each `applications/<company>-<date>/config.yaml` picks
a profile, a visual template, a language, and per-application overrides,
and doubles as a versioned record of what was sent to that company.

## Setup

Requires Python 3.11+ (pinned to 3.12 via `.python-version`; `uv` manages this automatically).

Also requires a local LaTeX distribution with `latexmk` on PATH (MiKTeX on
Windows, TeX Live elsewhere) to compile PDFs.

Install dependencies:

```bash
uv sync
```

This reads `pyproject.toml` and `uv.lock` and sets up a virtual environment with all dependencies.

## Adding content

Add a bullet to an existing role, or a new file under `data/experience/`
for a new role. Every bullet needs a repo-wide-unique `id`, a `tags` list,
and bilingual `text: {es: ..., en: ...}`. Run `make validate` after
editing to catch duplicate IDs, missing translations, or broken
references before generating anything:

```bash
make validate
```

Or directly:

```bash
uv run python -m scripts.validate
```

## Adding a profile

Create `profiles/<name>.yaml` listing which sections appear and how
they're filtered (`tag_filter`, `max_bullets_per_entry` / `max_items`).
See `profiles/backend.yaml` for a working example.

## Creating a new application

1. Create `applications/<company>-<date>/config.yaml` with `company`,
   `role_applied`, `profile`, `template` (`ats` or `visual`), `lang`
   (`es`/`en`), and optional `overrides.include_bullets` /
   `overrides.exclude_bullets` for one-off tweaks.
2. Run `make generate APP=<company>-<date>` to produce `cv.tex` and
   `cv.pdf` in that folder:

```bash
make generate APP=<company>-<date>
```

Or directly:

```bash
uv run python -m scripts.generate <company>-<date>
```

3. Commit the whole folder — `config.yaml`, `cv.tex`, and `cv.pdf`
   together are the historical record of that application.

To generate just the `.tex` without needing LaTeX installed, use the `--no-compile` flag:

```bash
uv run python -m scripts.generate <company>-<date> --no-compile
```

## Templates

- `ats`: single column, no tables/images — built for parseability by
  applicant tracking systems.
- `visual`: richer layout, supports certification badge images via the
  `badge_image` field in `data/certifications.yaml`.

## CI

Every push to `data/`, `profiles/`, `templates/`, or `applications/`
runs validation. Changes under `applications/` also trigger a build job
that compiles the affected PDFs and commits them back automatically.

---

## Open Source — Uso y contribución

Este repositorio es de código abierto (licencia MIT). Puedes clonarlo, usarlo localmente y contribuir.

- **Quickstart (para nuevos usuarios):** ver `QUICKSTART.md`.
- **Web app local:** `streamlit run web/app.py` (ver `QUICKSTART.md`).
- **Docker portable (sin instalar nada local):** `docker build -t cv-generator . && docker run -p 8501:8501 cv-generator`
- **Contribuciones y plantillas comunitarias:** ver `CONTRIBUTING.md` y `templates/modern.tex.j2` como referencia.
- **Documentación técnica:** `docs/superpowers/specs/` y `docs/superpowers/plans/`.
- **Tests y CI:** el proyecto mantiene 74 tests (`uv run pytest`) + validación (`make validate`). Toda contribución debe pasar ambos antes de ser aceptada.
