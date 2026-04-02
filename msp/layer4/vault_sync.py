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


# ---------------------------------------------------------------------------
# VaultSync
# ---------------------------------------------------------------------------

@dataclass
class VaultSync:
    """Bidirectional Obsidian vault ↔ markspace sync for MSP Layer 4.

    Attributes:
        vault_root:  Root path of the Obsidian vault.
        mark_space:  Shared MarkSpace instance.
        agent:       Authorized Agent for writing marks.
        scope:       Mark space scope for vault observations (default: "vault").
    """

    vault_root: Path
    mark_space: MarkSpace
    agent: Agent
    scope: str = "vault"

    def import_tagged(self, directory: str, tag: str = "msp") -> int:
        """Import vault pages tagged with `tag` as Observation marks.

        Walks all .md files under `vault_root / directory`, parses frontmatter,
        and writes each page whose tags list includes `tag` as an Observation
        mark with source=EXTERNAL_VERIFIED.

        Args:
            directory: Subdirectory of vault_root to scan (e.g. "MSP").
            tag:       Tag to filter on (default: "msp").

        Returns:
            Number of pages imported.
        """
        scan_dir = self.vault_root / directory
        if not scan_dir.exists():
            return 0

        count = 0
        for md_file in sorted(scan_dir.rglob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            fm, body = _parse_frontmatter(text)
            if not _has_tag(fm, tag):
                continue

            rel_path = str(md_file.relative_to(self.vault_root))
            self.mark_space.write(
                self.agent,
                Observation(
                    scope=self.scope,
                    topic="vault-page",
                    content={"path": rel_path, "text": body},
                    confidence=1.0,
                    source=Source.EXTERNAL_VERIFIED,
                ),
            )
            count += 1

        return count

    def export_observations(self, read_scope: str) -> int:
        """Export Observation marks to vault markdown files.

        Reads all Observation marks from `read_scope` and writes each as a
        markdown file under `vault_root/MSP/agent-output/`. Files are named
        by mark ID so re-running overwrites rather than accumulates.

        Each file gets frontmatter with tags: [msp-agent-output] and a body
        showing the topic, confidence, and content.

        Args:
            read_scope: The mark space scope to read observations from.

        Returns:
            Number of marks exported.
        """
        marks = self.mark_space.read(scope=read_scope, mark_type=None)
        observations = [m for m in marks if isinstance(m, Observation)]

        if not observations:
            return 0

        output_dir = self.vault_root / "MSP" / "agent-output"
        output_dir.mkdir(parents=True, exist_ok=True)

        for obs in observations:
            content_lines = [f"- **{k}:** {v}" for k, v in obs.content.items()]
            body = "\n".join([
                f"# {obs.topic}",
                "",
                f"**Confidence:** {obs.confidence}",
                "",
                "## Content",
                "",
                *content_lines,
            ])
            fm = {
                "tags": ["msp-agent-output"],
                "topic": obs.topic,
                "confidence": obs.confidence,
                "exported_at": datetime.datetime.utcnow().isoformat(),
            }
            fm_text = yaml.dump(fm, default_flow_style=False).strip()
            file_text = f"---\n{fm_text}\n---\n\n{body}\n"

            out_file = output_dir / f"{obs.id}.md"
            out_file.write_text(file_text, encoding="utf-8")

        return len(observations)
