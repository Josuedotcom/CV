from pathlib import Path

from scripts.validators import (
    check_unique_ids,
    check_bilingual_fields,
    check_override_ids_exist,
    check_tag_filters_match,
    check_badge_images_exist,
)


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


def test_check_override_ids_exist_handles_null_overrides_value():
    config = {"_source": "app/config.yaml", "overrides": None}
    assert check_override_ids_exist(config, known_ids={"a"}) == []


def test_check_tag_filters_match_passes_when_tag_present():
    profile = {"name": "backend", "sections": [{"type": "experience", "tag_filter": ["backend"]}]}
    items_by_type = {"experience": [{"id": "a", "tags": ["backend"]}]}
    assert check_tag_filters_match(profile, items_by_type) == []


def test_check_tag_filters_match_reports_zero_matches():
    profile = {"name": "backend", "sections": [{"type": "experience", "tag_filter": ["ghost-tag"]}]}
    items_by_type = {"experience": [{"id": "a", "tags": ["backend"]}]}
    errors = check_tag_filters_match(profile, items_by_type)
    assert len(errors) == 1
    assert "backend" in errors[0]
    assert "ghost-tag" in errors[0]


def test_check_tag_filters_match_ignores_sections_without_tag_filter():
    profile = {"name": "backend", "sections": [{"type": "education"}]}
    assert check_tag_filters_match(profile, items_by_type={}) == []


def test_check_tag_filters_match_handles_null_sections():
    profile = {"name": "backend", "sections": None}
    assert check_tag_filters_match(profile, items_by_type={}) == []


def test_check_tag_filters_match_handles_null_tags_on_item():
    profile = {"name": "backend", "sections": [{"type": "experience", "tag_filter": ["backend"]}]}
    items_by_type = {"experience": [{"id": "a", "tags": None}]}
    errors = check_tag_filters_match(profile, items_by_type)
    assert len(errors) == 1


def test_check_tag_filters_match_only_considers_items_of_the_sections_own_type():
    # `architecture` exists on an experience bullet but on no skill: the skills
    # section must still be reported, not silently pass on the cross-type match.
    profile = {"name": "backend", "sections": [{"type": "skills", "tag_filter": ["architecture"]}]}
    items_by_type = {
        "experience": [{"id": "exp-a", "tags": ["architecture"]}],
        "skills": [{"id": "skill-python", "tags": ["backend"]}],
    }

    errors = check_tag_filters_match(profile, items_by_type)

    assert len(errors) == 1
    assert "skills" in errors[0]
    assert "architecture" in errors[0]


def test_check_tag_filters_match_reports_unknown_section_type_as_zero_matches():
    profile = {"name": "backend", "sections": [{"type": "publications", "tag_filter": ["backend"]}]}
    items_by_type = {"experience": [{"id": "exp-a", "tags": ["backend"]}]}

    errors = check_tag_filters_match(profile, items_by_type)

    assert len(errors) == 1
    assert "publications" in errors[0]


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
