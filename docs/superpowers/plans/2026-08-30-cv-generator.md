# CV Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a data-driven CV generator: YAML content bank + Jinja2 LaTeX templates + a Python CLI that assembles a tailored `cv.tex`/`cv.pdf` per job application, validated and buildable both locally (MiKTeX) and in CI (GitHub Actions).

**Architecture:** Content lives once in `data/*.yaml` (bilingual, tagged). A `profile` YAML picks which sections/tags appear (structural variant). Each `applications/<name>/config.yaml` picks a profile, a visual `template`, a language, and per-application overrides, and doubles as the historical record. `scripts/generate.py` loads all of this, filters/orders content, renders a Jinja2 template into `.tex`, and compiles it with `latexmk`.

**Tech Stack:** Python 3.11+, PyYAML, Jinja2, pytest, latexmk (MiKTeX locally / TeX Live in CI), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-30-cv-generator-design.md`

## Global Constraints

- No dependencies beyond PyYAML, Jinja2, pytest — no schema/validation framework (e.g. pydantic); validation is hand-written per the spec's "Validation" section.
- Every bilingual field is always shaped `{es: ..., en: ...}` — never a bare string, never a third language key.
- Content-unit `id` values (bullets, skills, projects, education entries, certifications) must be unique across all of `data/`.
- Jinja2 environment always uses `StrictUndefined` — a missing template variable must fail generation, never render blank.
- The `ats` template must stay single-column with no tables, no `\multicols`, no images, per the spec's ATS-safety note.
- Every module function takes `repo_root: Path` (or an equivalent explicit path) as a parameter rather than relying on a hardcoded global, so it stays testable with `tmp_path`.

---

### Task 1: Project scaffolding + YAML data loader

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `scripts/__init__.py`
- Create: `scripts/data_loader.py`
- Test: `tests/test_data_loader.py`

**Interfaces:**
- Produces: `load_yaml_file(path: Path) -> dict` — parses one YAML file, adds `_source` (str path) to the returned dict.
- Produces: `load_yaml_dir(dir_path: Path) -> list[dict]` — loads every `*.yaml` file in a directory (sorted by filename) via `load_yaml_file`, returns the list.

- [ ] **Step 1: Create dependency and pytest config files**

`requirements.txt`:
```
pyyaml==6.0.2
jinja2==3.1.4
pytest==8.3.3
```

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: pyyaml, jinja2, pytest install without errors.

- [ ] **Step 3: Create `scripts/__init__.py`**

```python
```
(empty file — marks `scripts/` as a package)

- [ ] **Step 4: Write the failing tests**

`tests/test_data_loader.py`:
```python
from scripts.data_loader import load_yaml_file, load_yaml_dir


def test_load_yaml_file_parses_content_and_tags_source(tmp_path):
    file_path = tmp_path / "sample.yaml"
    file_path.write_text("name: {es: Hola, en: Hello}\n", encoding="utf-8")

    result = load_yaml_file(file_path)

    assert result["name"]["es"] == "Hola"
    assert result["_source"] == str(file_path)


def test_load_yaml_dir_loads_all_yaml_files_sorted(tmp_path):
    (tmp_path / "b.yaml").write_text("id: b\n", encoding="utf-8")
    (tmp_path / "a.yaml").write_text("id: a\n", encoding="utf-8")

    result = load_yaml_dir(tmp_path)

    assert [entry["id"] for entry in result] == ["a", "b"]
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `pytest tests/test_data_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.data_loader'`

- [ ] **Step 6: Implement `scripts/data_loader.py`**

```python
from pathlib import Path

import yaml


def load_yaml_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["_source"] = str(path)
    return data


def load_yaml_dir(dir_path: Path) -> list[dict]:
    return [load_yaml_file(path) for path in sorted(dir_path.glob("*.yaml"))]
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/test_data_loader.py -v`
Expected: 2 passed

- [ ] **Step 8: Commit**

```bash
git add requirements.txt pyproject.toml scripts/__init__.py scripts/data_loader.py tests/test_data_loader.py
git commit -m "feat: add YAML data loader"
```

---

### Task 2: Validator — unique content-unit IDs

**Files:**
- Create: `scripts/validators.py`
- Test: `tests/test_validators.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `check_unique_ids(items: list[dict]) -> list[str]` — items are dicts with `id` and `_source` keys; returns human-readable error strings (empty list = no duplicates).

- [ ] **Step 1: Write the failing tests**

`tests/test_validators.py`:
```python
from scripts.validators import check_unique_ids


def test_check_unique_ids_returns_no_errors_when_all_unique():
    items = [{"id": "a", "_source": "f1.yaml"}, {"id": "b", "_source": "f2.yaml"}]
    assert check_unique_ids(items) == []


def test_check_unique_ids_reports_duplicate_with_both_sources():
    items = [
        {"id": "dup", "_source": "f1.yaml"},
        {"id": "dup", "_source": "f2.yaml"},
    ]
    errors = check_unique_ids(items)
    assert len(errors) == 1
    assert "dup" in errors[0]
    assert "f1.yaml" in errors[0]
    assert "f2.yaml" in errors[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validators.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.validators'`

- [ ] **Step 3: Implement**

`scripts/validators.py`:
```python
def check_unique_ids(items: list[dict]) -> list[str]:
    seen: dict[str, str] = {}
    errors = []
    for item in items:
        item_id = item["id"]
        source = item.get("_source", "<unknown>")
        if item_id in seen:
            errors.append(
                f"Duplicate id '{item_id}' found in {source} "
                f"(first defined in {seen[item_id]})"
            )
        else:
            seen[item_id] = source
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validators.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/validators.py tests/test_validators.py
git commit -m "feat: validate unique content-unit ids"
```

---

### Task 3: Validator — bilingual field completeness

**Files:**
- Modify: `scripts/validators.py`
- Modify: `tests/test_validators.py`

**Interfaces:**
- Produces: `check_bilingual_fields(items: list[dict], field_names: list[str]) -> list[str]` — for each item and each named field that is a dict, requires both `es` and `en` to be present and non-empty.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_validators.py`:
```python
from scripts.validators import check_bilingual_fields


def test_check_bilingual_fields_passes_when_both_languages_present():
    items = [{"id": "a", "_source": "f.yaml", "text": {"es": "Hola", "en": "Hello"}}]
    assert check_bilingual_fields(items, ["text"]) == []


def test_check_bilingual_fields_reports_missing_language():
    items = [{"id": "a", "_source": "f.yaml", "text": {"es": "Hola", "en": ""}}]
    errors = check_bilingual_fields(items, ["text"])
    assert len(errors) == 1
    assert "'en'" in errors[0]
    assert "'a'" in errors[0]


def test_check_bilingual_fields_ignores_fields_not_present_on_item():
    items = [{"id": "a", "_source": "f.yaml", "text": {"es": "Hola", "en": "Hello"}}]
    assert check_bilingual_fields(items, ["text", "description"]) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validators.py -v`
Expected: FAIL with `ImportError: cannot import name 'check_bilingual_fields'`

- [ ] **Step 3: Implement**

Append to `scripts/validators.py`:
```python
def check_bilingual_fields(items: list[dict], field_names: list[str]) -> list[str]:
    errors = []
    for item in items:
        item_id = item.get("id", "<no id>")
        source = item.get("_source", "<unknown>")
        for field_name in field_names:
            value = item.get(field_name)
            if not isinstance(value, dict):
                continue
            for lang in ("es", "en"):
                if not value.get(lang):
                    errors.append(
                        f"Item '{item_id}' in {source} is missing '{lang}' "
                        f"text for field '{field_name}'"
                    )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validators.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/validators.py tests/test_validators.py
git commit -m "feat: validate bilingual field completeness"
```

---

### Task 4: Validator — override references exist

**Files:**
- Modify: `scripts/validators.py`
- Modify: `tests/test_validators.py`

**Interfaces:**
- Produces: `check_override_ids_exist(application_config: dict, known_ids: set[str]) -> list[str]` — checks `overrides.include_bullets`/`overrides.exclude_bullets` against a set of known valid IDs.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_validators.py`:
```python
from scripts.validators import check_override_ids_exist


def test_check_override_ids_exist_passes_when_all_known():
    config = {"_source": "app/config.yaml", "overrides": {"include_bullets": ["a"]}}
    assert check_override_ids_exist(config, known_ids={"a", "b"}) == []


def test_check_override_ids_exist_reports_unknown_id():
    config = {"_source": "app/config.yaml", "overrides": {"exclude_bullets": ["ghost"]}}
    errors = check_override_ids_exist(config, known_ids={"a"})
    assert len(errors) == 1
    assert "ghost" in errors[0]
    assert "app/config.yaml" in errors[0]


def test_check_override_ids_exist_handles_missing_overrides_key():
    config = {"_source": "app/config.yaml"}
    assert check_override_ids_exist(config, known_ids={"a"}) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validators.py -v`
Expected: FAIL with `ImportError: cannot import name 'check_override_ids_exist'`

- [ ] **Step 3: Implement**

Append to `scripts/validators.py`:
```python
def check_override_ids_exist(application_config: dict, known_ids: set[str]) -> list[str]:
    errors = []
    overrides = application_config.get("overrides", {})
    source = application_config.get("_source", "<unknown>")
    for key in ("include_bullets", "exclude_bullets"):
        for bullet_id in overrides.get(key, []):
            if bullet_id not in known_ids:
                errors.append(
                    f"{source}: overrides.{key} references unknown id '{bullet_id}'"
                )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validators.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/validators.py tests/test_validators.py
git commit -m "feat: validate application override id references"
```

---

### Task 5: Validator — profile tag filters match content

**Files:**
- Modify: `scripts/validators.py`
- Modify: `tests/test_validators.py`

**Interfaces:**
- Produces: `check_tag_filters_match(profile: dict, items: list[dict]) -> list[str]` — for each profile section with a `tag_filter`, requires at least one item to carry a matching tag.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_validators.py`:
```python
from scripts.validators import check_tag_filters_match


def test_check_tag_filters_match_passes_when_tag_present():
    profile = {"name": "backend", "sections": [{"type": "experience", "tag_filter": ["backend"]}]}
    items = [{"id": "a", "tags": ["backend"]}]
    assert check_tag_filters_match(profile, items) == []


def test_check_tag_filters_match_reports_zero_matches():
    profile = {"name": "backend", "sections": [{"type": "experience", "tag_filter": ["ghost-tag"]}]}
    items = [{"id": "a", "tags": ["backend"]}]
    errors = check_tag_filters_match(profile, items)
    assert len(errors) == 1
    assert "backend" in errors[0]
    assert "ghost-tag" in errors[0]


def test_check_tag_filters_match_ignores_sections_without_tag_filter():
    profile = {"name": "backend", "sections": [{"type": "education"}]}
    assert check_tag_filters_match(profile, items=[]) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validators.py -v`
Expected: FAIL with `ImportError: cannot import name 'check_tag_filters_match'`

- [ ] **Step 3: Implement**

Append to `scripts/validators.py`:
```python
def check_tag_filters_match(profile: dict, items: list[dict]) -> list[str]:
    errors = []
    profile_name = profile.get("name", profile.get("_source", "<unknown>"))
    for section in profile.get("sections", []):
        tag_filter = section.get("tag_filter")
        if not tag_filter:
            continue
        matches = any(set(item.get("tags", [])) & set(tag_filter) for item in items)
        if not matches:
            errors.append(
                f"Profile '{profile_name}' section '{section.get('type')}' "
                f"tag_filter {tag_filter} matches zero items"
            )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validators.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/validators.py tests/test_validators.py
git commit -m "feat: validate profile tag filters match at least one item"
```

---

### Task 6: Validator — certification badge images exist

**Files:**
- Modify: `scripts/validators.py`
- Modify: `tests/test_validators.py`

**Interfaces:**
- Produces: `check_badge_images_exist(certifications: list[dict], repo_root: Path) -> list[str]` — checks each certification's `badge_image` path resolves to a real file under `repo_root`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_validators.py`:
```python
from pathlib import Path

from scripts.validators import check_badge_images_exist


def test_check_badge_images_exist_passes_when_file_present(tmp_path):
    (tmp_path / "assets" / "badges").mkdir(parents=True)
    (tmp_path / "assets" / "badges" / "aws.png").write_bytes(b"fake-png")
    certs = [{"id": "cert-aws", "badge_image": "assets/badges/aws.png"}]

    assert check_badge_images_exist(certs, tmp_path) == []


def test_check_badge_images_exist_reports_missing_file(tmp_path):
    certs = [{"id": "cert-aws", "badge_image": "assets/badges/missing.png"}]

    errors = check_badge_images_exist(certs, tmp_path)

    assert len(errors) == 1
    assert "cert-aws" in errors[0]
    assert "missing.png" in errors[0]


def test_check_badge_images_exist_ignores_certs_without_badge(tmp_path):
    certs = [{"id": "cert-no-badge"}]
    assert check_badge_images_exist(certs, tmp_path) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validators.py -v`
Expected: FAIL with `ImportError: cannot import name 'check_badge_images_exist'`

- [ ] **Step 3: Implement**

Append to `scripts/validators.py` (add `from pathlib import Path` at the top of the file):
```python
def check_badge_images_exist(certifications: list[dict], repo_root: Path) -> list[str]:
    errors = []
    for cert in certifications:
        badge_path = cert.get("badge_image")
        if not badge_path:
            continue
        if not (repo_root / badge_path).is_file():
            errors.append(
                f"Certification '{cert.get('id')}' references missing badge image: {badge_path}"
            )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validators.py -v`
Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/validators.py tests/test_validators.py
git commit -m "feat: validate certification badge images exist"
```

---

### Task 7: `scripts/validate.py` CLI wiring all validators over real data

**Files:**
- Create: `scripts/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `load_yaml_file`, `load_yaml_dir` (Task 1); `check_unique_ids`, `check_bilingual_fields`, `check_override_ids_exist`, `check_tag_filters_match`, `check_badge_images_exist` (Tasks 2-6).
- Produces: `flatten_bullets(experience_entries: list[dict]) -> list[dict]`; `collect_all_ided_items(repo_root: Path) -> list[dict]`; `run_validation(repo_root: Path) -> list[str]`; `main() -> int` (CLI entrypoint, exit code 0/1).

- [ ] **Step 1: Write the failing tests**

`tests/test_validate.py`:
```python
import textwrap
from pathlib import Path

from scripts.validate import run_validation


def _write_minimal_repo(root: Path) -> None:
    (root / "data" / "experience").mkdir(parents=True)
    (root / "profiles").mkdir()
    (root / "applications" / "acme-2026-01-01").mkdir(parents=True)

    (root / "data" / "experience" / "acme.yaml").write_text(
        textwrap.dedent(
            """
            company: {es: Acme, en: Acme}
            role: {es: Dev, en: Dev}
            bullets:
              - id: exp-acme-1
                tags: [backend]
                text: {es: Hola, en: Hello}
            """
        ),
        encoding="utf-8",
    )
    (root / "data" / "skills.yaml").write_text("skills: []\n", encoding="utf-8")
    (root / "data" / "projects.yaml").write_text("projects: []\n", encoding="utf-8")
    (root / "data" / "education.yaml").write_text("education: []\n", encoding="utf-8")
    (root / "data" / "certifications.yaml").write_text("certifications: []\n", encoding="utf-8")
    (root / "profiles" / "backend.yaml").write_text(
        textwrap.dedent(
            """
            name: backend
            sections:
              - type: experience
                tag_filter: [backend]
            """
        ),
        encoding="utf-8",
    )
    (root / "applications" / "acme-2026-01-01" / "config.yaml").write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            lang: es
            overrides:
              include_bullets: [exp-acme-1]
            """
        ),
        encoding="utf-8",
    )


def test_run_validation_passes_on_consistent_minimal_repo(tmp_path):
    _write_minimal_repo(tmp_path)
    assert run_validation(tmp_path) == []


def test_run_validation_catches_duplicate_id(tmp_path):
    _write_minimal_repo(tmp_path)
    experience_file = tmp_path / "data" / "experience" / "acme.yaml"
    content = experience_file.read_text(encoding="utf-8")
    content += textwrap.dedent(
        """
              - id: exp-acme-1
                tags: [backend]
                text: {es: Otro, en: Other}
            """
        )
    experience_file.write_text(content, encoding="utf-8")

    errors = run_validation(tmp_path)

    assert any("exp-acme-1" in e for e in errors)


def test_run_validation_catches_unknown_override_id(tmp_path):
    _write_minimal_repo(tmp_path)
    config_file = tmp_path / "applications" / "acme-2026-01-01" / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            lang: es
            overrides:
              include_bullets: [ghost-id]
            """
        ),
        encoding="utf-8",
    )

    errors = run_validation(tmp_path)

    assert any("ghost-id" in e for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.validate'`

- [ ] **Step 3: Implement**

`scripts/validate.py`:
```python
import sys
from pathlib import Path

from scripts.data_loader import load_yaml_file, load_yaml_dir
from scripts.validators import (
    check_unique_ids,
    check_bilingual_fields,
    check_override_ids_exist,
    check_tag_filters_match,
    check_badge_images_exist,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def flatten_bullets(experience_entries: list[dict]) -> list[dict]:
    bullets = []
    for entry in experience_entries:
        for bullet in entry.get("bullets", []):
            bullet = dict(bullet)
            bullet.setdefault("_source", entry.get("_source"))
            bullets.append(bullet)
    return bullets


def collect_all_ided_items(repo_root: Path) -> list[dict]:
    experience = load_yaml_dir(repo_root / "data" / "experience")
    bullets = flatten_bullets(experience)
    skills = load_yaml_file(repo_root / "data" / "skills.yaml").get("skills", [])
    projects = load_yaml_file(repo_root / "data" / "projects.yaml").get("projects", [])
    education = load_yaml_file(repo_root / "data" / "education.yaml").get("education", [])
    certifications = load_yaml_file(repo_root / "data" / "certifications.yaml").get(
        "certifications", []
    )
    return bullets + skills + projects + education + certifications


def run_validation(repo_root: Path) -> list[str]:
    errors: list[str] = []
    all_items = collect_all_ided_items(repo_root)

    errors += check_unique_ids(all_items)
    errors += check_bilingual_fields(all_items, ["text", "name", "description", "degree"])

    certifications = load_yaml_file(repo_root / "data" / "certifications.yaml").get(
        "certifications", []
    )
    errors += check_badge_images_exist(certifications, repo_root)

    known_ids = {item["id"] for item in all_items if "id" in item}

    profiles = load_yaml_dir(repo_root / "profiles")
    for profile in profiles:
        errors += check_tag_filters_match(profile, all_items)

    applications_dir = repo_root / "applications"
    if applications_dir.is_dir():
        for config_path in sorted(applications_dir.glob("*/config.yaml")):
            config = load_yaml_file(config_path)
            errors += check_override_ids_exist(config, known_ids)

    return errors


def main() -> int:
    errors = run_validation(REPO_ROOT)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):\n")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validate.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: wire validate.py CLI over full data tree"
```

---

### Task 8: Content selector (tag filter + overrides + max count)

**Files:**
- Create: `scripts/content_selector.py`
- Test: `tests/test_content_selector.py`

**Interfaces:**
- Produces: `select_bullets(bullets: list[dict], tag_filter: list[str] | None, max_count: int | None, overrides: dict) -> list[dict]` — filters by tag (or lets everything through if `tag_filter` is `None`), always drops `exclude_bullets`, always force-adds `include_bullets` even if they don't match the tag filter, then truncates to `max_count` if given.

- [ ] **Step 1: Write the failing tests**

`tests/test_content_selector.py`:
```python
from scripts.content_selector import select_bullets


def _item(id_, tags):
    return {"id": id_, "tags": tags, "text": {"es": id_, "en": id_}}


def test_select_bullets_filters_by_tag():
    items = [_item("a", ["backend"]), _item("b", ["frontend"])]
    result = select_bullets(items, tag_filter=["backend"], max_count=None, overrides={})
    assert [i["id"] for i in result] == ["a"]


def test_select_bullets_none_tag_filter_keeps_everything():
    items = [_item("a", ["backend"]), _item("b", ["frontend"])]
    result = select_bullets(items, tag_filter=None, max_count=None, overrides={})
    assert [i["id"] for i in result] == ["a", "b"]


def test_select_bullets_exclude_override_wins_over_tag_match():
    items = [_item("a", ["backend"])]
    result = select_bullets(
        items, tag_filter=["backend"], max_count=None, overrides={"exclude_bullets": ["a"]}
    )
    assert result == []


def test_select_bullets_include_override_adds_non_matching_item():
    items = [_item("a", ["frontend"])]
    result = select_bullets(
        items, tag_filter=["backend"], max_count=None, overrides={"include_bullets": ["a"]}
    )
    assert [i["id"] for i in result] == ["a"]


def test_select_bullets_respects_max_count():
    items = [_item("a", ["backend"]), _item("b", ["backend"]), _item("c", ["backend"])]
    result = select_bullets(items, tag_filter=["backend"], max_count=2, overrides={})
    assert len(result) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_content_selector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.content_selector'`

- [ ] **Step 3: Implement**

`scripts/content_selector.py`:
```python
def select_bullets(
    bullets: list[dict],
    tag_filter: list[str] | None,
    max_count: int | None,
    overrides: dict,
) -> list[dict]:
    excluded = set(overrides.get("exclude_bullets", []))
    included_ids = set(overrides.get("include_bullets", []))

    selected = []
    for bullet in bullets:
        if bullet["id"] in excluded:
            continue
        matches_filter = tag_filter is None or bool(set(bullet.get("tags", [])) & set(tag_filter))
        forced_include = bullet["id"] in included_ids
        if matches_filter or forced_include:
            selected.append(bullet)

    if max_count is not None:
        selected = selected[:max_count]

    return selected
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_content_selector.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/content_selector.py tests/test_content_selector.py
git commit -m "feat: add tag/override-based content selector"
```

---

### Task 9: Jinja2 renderer with LaTeX-safe delimiters + strict undefined

**Files:**
- Create: `scripts/renderer.py`
- Test: `tests/test_renderer.py`

**Interfaces:**
- Produces: `build_environment(templates_dir: Path) -> jinja2.Environment`; `render_template(templates_dir: Path, template_name: str, context: dict) -> str`.

- [ ] **Step 1: Write the failing tests**

`tests/test_renderer.py`:
```python
import jinja2
import pytest

from scripts.renderer import render_template


def test_render_template_substitutes_variables(tmp_path):
    (tmp_path / "sample.tex.j2").write_text(r"Hello \VAR{name}", encoding="utf-8")

    result = render_template(tmp_path, "sample.tex.j2", {"name": "World"})

    assert result == "Hello World"


def test_render_template_supports_block_tags(tmp_path):
    (tmp_path / "sample.tex.j2").write_text(
        r"\BLOCK{for x in items}\VAR{x} \BLOCK{endfor}", encoding="utf-8"
    )

    result = render_template(tmp_path, "sample.tex.j2", {"items": ["a", "b"]})

    assert result == "a b "


def test_render_template_raises_on_missing_variable(tmp_path):
    (tmp_path / "sample.tex.j2").write_text(r"Hello \VAR{missing}", encoding="utf-8")

    with pytest.raises(jinja2.UndefinedError):
        render_template(tmp_path, "sample.tex.j2", {})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_renderer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.renderer'`

- [ ] **Step 3: Implement**

`scripts/renderer.py`:
```python
from pathlib import Path

import jinja2


def build_environment(templates_dir: Path) -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        line_comment_prefix="%%",
        trim_blocks=True,
        autoescape=False,
        undefined=jinja2.StrictUndefined,
    )


def render_template(templates_dir: Path, template_name: str, context: dict) -> str:
    env = build_environment(templates_dir)
    template = env.get_template(template_name)
    return template.render(**context)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_renderer.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/renderer.py tests/test_renderer.py
git commit -m "feat: add LaTeX-safe Jinja2 renderer"
```

---

### Task 10: `scripts/generate.py` — orchestrator CLI

**Files:**
- Create: `scripts/generate.py`
- Test: `tests/test_generate.py`

**Interfaces:**
- Consumes: `load_yaml_file`, `load_yaml_dir` (Task 1); `select_bullets` (Task 8); `render_template` (Task 9); `run_validation` (Task 7).
- Produces: `resolve_lang(value, lang: str)`; `build_experience_section(repo_root, section, overrides, lang) -> list[dict]`; `build_named_section(repo_root, filename, list_key, section, overrides, lang, extra_fields=None) -> list[dict]`; `build_context(repo_root, config, profile) -> dict`; `compile_pdf(tex_path: Path) -> None`; `generate(application_name: str, repo_root: Path = REPO_ROOT, compile: bool = True) -> Path`; `main() -> int`.

- [ ] **Step 1: Write the failing test**

`tests/test_generate.py`:
```python
import textwrap
from pathlib import Path

from scripts.generate import generate


def _write_repo(root: Path) -> None:
    (root / "data" / "experience").mkdir(parents=True)
    (root / "profiles").mkdir()
    (root / "templates").mkdir()
    (root / "applications" / "acme-2026-01-01").mkdir(parents=True)

    (root / "data" / "experience" / "acme.yaml").write_text(
        textwrap.dedent(
            """
            company: {es: Acme, en: Acme}
            role: {es: Dev, en: Dev}
            start_date: "2022-01"
            end_date: present
            bullets:
              - id: exp-acme-1
                tags: [backend]
                text: {es: Hice cosas, en: Did things}
            """
        ),
        encoding="utf-8",
    )
    (root / "data" / "skills.yaml").write_text("skills: []\n", encoding="utf-8")
    (root / "data" / "projects.yaml").write_text("projects: []\n", encoding="utf-8")
    (root / "data" / "education.yaml").write_text("education: []\n", encoding="utf-8")
    (root / "data" / "certifications.yaml").write_text("certifications: []\n", encoding="utf-8")
    (root / "profiles" / "backend.yaml").write_text(
        textwrap.dedent(
            """
            name: backend
            sections:
              - type: experience
                tag_filter: [backend]
            """
        ),
        encoding="utf-8",
    )
    (root / "templates" / "ats.tex.j2").write_text(
        r"\BLOCK{for role in experience}\VAR{role.company} - \VAR{role.role}"
        r"\BLOCK{for b in role.bullets}"
        "\n"
        r"\VAR{b}\BLOCK{endfor}\BLOCK{endfor}",
        encoding="utf-8",
    )
    (root / "applications" / "acme-2026-01-01" / "config.yaml").write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            template: ats
            lang: es
            """
        ),
        encoding="utf-8",
    )


def test_generate_writes_tex_file_with_rendered_content(tmp_path):
    _write_repo(tmp_path)

    tex_path = generate("acme-2026-01-01", repo_root=tmp_path, compile=False)

    assert tex_path == tmp_path / "applications" / "acme-2026-01-01" / "cv.tex"
    content = tex_path.read_text(encoding="utf-8")
    assert "Acme" in content
    assert "Hice cosas" in content


def test_generate_raises_when_validation_fails(tmp_path):
    _write_repo(tmp_path)
    experience_file = tmp_path / "data" / "experience" / "acme.yaml"
    experience_file.write_text(
        experience_file.read_text(encoding="utf-8")
        + textwrap.dedent(
            """
                  - id: exp-acme-1
                    tags: [backend]
                    text: {es: Otro, en: Other}
                """
        ),
        encoding="utf-8",
    )

    try:
        generate("acme-2026-01-01", repo_root=tmp_path, compile=False)
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "exp-acme-1" in str(exc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_generate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.generate'`

- [ ] **Step 3: Implement**

`scripts/generate.py`:
```python
import subprocess
import sys
from pathlib import Path

from scripts.content_selector import select_bullets
from scripts.data_loader import load_yaml_file, load_yaml_dir
from scripts.renderer import render_template
from scripts.validate import run_validation

REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_lang(value, lang: str):
    if isinstance(value, dict) and "es" in value and "en" in value:
        return value[lang]
    return value


def build_experience_section(repo_root: Path, section: dict, overrides: dict, lang: str) -> list[dict]:
    entries = load_yaml_dir(repo_root / "data" / "experience")
    result = []
    for entry in entries:
        selected = select_bullets(
            entry.get("bullets", []),
            tag_filter=section.get("tag_filter"),
            max_count=section.get("max_bullets_per_entry"),
            overrides=overrides,
        )
        if not selected:
            continue
        result.append(
            {
                "company": resolve_lang(entry["company"], lang),
                "role": resolve_lang(entry["role"], lang),
                "start_date": entry.get("start_date"),
                "end_date": entry.get("end_date"),
                "bullets": [resolve_lang(b["text"], lang) for b in selected],
            }
        )
    return result


def build_named_section(
    repo_root: Path,
    filename: str,
    list_key: str,
    section: dict,
    overrides: dict,
    lang: str,
    extra_fields: list[str] | None = None,
) -> list[dict]:
    items = load_yaml_file(repo_root / "data" / filename).get(list_key, [])
    selected = select_bullets(
        items,
        tag_filter=section.get("tag_filter"),
        max_count=section.get("max_items"),
        overrides=overrides,
    )
    result = []
    for item in selected:
        entry = {"name": resolve_lang(item.get("name"), lang)}
        for field in extra_fields or []:
            entry[field] = resolve_lang(item.get(field), lang)
        result.append(entry)
    return result


def build_context(repo_root: Path, config: dict, profile: dict) -> dict:
    lang = config["lang"]
    overrides = config.get("overrides", {})
    sections: dict = {}
    for section in profile.get("sections", []):
        section_type = section["type"]
        if section_type == "experience":
            sections["experience"] = build_experience_section(repo_root, section, overrides, lang)
        elif section_type == "skills":
            sections["skills"] = build_named_section(
                repo_root, "skills.yaml", "skills", section, overrides, lang
            )
        elif section_type == "projects":
            sections["projects"] = build_named_section(
                repo_root, "projects.yaml", "projects", section, overrides, lang,
                extra_fields=["description"],
            )
        elif section_type == "education":
            sections["education"] = build_named_section(
                repo_root, "education.yaml", "education", section, overrides, lang,
                extra_fields=["degree"],
            )
        elif section_type == "certifications":
            sections["certifications"] = build_named_section(
                repo_root, "certifications.yaml", "certifications", section, overrides, lang,
                extra_fields=["issuer", "date", "badge_image"],
            )
    return {
        "lang": lang,
        "company": config.get("company"),
        "role_applied": config.get("role_applied"),
        **{key: sections.get(key, []) for key in
           ("experience", "skills", "projects", "education", "certifications")},
    }


def compile_pdf(tex_path: Path) -> None:
    result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", tex_path.name],
        cwd=tex_path.parent,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log_tail = "\n".join(result.stdout.splitlines()[-40:])
        raise RuntimeError(f"latexmk failed for {tex_path}:\n{log_tail}")


def generate(application_name: str, repo_root: Path = REPO_ROOT, compile: bool = True) -> Path:
    app_dir = repo_root / "applications" / application_name
    config = load_yaml_file(app_dir / "config.yaml")

    errors = run_validation(repo_root)
    if errors:
        raise RuntimeError("Validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    profile = load_yaml_file(repo_root / "profiles" / f"{config['profile']}.yaml")
    context = build_context(repo_root, config, profile)

    template_name = f"{config['template']}.tex.j2"
    tex_content = render_template(repo_root / "templates", template_name, context)

    tex_path = app_dir / "cv.tex"
    tex_path.write_text(tex_content, encoding="utf-8")

    if compile:
        compile_pdf(tex_path)

    return tex_path


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: generate.py <application-name> [--no-compile]")
        return 1
    application_name = args[0]
    should_compile = "--no-compile" not in args
    try:
        generate(application_name, compile=should_compile)
    except RuntimeError as exc:
        print(str(exc))
        return 1
    suffix = "cv.tex and cv.pdf" if should_compile else "cv.tex"
    print(f"Generated {application_name}/{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_generate.py -v`
Expected: 2 passed

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: all tests passed (Tasks 1-10)

- [ ] **Step 6: Commit**

```bash
git add scripts/generate.py tests/test_generate.py
git commit -m "feat: add generate.py orchestrator CLI"
```

---

### Task 11: Walking skeleton — real ATS template + sample data + first real application

**Files:**
- Create: `templates/ats.tex.j2`
- Create: `data/experience/sample-company.yaml`
- Create: `data/skills.yaml`
- Create: `data/education.yaml`
- Create: `data/projects.yaml`
- Create: `data/certifications.yaml`
- Create: `profiles/backend.yaml`
- Create: `applications/sample-2026-08-30/config.yaml`

All sample content below is clearly placeholder — the user replaces it with real CV content once the pipeline is proven end-to-end.

- [ ] **Step 1: Create the ATS template**

`templates/ats.tex.j2`:
```latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\pagestyle{empty}

\begin{document}

\begin{center}
{\Large \textbf{Your Name}}\\
your.email@example.com
\end{center}

\BLOCK{if experience}
\section*{Experience}
\BLOCK{for role in experience}
\textbf{\VAR{role.role}} --- \VAR{role.company} (\VAR{role.start_date} -- \VAR{role.end_date})
\begin{itemize}[nosep]
\BLOCK{for bullet in role.bullets}
\item \VAR{bullet}
\BLOCK{endfor}
\end{itemize}
\BLOCK{endfor}
\BLOCK{endif}

\BLOCK{if skills}
\section*{Skills}
\VAR{skills|map(attribute='name')|join(', ')}
\BLOCK{endif}

\BLOCK{if education}
\section*{Education}
\BLOCK{for item in education}
\VAR{item.degree} --- \VAR{item.name}
\BLOCK{endfor}
\BLOCK{endif}

\BLOCK{if projects}
\section*{Projects}
\BLOCK{for project in projects}
\textbf{\VAR{project.name}}: \VAR{project.description}
\BLOCK{endfor}
\BLOCK{endif}

\end{document}
```

- [ ] **Step 2: Create sample experience data**

`data/experience/sample-company.yaml`:
```yaml
company: {es: "Empresa de Ejemplo", en: "Sample Company"}
role: {es: "Desarrollador Backend", en: "Backend Developer"}
start_date: "2022-01"
end_date: "present"
bullets:
  - id: exp-sample-migration
    tags: [backend, architecture]
    text:
      es: "Lideré la migración a microservicios, reduciendo el tiempo de deploy 40%."
      en: "Led the migration to microservices, cutting deploy time by 40%."
  - id: exp-sample-mentoring
    tags: [leadership, mentoring]
    text:
      es: "Mentoreé a 3 desarrolladores junior."
      en: "Mentored 3 junior developers."
```

- [ ] **Step 3: Create the remaining (empty-but-valid) data files**

`data/skills.yaml`:
```yaml
skills:
  - id: skill-python
    tags: [backend]
    name: {es: "Python", en: "Python"}
```

`data/education.yaml`:
```yaml
education:
  - id: edu-sample-university
    tags: [education]
    name: {es: "Universidad de Ejemplo", en: "Sample University"}
    degree: {es: "Ingeniería en Sistemas", en: "Systems Engineering"}
    start_date: "2016-01"
    end_date: "2021-12"
```

`data/projects.yaml`:
```yaml
projects: []
```

`data/certifications.yaml`:
```yaml
certifications: []
```

- [ ] **Step 4: Create the backend profile**

`profiles/backend.yaml`:
```yaml
name: backend
sections:
  - type: experience
    tag_filter: [backend]
    max_bullets_per_entry: 4
  - type: skills
    tag_filter: [backend]
  - type: education
```

- [ ] **Step 5: Create the first application**

`applications/sample-2026-08-30/config.yaml`:
```yaml
company: "Sample Company"
role_applied: "Backend Engineer"
date: 2026-08-30
profile: backend
template: ats
lang: es
notes: "Walking-skeleton verification application — safe to delete once verified."
```

- [ ] **Step 6: Run the full pipeline for real, including LaTeX compilation**

Run: `python scripts/generate.py sample-2026-08-30`
Expected: prints `Generated sample-2026-08-30/cv.tex and cv.pdf`; `applications/sample-2026-08-30/cv.pdf` exists and opens as a valid one-page PDF containing the sample experience/skills/education text.

- [ ] **Step 7: Run the full automated test suite once more**

Run: `pytest -v`
Expected: all tests still passed (this task added no new Python code)

- [ ] **Step 8: Commit**

```bash
git add templates/ats.tex.j2 data/ profiles/backend.yaml applications/sample-2026-08-30
git commit -m "feat: add ATS template and walking-skeleton sample application"
```

---

### Task 12: Visual template with certification badges

**Files:**
- Create: `templates/visual.tex.j2`
- Create: `assets/badges/sample-badge.png`
- Create: `applications/sample-visual-2026-08-30/config.yaml`
- Modify: `data/certifications.yaml`
- Modify: `profiles/backend.yaml`
- Modify: `tests/test_generate.py`

**Interfaces:**
- Consumes: `generate` (Task 10), `build_context`'s `certifications` section
  (Task 10 already implements this branch — it has no test yet, since
  Task 10's test only exercised the `experience` section type).

Note: `build_context`'s certifications handling was already written in
Task 10. This task adds the first coverage for that code path (no new
Python logic), plus the real template file and a second sample
application that proves it compiles end-to-end with an actual image.

- [ ] **Step 1: Add a coverage test for the certifications section path**

Append to `tests/test_generate.py`:
```python
def test_generate_certifications_section_resolves_lang_and_badge_path(tmp_path):
    _write_repo(tmp_path)
    (tmp_path / "data" / "certifications.yaml").write_text(
        textwrap.dedent(
            """
            certifications:
              - id: cert-aws
                tags: [cloud]
                name: {es: "AWS Solutions Architect", en: "AWS Solutions Architect"}
                issuer: "Amazon Web Services"
                date: "2023-05"
                badge_image: assets/badges/aws.png
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "profiles" / "backend.yaml").write_text(
        textwrap.dedent(
            """
            name: backend
            sections:
              - type: experience
                tag_filter: [backend]
              - type: certifications
                tag_filter: [cloud]
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "templates" / "visual.tex.j2").write_text(
        r"\BLOCK{for cert in certifications}"
        r"\includegraphics{\VAR{cert.badge_image}} \VAR{cert.name}"
        r"\BLOCK{endfor}",
        encoding="utf-8",
    )
    (tmp_path / "applications" / "acme-2026-01-01" / "config.yaml").write_text(
        textwrap.dedent(
            """
            company: Acme
            profile: backend
            template: visual
            lang: es
            """
        ),
        encoding="utf-8",
    )

    tex_path = generate("acme-2026-01-01", repo_root=tmp_path, compile=False)

    content = tex_path.read_text(encoding="utf-8")
    assert "assets/badges/aws.png" in content
    assert "AWS Solutions Architect" in content
```

This test is fully self-contained — it writes its own `tmp_path/templates/visual.tex.j2`, so it does not depend on the real `templates/visual.tex.j2` created in Step 3 below.

- [ ] **Step 2: Run the test**

Run: `pytest tests/test_generate.py -v`
Expected: 3 passed — this confirms `build_context`'s existing `certifications` branch (written in Task 10) correctly resolves the bilingual `name` and passes `badge_image` through unchanged. If it fails, the bug is in Task 10's `build_named_section`/`build_context`, not in anything new — fix it there before continuing.

- [ ] **Step 3: Create the real visual template**

`templates/visual.tex.j2`:
```latex
\documentclass[11pt]{article}
\usepackage[margin=0.8in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{titlesec}
\titleformat{\section}{\large\bfseries}{}{0em}{}[\titlerule]
\pagestyle{empty}

\begin{document}

\begin{center}
{\huge \textbf{Your Name}}\\[4pt]
your.email@example.com
\end{center}

\BLOCK{if experience}
\section*{Experience}
\BLOCK{for role in experience}
\textbf{\VAR{role.role}} --- \VAR{role.company} \hfill \VAR{role.start_date} -- \VAR{role.end_date}
\begin{itemize}[leftmargin=*, nosep]
\BLOCK{for bullet in role.bullets}
\item \VAR{bullet}
\BLOCK{endfor}
\end{itemize}
\BLOCK{endfor}
\BLOCK{endif}

\BLOCK{if certifications}
\section*{Certifications}
\BLOCK{for cert in certifications}
\noindent
\BLOCK{if cert.badge_image}
\includegraphics[height=0.5cm]{\VAR{cert.badge_image}}
\BLOCK{endif}
\textbf{\VAR{cert.name}} --- \VAR{cert.issuer} (\VAR{cert.date})\\
\BLOCK{endfor}
\BLOCK{endif}

\BLOCK{if skills}
\section*{Skills}
\VAR{skills|map(attribute='name')|join(', ')}
\BLOCK{endif}

\end{document}
```

- [ ] **Step 4: Create a real (valid, minimal) badge image asset**

Run:
```bash
mkdir -p assets/badges
printf '%s' "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=" | base64 -d > assets/badges/sample-badge.png
```
Expected: `assets/badges/sample-badge.png` exists (a valid 1x1 transparent PNG, small enough to keep in git as a placeholder — the user swaps in real certification badges later).

- [ ] **Step 5: Add a sample certification and extend the sample profile**

Modify `data/certifications.yaml` (created empty in Task 11):
```yaml
certifications:
  - id: cert-sample-cloud
    tags: [backend]
    name: {es: "Certificación de Ejemplo", en: "Sample Certification"}
    issuer: "Sample Issuer"
    date: "2023-05"
    badge_image: assets/badges/sample-badge.png
```

Modify `profiles/backend.yaml` (created in Task 11) to add a certifications section:
```yaml
name: backend
sections:
  - type: experience
    tag_filter: [backend]
    max_bullets_per_entry: 4
  - type: skills
    tag_filter: [backend]
  - type: education
  - type: certifications
    tag_filter: [backend]
```

- [ ] **Step 6: Create a second sample application using the visual template**

`applications/sample-visual-2026-08-30/config.yaml`:
```yaml
company: "Sample Company"
role_applied: "Backend Engineer"
date: 2026-08-30
profile: backend
template: visual
lang: es
notes: "Walking-skeleton verification for the visual template — safe to delete once verified."
```

- [ ] **Step 7: Run the full pipeline for real, including LaTeX compilation**

Run: `python scripts/generate.py sample-visual-2026-08-30`
Expected: prints `Generated sample-visual-2026-08-30/cv.tex and cv.pdf`; `applications/sample-visual-2026-08-30/cv.pdf` exists, opens as a valid PDF, and shows the sample certification with its badge image next to it.

- [ ] **Step 8: Re-run the full automated test suite**

Run: `pytest -v`
Expected: all tests passed

- [ ] **Step 9: Commit**

```bash
git add templates/visual.tex.j2 assets/badges/sample-badge.png data/certifications.yaml profiles/backend.yaml applications/sample-visual-2026-08-30 tests/test_generate.py
git commit -m "feat: add visual template with certification badge support"
```

---

### Task 13: Makefile for local workflow parity with CI

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Create the Makefile**

`Makefile`:
```makefile
.PHONY: validate generate

validate:
	python scripts/validate.py

generate:
	python scripts/generate.py $(APP)
```

- [ ] **Step 2: Verify both targets work**

Run: `make validate`
Expected: `Validation passed.`

Run: `make generate APP=sample-2026-08-30`
Expected: `Generated sample-2026-08-30/cv.tex and cv.pdf`

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "feat: add Makefile mirroring CI targets"
```

---

### Task 14: GitHub Actions CI (validate on every push, build+commit PDF on applications/ changes)

**Files:**
- Create: `.github/workflows/build-cv.yml`

- [ ] **Step 1: Create the workflow**

`.github/workflows/build-cv.yml`:
```yaml
name: Build CV

on:
  push:
    paths:
      - "applications/**"
      - "data/**"
      - "profiles/**"
      - "templates/**"
  workflow_dispatch:
    inputs:
      application:
        description: "Application folder name to build (leave empty to build all changed)"
        required: false

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python scripts/validate.py

  build:
    needs: validate
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - name: Install LaTeX
        run: sudo apt-get update && sudo apt-get install -y texlive-latex-extra latexmk
      - name: Determine applications to build
        id: apps
        run: |
          if [ -n "${{ github.event.inputs.application }}" ]; then
            echo "list=${{ github.event.inputs.application }}" >> "$GITHUB_OUTPUT"
          else
            CHANGED=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} -- applications/ | cut -d/ -f2 | sort -u | tr '\n' ' ')
            echo "list=$CHANGED" >> "$GITHUB_OUTPUT"
          fi
      - name: Generate and compile
        run: |
          for app in ${{ steps.apps.outputs.list }}; do
            python scripts/generate.py "$app"
          done
      - name: Commit compiled PDFs
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add applications/*/cv.pdf
          git diff --cached --quiet || git commit -m "chore: rebuild CV PDF(s)"
          git push
```

- [ ] **Step 2: Verify in CI**

Commit and push this file, then push a trivial change under `applications/sample-2026-08-30/` (e.g. touch `config.yaml`'s `notes` field) to trigger the workflow.
Expected: both the `validate` and `build` jobs complete green in the GitHub Actions tab, and `applications/sample-2026-08-30/cv.pdf` gets an automated commit if it changed.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build-cv.yml
git commit -m "feat: add CI workflow to validate and build CV PDFs"
```

---

### Task 15: README — usage documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write the README**

`README.md`:
```markdown
# CV Generator

Data-driven LaTeX CV generator. Content lives once in `data/*.yaml`
(bilingual, tagged); `profiles/*.yaml` pick which content shows up for a
given kind of role; each `applications/<company>-<date>/config.yaml` picks
a profile, a visual template, a language, and per-application overrides,
and doubles as a versioned record of what was sent to that company.

## Setup

```bash
pip install -r requirements.txt
```

Requires a local LaTeX distribution with `latexmk` on PATH (MiKTeX on
Windows, TeX Live elsewhere) to compile PDFs.

## Adding content

Add a bullet to an existing role, or a new file under `data/experience/`
for a new role. Every bullet needs a repo-wide-unique `id`, a `tags` list,
and bilingual `text: {es: ..., en: ...}`. Run `make validate` after
editing to catch duplicate IDs, missing translations, or broken
references before generating anything.

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
   `cv.pdf` in that folder.
3. Commit the whole folder — `config.yaml`, `cv.tex`, and `cv.pdf`
   together are the historical record of that application.

Use `--no-compile` (`python scripts/generate.py <name> --no-compile`) to
generate just the `.tex` without needing LaTeX installed.

## Templates

- `ats`: single column, no tables/images — built for parseability by
  applicant tracking systems.
- `visual`: richer layout, supports certification badge images via the
  `badge_image` field in `data/certifications.yaml`.

## CI

Every push to `data/`, `profiles/`, `templates/`, or `applications/`
runs validation. Changes under `applications/` also trigger a build job
that compiles the affected PDFs and commits them back automatically.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add usage README"
```
