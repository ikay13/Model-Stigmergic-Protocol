"""Tests for ContextAugmentation (CARL) — intent detection and JIT rule injection."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from msp.layer5.carl import ContextAugmentation


RULES_DIR = Path(__file__).parent.parent.parent / "msp" / "layer5" / "rules"


@pytest.fixture
def carl():
    ms = MagicMock()
    loader = MagicMock()
    loader.load.return_value = MagicMock(references=[], as_text=MagicMock(return_value=""))
    agent = MagicMock()
    return ContextAugmentation(markspace=ms, loader=loader, rules_dir=RULES_DIR, agent=agent)


def _make_intent(topic: str, created_at: float = 0.0):
    from markspace import Intent
    m = MagicMock(spec=Intent)
    m.action = topic
    m.resource = topic
    m.created_at = created_at
    return m


def test_detect_domains_development_keywords(carl):
    marks = [_make_intent("implement the feature with TDD")]
    domains = carl.detect_domains(marks)
    assert "development" in domains


def test_detect_domains_debugging_keywords(carl):
    marks = [_make_intent("fix the bug in the auth module")]
    domains = carl.detect_domains(marks)
    assert "debugging" in domains


def test_detect_domains_stigmergy_keywords(carl):
    marks = [_make_intent("coordinate agents via marks")]
    domains = carl.detect_domains(marks)
    assert "stigmergy" in domains


def test_detect_domains_no_match_returns_empty(carl):
    marks = [_make_intent("xyzzy frobnicator")]
    domains = carl.detect_domains(marks)
    assert domains == []


def test_load_rules_resolves_existing_paths(carl):
    paths = carl.load_rules(["development", "debugging"])
    assert all(p.exists() for p in paths)
    assert len(paths) == 2


def test_load_rules_ignores_missing_domains(carl):
    paths = carl.load_rules(["development", "nonexistent_domain"])
    assert len(paths) == 1


def test_inject_returns_augmented_config(carl):
    marks = [_make_intent("implement the feature")]
    carl.markspace.read.return_value = marks
    config = carl.inject({"session_id": "s1"})
    assert "session_id" in config
    assert "carl_domains" in config


def test_inject_emits_observation_mark(carl):
    marks = [_make_intent("fix the bug")]
    carl.markspace.read.return_value = marks
    carl.inject({"session_id": "s1"})
    assert carl.markspace.write.called


def test_no_domain_scores_negative(carl):
    """All domain scores are >= 0 for any input."""
    marks = [_make_intent("some random task description here")]
    scores = carl._score_domains(marks)
    assert all(v >= 0 for v in scores.values())


def test_inject_filters_stale_intent_marks():
    """Stale Intent marks (created_at older than max_age) are excluded from domain detection."""
    import time
    from markspace import Intent
    from msp.layer5.carl import ContextAugmentation

    ms = MagicMock()
    loader = MagicMock()
    loader.load.return_value = MagicMock(references=[], as_text=MagicMock(return_value=""))
    agent = MagicMock()

    carl = ContextAugmentation(
        markspace=ms, loader=loader, rules_dir=RULES_DIR, agent=agent, max_age=3600.0
    )

    # Stale mark: created 2 hours ago
    stale = MagicMock(spec=Intent)
    stale.action = "fix the bug"
    stale.resource = "fix the bug"
    stale.created_at = time.time() - 7200.0  # 2 hours ago

    # Fresh mark with created_at=0.0 (backward-compat sentinel — treated as fresh)
    fresh = MagicMock(spec=Intent)
    fresh.action = "implement the feature"
    fresh.resource = "implement the feature"
    fresh.created_at = 0.0

    ms.read.return_value = [stale, fresh]
    config = carl.inject({"session_id": "s1"})

    domains = config["carl_domains"]
    assert "development" in domains, "fresh mark's domain should be present"
    assert "debugging" not in domains, "stale mark's domain should be filtered out"


def test_inject_keeps_zero_created_at_marks():
    """Marks with created_at=0.0 are never filtered — backward-compat with mocked/test marks."""
    import time
    from markspace import Intent
    from msp.layer5.carl import ContextAugmentation

    ms = MagicMock()
    loader = MagicMock()
    loader.load.return_value = MagicMock(references=[], as_text=MagicMock(return_value=""))
    agent = MagicMock()

    carl = ContextAugmentation(
        markspace=ms, loader=loader, rules_dir=RULES_DIR, agent=agent, max_age=1.0  # very short window
    )

    # Mark with created_at=0.0 — should always survive the filter
    zero_mark = MagicMock(spec=Intent)
    zero_mark.action = "research the topic"
    zero_mark.resource = "research the topic"
    zero_mark.created_at = 0.0

    ms.read.return_value = [zero_mark]
    config = carl.inject({"session_id": "s2"})

    assert "research" in config["carl_domains"], "zero created_at mark must not be filtered"
