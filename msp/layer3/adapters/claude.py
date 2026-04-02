"""ClaudeAdapter: MSP provider adapter for Anthropic Claude.

Uses markspace's existing LLMClient (Layer 1) to call the Anthropic API.
Expects the LLM to respond with a JSON object:

  {
    "observations": [
      {"topic": str, "content": dict, "confidence": float}
    ],
    "needs": [str],
    "reasoning": str
  }

If the LLM returns non-JSON, falls back to AgentResponse with empty
observations/needs and the raw text preserved for debugging.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from markspace.llm import LLMClient, LLMConfig

from msp.layer3.adapter import AgentResponse, AgentRound, ProviderAdapter

_SYSTEM_PROMPT = """\
You are an MSP agent participating in a stigmergic multi-agent coordination system.

Your job:
1. Read the workspace context and current task instructions below.
2. Identify what observations are worth recording for other agents.
3. Identify any questions that need principal (human) input.
4. Respond ONLY with a JSON object in this exact format:

{
  "observations": [
    {"topic": "<string>", "content": {<any JSON>}, "confidence": <0.0-1.0>}
  ],
  "needs": ["<question string>"],
  "reasoning": "<brief explanation of your analysis>"
}

If you have nothing to observe or ask, return empty arrays.
Do NOT include any text outside the JSON object.
"""


@dataclass
class ClaudeAdapter(ProviderAdapter):
    """MSP adapter for Anthropic Claude models.

    Attributes:
        config: LLMConfig pointing to the Anthropic API.
    """

    config: LLMConfig
    _client: LLMClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = LLMClient(self.config)

    @property
    def provider_name(self) -> str:
        return "claude"

    def run_round(self, round_: AgentRound) -> AgentResponse:
        """Run one agent reasoning round via the Anthropic API."""
        user_message = (
            f"## Agent Identity\n{round_.uri}\n\n"
            f"## Instructions\n{round_.instructions}\n\n"
            f"## Workspace Context\n{round_.context}"
        )
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        response = self._client.chat(messages)
        raw_text = response["choices"][0]["message"]["content"]

        return _parse_response(raw_text)

    def close(self) -> None:
        """Release the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "ClaudeAdapter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _parse_response(raw_text: str) -> AgentResponse:
    """Parse JSON from LLM response; degrade gracefully on failure."""
    try:
        data = json.loads(raw_text.strip())
        return AgentResponse(
            observations=data.get("observations", []),
            needs=data.get("needs", []),
            raw_text=raw_text,
        )
    except (json.JSONDecodeError, AttributeError):
        return AgentResponse(observations=[], needs=[], raw_text=raw_text)
