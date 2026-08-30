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
