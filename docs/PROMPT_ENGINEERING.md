# Prompt engineering: v1 -> v2, with evidence

`asrserve.agents.eval` runs the same set of sample call transcripts
(`tests/fixtures/transcripts/`) through two versions of the meeting-summary
prompt and scores the outputs on deterministic heuristics -- no LLM-as-judge,
so the numbers are reproducible and free to re-run on every prompt edit.

## v1 (naive)

```
Summarize this meeting transcript.

Transcript:
{{ transcript }}
```

This is what almost anyone writes first. It works, but left unconstrained a
general-purpose chat model tends to:
- open with a throat-clearing preamble ("Here is a summary of the call:")
- write prose paragraphs instead of scannable bullets
- weight airtime, not decision-relevance -- a 5-minute tangent about
  scheduling gets as much space as the one number that changed the budget
- summarize *that a topic was discussed* without saying what was decided

## v2 (constrained)

Adds: a role ("case-team assistant" not "helpful assistant"), a hard bullet
cap, an explicit definition of what makes a bullet "concrete" (a decision, a
number, or a named open question), a rule against inventing structure when
the transcript is genuinely inconclusive, and a ban on the preamble line.
See [`meeting_summary_v2.txt`](../src/asrserve/agents/prompts/templates/meeting_summary_v2.txt)
for the exact text.

## Running the comparison yourself

```bash
./scripts/run_prompt_eval.sh
```

This calls the configured LLM provider for real (costs a handful of tokens
per transcript x template) and writes a full per-transcript report to
`eval_runs/prompt_eval_<timestamp>.json`, plus prints the aggregate table.

## Real results (2026-09-22, `LLM_PROVIDER=groq`, `openai/gpt-oss-120b`)

| metric | meeting_summary_v1 | meeting_summary_v2 |
|---|---|---|
| avg bullet count | 19.0 | 4.5 |
| preamble rate | 0.0 | 0.0 |
| avg concrete-bullet ratio | 0.30 | 0.90 |
| avg word count | 225.0 | 70.5 |
| avg output tokens | 398.5 | 560.0 |

Full per-transcript report: `eval_runs/prompt_eval_20260922T140717Z.json`
(gitignored -- re-run the script to regenerate).

**Reading these numbers:** v2's hard bullet cap and "concrete bullet"
definition worked as designed -- bullet count dropped ~4x and the
concrete-bullet ratio tripled, i.e. v2 mostly stopped restating that a topic
was discussed and started saying what was decided. Preamble rate was 0 for
both, so that specific failure mode didn't show up on this model even for
v1 (worth re-checking against a different model, since preamble-stripping
behavior varies by provider). The one real tradeoff: v2 spends *more*
output tokens per call despite shorter, denser text -- the constrained
prompt asks the model to reason about what counts as "concrete" before
picking bullets, which shows up as reasoning/thinking tokens on
`openai/gpt-oss-120b`. Worth surfacing in an interview: a stricter prompt
traded token cost for output quality, and that tradeoff is measurable, not
assumed.

**Status:** the harness is real and unit-tested (`tests/test_prompts_and_eval.py`
covers the scoring functions against fixed strings, no network needed), and
the table above is a real run against a live model, not a placeholder.

## Regenerating the live API sample

`README.md`'s Verification status section references a saved live sample of
`/agent/summarize` + `/agent/action-items` output. Regenerate it with:

```python
from fastapi.testclient import TestClient
from asrserve.api.main import app
import pathlib, json

transcript = pathlib.Path("tests/fixtures/transcripts/client_kickoff_01.txt").read_text(encoding="utf-8")
client = TestClient(app)

r1 = client.post("/agent/summarize", json={"transcript": transcript})
r2 = client.post("/agent/action-items", json={"transcript": transcript})

pathlib.Path("eval_runs").mkdir(exist_ok=True)
pathlib.Path("eval_runs/live_api_sample.json").write_text(
    json.dumps({"summarize": r1.json(), "action_items": r2.json()}, indent=2), encoding="utf-8"
)
```

Requires a valid key for whichever `LLM_PROVIDER` is set in `.env`.

## Why this matters for the role

This is the concrete version of "prompt optimization" and "structured
experimentation with different tools" -- not vibes-based iteration in a
playground, but a prompt change justified by a before/after measurement a
non-technical stakeholder could also read.
