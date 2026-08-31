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


def test_select_bullets_forced_include_survives_max_count_truncation():
    # The forced-include sits last in source order, behind enough tag matches to
    # fill max_count: truncation must never drop an explicit override.
    items = [
        _item("a", ["backend"]),
        _item("b", ["backend"]),
        _item("c", ["backend"]),
        _item("forced", ["frontend"]),
    ]

    result = select_bullets(
        items,
        tag_filter=["backend"],
        max_count=2,
        overrides={"include_bullets": ["forced"]},
    )

    ids = [i["id"] for i in result]
    assert "forced" in ids
    assert len(result) == 2


def test_select_bullets_max_count_smaller_than_forced_includes_keeps_all_forced():
    items = [_item("a", ["backend"]), _item("f1", ["frontend"]), _item("f2", ["frontend"])]

    result = select_bullets(
        items,
        tag_filter=["backend"],
        max_count=1,
        overrides={"include_bullets": ["f1", "f2"]},
    )

    assert [i["id"] for i in result] == ["f1", "f2"]


def test_select_bullets_exclude_wins_over_include_override():
    items = [_item("a", ["frontend"])]

    result = select_bullets(
        items,
        tag_filter=["backend"],
        max_count=None,
        overrides={"include_bullets": ["a"], "exclude_bullets": ["a"]},
    )

    assert result == []


def test_select_bullets_handles_null_tags_on_item():
    items = [{"id": "a", "tags": None, "text": {"es": "a", "en": "a"}}]
    result = select_bullets(items, tag_filter=["backend"], max_count=None, overrides={})
    assert result == []


def test_select_bullets_handles_null_exclude_bullets_override():
    items = [_item("a", ["backend"])]
    result = select_bullets(
        items, tag_filter=["backend"], max_count=None, overrides={"exclude_bullets": None}
    )
    assert [i["id"] for i in result] == ["a"]


def test_select_bullets_handles_null_include_bullets_override():
    items = [_item("a", ["frontend"])]
    result = select_bullets(
        items, tag_filter=["backend"], max_count=None, overrides={"include_bullets": None}
    )
    assert result == []
