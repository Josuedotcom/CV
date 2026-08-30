from scripts.validators import check_unique_ids, check_bilingual_fields


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


def test_check_override_ids_exist_handles_null_overrides_value():
    config = {"_source": "app/config.yaml", "overrides": None}
    assert check_override_ids_exist(config, known_ids={"a"}) == []


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
