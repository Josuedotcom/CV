# CV Generator — Design

Date: 2026-08-30
Status: Approved by user, pending implementation plan

## Problem

The user applies to different roles (backend, frontend, management, etc.)
and wants each CV to be tailored per application — both structurally
(which sections/achievements appear) and in fine detail (which bullets,
in what order) — without hand-editing a monolithic `.tex` file per
application and without duplicating content across languages.

Requirements gathered during brainstorming:

1. Support both structural variants (different "profiles" per role type)
   and fine-grained per-application tweaks (include/exclude specific
   achievements).
2. Content is stored once, tagged, and selected per application — not
   copy-pasted and hand-edited each time.
3. Bilingual (Spanish + English) from day one, even though English isn't
   used yet.
4. Build locally via MiKTeX (`latexmk`) and via GitHub Actions CI.
5. Keep a versioned history of what was sent to each company/vacancy:
   which content, which template, when.
6. Multiple visual templates: at least one ATS-oriented layout (plain,
   parseable) and one human-reviewed/visual layout (richer design,
   supports certification badge images).

## Chosen Approach

Data-driven generation: content lives as YAML (source of truth,
LaTeX-agnostic), a Python script renders it through a Jinja2 template
into a final `.tex` file, which is then compiled to PDF by a LaTeX
engine (MiKTeX locally, a LaTeX GitHub Action in CI).

This was chosen over "pure LaTeX modular includes" because:

- Content validation (duplicate IDs, missing translations, broken tag
  references) can be checked programmatically before ever touching
  LaTeX.
- Content is decoupled from the rendering format — the same YAML could
  later feed a non-LaTeX renderer if ever needed.

Note on a claim made during discussion: switching LaTeX distributions
(e.g., MiKTeX → TeX Live) is **not** a reason to prefer this approach —
`.tex` files are portable across distributions either way, since that's
the point of the LaTeX format. The real advantages are the two listed
above (validation, decoupling), not distro portability.

## Repository Structure

```
data/                     Source of truth: bilingual, tagged content
  experience/<company-slug>.yaml
  education.yaml
  skills.yaml
  projects.yaml
  certifications.yaml

profiles/                 Structural variants (what content, what order)
  backend.yaml
  frontend.yaml
  management.yaml

templates/                Visual variants (how it looks)
  ats.tex.j2               Single column, no tables/images, ATS-safe
  visual.tex.j2             Richer layout, supports certification badges

assets/
  badges/                  Certification badge images (referenced by data)

applications/              One folder per job application = history
  <company>-<date>/
    config.yaml             Which profile, which template, lang, overrides
    cv.tex                  Generated (not hand-edited)
    cv.pdf                  Compiled output, committed

scripts/
  generate.py              Assembles data + profile + config -> cv.tex, compiles
  validate.py              Schema/consistency checks over data/, profiles/, applications/

.github/workflows/
  build-cv.yml             Validate on every push; generate+compile on applications/ changes

Makefile                   Local targets mirroring CI: validate, generate, pdf
```

## Data Flow

1. **`data/*.yaml`** holds the facts: one entry per job/degree/skill/
   project/certification, each item tagged (`tags: [...]`) and bilingual
   (`text: {es: ..., en: ...}`).
2. **`profiles/<name>.yaml`** declares which sections appear and how
   content is filtered/limited per section (`tag_filter`,
   `max_bullets_per_entry`, etc.). This is the structural-variant axis.
3. **`applications/<company>-<date>/config.yaml`** picks a `profile`, a
   `template`, a `lang`, and any per-application `overrides`
   (`include_bullets` / `exclude_bullets` by ID). This is the
   fine-tuning axis and doubles as the historical record of what was
   sent where.
4. **`scripts/generate.py`** loads config → profile → the relevant
   `data/*.yaml` files, filters/orders bullets per profile rules, applies
   overrides, resolves the chosen language, and renders the selected
   Jinja2 template into `applications/<company>-<date>/cv.tex`. It then
   invokes `latexmk` to produce `cv.pdf` in the same folder.

### Example schemas

`data/experience/<company-slug>.yaml`:
```yaml
company: {es: "Empresa X", en: "Company X"}
role:    {es: "Desarrollador Backend", en: "Backend Developer"}
start_date: "2022-01"
end_date: "present"
bullets:
  - id: exp-companyx-microservices
    tags: [backend, architecture, leadership]
    text:
      es: "Lideré la migración a microservicios, reduciendo el tiempo de deploy 40%."
      en: "Led the migration to microservices, cutting deploy time by 40%."
```

`profiles/backend.yaml`:
```yaml
name: backend
sections:
  - type: experience
    tag_filter: [backend]
    max_bullets_per_entry: 4
  - type: skills
    tag_filter: [backend, devops]
  - type: education
  - type: projects
    tag_filter: [backend]
    max_items: 2
```

`applications/acme-2026-08-30/config.yaml`:
```yaml
company: "Acme Inc"
role_applied: "Senior Backend Engineer"
date: 2026-08-30
profile: backend
template: ats
lang: es
overrides:
  include_bullets: [exp-companyx-oncall]
  exclude_bullets: [exp-companyx-mentoring]
notes: "Pedían experiencia con Kafka, destaqué el proyecto Y"
```

`data/certifications.yaml` (badge support):
```yaml
certifications:
  - id: cert-aws-saa
    name: {es: "AWS Solutions Architect Associate", en: "AWS Solutions Architect Associate"}
    issuer: "Amazon Web Services"
    date: "2023-05"
    badge_image: assets/badges/aws-saa.png
    tags: [cloud, aws]
```
The `visual` template renders `badge_image` inline; the `ats` template
ignores it and prints plain text only.

## Templates (profile vs. template separation)

`profile` answers "what content appears"; `template` answers "how it's
rendered." They are independent axes, both selected in a given
application's `config.yaml`.

- `templates/ats.tex.j2`: single column, no tables, no `\multicols`, no
  images, standard fonts, `hyperref` for links. Deliberately minimal —
  LaTeX-produced PDFs are not automatically ATS-safe just by avoiding
  graphics; layout tricks (multi-column, tables) are a common cause of
  broken text extraction in ATS parsers, so this template avoids them
  entirely.
- `templates/visual.tex.j2`: richer layout, may use multiple columns,
  icons, and certification badge images.

## Validation

`scripts/validate.py` runs standalone (CI, `make validate`) and as a
pre-step inside `generate.py`. Checks:

- Bullet/entry `id` values are unique across all of `data/`.
- Every bilingual field has both `es` and `en` populated — no silent
  fallback.
- Every `include_bullets`/`exclude_bullets` ID in an application config
  resolves to a real entry in `data/`.
- Every `tag_filter` in a profile matches at least one bullet (a filter
  matching zero items is very likely a typo).
- Every `badge_image` path referenced in `data/certifications.yaml`
  exists under `assets/badges/`.

## Error Handling

- Jinja2 renders with `StrictUndefined`: a template referencing a
  missing variable fails generation loudly instead of producing a CV
  with a silently blank section.
- If `latexmk` fails, `generate.py` surfaces the tail of the LaTeX log
  instead of swallowing the error.

## CI / Build

`.github/workflows/build-cv.yml`:

1. Triggers on push touching `applications/**`, `data/**`,
   `profiles/**`, `templates/**`, plus manual `workflow_dispatch` with
   an application name input.
2. Fast job on every push/PR: run `scripts/validate.py` over all of
   `data/` — fails before any LaTeX compilation is attempted.
3. Build job: diff which `applications/*` folders changed, run
   `generate.py` for those, compile via a LaTeX GitHub Action
   (`xu-cheng/latex-action` or equivalent), and commit the resulting
   `cv.pdf` back into the same application folder so the versioned PDF
   never drifts from the `.tex`/data that produced it.

Local development mirrors CI via a `Makefile`:
`make validate`, `make generate APP=<name>`, `make pdf APP=<name>`
(using the user's local MiKTeX installation).

## Out of Scope (for this design)

- Automatic tag-based "best CV for this job description" generation
  (would require NLP/matching logic — a separate future project if
  ever pursued).
- Non-LaTeX output formats (HTML/Markdown rendering of the same data),
  even though the architecture doesn't preclude adding one later.
