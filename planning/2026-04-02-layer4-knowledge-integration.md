# Layer 4: Knowledge Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MSP's knowledge integration layer: a `VaultSync` class that imports Obsidian vault pages tagged `#msp` into the markspace as `Observation` marks (with `source=EXTERNAL_VERIFIED`), and exports agent `Observation` marks back to the vault as markdown files tagged `#msp-agent-output`.

**Architecture:** `VaultSync` reads `.md` files from the Obsidian vault, parses YAML frontmatter with `pyyaml`, and imports pages whose `tags` list includes `"msp"` as `Observation` marks in a dedicated `"vault"` scope. On export, it reads `Observation` marks from a given markspace scope and writes them as markdown files (with frontmatter) into `MSP/agent-output/` in the vault. Import and export are both on-demand (explicit method calls), not automatic.

**Tech Stack:** Python 3.10+, pyyaml (already in `.venv/`), markspace, pytest, unittest.mock — no new dependencies.

---

## File Map

**Create:**
- `msp/layer4/__init__.py` — package root
- `msp/layer4/vault_sync.py` — `VaultSync`: import (vault → marks) and export (marks → vault)
- `tests/layer4/__init__.py` — empty
- `tests/layer4/test_vault_sync.py` — all Layer 4 tests

**No existing files modified** (additive only).

---

## Verified APIs

### markspace (confirmed working)

```python
from markspace import Agent, MarkSpace, Scope, DecayConfig, Observation, Source

scope = Scope(
    name="vault",
    observation_topics=["*"],
    decay=DecayConfig(
        observation_half_life=3600.0,
        warning_half_life=3600.0,
        intent_ttl=1800.0,
    ),
)
agent = Agent(name="vault-importer", scopes={"vault": ["observation"]})
space = MarkSpace(scopes=[scope])

obs = Observation(
    scope="vault",
    topic="vault-page",
    content={"text": "...", "path": "MSP/test.md"},
    confidence=1.0,
    source=Source.EXTERNAL_VERIFIED,
)
space.write(agent, obs)
marks = space.read(scope="vault", mark_type=None)
# marks[0].content == {"text": "...", "path": "MSP/test.md"}
# marks[0].topic == "vault-page"
# marks[0].confidence == 1.0
```

### pyyaml frontmatter parsing

Vault files use `---` delimited YAML frontmatter:
```markdown
---
tags: [session, msp]
date: 2026-04-02
agent: claude-sonnet-4-6
---

# Body text here
```

Parse pattern (no external library needed beyond pyyaml):
```python
import yaml

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). frontmatter_dict is {} if none."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    return yaml.safe_load(fm_text) or {}, body
```

### Vault path

```python
VAULT_ROOT = Path("/home/orin/Documents/Obsidian Vault")
MSP_DIR = VAULT_ROOT / "MSP"
AGENT_OUTPUT_DIR = MSP_DIR / "agent-output"
```

---

## Task 1: Package Scaffold

**Files:**
- Create: `msp/layer4/__init__.py`
- Create: `tests/layer4/__init__.py`

- [ ] **Step 1: Create init files**

`msp/layer4/__init__.py`:
```python
"""Layer 4: Knowledge Integration — Obsidian vault sync."""

__all__ = ["VaultSync"]


def __getattr__(name: str):
    if name in __all__:
        import importlib
        mod = importlib.import_module("msp.layer4.vault_sync")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

`tests/layer4/__init__.py` — empty file.

- [ ] **Step 2: Verify import works**

```bash
cd /home/orin/Model-Stigmergic-Protocol/.worktrees/layer4-knowledge-integration && source .venv/bin/activate
python -c "import msp.layer4; print('layer4 OK')"
```
Expected: `layer4 OK`

- [ ] **Step 3: Run full suite — confirm no breakage**

```bash
python -m pytest tests/ -q
```
Expected: 358 passed.

- [ ] **Step 4: Commit**

```bash
git add msp/layer4/__init__.py tests/layer4/__init__.py
git commit -m "feat(layer4): scaffold msp/layer4 package"
```

---

## Task 2: Frontmatter Parser

**Files:**
- Create: `msp/layer4/vault_sync.py` (partial — just the parser + `_has_tag` helper)
- Create: `tests/layer4/test_vault_sync.py` (partial — just parser tests)

This task builds the parsing foundation that all later tasks depend on.

- [ ] **Step 1: Write failing tests**

Create `tests/layer4/test_vault_sync.py`:

```python
# tests/layer4/test_vault_sync.py
from msp.layer4.vault_sync import _parse_frontmatter, _has_tag


def test_parse_frontmatter_with_tags():
    """Parses YAML frontmatter and returns body separately."""
    text = "---\ntags: [session, msp]\ndate: 2026-04-02\n---\n\n# Hello\n\nBody text."
    fm, body = _parse_frontmatter(text)
    assert fm["tags"] == ["session", "msp"]
    assert fm["date"].isoformat() == "2026-04-02"
    assert body == "# Hello\n\nBody text."


def test_parse_frontmatter_no_frontmatter():
    """Returns empty dict and full text when no frontmatter present."""
    text = "# Just a heading\n\nNo frontmatter here."
    fm, body = _parse_frontmatter(text)
    assert fm == {}
    assert body == text


def test_parse_frontmatter_empty_frontmatter():
    """Returns empty dict when frontmatter block is empty."""
    text = "---\n---\n\n# Body"
    fm, body = _parse_frontmatter(text)
    assert fm == {}
    assert "# Body" in body


def test_has_tag_true():
    """_has_tag returns True when tag is in frontmatter tags list."""
    fm = {"tags": ["session", "msp", "multi-agent"]}
    assert _has_tag(fm, "msp") is True


def test_has_tag_false():
    """_has_tag returns False when tag is absent."""
    fm = {"tags": ["session", "notes"]}
    assert _has_tag(fm, "msp") is False


def test_has_tag_no_tags_key():
    """_has_tag returns False when frontmatter has no tags key."""
    fm = {"date": "2026-04-02"}
    assert _has_tag(fm, "msp") is False
```

- [ ] **Step 2: Run to verify 6 failures**

```bash
cd /home/orin/Model-Stigmergic-Protocol/.worktrees/layer4-knowledge-integration && source .venv/bin/activate
python -m pytest tests/layer4/test_vault_sync.py -v
```
Expected: 6 failures — `ImportError`.

- [ ] **Step 3: Implement parser in `msp/layer4/vault_sync.py`**

Create `msp/layer4/vault_sync.py`:

```python
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
```

- [ ] **Step 4: Run parser tests — verify 6 pass**

```bash
python -m pytest tests/layer4/test_vault_sync.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest tests/ -q
```
Expected: 364 passed.

- [ ] **Step 6: Commit**

```bash
git add msp/layer4/vault_sync.py tests/layer4/test_vault_sync.py
git commit -m "feat(layer4): add frontmatter parser and tag helper"
```

---

## Task 3: VaultSync Import (vault → marks)

**Files:**
- Modify: `msp/layer4/vault_sync.py` — add `VaultSync` dataclass + `import_tagged` method
- Modify: `tests/layer4/test_vault_sync.py` — append import tests

- [ ] **Step 1: Append import tests to `tests/layer4/test_vault_sync.py`**

Append to the end of the existing file:

```python
# --- VaultSync.import_tagged tests ---

from pathlib import Path
from unittest.mock import MagicMock
from markspace import Agent, MarkSpace, Scope, DecayConfig, Source
from msp.layer4.vault_sync import VaultSync


def _make_vault(tmp_path: Path) -> Path:
    """Create a minimal fake vault for testing."""
    vault = tmp_path / "vault"
    msp_dir = vault / "MSP"
    msp_dir.mkdir(parents=True)

    # Tagged page — should be imported
    (msp_dir / "tagged.md").write_text(
        "---\ntags: [msp, project]\ntitle: Tagged Page\n---\n\n# Tagged\n\nSome content."
    )
    # Untagged page — should be skipped
    (msp_dir / "untagged.md").write_text(
        "---\ntags: [notes]\n---\n\n# Untagged\n\nIgnored."
    )
    # No frontmatter — should be skipped
    (msp_dir / "bare.md").write_text("# No frontmatter\n\nJust text.")
    return vault


def _make_vault_scope_and_agent():
    """Create a minimal MarkSpace with vault scope."""
    scope = Scope(
        name="vault",
        observation_topics=["*"],
        decay=DecayConfig(
            observation_half_life=3600.0,
            warning_half_life=3600.0,
            intent_ttl=1800.0,
        ),
    )
    space = MarkSpace(scopes=[scope])
    agent = Agent(name="vault-importer", scopes={"vault": ["observation"]})
    return space, agent


def test_import_tagged_imports_only_tagged_pages(tmp_path):
    """import_tagged writes only #msp-tagged pages as Observation marks."""
    vault = _make_vault(tmp_path)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    count = syncer.import_tagged(directory="MSP", tag="msp")

    assert count == 1
    marks = space.read(scope="vault", mark_type=None)
    assert len(marks) == 1
    assert marks[0].topic == "vault-page"
    assert marks[0].source == Source.EXTERNAL_VERIFIED
    assert marks[0].confidence == 1.0


def test_import_tagged_content_has_path_and_text(tmp_path):
    """Imported mark content includes the vault-relative path and page body."""
    vault = _make_vault(tmp_path)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    syncer.import_tagged(directory="MSP", tag="msp")

    marks = space.read(scope="vault", mark_type=None)
    content = marks[0].content
    assert "MSP/tagged.md" in content["path"]
    assert "Some content." in content["text"]


def test_import_tagged_returns_count(tmp_path):
    """import_tagged returns the number of pages imported."""
    vault = _make_vault(tmp_path)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    count = syncer.import_tagged(directory="MSP", tag="msp")
    assert count == 1


def test_import_tagged_empty_directory(tmp_path):
    """import_tagged returns 0 when no tagged pages exist."""
    vault = tmp_path / "vault"
    (vault / "MSP").mkdir(parents=True)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    count = syncer.import_tagged(directory="MSP", tag="msp")
    assert count == 0
```

- [ ] **Step 2: Run new tests — verify 4 failures**

```bash
cd /home/orin/Model-Stigmergic-Protocol/.worktrees/layer4-knowledge-integration && source .venv/bin/activate
python -m pytest tests/layer4/test_vault_sync.py -v -k "import"
```
Expected: 4 failures — `ImportError` or `AttributeError` (VaultSync not yet defined).

- [ ] **Step 3: Add `VaultSync` dataclass + `import_tagged` to `msp/layer4/vault_sync.py`**

Append to the end of `msp/layer4/vault_sync.py` (after the `_has_tag` function):

```python

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
```

- [ ] **Step 4: Run import tests — verify 4 pass**

```bash
python -m pytest tests/layer4/test_vault_sync.py -v -k "import"
```
Expected: 4 passed.

- [ ] **Step 5: Run full test file**

```bash
python -m pytest tests/layer4/test_vault_sync.py -v
```
Expected: 10 passed (6 parser + 4 import).

- [ ] **Step 6: Run full suite**

```bash
python -m pytest tests/ -q
```
Expected: 368 passed.

- [ ] **Step 7: Commit**

```bash
git add msp/layer4/vault_sync.py tests/layer4/test_vault_sync.py
git commit -m "feat(layer4): implement VaultSync.import_tagged — vault pages → marks"
```

---

## Task 4: VaultSync Export (marks → vault)

**Files:**
- Modify: `msp/layer4/vault_sync.py` — add `export_observations` method
- Modify: `tests/layer4/test_vault_sync.py` — append export tests

- [ ] **Step 1: Append export tests to `tests/layer4/test_vault_sync.py`**

Append to the end of the existing file:

```python
# --- VaultSync.export_observations tests ---

import yaml as _yaml
from markspace import Observation, Source


def _make_export_space_and_agent():
    """MarkSpace with an 'msp' scope for agent observations."""
    scope = Scope(
        name="msp",
        observation_topics=["*"],
        decay=DecayConfig(
            observation_half_life=3600.0,
            warning_half_life=3600.0,
            intent_ttl=1800.0,
        ),
    )
    space = MarkSpace(scopes=[scope])
    agent = Agent(name="test-agent", scopes={"msp": ["observation"]})
    return space, agent


def _write_observation(space, agent, topic, content, confidence=0.9):
    space.write(
        agent,
        Observation(
            scope="msp",
            topic=topic,
            content=content,
            confidence=confidence,
            source=Source.FLEET,
        ),
    )


def test_export_observations_writes_files(tmp_path):
    """export_observations writes one markdown file per observation."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "on track"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    count = syncer.export_observations(read_scope="msp")

    assert count == 1
    output_files = list((vault / "MSP" / "agent-output").glob("*.md"))
    assert len(output_files) == 1


def test_export_observations_frontmatter_tags(tmp_path):
    """Exported files are tagged with #msp-agent-output."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "ok"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    syncer.export_observations(read_scope="msp")

    output_file = list((vault / "MSP" / "agent-output").glob("*.md"))[0]
    text = output_file.read_text()
    fm, _ = _parse_frontmatter(text)
    assert "msp-agent-output" in fm["tags"]


def test_export_observations_content_in_body(tmp_path):
    """Exported file body contains the observation topic and content."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "on track", "detail": "all good"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    syncer.export_observations(read_scope="msp")

    output_file = list((vault / "MSP" / "agent-output").glob("*.md"))[0]
    body = output_file.read_text()
    assert "progress" in body
    assert "on track" in body


def test_export_observations_overwrites_existing(tmp_path):
    """export_observations overwrites existing files for the same mark id."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "first"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")

    # Export twice — should still be 1 file, 1 count each time
    syncer.export_observations(read_scope="msp")
    syncer.export_observations(read_scope="msp")

    output_files = list((vault / "MSP" / "agent-output").glob("*.md"))
    assert len(output_files) == 1


def test_export_observations_no_marks(tmp_path):
    """export_observations returns 0 when no marks exist."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    count = syncer.export_observations(read_scope="msp")
    assert count == 0
```

- [ ] **Step 2: Run new tests — verify 5 failures**

```bash
cd /home/orin/Model-Stigmergic-Protocol/.worktrees/layer4-knowledge-integration && source .venv/bin/activate
python -m pytest tests/layer4/test_vault_sync.py -v -k "export"
```
Expected: 5 failures — `AttributeError` (export_observations not yet defined).

- [ ] **Step 3: Add `export_observations` to `VaultSync` in `msp/layer4/vault_sync.py`**

Inside the `VaultSync` class (after `import_tagged`), append this method:

```python
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
        observations = [m for m in marks if type(m).__name__ == "Observation"]

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
```

- [ ] **Step 4: Run export tests — verify 5 pass**

```bash
python -m pytest tests/layer4/test_vault_sync.py -v -k "export"
```
Expected: 5 passed.

- [ ] **Step 5: Run full test file**

```bash
python -m pytest tests/layer4/test_vault_sync.py -v
```
Expected: 15 passed (6 parser + 4 import + 5 export).

- [ ] **Step 6: Run full suite**

```bash
python -m pytest tests/ -q
```
Expected: 373 passed.

- [ ] **Step 7: Commit**

```bash
git add msp/layer4/vault_sync.py tests/layer4/test_vault_sync.py
git commit -m "feat(layer4): implement VaultSync.export_observations — marks → vault"
```

---

## Task 5: Final Validation + Push

- [ ] **Step 1: Run full test suite**

```bash
cd /home/orin/Model-Stigmergic-Protocol/.worktrees/layer4-knowledge-integration && source .venv/bin/activate
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```
Expected: 373 passed, 0 failures.

- [ ] **Step 2: Verify end-to-end imports**

```bash
python -c "
from msp.layer4.vault_sync import VaultSync, _parse_frontmatter, _has_tag
from msp.layer1 import MarkSpace, Agent
print('Layer 4 imports OK')
print('Layer 1+4 cross-import OK')
"
```
Expected: both lines printed.

- [ ] **Step 3: Merge to main and push**

```bash
cd /home/orin/Model-Stigmergic-Protocol
git checkout main
git merge --no-ff feature/layer4-knowledge-integration -m "feat(layer4): knowledge integration — VaultSync bidirectional Obsidian vault sync"
git push origin main
```

---

## Summary

After this plan:

| Component | What |
|---|---|
| `msp/layer4/vault_sync.py` | `VaultSync` + `_parse_frontmatter` + `_has_tag` |
| `VaultSync.import_tagged(dir, tag)` | Vault pages tagged `#msp` → `Observation` marks (`EXTERNAL_VERIFIED`) |
| `VaultSync.export_observations(scope)` | `Observation` marks → `MSP/agent-output/*.md` files |

**Test count:** 373 (358 existing + 15 new)
**New dependencies:** none (pyyaml already in `.venv/`)
