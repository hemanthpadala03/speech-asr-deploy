"""Structured prompt experimentation harness.

Compares prompt template versions (e.g. meeting_summary_v1 vs. v2) against a
fixed set of sample transcripts, scores each output against cheap
deterministic heuristics (not another LLM call -- reproducible, free, and
fast enough to run on every prompt edit), and writes a comparison report.

This is the "prompt optimization" story made concrete: v1 was the naive
first attempt, this harness is what showed it was too verbose and missed
concrete decisions, and v2 is the fix -- see docs/PROMPT_ENGINEERING.md for
the write-up.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from asrserve.agents.llm_client import LLMClient, build_client
from asrserve.agents.prompts.loader import render_prompt

_FIXTURES = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "transcripts"

_PREAMBLE_PATTERNS = re.compile(r"^(here is|here's|sure[,!]|summary:)", re.IGNORECASE)
_NUMBER_OR_DECISION = re.compile(r"\d|will |decided|agreed|approved|\$")


@dataclass
class PromptScore:
    template: str
    transcript_id: str
    bullet_count: int
    has_preamble: bool
    concrete_bullet_ratio: float
    word_count: int
    input_tokens: int
    output_tokens: int
    raw_output: str


def _score_summary(text: str) -> dict[str, Any]:
    lines = [line.strip("-* ").strip() for line in text.strip().splitlines() if line.strip()]
    bullets = [line for line in lines if line]
    concrete = sum(1 for b in bullets if _NUMBER_OR_DECISION.search(b))
    return {
        "bullet_count": len(bullets),
        "has_preamble": bool(_PREAMBLE_PATTERNS.match(text.strip())),
        "concrete_bullet_ratio": (concrete / len(bullets)) if bullets else 0.0,
        "word_count": len(text.split()),
    }


def load_fixture_transcripts() -> dict[str, str]:
    if not _FIXTURES.exists():
        return {}
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(_FIXTURES.glob("*.txt"))}


def run_eval(
    templates: list[str],
    transcripts: dict[str, str] | None = None,
    client: LLMClient | None = None,
) -> list[PromptScore]:
    client = client or build_client()
    transcripts = transcripts if transcripts is not None else load_fixture_transcripts()
    results: list[PromptScore] = []

    for transcript_id, transcript in transcripts.items():
        for template in templates:
            prompt = render_prompt(template, transcript=transcript)
            resp = client.complete(system_prompt="You are a helpful assistant.", user_prompt=prompt)
            metrics = _score_summary(resp.text)
            results.append(
                PromptScore(
                    template=template,
                    transcript_id=transcript_id,
                    input_tokens=resp.input_tokens,
                    output_tokens=resp.output_tokens,
                    raw_output=resp.text,
                    **metrics,
                )
            )
    return results


def summarize_scores(results: list[PromptScore]) -> dict[str, dict[str, float]]:
    by_template: dict[str, list[PromptScore]] = {}
    for r in results:
        by_template.setdefault(r.template, []).append(r)

    summary = {}
    for template, scores in by_template.items():
        n = len(scores)
        summary[template] = {
            "avg_bullet_count": sum(s.bullet_count for s in scores) / n,
            "preamble_rate": sum(s.has_preamble for s in scores) / n,
            "avg_concrete_bullet_ratio": sum(s.concrete_bullet_ratio for s in scores) / n,
            "avg_word_count": sum(s.word_count for s in scores) / n,
            "avg_output_tokens": sum(s.output_tokens for s in scores) / n,
        }
    return summary


def write_report(results: list[PromptScore], out_dir: Path | None = None) -> Path:
    out_dir = out_dir or (Path(__file__).parent.parent.parent.parent / "eval_runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"prompt_eval_{stamp}.json"
    payload = {
        "results": [asdict(r) for r in results],
        "summary": summarize_scores(results),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    results = run_eval(templates=["meeting_summary_v1", "meeting_summary_v2"])
    summary = summarize_scores(results)
    print(json.dumps(summary, indent=2))
    report_path = write_report(results)
    print(f"\nFull report: {report_path}")
