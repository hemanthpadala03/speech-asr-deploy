# asrserve -- voice intelligence platform

Turns a call/meeting recording into a transcript, a decision-focused
summary, and a structured action-item list -- and shows the two halves of
shipping an AI tool that most portfolios only show one of: the production
deployment side (FastAPI, Docker, ECS Fargate + ALB via Terraform, CI) and
the applied-GenAI side (multi-provider LLM integration, versioned prompt
engineering with a measurable eval harness, a "custom GPT"-style assistant
config, and an n8n automation a non-engineer can own).

```
audio -> [faster-whisper ASR] -> transcript -> [LLM agent] -> summary + action items -> Slack (via n8n)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full diagram and
[docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) for how the prompts
were iterated with evidence, not vibes.

## Why this project exists

Built as a portfolio piece pairing [transformer-from-scratch](https://github.com/hemanthpadala03/transformer-from-scratch)
(model internals) with the other half of ML/AI work: integrating existing
AI tools (ASR + LLM APIs) into something a non-technical stakeholder could
actually use day to day. That second half is also, directly, the day-to-day
of an Applied AI role at a consultancy -- configuring AI tools for a team,
prompt engineering, lightweight API integrations, and workflow automation
(n8n) rather than training models from scratch.

## What's actually in here

| Layer | What it demonstrates |
|---|---|
| `src/asrserve/inference/` | faster-whisper (CTranslate2, int8, CPU) ASR wrapper + SRT export |
| `src/asrserve/agents/llm_client.py` | Provider-agnostic LLM client -- OpenAI, Anthropic, and Groq behind one interface, swappable via one env var |
| `src/asrserve/agents/prompts/` | Versioned Jinja prompt templates (`_v1`, `_v2`) -- prompt engineering as a file diff, not a buried string |
| `src/asrserve/agents/custom_assistants/case_team_copilot.yaml` | A "custom GPT" as data: system prompt, allowed tools, guardrails, task-to-prompt mapping |
| `src/asrserve/agents/eval.py` | Structured A/B prompt experimentation harness with deterministic scoring -- see [docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) |
| `src/asrserve/api/` | FastAPI service exposing `/transcribe`, `/agent/summarize`, `/agent/action-items`, `/health`, `/metrics` |
| `automations/n8n/` | An importable n8n workflow chaining the above into a hands-off Slack pipeline -- see [automations/README.md](automations/README.md) |
| `docker/`, `infra/terraform/` | Container + ECS Fargate/ALB/ECR/CloudWatch IaC for a real deployment |
| `docs/OPERATIONS_RUNBOOK.md` | Non-engineer-facing troubleshooting/onboarding guide, including the known gaps (no PII redaction, no diarization) that would block using this on a real client engagement as-is |
| `tests/` | 27 unit/API tests, all mocked at the provider-SDK boundary (no network needed to run CI) |

## Quickstart

```bash
pip install -e ".[dev]"
cp env.example .env   # fill in GROQ_API_KEY (free, no card: console.groq.com/keys)
                       # or OPENAI_API_KEY / ANTHROPIC_API_KEY
./scripts/run_local.sh   # or run_local.ps1 on Windows
# -> http://localhost:8000/docs
```

Try the prompt eval harness (real LLM calls, a few cents of tokens):
```bash
./scripts/run_prompt_eval.sh
```

Run the test suite (mocked, free, no network):
```bash
pytest tests/ -q
```

## Verification status (what's real vs. designed)

Following the same rule as the rest of this portfolio: verified means
actually run in this environment, not just written.

**Verified, real runs:**
- Full test suite: **27/27 passing** (`pytest tests/ -q`), covering the LLM
  client's provider-selection and response-parsing logic, the prompt
  loader, the eval scoring heuristics, the custom-assistant task runner, and
  every API route -- all against mocked provider SDKs, so this runs in CI
  with no API key.
- `ruff check src tests` -- clean.
- **Real end-to-end ASR transcription**, not mocked: downloaded a public
  domain speech sample (JFK's inaugural address excerpt, the same one used
  in OpenAI Whisper's own test suite) and ran it through the actual
  faster-whisper pipeline (`tiny` model, CPU, int8) via
  `WhisperASR.transcribe()`. It correctly transcribed: *"And so, my fellow
  Americans, ask not what your country can do for you, ask what you can do
  for your country."*
- **The LLM agent layer's live call path -- now actually run**, end to end,
  through the real FastAPI app (`TestClient`, not mocked) against Groq
  (`openai/gpt-oss-120b`, free tier, no card required). Both routes were
  called with a seeded sample transcript
  (`tests/fixtures/transcripts/client_kickoff_01.txt`) and produced real,
  correct model output:
  - `POST /agent/summarize` -> a 5-bullet decision-focused summary that
    correctly pulled out the numeric target, the CEO's headcount
    constraint, the owner/deadline for the follow-up data pull, and the
    caveat about what's included in the 18% cost figure.
  - `POST /agent/action-items` -> two structured action items, each with
    the correct `owner`/`due`/`confidence`, extracted via Groq
    function-calling (`GroqClient` uses tool-calling for structured output
    rather than `response_format=json_schema`, since Groq's json_schema
    support is inconsistent across models -- function calling is the one
    structured-output path it reliably supports everywhere).
  - Full request/response JSON saved at `eval_runs/live_api_sample.json`
    (gitignored -- regenerate with the snippet in
    [docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md)).
- **The prompt v1-vs-v2 eval harness -- run for real** via
  `./scripts/run_prompt_eval.sh` against Groq. See
  [docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) for the full
  comparison table; headline result: v2's constrained prompt cut bullet
  count from 19 to 4.5 and tripled the concrete-bullet ratio (0.30 -> 0.90)
  at the cost of more output tokens per call.
- SDK integration sanity-checked against the versions actually installed
  (`anthropic` 1.5.0, `openai` 2.17.0) -- the `chat.completions.create` /
  `messages.create` call shapes this code relies on still match.

**Note on the original OpenAI/Anthropic path:** the `OPENAI_API_KEY`
available in this environment returned `insufficient_quota` (`credit_balance_exhausted`)
on a real call, and no `ANTHROPIC_API_KEY` was available -- both correctly
surfaced as normal API errors, not code bugs. Rather than wait on funding a
paid key, `LLM_PROVIDER=groq` (free tier) was used to get a genuinely live
run instead; the `OpenAIClient`/`AnthropicClient` code paths remain
unverified live but are covered by the same mocked unit tests as
`GroqClient` and should work identically given a funded key -- the three
clients share the same `LLMClient` interface and are exercised by the same
test suite.

**Designed but not live-verified:**
- **Terraform.** Authored by hand (no `terraform` CLI available in this
  environment to run `validate`/`plan`); not applied against real AWS.
  Consistent with how the rest of this portfolio treats infra: designed,
  not deployed, until stated otherwise.
- **n8n workflow.** Valid JSON (round-trips through `json.load`), matches
  n8n's node/connection schema, but not imported into a running n8n
  instance in this environment.

## Roadmap / explicitly known gaps

- No speaker diarization, no PII redaction before transcripts reach an
  external LLM provider (see the runbook's "known gaps" section -- this is
  the reason to call this a prototype, not something to point at real
  client data).
- No auth on the API (fine for a portfolio demo behind a private ALB; not
  fine for anything with real case data).
- Whisper fine-tuning on domain-specific audio (the original plan for this
  project) was descoped in favor of the agent/automation layer above, which
  maps more directly to applied-AI/GenAI-integration roles than to ASR
  research.
