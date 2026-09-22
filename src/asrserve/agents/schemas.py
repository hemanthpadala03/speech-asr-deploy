"""JSON schemas passed to the LLM for structured (tool-call / json_schema) output."""

ACTION_ITEMS_SCHEMA = {
    "type": "object",
    "properties": {
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "owner": {"type": "string"},
                    "due": {"type": ["string", "null"]},
                    "confidence": {"type": "string", "enum": ["high", "low"]},
                },
                "required": ["task", "owner", "due", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["action_items"],
    "additionalProperties": False,
}
