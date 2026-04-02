import pytest
from msp.layer3.identity import AgentURI


def test_parse_simple_uri():
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.trust_root == "ikay13"
    assert uri.capability_path == "planning/architect"
    assert uri.unique_id == "claude-opus-01"


def test_parse_single_segment_capability():
    uri = AgentURI.parse("agent://ikay13/research/gemini-ultra-01")
    assert uri.trust_root == "ikay13"
    assert uri.capability_path == "research"
    assert uri.unique_id == "gemini-ultra-01"


def test_str_roundtrip():
    original = "agent://ikay13/planning/architect/claude-opus-01"
    assert str(AgentURI.parse(original)) == original


def test_invalid_scheme_raises():
    with pytest.raises(ValueError, match="agent://"):
        AgentURI.parse("https://ikay13/planning/claude-01")


def test_too_few_segments_raises():
    with pytest.raises(ValueError, match="segments"):
        AgentURI.parse("agent://ikay13/claude-01")


def test_capability_parts():
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.capability_parts() == ["planning", "architect"]


def test_matches_capability_exact():
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.matches_capability("planning/architect") is True
    assert uri.matches_capability("planning/builder") is False


def test_matches_capability_wildcard():
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.matches_capability("planning/*") is True
    assert uri.matches_capability("execution/*") is False
