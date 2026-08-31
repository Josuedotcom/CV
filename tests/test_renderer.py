import jinja2
import pytest

from scripts.renderer import escape_latex, render_template


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


def test_escape_latex_escapes_percent_and_ampersand():
    assert escape_latex("40% and R&D") == r"40\% and R\&D"


def test_escape_latex_escapes_all_special_chars():
    assert escape_latex(r"$100 & 50% (1_2^3) {key}: value~end") == r"\$100 \& 50\% (1\_2\^{}3) \{key\}: value\~{}end"


def test_escape_latex_passes_through_non_string_values():
    assert escape_latex(None) is None
    assert escape_latex(42) == 42


def test_render_template_escapes_special_chars_with_latex_filter(tmp_path):
    (tmp_path / "sample.tex.j2").write_text(
        r"\VAR{text|latex}", encoding="utf-8"
    )

    result = render_template(tmp_path, "sample.tex.j2", {"text": "40% and R&D"})

    assert result == r"40\% and R\&D"
