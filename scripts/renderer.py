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
