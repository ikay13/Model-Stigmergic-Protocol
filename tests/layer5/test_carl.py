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


def _make_intent(topic: str):
    from markspace import Intent
    m = MagicMock(spec=Intent)
    m.action = topic
    m.resource = topic
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
