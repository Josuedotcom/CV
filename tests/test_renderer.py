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
