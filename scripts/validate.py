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
        for bullet in entry.get("bullets") or []:
            bullet = dict(bullet)
            bullet.setdefault("_source", entry.get("_source"))
            bullets.append(bullet)
    return bullets


def collect_all_ided_items(repo_root: Path) -> list[dict]:
    experience = load_yaml_dir(repo_root / "data" / "experience")
    bullets = flatten_bullets(experience)
    skills = load_yaml_file(repo_root / "data" / "skills.yaml").get("skills") or []
    projects = load_yaml_file(repo_root / "data" / "projects.yaml").get("projects") or []
    education = load_yaml_file(repo_root / "data" / "education.yaml").get("education") or []
    certifications = load_yaml_file(repo_root / "data" / "certifications.yaml").get(
        "certifications"
    ) or []
    return bullets + skills + projects + education + certifications


def run_validation(repo_root: Path) -> list[str]:
    errors: list[str] = []
    all_items = collect_all_ided_items(repo_root)

    errors += check_unique_ids(all_items)
    errors += check_bilingual_fields(all_items, ["text", "name", "description", "degree"])

    certifications = load_yaml_file(repo_root / "data" / "certifications.yaml").get(
        "certifications"
    ) or []
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
