# Web App Form Design — Content Creation

**S#:** S1-S3 (form design)
**Spec:** odd/tasks/cv-oss-app.md (existing feature doc)
**Scope confirmed by user:** Profile + Experience + Application form (3 steps), with intentional writing-style labels.

## Specs (S#)

S1: Add a "Crear perfil" step (Streamlit form) that writes `data/profile.yaml` with bilingual fields (`name`, `title`, `email`, `phone`, `summary` in `{es: ..., en: ...}`).
S2: Add a "Crear experiencia" step that writes `data/experience/<id>.yaml` with bilingual `company`, `role`, `bullets` (each bullet needs `id`, `tags`, `text: {es, en}`). Form includes writing-style guidance (example text).
S3: Keep existing application step but add labels explaining what each field is and writing style (e.g., "Resumen — 2-4 líneas concisas, bilingüe").
S4: All generated YAML must pass `make validate` (unique ids, bilingual fields, tags present).

## Non-goals

- No skills/education/certifications forms (user confirmed only profile + experience + app).
- No automatic PDF compilation in the form (existing `compile_pdf` checkbox stays).
- No removal of existing CLI workflow (`scripts/generate.py` stays intact).

## Design notes

- Use `st.form` so inputs are submitted together (avoids partial saves).
- Auto-generate `id` for experience bullets from company/role + counter.
- Add `st.info()` or `st.markdown()` with writing-style examples near each input.
- Preserve `REPO_ROOT` and existing `generate()` call; only add form sections before the existing application form.
