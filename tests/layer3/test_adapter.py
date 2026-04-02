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


# --- ClaudeAdapter tests ---

from unittest.mock import patch
from msp.layer3.adapters.claude import ClaudeAdapter
from markspace.llm import LLMConfig


def _mock_llm_response(text: str) -> dict:
    """Build a minimal OpenAI-format LLM response."""
    return {
        "choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    }


def test_claude_adapter_provider_name():
    """ClaudeAdapter reports provider_name as 'claude'."""
    config = LLMConfig.anthropic(api_key="test-key", model="claude-sonnet-4-6")
    adapter = ClaudeAdapter(config=config)
    assert adapter.provider_name == "claude"


def test_claude_adapter_parses_json_observations():
    """ClaudeAdapter parses JSON observations from LLM response."""
    config = LLMConfig.anthropic(api_key="test-key", model="claude-sonnet-4-6")
    adapter = ClaudeAdapter(config=config)

    json_response = '''{
  "observations": [
    {"topic": "progress", "content": {"status": "on track"}, "confidence": 0.85}
  ],
  "needs": [],
  "reasoning": "The workspace context shows work is progressing normally."
}'''

    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-01")
    round_ = AgentRound(context="# Workspace", uri=uri, instructions="Assess progress.")

    with patch.object(adapter._client, "chat", return_value=_mock_llm_response(json_response)):
        resp = adapter.run_round(round_)

    assert len(resp.observations) == 1
    assert resp.observations[0]["topic"] == "progress"
    assert resp.observations[0]["confidence"] == 0.85
    assert resp.needs == []
    assert "on track" in resp.raw_text


def test_claude_adapter_parses_needs():
    """ClaudeAdapter parses needs from LLM response."""
    config = LLMConfig.anthropic(api_key="test-key", model="claude-sonnet-4-6")
    adapter = ClaudeAdapter(config=config)

    json_response = '''{
  "observations": [],
  "needs": ["Should we proceed with Stage 03 now?"],
  "reasoning": "Stage 02 is complete but I need direction on timing."
}'''

    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-01")
    round_ = AgentRound(context="ctx", uri=uri, instructions="What next?")

    with patch.object(adapter._client, "chat", return_value=_mock_llm_response(json_response)):
        resp = adapter.run_round(round_)

    assert resp.needs == ["Should we proceed with Stage 03 now?"]
    assert resp.observations == []


def test_claude_adapter_handles_malformed_json():
    """ClaudeAdapter returns raw text when LLM response is not valid JSON."""
    config = LLMConfig.anthropic(api_key="test-key", model="claude-sonnet-4-6")
    adapter = ClaudeAdapter(config=config)

    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-01")
    round_ = AgentRound(context="ctx", uri=uri, instructions="go")

    with patch.object(adapter._client, "chat", return_value=_mock_llm_response("Not valid JSON at all.")):
        resp = adapter.run_round(round_)

    # Graceful degradation: no observations/needs, raw text preserved
    assert resp.observations == []
    assert resp.needs == []
    assert resp.raw_text == "Not valid JSON at all."
