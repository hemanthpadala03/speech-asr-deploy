# Operations runbook (case-team-facing)

Written for the person answering "the call summary tool broke" from a case
team member who does not want to read source code -- the "providing
operational support" and "onboarding to AI-enabled workflows" part of the
role, made concrete.

## Onboarding a new case team in under 10 minutes

1. Confirm they have a way to get a recording (Zoom/Teams cloud recording,
   or a local file) as a `.wav`/`.mp3`/`.m4a`.
2. Point them at the n8n webhook URL (see
   [`automations/README.md`](../automations/README.md)) or, for a single ad
   hoc file, the `/transcribe` -> `/agent/summarize` calls directly via the
   FastAPI docs UI at `/docs` -- no code needed either way.
3. Tell them where the output lands (Slack channel configured in the n8n
   workflow's `SLACK_CASE_TEAM_CHANNEL`).
4. Set expectations: a ~30-60 second call takes a few seconds to transcribe
   on CPU with the `small` model; longer calls scale roughly linearly.

## "The summary is missing something important"

This is a prompt problem, not a code bug 90% of the time.
1. Ask for the specific transcript. Add it to
   `tests/fixtures/transcripts/` as a new `.txt` fixture.
2. Run `./scripts/run_prompt_eval.sh` -- does the current prompt version
   score badly against it (low concrete-bullet ratio, high preamble rate)?
3. If yes: propose a prompt edit in
   `agents/prompts/templates/meeting_summary_v3.txt`, re-run the eval, and
   only ship it if the aggregate numbers improve without regressing the
   other fixtures. See [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md).
4. If the eval numbers look fine but the team still isn't happy: the
   heuristics may not capture what "good" means for their specific case --
   that's a signal to add a new heuristic to `agents/eval.py`, not to
   eyeball-tune the prompt.

## "/transcribe is returning garbage / wrong language"

- Check `/health` -- `asr_model_size` should be `small` or larger in
  production (`tiny` is for fast local dev only, it hallucinates far more on
  accented or noisy audio).
- faster-whisper auto-detects language from the first 30s; if a call
  switches languages mid-way (common in a German case team on an
  English-language client call), the whole transcript may get tagged wrong.
  There is no per-segment language override yet -- flag as a known gap.

## "The LLM call is failing / no summary comes back"

1. Check `LLM_PROVIDER` in `.env`/the deployed secret matches which key is
   actually funded -- an `insufficient_quota` error on OpenAI silently looks
   identical to a wrong key from the case team's point of view. Both surface
   as a 500 from `/agent/summarize`; check the FastAPI logs (each request is
   tagged with an `X-Request-ID`, see `middleware.py`) for the real
   provider error.
2. `LLM_PROVIDER=anthropic` as a fallback swap is one env var, not a
   redeploy of application code (`agents/llm_client.py`).

## Known gaps (say this out loud in onboarding, don't let it surprise anyone)

- No speaker diarization -- transcripts don't attribute lines to specific
  speakers unless someone states their name in the audio.
- No PII/confidentiality scrubbing before a transcript is sent to an
  external LLM provider -- for a real client engagement this needs a
  redaction pass or an on-prem/VPC-scoped model before this pipeline touches
  anything client-confidential. This is the single biggest reason this repo
  is a portfolio/prototype, not something to point at a real case team's
  recordings as-is.
