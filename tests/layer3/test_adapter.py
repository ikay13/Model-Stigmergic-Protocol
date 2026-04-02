# tests/layer3/test_adapter.py
import pytest
from msp.layer3.adapter import AgentRound, AgentResponse, ProviderAdapter
from msp.layer3.identity import AgentURI


def test_agent_round_fields():
    """AgentRound holds context, URI, and instructions."""
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-01")
    round_ = AgentRound(
        context="# Workspace\nSome context here.",
        uri=uri,
        instructions="Analyze the current marks and write an observation.",
    )
    assert round_.context == "# Workspace\nSome context here."
    assert round_.uri == uri
    assert round_.instructions == "Analyze the current marks and write an observation."


def test_agent_response_fields():
    """AgentResponse holds observations, needs, and raw text."""
    resp = AgentResponse(
        observations=[{"topic": "progress", "content": {"status": "ok"}, "confidence": 0.9}],
        needs=[],
        raw_text="I observed that progress is on track.",
    )
    assert len(resp.observations) == 1
    assert resp.observations[0]["topic"] == "progress"
    assert resp.needs == []
    assert "progress" in resp.raw_text


def test_provider_adapter_is_abstract():
    """ProviderAdapter cannot be instantiated directly."""
    with pytest.raises(TypeError):
        ProviderAdapter()


def test_concrete_adapter_must_implement_run_round():
    """A concrete adapter that doesn't implement run_round raises TypeError."""
    class IncompleteAdapter(ProviderAdapter):
        @property
        def provider_name(self) -> str:
            return "incomplete"
        # missing: run_round

    with pytest.raises(TypeError):
        IncompleteAdapter()


def test_concrete_adapter_works():
    """A fully implemented adapter can be instantiated and called."""
    class MockAdapter(ProviderAdapter):
        @property
        def provider_name(self) -> str:
            return "mock"

        def run_round(self, round_: AgentRound) -> AgentResponse:
            return AgentResponse(
                observations=[{"topic": "test", "content": {}, "confidence": 1.0}],
                needs=[],
                raw_text="mock response",
            )

    adapter = MockAdapter()
    uri = AgentURI.parse("agent://ikay13/test/mock-01")
    round_ = AgentRound(context="ctx", uri=uri, instructions="go")
    resp = adapter.run_round(round_)
    assert resp.raw_text == "mock response"
