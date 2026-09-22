# Automations

`n8n/meeting_pipeline.workflow.json` is an importable n8n workflow that turns
`asrserve` into a hands-off pipeline for a case team, with no code required
on their side:

```
Webhook (new recording dropped in) 
  -> POST /transcribe            (asrserve: audio -> text)
      -> POST /agent/summarize       (asrserve: text -> 3-5 bullet summary)
      -> POST /agent/action-items    (asrserve: text -> structured tasks)
          -> Slack message to the case team channel
```

## Why n8n and not another Python script

This is deliberately a separate layer from the FastAPI service, not more
Python. A case team's actual ask ("can we get a Slack summary every time a
call gets uploaded") is a *workflow* problem, not a modeling problem -- and
n8n lets a non-engineer on the team see the pipeline as boxes and arrows,
disable a step, add a Notion/Jira node, or change the Slack channel without
filing a ticket. `asrserve` stays the reusable engine (transcription +
LLM extraction) behind a stable HTTP contract; n8n is the glue a business
user can actually own.

## To import

1. In n8n: Workflows -> Import from File -> select `meeting_pipeline.workflow.json`.
2. Set two environment variables in the n8n instance: `ASRSERVE_BASE_URL`
   (e.g. `http://localhost:8000`) and `SLACK_CASE_TEAM_CHANNEL`.
3. Connect a Slack credential to the "Post to Case Team Slack" node.
4. Activate the workflow; the webhook URL n8n generates is what a recording
   tool (e.g. a Zoom/Teams recording webhook, or a simple upload form) posts
   the audio file to.

**Status:** designed and validated as well-formed n8n JSON (`json.load`
round-trips it); not run against a live n8n instance in this environment,
since that would require standing up n8n itself. The HTTP contract it calls
against (`/transcribe`, `/agent/summarize`, `/agent/action-items`) is the
same one covered by `tests/test_api.py`.
