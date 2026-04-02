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
