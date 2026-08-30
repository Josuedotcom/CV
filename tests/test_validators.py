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
