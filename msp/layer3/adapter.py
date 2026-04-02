"""Abstract provider adapter interface for MSP Layer 3.

Defines the contract any LLM provider must satisfy to participate in an
MSP agent fleet. Each provider adapter wraps one LLM backend and translates
between MSP's coordination model and the provider's native API.

AgentRound  — input to one reasoning round (context + identity + instructions)
AgentResponse — output (observations to write + needs to escalate + raw text)
ProviderAdapter — abstract base class all adapters implement
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from msp.layer3.identity import AgentURI


@dataclass
class AgentRound:
    """Input to a provider for one reasoning round.

    Attributes:
        context:      Assembled text from ContextLoader (Layer 2 output).
        uri:          The agent's identity URI.
        instructions: System-level task instructions for this round.
    """

    context: str
    uri: AgentURI
    instructions: str


@dataclass
class AgentResponse:
    """Output from a provider after one reasoning round.

    Attributes:
        observations: List of observation mark payloads the agent wants written.
                      Each dict must have "topic" (str), "content" (dict),
                      and "confidence" (float 0-1).
        needs:        List of question strings for the principal.
        raw_text:     Raw LLM output for debugging and audit.
    """

    observations: list[dict] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    raw_text: str = ""


class ProviderAdapter(ABC):
    """Abstract base class for MSP provider adapters.

    Implement one subclass per LLM provider (Claude, Codex, Gemini, etc.).
    The adapter is responsible for:
    1. Formatting AgentRound into the provider's native request format.
    2. Calling the provider API.
    3. Parsing the response into AgentResponse.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name (e.g. "claude", "codex", "gemini")."""
        ...

    @abstractmethod
    def run_round(self, round_: AgentRound) -> AgentResponse:
        """Execute one agent reasoning round and return the response."""
        ...
