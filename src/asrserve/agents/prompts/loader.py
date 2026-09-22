"""Loads versioned Jinja prompt templates from templates/.

Prompts are files, not string literals buried in application code, so a
non-engineer (or a future me, in an interview) can read the exact wording a
case team's assistant uses and diff it version over version.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATES_DIR = Path(__file__).parent / "templates"


@lru_cache
def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_prompt(name: str, **context: object) -> str:
    """name like 'meeting_summary_v2' -> loads meeting_summary_v2.txt"""
    template = _env().get_template(f"{name}.txt")
    return template.render(**context)


def list_versions(prefix: str) -> list[str]:
    """All template names sharing a prefix, e.g. list_versions('meeting_summary') -> ['meeting_summary_v1', 'meeting_summary_v2']"""
    return sorted(
        p.stem for p in _TEMPLATES_DIR.glob(f"{prefix}_v*.txt")
    )
