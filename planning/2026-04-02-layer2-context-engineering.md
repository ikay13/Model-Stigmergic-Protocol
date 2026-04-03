# Layer 2: Context Engineering Infrastructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MSP's filesystem-based context engineering infrastructure — a 5-layer ICM-inspired hierarchy with OpenViking-style tiered context loading, implemented as a Python module and workspace template.

**Architecture:** ICM's 5 layers (CLAUDE.md → CONTEXT.md → stage CONTEXT.md → references → artifacts) map MSP agents to the right context at the right time. OpenViking's L0/L1/L2 pattern (abstract/overview/full) reduces token cost by loading only what's needed. A `context_loader.py` module reads the filesystem and delivers budget-aware context to any markspace agent.

**Tech Stack:** Python 3.10+, pydantic, pytest, hypothesis — same stack as markspace. Virtual env at `.venv/`.

---

## File Map

**Create:**
- `msp/__init__.py` — package root
- `msp/layer2/__init__.py`
- `msp/layer2/workspace.py` — workspace discovery and navigation
- `msp/layer2/context_loader.py` — 5-layer context loading with token budgets
- `msp/layer2/stage.py` — stage contract parsing and validation
- `msp/layer2/tier.py` — L0/L1/L2 tiered content (.abstract, .overview, full)
- `msp/templates/workspace/CLAUDE.md` — Layer 0 template
- `msp/templates/workspace/CONTEXT.md` — Layer 1 routing template
- `msp/templates/workspace/stages/01-example/CONTEXT.md` — Layer 2 stage contract template
- `msp/templates/workspace/stages/01-example/references/.gitkeep`
- `msp/templates/workspace/stages/01-example/output/.gitkeep`
- `msp/templates/workspace/_config/.gitkeep`
- `msp/workspaces/msp-development/CLAUDE.md` — actual MSP workspace Layer 0
- `msp/workspaces/msp-development/CONTEXT.md` — actual MSP workspace routing
- `tests/layer2/__init__.py`
- `tests/layer2/test_workspace.py`
- `tests/layer2/test_context_loader.py`
- `tests/layer2/test_stage.py`
- `tests/layer2/test_tier.py`

**Modify:**
- `pyproject.toml` — add `msp` package

---

## Task 1: Package Scaffold

**Files:**
- Create: `msp/__init__.py`
- Create: `msp/layer2/__init__.py`
- Create: `tests/layer2/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create package init files**

```python
# msp/__init__.py
"""Model Stigmergic Protocol — Python implementation."""

__version__ = "0.1.0"
```

```python
# msp/layer2/__init__.py
"""Layer 2: Context Engineering Infrastructure."""

from msp.layer2.workspace import Workspace
from msp.layer2.context_loader import ContextLoader
from msp.layer2.stage import StageContract
from msp.layer2.tier import TieredContent

__all__ = ["Workspace", "ContextLoader", "StageContract", "TieredContent"]
```

```python
# tests/layer2/__init__.py
```

- [ ] **Step 2: Update pyproject.toml to include msp package**

Add to `[tool.hatch.build.targets.wheel]`:
```toml
packages = ["markspace", "msp"]
```

Add to `[project]` dependencies:
```toml
dependencies = [
    "pydantic>=2.0,<3.0",
    "httpx>=0.24,<1.0",
    "python-dotenv>=1.0,<2.0",
]
```

- [ ] **Step 3: Install in venv**

```bash
source .venv/bin/activate && pip install -e .
```

Expected: Successfully installed markspace-... in editable mode.

- [ ] **Step 4: Commit**

```bash
git add msp/ tests/layer2/ pyproject.toml
git commit -m "feat(layer2): scaffold msp package"
```

---

## Task 2: Tiered Content (L0/L1/L2)

**Files:**
- Create: `msp/layer2/tier.py`
- Create: `tests/layer2/test_tier.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/layer2/test_tier.py
from pathlib import Path
import pytest
from msp.layer2.tier import TieredContent

def test_l0_loads_abstract_file(tmp_path):
    """L0 loads .abstract file when present."""
    doc = tmp_path / "guide.md"
    doc.write_text("# Full content — many lines of detail")
    abstract = tmp_path / ".abstract"
    abstract.write_text("One-sentence summary of the guide.")

    tc = TieredContent(doc)
    assert tc.l0() == "One-sentence summary of the guide."

def test_l0_falls_back_to_first_line(tmp_path):
    """L0 falls back to first non-empty line if no .abstract exists."""
    doc = tmp_path / "guide.md"
    doc.write_text("# Guide Title\nMore content below.")

    tc = TieredContent(doc)
    assert tc.l0() == "# Guide Title"

def test_l1_loads_overview_file(tmp_path):
    """L1 loads .overview file when present."""
    doc = tmp_path / "guide.md"
    doc.write_text("# Full content")
    overview = tmp_path / ".overview"
    overview.write_text("## Overview\nKey points here.")

    tc = TieredContent(doc)
    assert tc.l1() == "## Overview\nKey points here."

def test_l1_falls_back_to_full_content_under_2k(tmp_path):
    """L1 returns full content when no .overview and content is under 2k tokens."""
    doc = tmp_path / "guide.md"
    doc.write_text("Short content.")

    tc = TieredContent(doc)
    assert tc.l1() == "Short content."

def test_l2_always_returns_full_content(tmp_path):
    """L2 always returns full file content."""
    doc = tmp_path / "guide.md"
    doc.write_text("# Full\nAll content here.")

    tc = TieredContent(doc)
    assert tc.l2() == "# Full\nAll content here."

def test_token_estimate(tmp_path):
    """Token estimate is approximately len/4."""
    doc = tmp_path / "guide.md"
    doc.write_text("a" * 400)
    tc = TieredContent(doc)
    assert tc.token_estimate(doc.read_text()) == 100
```

- [ ] **Step 2: Run to verify failure**

```bash
source .venv/bin/activate && python -m pytest tests/layer2/test_tier.py -v
```

Expected: 6 failures — `ImportError: cannot import name 'TieredContent'`

- [ ] **Step 3: Implement TieredContent**

```python
# msp/layer2/tier.py
"""L0/L1/L2 tiered content loading for filesystem resources.

Inspired by OpenViking's .abstract/.overview hidden file pattern.
L0: ~100 tokens — quick relevance check
L1: ~2k tokens  — structure and key points
L2: full content — deep read when necessary
"""
from pathlib import Path


class TieredContent:
    """Provides L0/L1/L2 access to a file's content."""

    TOKENS_PER_CHAR = 0.25  # approximation: 1 token ≈ 4 chars

    def __init__(self, path: Path) -> None:
        self.path = path

    def l0(self) -> str:
        """Abstract: one-sentence summary (~100 tokens)."""
        abstract = self.path.parent / ".abstract"
        if abstract.exists():
            return abstract.read_text().strip()
        # fall back: first non-empty line of the file
        for line in self.path.read_text().splitlines():
            if line.strip():
                return line.strip()
        return ""

    def l1(self) -> str:
        """Overview: core information (~2k tokens)."""
        overview = self.path.parent / ".overview"
        if overview.exists():
            return overview.read_text().strip()
        # fall back: full content if under 2k tokens
        content = self.path.read_text()
        if self.token_estimate(content) <= 2000:
            return content
        # truncate to ~2k tokens
        limit = int(2000 / self.TOKENS_PER_CHAR)
        return content[:limit]

    def l2(self) -> str:
        """Full content — load only when necessary."""
        return self.path.read_text()

    def token_estimate(self, text: str) -> int:
        """Approximate token count (1 token ≈ 4 chars)."""
        return int(len(text) * self.TOKENS_PER_CHAR)
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python -m pytest tests/layer2/test_tier.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add msp/layer2/tier.py tests/layer2/test_tier.py
git commit -m "feat(layer2): implement L0/L1/L2 tiered content loading"
```

---

## Task 3: Stage Contract

**Files:**
- Create: `msp/layer2/stage.py`
- Create: `tests/layer2/test_stage.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/layer2/test_stage.py
from pathlib import Path
import pytest
from msp.layer2.stage import StageContract, StageInput, StageOutput

VALID_CONTEXT = """\
## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Previous stage | ../01-research/output/notes.md | Full file | Source material |
| Style guide | ../../_config/voice.md | Voice Rules section | Tone guidance |

## Process

1. Read inputs
2. Produce output

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Script | output/script.md | Markdown |
"""

def test_parse_inputs(tmp_path):
    """Parses Inputs table into StageInput list."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert len(contract.inputs) == 2
    assert contract.inputs[0].source == "Previous stage"
    assert contract.inputs[0].location == "../01-research/output/notes.md"

def test_parse_outputs(tmp_path):
    """Parses Outputs table into StageOutput list."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert len(contract.outputs) == 1
    assert contract.outputs[0].artifact == "Script"
    assert contract.outputs[0].location == "output/script.md"

def test_parse_process(tmp_path):
    """Parses Process section into list of steps."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert len(contract.process_steps) == 2
    assert contract.process_steps[0] == "Read inputs"

def test_missing_section_raises(tmp_path):
    """Raises ValueError if required section is missing."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text("## Process\n1. Only process, no inputs or outputs")
    with pytest.raises(ValueError, match="Inputs"):
        StageContract.from_file(ctx)

def test_context_under_500_tokens(tmp_path):
    """A well-formed CONTEXT.md stays within the 500 token budget."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert contract.token_estimate() <= 500
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/layer2/test_stage.py -v
```

Expected: 5 failures — `ImportError`

- [ ] **Step 3: Implement StageContract**

```python
# msp/layer2/stage.py
"""Stage contract parsing from ICM-style CONTEXT.md files.

Each stage defines a contract with three sections:
  Inputs  — what to load and from where
  Process — ordered steps to execute
  Outputs — artifacts to produce and where

CONTEXT.md files must stay under 500 tokens (ICM: ~80 lines max).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StageInput:
    source: str
    location: str
    scope: str
    why: str


@dataclass
class StageOutput:
    artifact: str
    location: str
    format: str


@dataclass
class StageContract:
    path: Path
    inputs: list[StageInput] = field(default_factory=list)
    process_steps: list[str] = field(default_factory=list)
    outputs: list[StageOutput] = field(default_factory=list)

    TOKENS_PER_CHAR = 0.25

    @classmethod
    def from_file(cls, path: Path) -> "StageContract":
        text = path.read_text()
        contract = cls(path=path)
        contract.inputs = _parse_inputs(text)
        contract.process_steps = _parse_process(text)
        contract.outputs = _parse_outputs(text)
        return contract

    def token_estimate(self) -> int:
        return int(len(self.path.read_text()) * self.TOKENS_PER_CHAR)


def _extract_section(text: str, name: str) -> str:
    pattern = rf"##\s+{name}\s*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise ValueError(f"Missing required section: {name}")
    return match.group(1).strip()


def _parse_table_rows(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        if line.startswith("|") and not re.match(r"\|[-\s|]+\|", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] not in ("Source", "Artifact"):  # skip header
                rows.append(cells)
    return rows


def _parse_inputs(text: str) -> list[StageInput]:
    section = _extract_section(text, "Inputs")
    return [
        StageInput(source=r[0], location=r[1], scope=r[2], why=r[3])
        for r in _parse_table_rows(section)
        if len(r) >= 4
    ]


def _parse_outputs(text: str) -> list[StageOutput]:
    section = _extract_section(text, "Outputs")
    return [
        StageOutput(artifact=r[0], location=r[1], format=r[2])
        for r in _parse_table_rows(section)
        if len(r) >= 3
    ]


def _parse_process(text: str) -> list[str]:
    section = _extract_section(text, "Process")
    steps = []
    for line in section.splitlines():
        match = re.match(r"^\d+\.\s+(.+)", line)
        if match:
            steps.append(match.group(1).strip())
    return steps
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python -m pytest tests/layer2/test_stage.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add msp/layer2/stage.py tests/layer2/test_stage.py
git commit -m "feat(layer2): implement ICM stage contract parsing"
```

---

## Task 4: Workspace Navigator

**Files:**
- Create: `msp/layer2/workspace.py`
- Create: `tests/layer2/test_workspace.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/layer2/test_workspace.py
from pathlib import Path
import pytest
from msp.layer2.workspace import Workspace


def _make_workspace(tmp_path: Path) -> Path:
    """Create a minimal ICM workspace for testing."""
    root = tmp_path / "my-workspace"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Workspace\n\n## Folder Map\n")
    (root / "CONTEXT.md").write_text(
        "## Inputs\n| Source | File/Location | Section/Scope | Why |\n"
        "|--------|--------------|---------------|-----|\n\n"
        "## Process\n1. Route task\n\n"
        "## Outputs\n| Artifact | Location | Format |\n|----------|----------|--------|\n"
    )
    stage = root / "stages" / "01-research"
    stage.mkdir(parents=True)
    (stage / "CONTEXT.md").write_text(
        "## Inputs\n| Source | File/Location | Section/Scope | Why |\n"
        "|--------|--------------|---------------|-----|\n\n"
        "## Process\n1. Research\n\n"
        "## Outputs\n| Artifact | Location | Format |\n|----------|----------|--------|\n"
        "| Notes | output/notes.md | Markdown |\n"
    )
    (stage / "output").mkdir()
    return root


def test_discover_stages(tmp_path):
    """Discovers numbered stage directories."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    stages = ws.stages()
    assert len(stages) == 1
    assert stages[0].name == "01-research"


def test_layer0_is_claude_md(tmp_path):
    """Layer 0 returns CLAUDE.md content."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    assert "# Workspace" in ws.layer0()


def test_layer1_is_root_context(tmp_path):
    """Layer 1 returns root CONTEXT.md content."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    assert "Route task" in ws.layer1()


def test_stage_contract(tmp_path):
    """Returns parsed StageContract for a named stage."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    contract = ws.stage_contract("01-research")
    assert contract.process_steps == ["Research"]


def test_stage_complete_when_output_exists(tmp_path):
    """Stage is complete when output/ has non-gitkeep files."""
    root = _make_workspace(tmp_path)
    output = root / "stages" / "01-research" / "output"
    (output / "notes.md").write_text("Research notes.")
    ws = Workspace(root)
    assert ws.stage_complete("01-research") is True


def test_stage_pending_when_output_empty(tmp_path):
    """Stage is pending when output/ is empty."""
    root = _make_workspace(tmp_path)
    ws = Workspace(root)
    assert ws.stage_complete("01-research") is False


def test_invalid_workspace_raises(tmp_path):
    """Raises ValueError if root lacks CLAUDE.md."""
    ws = Workspace(tmp_path)
    with pytest.raises(ValueError, match="CLAUDE.md"):
        ws.layer0()
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/layer2/test_workspace.py -v
```

Expected: 7 failures — `ImportError`

- [ ] **Step 3: Implement Workspace**

```python
# msp/layer2/workspace.py
"""Workspace discovery and navigation for ICM-structured directories.

A workspace is a folder containing:
  CLAUDE.md   — Layer 0: always-loaded identity (~800 tokens)
  CONTEXT.md  — Layer 1: task routing (~300 tokens)
  stages/     — numbered stage folders (01-name, 02-name, ...)
  _config/    — Layer 3: stable reference material
"""
from __future__ import annotations

import re
from pathlib import Path

from msp.layer2.stage import StageContract


class Workspace:
    """Navigate an ICM workspace filesystem."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def layer0(self) -> str:
        """Layer 0: CLAUDE.md content."""
        path = self.root / "CLAUDE.md"
        if not path.exists():
            raise ValueError(f"CLAUDE.md not found in {self.root}")
        return path.read_text()

    def layer1(self) -> str:
        """Layer 1: root CONTEXT.md content."""
        path = self.root / "CONTEXT.md"
        if not path.exists():
            raise ValueError(f"CONTEXT.md not found in {self.root}")
        return path.read_text()

    def stages(self) -> list[Path]:
        """Return numbered stage directories in order."""
        stages_dir = self.root / "stages"
        if not stages_dir.exists():
            return []
        return sorted(
            (p for p in stages_dir.iterdir()
             if p.is_dir() and re.match(r"^\d+", p.name)),
            key=lambda p: p.name,
        )

    def stage_contract(self, stage_name: str) -> StageContract:
        """Parse and return the StageContract for a named stage."""
        context = self.root / "stages" / stage_name / "CONTEXT.md"
        if not context.exists():
            raise ValueError(f"CONTEXT.md not found for stage: {stage_name}")
        return StageContract.from_file(context)

    def stage_complete(self, stage_name: str) -> bool:
        """True if the stage output/ folder contains non-gitkeep files."""
        output = self.root / "stages" / stage_name / "output"
        if not output.exists():
            return False
        files = [f for f in output.iterdir()
                 if f.is_file() and f.name != ".gitkeep"]
        return len(files) > 0

    def status(self) -> str:
        """ASCII pipeline status — mirrors ICM's `status` trigger."""
        lines = [f"Pipeline Status: {self.root.name}", ""]
        for stage in self.stages():
            marker = "COMPLETE" if self.stage_complete(stage.name) else "PENDING"
            lines.append(f"  [{stage.name}]  {marker}")
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python -m pytest tests/layer2/test_workspace.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add msp/layer2/workspace.py tests/layer2/test_workspace.py
git commit -m "feat(layer2): implement ICM workspace navigator"
```

---

## Task 5: Context Loader

**Files:**
- Create: `msp/layer2/context_loader.py`
- Create: `tests/layer2/test_context_loader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/layer2/test_context_loader.py
from pathlib import Path
import pytest
from msp.layer2.context_loader import ContextLoader, ContextBundle
from tests.layer2.test_workspace import _make_workspace


def test_load_returns_bundle(tmp_path):
    """load() returns a ContextBundle with all layers."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load(stage="01-research")
    assert isinstance(bundle, ContextBundle)
    assert bundle.layer0 != ""
    assert bundle.layer1 != ""
    assert bundle.layer2 is not None


def test_bundle_respects_token_budget(tmp_path):
    """ContextBundle total token estimate respects budget."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load(stage="01-research", token_budget=2000)
    assert bundle.total_tokens() <= 2000


def test_no_stage_loads_layers_0_and_1_only(tmp_path):
    """Without stage, loads only Layer 0 and 1."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load()
    assert bundle.layer0 != ""
    assert bundle.layer1 != ""
    assert bundle.layer2 is None


def test_bundle_as_text(tmp_path):
    """as_text() concatenates layers with separators."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    bundle = loader.load(stage="01-research")
    text = bundle.as_text()
    assert "---" in text
    assert "# Workspace" in text


def test_missing_stage_raises(tmp_path):
    """Raises ValueError for unknown stage name."""
    root = _make_workspace(tmp_path)
    loader = ContextLoader(root)
    with pytest.raises(ValueError, match="Stage not found"):
        loader.load(stage="99-nonexistent")
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/layer2/test_context_loader.py -v
```

Expected: 5 failures — `ImportError`

- [ ] **Step 3: Implement ContextLoader**

```python
# msp/layer2/context_loader.py
"""Budget-aware context loader for MSP agents.

Loads the right context at the right time using the ICM 5-layer hierarchy.
Respects markspace token budget properties (P59-P63).

Layer 0 (~800t)  : always loaded — workspace identity
Layer 1 (~300t)  : always loaded — routing table
Layer 2 (~500t)  : loaded per stage — stage contract
Layer 3 (varies) : loaded selectively — reference material
Layer 4 (varies) : loaded selectively — working artifacts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from msp.layer2.stage import StageContract
from msp.layer2.workspace import Workspace


@dataclass
class ContextBundle:
    """Assembled context for one agent round."""
    layer0: str = ""
    layer1: str = ""
    layer2: StageContract | None = None
    references: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    TOKENS_PER_CHAR = 0.25

    def _estimate(self, text: str) -> int:
        return int(len(text) * self.TOKENS_PER_CHAR)

    def total_tokens(self) -> int:
        total = self._estimate(self.layer0) + self._estimate(self.layer1)
        if self.layer2:
            total += self.layer2.token_estimate()
        total += sum(self._estimate(r) for r in self.references)
        total += sum(self._estimate(a) for a in self.artifacts)
        return total

    def as_text(self) -> str:
        parts = []
        if self.layer0:
            parts.append(self.layer0)
        if self.layer1:
            parts.append(self.layer1)
        if self.layer2:
            parts.append(self.layer2.path.read_text())
        parts.extend(self.references)
        parts.extend(self.artifacts)
        return "\n\n---\n\n".join(parts)


class ContextLoader:
    """Loads MSP agent context from an ICM workspace."""

    def __init__(self, root: Path) -> None:
        self.workspace = Workspace(root)

    def load(
        self,
        stage: str | None = None,
        token_budget: int = 8000,
    ) -> ContextBundle:
        """Load context for an agent round.

        Args:
            stage: stage name (e.g. "01-research"). None = routing only.
            token_budget: max tokens to deliver (maps to markspace P61).
        """
        bundle = ContextBundle()

        # Layer 0 — always load
        bundle.layer0 = self.workspace.layer0()

        # Layer 1 — always load
        bundle.layer1 = self.workspace.layer1()

        if stage is not None:
            # Validate stage exists
            stage_names = [s.name for s in self.workspace.stages()]
            if stage not in stage_names:
                raise ValueError(f"Stage not found: {stage}")

            # Layer 2 — stage contract
            bundle.layer2 = self.workspace.stage_contract(stage)

            # Layer 3 + 4 — load from inputs table if budget allows
            remaining = token_budget - bundle.total_tokens()
            if remaining > 0 and bundle.layer2:
                self._load_inputs(bundle, stage, remaining)

        return bundle

    def _load_inputs(
        self, bundle: ContextBundle, stage: str, budget: int
    ) -> None:
        """Load Layer 3/4 inputs declared in the stage contract."""
        TOKENS_PER_CHAR = 0.25
        stage_path = self.workspace.root / "stages" / stage
        used = 0

        for inp in bundle.layer2.inputs:
            target = (stage_path / inp.location).resolve()
            if not target.exists():
                continue
            content = target.read_text()
            cost = int(len(content) * TOKENS_PER_CHAR)
            if used + cost > budget:
                break
            # Classify as Layer 3 (references/) or Layer 4 (output/)
            if "output" in inp.location:
                bundle.artifacts.append(content)
            else:
                bundle.references.append(content)
            used += cost
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python -m pytest tests/layer2/test_context_loader.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Run full test suite — verify nothing broken**

```bash
python -m pytest tests/ -v
```

Expected: all layer2 tests + all original 312 markspace tests pass.

- [ ] **Step 6: Commit**

```bash
git add msp/layer2/context_loader.py tests/layer2/test_context_loader.py
git commit -m "feat(layer2): implement budget-aware context loader"
```

---

## Task 6: Workspace Template

**Files:**
- Create: `msp/templates/workspace/CLAUDE.md`
- Create: `msp/templates/workspace/CONTEXT.md`
- Create: `msp/templates/workspace/stages/01-example/CONTEXT.md`
- Create: `msp/templates/workspace/stages/01-example/references/.gitkeep`
- Create: `msp/templates/workspace/stages/01-example/output/.gitkeep`
- Create: `msp/templates/workspace/_config/.gitkeep`

- [ ] **Step 1: Create Layer 0 template (CLAUDE.md)**

```bash
mkdir -p msp/templates/workspace/stages/01-example/references
mkdir -p msp/templates/workspace/stages/01-example/output
mkdir -p msp/templates/workspace/_config
```

`msp/templates/workspace/CLAUDE.md`:
```markdown
# {{WORKSPACE_NAME}}

{{WORKSPACE_DESCRIPTION}}

## Folder Map

```
{{WORKSPACE_NAME}}/
├── CLAUDE.md              (Layer 0: workspace identity — always loaded)
├── CONTEXT.md             (Layer 1: task routing)
├── stages/
│   ├── 01-{{STAGE_NAME}}/
│   │   ├── CONTEXT.md     (Layer 2: stage contract)
│   │   ├── references/    (Layer 3: stable reference material)
│   │   └── output/        (Layer 4: working artifacts)
└── _config/               (Layer 3: cross-stage configuration)
```

## Routing

| You want to... | Go to |
|----------------|-------|
| Start stage 01 | `stages/01-{{STAGE_NAME}}/CONTEXT.md` |

## Triggers

| Keyword | Action |
|---------|--------|
| `setup` | Onboarding questionnaire |
| `status` | Show pipeline completion |
```

- [ ] **Step 2: Create Layer 1 template (CONTEXT.md)**

`msp/templates/workspace/CONTEXT.md`:
```markdown
# {{WORKSPACE_NAME}} — Task Routing

Read this file first. It tells you where to go.

## Task Routing

| Task | Stage | Go to |
|------|-------|-------|
| {{TASK_1}} | 01-{{STAGE_NAME}} | `stages/01-{{STAGE_NAME}}/CONTEXT.md` |

## Pipeline Status

Run `status` to see which stages are complete.
```

- [ ] **Step 3: Create Layer 2 template (stage CONTEXT.md)**

`msp/templates/workspace/stages/01-example/CONTEXT.md`:
```markdown
# Stage 01: {{STAGE_NAME}}

{{STAGE_DESCRIPTION}}

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Config | ../../_config/{{CONFIG_FILE}}.md | Full file | {{WHY}} |

## Process

1. Read inputs
2. {{PROCESS_STEP_2}}
3. Run audit checks (see below)
4. Write to output/

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| {{ARTIFACT_NAME}} | output/{{ARTIFACT_FILE}}.md | Markdown |

## Audit

| Check | Pass Condition |
|-------|---------------|
| {{CHECK_NAME}} | {{PASS_CONDITION}} |
```

- [ ] **Step 4: Add .gitkeep files**

```bash
touch msp/templates/workspace/stages/01-example/references/.gitkeep
touch msp/templates/workspace/stages/01-example/output/.gitkeep
touch msp/templates/workspace/_config/.gitkeep
```

- [ ] **Step 5: Commit**

```bash
git add msp/templates/
git commit -m "feat(layer2): add ICM workspace template"
```

---

## Task 7: MSP Development Workspace

Create the actual MSP project workspace using the template.

**Files:**
- Create: `msp/workspaces/msp-development/CLAUDE.md`
- Create: `msp/workspaces/msp-development/CONTEXT.md`
- Create: `msp/workspaces/msp-development/stages/01-coordination-core/CONTEXT.md`
- Create: `msp/workspaces/msp-development/stages/02-context-layer/CONTEXT.md`
- Create: `msp/workspaces/msp-development/stages/03-multi-provider/CONTEXT.md`
- Create: `msp/workspaces/msp-development/stages/04-knowledge-layer/CONTEXT.md`

- [ ] **Step 1: Create workspace directories**

```bash
mkdir -p msp/workspaces/msp-development/stages/01-coordination-core/{references,output}
mkdir -p msp/workspaces/msp-development/stages/02-context-layer/{references,output}
mkdir -p msp/workspaces/msp-development/stages/03-multi-provider/{references,output}
mkdir -p msp/workspaces/msp-development/stages/04-knowledge-layer/{references,output}
mkdir -p msp/workspaces/msp-development/_config
```

- [ ] **Step 2: Create CLAUDE.md (Layer 0)**

`msp/workspaces/msp-development/CLAUDE.md`:
```markdown
# MSP Development Workspace

Build the Model Stigmergic Protocol infrastructure layer by layer.

## Folder Map

```
msp-development/
├── CLAUDE.md                          (Layer 0: always loaded)
├── CONTEXT.md                         (Layer 1: task routing)
├── stages/
│   ├── 01-coordination-core/          (markspace + signal field + ECS)
│   ├── 02-context-layer/              (this workspace — filesystem context)
│   ├── 03-multi-provider/             (agent:// identity + adapters)
│   └── 04-knowledge-layer/            (Obsidian + memboot integration)
└── _config/
    ├── architecture.md                (links to planning/ARCHITECTURE.md)
    └── candidates.md                  (links to ~/workshop/candidates/)
```

## Routing

| You want to... | Go to |
|----------------|-------|
| Work on coordination core | `stages/01-coordination-core/CONTEXT.md` |
| Work on context layer (current) | `stages/02-context-layer/CONTEXT.md` |
| Work on multi-provider | `stages/03-multi-provider/CONTEXT.md` |
| Work on knowledge layer | `stages/04-knowledge-layer/CONTEXT.md` |

## Triggers

| Keyword | Action |
|---------|--------|
| `status` | Show pipeline completion across all 4 stages |
```

- [ ] **Step 3: Create CONTEXT.md (Layer 1)**

`msp/workspaces/msp-development/CONTEXT.md`:
```markdown
# MSP Development — Task Routing

## Active Stage

**Stage 02: Context Layer** — currently in progress.

## Implementation Order

| Stage | Name | Status |
|-------|------|--------|
| 01 | Coordination Core | ✅ markspace validated (312/312 tests) |
| 02 | Context Layer | 🔨 In progress |
| 03 | Multi-Provider | Pending |
| 04 | Knowledge Layer | Pending |

## Key References

| Resource | Location | What it covers |
|----------|----------|----------------|
| Architecture | `../../planning/ARCHITECTURE.md` | Full 5-layer design + candidate map |
| Candidate Inventory | `../../planning/CANDIDATES.md` | 29 evaluated projects |
| markspace spec | `../../docs/spec.md` | 66 formal properties |
```

- [ ] **Step 4: Create stage 02 contract (Layer 2)**

`msp/workspaces/msp-development/stages/02-context-layer/CONTEXT.md`:
```markdown
# Stage 02: Context Layer

Build the ICM-inspired filesystem context hierarchy — the `msp/layer2/` Python module.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Architecture | ../../../planning/ARCHITECTURE.md | Layer 2 section | Design spec |
| ICM conventions | ../../../../workshop/candidates/Interpreted-Context-Methdology/_core/CONVENTIONS.md | Full file | Patterns to follow |
| markspace spec | ../../../docs/spec.md | Section 9.10 Token Budgets | Budget integration |

## Process

1. Implement `msp/layer2/tier.py` (L0/L1/L2 tiered content)
2. Implement `msp/layer2/stage.py` (stage contract parsing)
3. Implement `msp/layer2/workspace.py` (workspace navigation)
4. Implement `msp/layer2/context_loader.py` (budget-aware loading)
5. Create workspace template in `msp/templates/workspace/`
6. Create MSP development workspace in `msp/workspaces/msp-development/`
7. Run full test suite — verify 312 + new tests pass

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Layer 2 module | msp/layer2/ | Python package |
| Workspace template | msp/templates/workspace/ | Markdown files |
| MSP workspace | msp/workspaces/msp-development/ | ICM workspace |
| Tests | tests/layer2/ | pytest |

## Audit

| Check | Pass Condition |
|-------|---------------|
| All tests pass | `pytest tests/ -v` shows 0 failures |
| CONTEXT.md files under 80 lines | `wc -l` on each CONTEXT.md ≤ 80 |
| Token budget respected | `ContextLoader.load(budget=8000).total_tokens() <= 8000` |
| No circular references | Stage folders only reference parent `_config/` or sibling `output/` |
```

- [ ] **Step 5: Add .gitkeep files**

```bash
touch msp/workspaces/msp-development/stages/01-coordination-core/output/.gitkeep
touch msp/workspaces/msp-development/stages/01-coordination-core/references/.gitkeep
touch msp/workspaces/msp-development/stages/02-context-layer/references/.gitkeep
touch msp/workspaces/msp-development/stages/03-multi-provider/output/.gitkeep
touch msp/workspaces/msp-development/stages/03-multi-provider/references/.gitkeep
touch msp/workspaces/msp-development/stages/04-knowledge-layer/output/.gitkeep
touch msp/workspaces/msp-development/stages/04-knowledge-layer/references/.gitkeep
touch msp/workspaces/msp-development/_config/.gitkeep
```

- [ ] **Step 6: Mark stage 02 as complete with output**

```bash
# Stage 02 output is the msp/layer2/ module itself — symlink or note
echo "Stage 02 complete. Output: msp/layer2/ Python module." \
  > msp/workspaces/msp-development/stages/02-context-layer/output/stage-02-complete.md
```

- [ ] **Step 7: Commit**

```bash
git add msp/workspaces/
git commit -m "feat(layer2): create MSP development workspace"
```

---

## Task 8: Final Validation

- [ ] **Step 1: Run full test suite**

```bash
source .venv/bin/activate && python -m pytest tests/ -v
```

Expected: 312 markspace tests + ~23 layer2 tests = 335+ passed, 0 failures.

- [ ] **Step 2: Verify CONTEXT.md files are under 80 lines**

```bash
find msp/workspaces msp/templates -name "CONTEXT.md" | xargs wc -l
```

Expected: all under 80 lines.

- [ ] **Step 3: Verify context loader end-to-end**

```python
# Run in Python REPL:
from pathlib import Path
from msp.layer2.context_loader import ContextLoader

loader = ContextLoader(Path("msp/workspaces/msp-development"))
bundle = loader.load(stage="02-context-layer", token_budget=8000)
print(f"Total tokens: {bundle.total_tokens()}")
print(bundle.as_text()[:500])
```

Expected: total_tokens ≤ 8000, text contains Layer 0 and Layer 2 content.

- [ ] **Step 4: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 5: Update MSP project tracker**

Update `~/Documents/Obsidian Vault/MSP/MSP Project.md`:
- Mark "Begin Layer 2 design" as complete
- Mark "Implement Layer 2 Python module" as complete
- Set current step to "Stage 03: Multi-Provider"

---

## Summary

After completing this plan:
- `msp/layer2/` — Python module with tiered content, stage contracts, workspace navigation, budget-aware loading
- `msp/templates/workspace/` — reusable ICM workspace template
- `msp/workspaces/msp-development/` — actual MSP project workspace
- 335+ tests passing (312 markspace + ~23 layer2)
- Layer 2 ready for Layer 3 (multi-provider adapters) to build on top of
