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
            entry.get("bullets") or [],
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
    items = load_yaml_file(repo_root / "data" / filename).get(list_key) or []
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
            value = resolve_lang(item.get(field), lang)
            # Convert badge_image paths to relative paths for LaTeX compilation
            # App cv.tex is at repo_root/applications/<name>/cv.tex (2 levels below repo_root)
            # Use forward slashes for LaTeX compatibility on Windows
            if field == "badge_image" and value:
                value = ("../../" + value).replace("\\", "/")
            entry[field] = value
        result.append(entry)
    return result


def build_context(repo_root: Path, config: dict, profile: dict) -> dict:
    lang = config["lang"]
    overrides = config.get("overrides") or {}
    sections: dict = {}
    for section in profile.get("sections") or []:
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
