"""Loads a `custom_assistants/*.yaml` config and runs its tasks.

This is the piece that turns the prompt templates + llm_client into
something that behaves like a configured "custom GPT": load a persona once,
run named tasks against it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from asrserve.agents import schemas as schema_module
from asrserve.agents.llm_client import LLMClient, LLMResponse, build_client
from asrserve.agents.prompts.loader import render_prompt

_ASSISTANTS_DIR = Path(__file__).parent / "custom_assistants"


class Assistant:
    def __init__(self, config: dict[str, Any], client: LLMClient | None = None):
        self._config = config
        self._client = client or build_client()

    @classmethod
    def load(cls, name: str, client: LLMClient | None = None) -> "Assistant":
        path = _ASSISTANTS_DIR / f"{name}.yaml"
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(config, client=client)

    def run_task(self, task_name: str, **prompt_context: Any) -> LLMResponse:
        task = self._config["tasks"][task_name]
        schema_name = task.get("schema")
        json_schema = getattr(schema_module, schema_name) if schema_name else None

        user_prompt = render_prompt(task["prompt_template"], **prompt_context)
        return self._client.complete(
            system_prompt=self._config["system_prompt"],
            user_prompt=user_prompt,
            json_schema=json_schema,
        )
