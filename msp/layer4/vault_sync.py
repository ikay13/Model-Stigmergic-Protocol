"""VaultSync: bidirectional Obsidian vault ↔ markspace integration for MSP Layer 4.

Import: vault pages tagged #msp → Observation marks (source=EXTERNAL_VERIFIED)
Export: Observation marks → vault markdown files tagged #msp-agent-output

Both directions are on-demand (explicit method calls, not automatic).
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from markspace import Agent, MarkSpace, Observation, Source
from msp.layer3.identity import AgentURI


# ---------------------------------------------------------------------------
# Frontmatter helpers (module-level, used by VaultSync and tests)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown string.

    Returns:
        (frontmatter_dict, body_text)
        frontmatter_dict is {} if no valid frontmatter block found.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    return yaml.safe_load(fm_text) or {}, body


def _has_tag(frontmatter: dict, tag: str) -> bool:
    """Return True if tag is present in frontmatter's tags list."""
    tags = frontmatter.get("tags", [])
    return tag in tags
