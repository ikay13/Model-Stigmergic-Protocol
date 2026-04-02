"""AgentURI: topology-independent agent identity for MSP.

URI format:  agent://{trust_root}/{capability_path}/{unique_id}

Examples:
  agent://ikay13/planning/architect/claude-opus-01
  agent://ikay13/execution/builder/codex-pro-01
  agent://ikay13/research/gemini-ultra-01

Based on Rodriguez (2026) agent:// URI scheme.
"""
from __future__ import annotations

from dataclasses import dataclass

_SCHEME = "agent://"


@dataclass(frozen=True)
class AgentURI:
    """Immutable agent identity URI."""

    trust_root: str
    capability_path: str
    unique_id: str

    @classmethod
    def parse(cls, uri: str) -> "AgentURI":
        """Parse an agent:// URI string.

        Raises:
            ValueError: if the URI scheme is wrong or has too few segments.
        """
        if not uri.startswith(_SCHEME):
            raise ValueError(
                f"Invalid URI scheme — expected 'agent://', got: {uri!r}"
            )
        remainder = uri[len(_SCHEME):]
        parts = remainder.split("/")
        # Need: trust_root / at-least-one-capability / unique_id  (3+ parts)
        if len(parts) < 3:
            raise ValueError(
                f"URI needs at least 3 path segments "
                f"(trust_root/capability/unique_id), got {len(parts)} segments: {uri!r}"
            )
        trust_root = parts[0]
        unique_id = parts[-1]
        capability_path = "/".join(parts[1:-1])
        return cls(trust_root=trust_root, capability_path=capability_path, unique_id=unique_id)

    def __str__(self) -> str:
        return f"{_SCHEME}{self.trust_root}/{self.capability_path}/{self.unique_id}"

    def capability_parts(self) -> list[str]:
        """Return capability path split by '/'."""
        return self.capability_path.split("/")

    def matches_capability(self, pattern: str) -> bool:
        """Match capability path against a pattern.

        Supports trailing '/*' wildcard:
          "planning/*"  matches "planning/architect", "planning/builder"
          "planning"    matches only "planning"
        """
        if pattern.endswith("/*"):
            prefix = pattern[:-2]
            return (
                self.capability_path == prefix
                or self.capability_path.startswith(prefix + "/")
            )
        return self.capability_path == pattern
