# Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │                 asrserve (FastAPI)            │
  audio file  ─────▶│  POST /transcribe                             │
                    │   -> faster-whisper (CTranslate2, int8, CPU)  │
                    │   -> text + SRT                               │
                    │                                                │
  transcript  ─────▶│  POST /agent/summarize                        │
                    │  POST /agent/action-items                     │
                    │   -> Assistant (custom_assistants/*.yaml)     │
                    │       -> prompts/templates/*.txt (versioned)  │
                    │       -> llm_client (OpenAI | Anthropic)      │
                    └─────────────────────────────────────────────┘
                              ▲                          │
                              │                          ▼
                    n8n workflow                 Slack / Jira / Notion
                 (automations/n8n/*.json)          (whatever the case
                  business-owned, no code            team already uses)
```

## Layers and why they're separate

**`inference/`** -- ASR only. Knows nothing about prompts, providers, or
business logic. Swappable for a different ASR backend without touching the
agent layer.

**`agents/`** -- the GenAI layer. Three things live here, deliberately kept
as data/config rather than hardcoded Python where possible:
- `llm_client.py`: one `LLMClient` interface, two backends (`OpenAIClient`,
  `AnthropicClient`). Everything downstream calls `.complete(system_prompt,
  user_prompt, json_schema)` and gets back a normalized `LLMResponse` --
  swapping providers is an env var (`LLM_PROVIDER`), not a code change.
- `prompts/templates/*.txt`: Jinja templates, versioned by filename suffix
  (`_v1`, `_v2`). See [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md).
- `custom_assistants/*.yaml`: a "custom GPT" as data -- system prompt,
  allowed tools, guardrails, and which prompt template/schema each task
  uses. `assistant.py` loads one and exposes `run_task(name, **context)`.

**`api/`** -- thin FastAPI routes over the two layers above. No business
logic lives in a route handler; each one composes `inference` and/or
`agents` and returns a typed Pydantic response.

**`automations/n8n/`** -- the actual thing a case team touches. `asrserve`
is the reusable engine behind a stable HTTP contract; n8n is where a
business user wires it into Slack/Jira/whatever without asking an engineer.

## Deployment path (designed, not applied)

`docker/` builds the FastAPI service into a container.
`infra/terraform/` provisions ECS Fargate + ALB + ECR + CloudWatch to run it
on AWS, with CPU target-tracking autoscaling. Secrets (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`) are read from Secrets Manager at task start, never baked
into the image or tfvars. This half of the project is infrastructure-as-code
only -- see the main README's verification status for exactly what has and
hasn't been run in this environment.
