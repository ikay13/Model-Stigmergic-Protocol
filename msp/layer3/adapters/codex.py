"""CodexAdapter: MSP provider adapter for OpenAI Codex CLI.

Wraps `codex exec` as a subprocess. The AgentRound context and instructions
are injected as the prompt. Codex is instructed to respond with the same JSON
schema all MSP adapters use:

  {
    "observations": [{"topic": str, "content": dict, "confidence": float}],
    "needs": [str],
    "reasoning": str
  }
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field

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
class CodexAdapter(ProviderAdapter):
    """MSP adapter for OpenAI Codex CLI.

    Attributes:
        codex_bin: Path to the codex executable (default: "codex").
        model:     Model override passed via --model flag (optional).
        timeout:   Subprocess timeout in seconds.
    """

    codex_bin: str = "codex"
    model: str | None = None
    timeout: int = 120

    @property
    def provider_name(self) -> str:
        return "codex"

    def run_round(self, round_: AgentRound) -> AgentResponse:
        """Run one agent reasoning round via codex exec."""
        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"## Agent Identity\n{round_.uri}\n\n"
            f"## Instructions\n{round_.instructions}\n\n"
            f"## Workspace Context\n{round_.context}"
        )

        cmd = [self.codex_bin, "exec", prompt]
        if self.model:
            cmd += ["--model", self.model]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        raw_text = result.stdout.strip()
        return _parse_response(raw_text)


def _parse_response(raw_text: str) -> AgentResponse:
    """Parse JSON from codex output; degrade gracefully on failure."""
    try:
        data = json.loads(raw_text)
        return AgentResponse(
            observations=data.get("observations", []),
            needs=data.get("needs", []),
            raw_text=raw_text,
        )
    except (json.JSONDecodeError, AttributeError):
        return AgentResponse(observations=[], needs=[], raw_text=raw_text)
