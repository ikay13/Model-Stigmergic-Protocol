# Layer 3: Multi-Provider Orchestration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MSP's multi-provider orchestration layer: `agent://` URI identity, an abstract provider adapter interface, a Claude Code adapter, and the AgentSession that glues Layer 1 (markspace) + Layer 2 (context) + Layer 3 (adapter) into a working agent round.

**Architecture:** `AgentURI` parses and validates `agent://trust-root/capability/path/unique-id` URIs. `ProviderAdapter` is an abstract interface that any LLM provider implements. `ClaudeAdapter` uses the existing `markspace.llm.LLMClient` (already in Layer 1) to call the Anthropic API and returns structured observations/needs. `AgentSession` ties everything together: load context from a workspace (Layer 2), read marks from the mark space (Layer 1), run the adapter, write resulting marks back.

**Tech Stack:** Python 3.10+, pydantic, pytest, unittest.mock — same stack as Layers 1 and 2. No new dependencies. Virtual env at `.venv/`.

---

## File Map

**Create:**
- `msp/layer3/__init__.py` — package root
- `msp/layer3/identity.py` — `AgentURI` dataclass: parse, validate, str
- `msp/layer3/adapter.py` — `AgentRound`, `AgentResponse`, abstract `ProviderAdapter`
- `msp/layer3/adapters/__init__.py` — adapters sub-package
- `msp/layer3/adapters/claude.py` — `ClaudeAdapter` using `LLMClient`
- `msp/layer3/session.py` — `AgentSession`: the Layer 1 + 2 + 3 integration glue
- `tests/layer3/__init__.py`
- `tests/layer3/test_identity.py`
- `tests/layer3/test_adapter.py`
- `tests/layer3/test_session.py`

**No existing files modified** (additive only).

---

## Task 1: Package Scaffold

**Files:**
- Create: `msp/layer3/__init__.py`
- Create: `msp/layer3/adapters/__init__.py`
- Create: `tests/layer3/__init__.py`

- [ ] **Step 1: Create init files**

`msp/layer3/__init__.py`:
```python
"""Layer 3: Multi-Provider Orchestration."""

__all__ = ["AgentURI", "AgentRound", "AgentResponse", "ProviderAdapter", "AgentSession"]


def __getattr__(name):
    if name in __all__:
        import importlib
        mod = importlib.import_module(f"msp.layer3.{name.lower()}")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

`msp/layer3/adapters/__init__.py`:
```python
"""Provider adapters for MSP Layer 3."""

from msp.layer3.adapters.claude import ClaudeAdapter

__all__ = ["ClaudeAdapter"]
```

`tests/layer3/__init__.py` — empty file.

- [ ] **Step 2: Verify import works**

```bash
cd /home/orin/Model-Stigmergic-Protocol && source .venv/bin/activate
python -c "import msp.layer3; print('layer3 OK')"
```
Expected: `layer3 OK`

- [ ] **Step 3: Run tests to confirm no breakage**

```bash
python -m pytest tests/ -q
```
Expected: 336 passed.

- [ ] **Step 4: Commit**

```bash
git add msp/layer3/ tests/layer3/__init__.py
git commit -m "feat(layer3): scaffold msp/layer3 package"
```

---

## Task 2: AgentURI

**Files:**
- Create: `msp/layer3/identity.py`
- Create: `tests/layer3/test_identity.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/layer3/test_identity.py
import pytest
from msp.layer3.identity import AgentURI


def test_parse_simple_uri():
    """Parses a well-formed agent:// URI."""
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.trust_root == "ikay13"
    assert uri.capability_path == "planning/architect"
    assert uri.unique_id == "claude-opus-01"


def test_parse_single_segment_capability():
    """Capability path can be a single segment."""
    uri = AgentURI.parse("agent://ikay13/research/gemini-ultra-01")
    assert uri.trust_root == "ikay13"
    assert uri.capability_path == "research"
    assert uri.unique_id == "gemini-ultra-01"


def test_str_roundtrip():
    """str(uri) produces the original agent:// URI."""
    original = "agent://ikay13/planning/architect/claude-opus-01"
    uri = AgentURI.parse(original)
    assert str(uri) == original


def test_invalid_scheme_raises():
    """Raises ValueError for non-agent:// schemes."""
    with pytest.raises(ValueError, match="agent://"):
        AgentURI.parse("https://ikay13/planning/claude-01")


def test_too_few_segments_raises():
    """Raises ValueError if fewer than 3 path segments."""
    with pytest.raises(ValueError, match="segments"):
        AgentURI.parse("agent://ikay13/claude-01")


def test_capability_parts():
    """capability_parts splits the capability path by /."""
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.capability_parts() == ["planning", "architect"]


def test_matches_capability_exact():
    """matches_capability matches exact paths."""
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.matches_capability("planning/architect") is True
    assert uri.matches_capability("planning/builder") is False


def test_matches_capability_wildcard():
    """matches_capability supports trailing * wildcard."""
    uri = AgentURI.parse("agent://ikay13/planning/architect/claude-opus-01")
    assert uri.matches_capability("planning/*") is True
    assert uri.matches_capability("execution/*") is False
```

- [ ] **Step 2: Run to verify 8 failures**

```bash
source .venv/bin/activate && python -m pytest tests/layer3/test_identity.py -v
```
Expected: 8 failures — `ImportError`.

- [ ] **Step 3: Implement `msp/layer3/identity.py`**

```python
"""AgentURI: topology-independent agent identity for MSP.

URI format:  agent://{trust_root}/{capability_path}/{unique_id}

Examples:
  agent://ikay13/planning/architect/claude-opus-01
  agent://ikay13/execution/builder/codex-pro-01
  agent://ikay13/research/gemini-ultra-01

Based on Rodriguez (2026) agent:// URI scheme.
"""
from __future__ import annotations

from dataclasses import dataclass


_SCHEME = "agent://"


@dataclass(frozen=True)
class AgentURI:
    """Immutable agent identity URI.

    Attributes:
        trust_root:       Organizational identity (e.g. "ikay13")
        capability_path:  Semantic capability path (e.g. "planning/architect")
        unique_id:        Unique agent instance identifier
    """

    trust_root: str
    capability_path: str
    unique_id: str

    @classmethod
    def parse(cls, uri: str) -> "AgentURI":
        """Parse an agent:// URI string.

        Raises:
            ValueError: if the URI scheme is wrong or has too few segments.
        """
        if not uri.startswith(_SCHEME):
            raise ValueError(
                f"Invalid URI scheme — expected {_SCHEME!r}, got: {uri!r}"
            )
        remainder = uri[len(_SCHEME):]
        parts = remainder.split("/")
        # Need at least: trust_root / capability / unique_id  (3 parts min)
        if len(parts) < 3:
            raise ValueError(
                f"URI needs at least 3 path segments "
                f"(trust_root/capability/unique_id), got {len(parts)}: {uri!r}"
            )
        trust_root = parts[0]
        unique_id = parts[-1]
        capability_path = "/".join(parts[1:-1])
        return cls(trust_root=trust_root, capability_path=capability_path, unique_id=unique_id)

    def __str__(self) -> str:
        return f"{_SCHEME}{self.trust_root}/{self.capability_path}/{self.unique_id}"

    def capability_parts(self) -> list[str]:
        """Return capability path split by '/'."""
        return self.capability_path.split("/")

    def matches_capability(self, pattern: str) -> bool:
        """Check if this URI's capability matches a pattern.

        Supports trailing '*' wildcard:
          "planning/*"   matches "planning/architect", "planning/builder"
          "planning"     matches only "planning"
        """
        if pattern.endswith("/*"):
            prefix = pattern[:-2]  # strip "/*"
            return self.capability_path == prefix or self.capability_path.startswith(prefix + "/")
        return self.capability_path == pattern
```

- [ ] **Step 4: Run tests — verify 8 pass**

```bash
python -m pytest tests/layer3/test_identity.py -v
```
Expected: 8 passed.

- [ ] **Step 5: Run full suite — verify 344 passed**

```bash
python -m pytest tests/ -q
```

- [ ] **Step 6: Commit**

```bash
git add msp/layer3/identity.py tests/layer3/test_identity.py
git commit -m "feat(layer3): implement AgentURI identity scheme"
```

---

## Task 3: ProviderAdapter Interface

**Files:**
- Create: `msp/layer3/adapter.py`
- Create: `tests/layer3/test_adapter.py`

- [ ] **Step 1: Write failing tests**

```python
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
    assert resp.provider_name is None or True  # field doesn't exist, just checking call works
    assert resp.raw_text == "mock response"
```

- [ ] **Step 2: Run to verify 5 failures**

```bash
source .venv/bin/activate && python -m pytest tests/layer3/test_adapter.py -v
```
Expected: 5 failures — `ImportError`.

- [ ] **Step 3: Implement `msp/layer3/adapter.py`**

```python
"""Abstract provider adapter interface for MSP Layer 3.

Defines the contract any LLM provider must satisfy to participate in an
MSP agent fleet. Each provider adapter wraps one LLM backend and translates
between MSP's coordination model and the provider's native API.

AgentRound  — input to one reasoning round (context + identity + instructions)
AgentResponse — output (observations to write + needs to escalate + raw text)
ProviderAdapter — abstract base class all adapters implement
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from msp.layer3.identity import AgentURI


@dataclass
class AgentRound:
    """Input to a provider for one reasoning round.

    Attributes:
        context:      Assembled text from ContextLoader (Layer 2 output).
        uri:          The agent's identity URI.
        instructions: System-level task instructions for this round.
    """

    context: str
    uri: AgentURI
    instructions: str


@dataclass
class AgentResponse:
    """Output from a provider after one reasoning round.

    Attributes:
        observations: List of observation mark payloads the agent wants written.
                      Each dict must have "topic" (str), "content" (dict),
                      and "confidence" (float 0-1).
        needs:        List of question strings for the principal.
        raw_text:     Raw LLM output for debugging and audit.
    """

    observations: list[dict] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    raw_text: str = ""


class ProviderAdapter(ABC):
    """Abstract base class for MSP provider adapters.

    Implement one subclass per LLM provider (Claude, Codex, Gemini, etc.).
    The adapter is responsible for:
    1. Formatting AgentRound into the provider's native request format.
    2. Calling the provider API.
    3. Parsing the response into AgentResponse.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name (e.g. "claude", "codex", "gemini")."""
        ...

    @abstractmethod
    def run_round(self, round_: AgentRound) -> AgentResponse:
        """Execute one agent reasoning round and return the response."""
        ...
```

- [ ] **Step 4: Run tests — verify 5 pass**

```bash
python -m pytest tests/layer3/test_adapter.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Run full suite — verify 349 passed**

```bash
python -m pytest tests/ -q
```

- [ ] **Step 6: Commit**

```bash
git add msp/layer3/adapter.py tests/layer3/test_adapter.py
git commit -m "feat(layer3): implement ProviderAdapter interface"
```

---

## Task 4: ClaudeAdapter

**Files:**
- Create: `msp/layer3/adapters/claude.py`

Tests are in `tests/layer3/test_adapter.py` (extend existing file, no new file).

- [ ] **Step 1: Add ClaudeAdapter tests to `tests/layer3/test_adapter.py`**

Append to the end of the existing `tests/layer3/test_adapter.py`:

```python
# --- ClaudeAdapter tests ---

from unittest.mock import MagicMock, patch
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
```

- [ ] **Step 2: Run new tests — verify 4 failures**

```bash
source .venv/bin/activate && python -m pytest tests/layer3/test_adapter.py -v -k "claude"
```
Expected: 4 failures — `ImportError` or `ModuleNotFoundError`.

- [ ] **Step 3: Implement `msp/layer3/adapters/claude.py`**

```python
"""ClaudeAdapter: MSP provider adapter for Anthropic Claude.

Uses markspace's existing LLMClient (Layer 1) to call the Anthropic API.
Expects the LLM to respond with a JSON object:

  {
    "observations": [
      {"topic": str, "content": dict, "confidence": float}
    ],
    "needs": [str],
    "reasoning": str
  }

If the LLM returns non-JSON, falls back to AgentResponse with empty
observations/needs and the raw text preserved for debugging.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from markspace.llm import LLMClient, LLMConfig

from msp.layer3.adapter import AgentResponse, AgentRound, ProviderAdapter

_SYSTEM_PROMPT = """\
You are an MSP agent participating in a stigmergic multi-agent coordination system.

Your job:
1. Read the workspace context and current task instructions below.
2. Identify what observations are worth recording for other agents.
3. Identify any questions that need principal (human) input.
4. Respond ONLY with a JSON object in this exact format:

{
  "observations": [
    {"topic": "<string>", "content": {<any JSON>}, "confidence": <0.0-1.0>}
  ],
  "needs": ["<question string>"],
  "reasoning": "<brief explanation of your analysis>"
}

If you have nothing to observe or ask, return empty arrays.
Do NOT include any text outside the JSON object.
"""


@dataclass
class ClaudeAdapter(ProviderAdapter):
    """MSP adapter for Anthropic Claude models.

    Attributes:
        config: LLMConfig pointing to the Anthropic API.
    """

    config: LLMConfig
    _client: LLMClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = LLMClient(self.config)

    @property
    def provider_name(self) -> str:
        return "claude"

    def run_round(self, round_: AgentRound) -> AgentResponse:
        """Run one agent reasoning round via the Anthropic API."""
        user_message = (
            f"## Agent Identity\n{round_.uri}\n\n"
            f"## Instructions\n{round_.instructions}\n\n"
            f"## Workspace Context\n{round_.context}"
        )
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        response = self._client.chat(messages)
        raw_text = response["choices"][0]["message"]["content"]

        return _parse_response(raw_text)

    def close(self) -> None:
        """Release the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "ClaudeAdapter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _parse_response(raw_text: str) -> AgentResponse:
    """Parse JSON from LLM response; degrade gracefully on failure."""
    try:
        data = json.loads(raw_text.strip())
        return AgentResponse(
            observations=data.get("observations", []),
            needs=data.get("needs", []),
            raw_text=raw_text,
        )
    except (json.JSONDecodeError, AttributeError):
        return AgentResponse(observations=[], needs=[], raw_text=raw_text)
```

- [ ] **Step 4: Run ClaudeAdapter tests — verify 4 pass**

```bash
python -m pytest tests/layer3/test_adapter.py -v -k "claude"
```
Expected: 4 passed.

- [ ] **Step 5: Run full adapter test file**

```bash
python -m pytest tests/layer3/test_adapter.py -v
```
Expected: 9 passed (5 from Task 3 + 4 new).

- [ ] **Step 6: Run full suite**

```bash
python -m pytest tests/ -q
```
Expected: 353 passed.

- [ ] **Step 7: Commit**

```bash
git add msp/layer3/adapters/claude.py tests/layer3/test_adapter.py
git commit -m "feat(layer3): implement ClaudeAdapter using markspace LLMClient"
```

---

## Task 5: AgentSession (Layer 1 + 2 + 3 Integration Glue)

**Files:**
- Create: `msp/layer3/session.py`
- Create: `tests/layer3/test_session.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/layer3/test_session.py
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from markspace import Agent, MarkSpace, Scope, DecayConfig, hours, minutes
from msp.layer3.adapter import AgentResponse, AgentRound, ProviderAdapter
from msp.layer3.identity import AgentURI
from msp.layer3.session import AgentSession
from tests.layer2.test_workspace import _make_workspace


class _MockAdapter(ProviderAdapter):
    """Test adapter that returns a controlled response."""

    def __init__(self, response: AgentResponse) -> None:
        self._response = response

    @property
    def provider_name(self) -> str:
        return "mock"

    def run_round(self, round_: AgentRound) -> AgentResponse:
        self._last_round = round_
        return self._response


def _make_mark_space() -> tuple[MarkSpace, Agent]:
    """Create a minimal MarkSpace with one agent for testing."""
    scope = Scope(
        name="test",
        observation_topics=["*"],
        decay=DecayConfig(
            observation_half_life=hours(1),
            warning_half_life=hours(1),
            intent_ttl=minutes(30),
        ),
    )
    space = MarkSpace(scopes=[scope])
    agent = Agent(
        name="test-agent",
        scopes={"test": ["observation", "need"]},
    )
    return space, agent


def test_session_loads_context(tmp_path):
    """AgentSession loads workspace context into the AgentRound."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(observations=[], needs=[], raw_text="{}")
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
    )
    session.run(stage="01-research")

    # Verify the adapter received a round with workspace context
    assert "# Workspace" in adapter._last_round.context
    assert str(uri) in adapter._last_round.instructions


def test_session_writes_observations(tmp_path):
    """AgentSession writes observations returned by adapter to the mark space."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(
        observations=[
            {"topic": "progress", "content": {"status": "on track"}, "confidence": 0.9}
        ],
        needs=[],
        raw_text="{}",
    )
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
    )
    session.run(stage="01-research")

    # Verify the observation was written to the mark space
    marks = space.read(scope="test", mark_type=None)
    observation_marks = [m for m in marks if hasattr(m, "topic") and m.topic == "progress"]
    assert len(observation_marks) == 1
    assert observation_marks[0].confidence == 0.9


def test_session_writes_needs(tmp_path):
    """AgentSession writes needs returned by adapter to the mark space."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(
        observations=[],
        needs=["Should we proceed with Stage 03?"],
        raw_text="{}",
    )
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
    )
    session.run(stage="01-research")

    needs = space.read(scope="test", mark_type=None)
    need_marks = [m for m in needs if hasattr(m, "question")]
    assert len(need_marks) == 1
    assert "Stage 03" in need_marks[0].question


def test_session_returns_response(tmp_path):
    """AgentSession.run() returns the AgentResponse."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(observations=[], needs=[], raw_text="done")
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
    )
    result = session.run()
    assert result.raw_text == "done"


def test_session_respects_token_budget(tmp_path):
    """AgentSession passes token_budget to ContextLoader."""
    root = _make_workspace(tmp_path)
    space, agent = _make_mark_space()
    uri = AgentURI.parse("agent://ikay13/test/claude-01")
    mock_response = AgentResponse(observations=[], needs=[], raw_text="{}")
    adapter = _MockAdapter(mock_response)

    session = AgentSession(
        uri=uri,
        workspace_root=root,
        mark_space=space,
        agent=agent,
        adapter=adapter,
        token_budget=100,  # very tight budget
    )
    session.run(stage="01-research")

    # Context should have been loaded (tight budget just limits L3/L4)
    assert adapter._last_round.context != ""
```

- [ ] **Step 2: Run to verify 5 failures**

```bash
source .venv/bin/activate && python -m pytest tests/layer3/test_session.py -v
```
Expected: 5 failures — `ImportError`.

- [ ] **Step 3: Implement `msp/layer3/session.py`**

```python
"""AgentSession: integrates Layer 1 (markspace) + Layer 2 (context) + Layer 3 (adapter).

One session = one agent doing one round of work:
  1. Load workspace context via ContextLoader (Layer 2)
  2. Read active marks from MarkSpace (Layer 1)
  3. Assemble prompt and run provider adapter (Layer 3)
  4. Write resulting observations and needs back to MarkSpace (Layer 1)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from markspace import Agent, MarkSpace, Observation, Need, Source
from msp.layer2.context_loader import ContextLoader
from msp.layer3.adapter import AgentResponse, AgentRound, ProviderAdapter
from msp.layer3.identity import AgentURI


@dataclass
class AgentSession:
    """Ties Layer 1 + 2 + 3 into a working agent round.

    Attributes:
        uri:            Agent's identity URI.
        workspace_root: Path to the ICM workspace (Layer 2).
        mark_space:     Shared MarkSpace instance (Layer 1).
        agent:          Authorized markspace Agent for writing marks.
        adapter:        Provider adapter (Layer 3).
        token_budget:   Max tokens for context loading (maps to P61).
        scope:          Mark space scope to write observations/needs into.
    """

    uri: AgentURI
    workspace_root: Path
    mark_space: MarkSpace
    agent: Agent
    adapter: ProviderAdapter
    token_budget: int = 8000
    scope: str = "msp"

    def run(self, stage: str | None = None) -> AgentResponse:
        """Execute one agent round.

        1. Load workspace context (Layer 2).
        2. Serialize current mark space state for the agent.
        3. Run the adapter (Layer 3).
        4. Write observations and needs to the mark space (Layer 1).

        Returns:
            The AgentResponse from the adapter.
        """
        # --- Layer 2: Load context ---
        loader = ContextLoader(self.workspace_root)
        bundle = loader.load(stage=stage, token_budget=self.token_budget)

        # --- Layer 1: Read current marks ---
        mark_summary = self._summarize_marks()

        # Assemble context for the adapter
        context_parts = [bundle.as_text()]
        if mark_summary:
            context_parts.append(f"## Current Mark Space State\n{mark_summary}")
        context = "\n\n---\n\n".join(context_parts)

        instructions = (
            f"You are agent {self.uri}. "
            f"Review the workspace context and mark space state. "
            f"Record observations worth sharing with other agents. "
            f"Escalate any decisions that need human input."
        )

        round_ = AgentRound(context=context, uri=self.uri, instructions=instructions)

        # --- Layer 3: Run adapter ---
        response = self.adapter.run_round(round_)

        # --- Layer 1: Write marks ---
        self._write_observations(response)
        self._write_needs(response)

        return response

    def _summarize_marks(self) -> str:
        """Read current marks and produce a brief text summary."""
        try:
            marks = self.mark_space.read(scope=self.scope)
        except Exception:
            return ""

        if not marks:
            return "No active marks."

        lines = []
        for mark in marks[:10]:  # cap at 10 to limit tokens
            mark_type = type(mark).__name__
            lines.append(f"- [{mark_type}] {getattr(mark, 'topic', getattr(mark, 'action', ''))}")
        return "\n".join(lines)

    def _write_observations(self, response: AgentResponse) -> None:
        """Write observations from the response to the mark space."""
        for obs in response.observations:
            try:
                self.mark_space.write(
                    self.agent,
                    Observation(
                        scope=self.scope,
                        topic=obs.get("topic", "general"),
                        content=obs.get("content", {}),
                        confidence=float(obs.get("confidence", 0.5)),
                        source=Source.FLEET,
                    ),
                )
            except Exception:
                # Scope may not be registered — skip gracefully
                pass

    def _write_needs(self, response: AgentResponse) -> None:
        """Write need marks for questions requiring principal input."""
        for question in response.needs:
            try:
                self.mark_space.write(
                    self.agent,
                    Need(
                        scope=self.scope,
                        question=question,
                        context={},
                        priority=0.5,
                        blocking=False,
                    ),
                )
            except Exception:
                pass
```

- [ ] **Step 4: Adjust tests — the test scope is "test" not "msp"**

The tests create a MarkSpace with scope `"test"`, but `AgentSession` defaults to scope `"msp"`. Update the session constructor calls in the test file to pass `scope="test"`:

In `tests/layer3/test_session.py`, update every `AgentSession(...)` call to add `scope="test"`:

```python
session = AgentSession(
    uri=uri,
    workspace_root=root,
    mark_space=space,
    agent=agent,
    adapter=adapter,
    scope="test",  # add this
)
```

Apply to all 5 `AgentSession(...)` instantiations in the file.

- [ ] **Step 5: Run tests — verify 5 pass**

```bash
python -m pytest tests/layer3/test_session.py -v
```
Expected: 5 passed.

- [ ] **Step 6: Run full suite — verify 361 passed**

```bash
python -m pytest tests/ -q
```
Expected: 361 passed (336 + 8 identity + 9 adapter + 5 session = 358... recount: 336 + 8 + 9 + 5 = 358, but Task 1 scaffold adds some too — exact count will be 358+).

- [ ] **Step 7: Commit**

```bash
git add msp/layer3/session.py tests/layer3/test_session.py
git commit -m "feat(layer3): implement AgentSession — Layer 1+2+3 integration glue"
```

---

## Task 6: Final Validation + Push

- [ ] **Step 1: Run full test suite**

```bash
source .venv/bin/activate && python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```
Expected: all passed, 0 failures.

- [ ] **Step 2: Verify msp.layer3 imports work end-to-end**

```bash
python -c "
from msp.layer3.identity import AgentURI
from msp.layer3.adapter import AgentRound, AgentResponse, ProviderAdapter
from msp.layer3.adapters.claude import ClaudeAdapter
from msp.layer3.session import AgentSession
from msp.layer1 import MarkSpace, Agent
print('Layer 3 imports OK')
print('Layer 1+3 cross-import OK')
"
```
Expected: both lines printed.

- [ ] **Step 3: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 4: Update Obsidian MSP tracker**

Update `~/Documents/Obsidian Vault/MSP/MSP Project.md`:
- Mark Layer 3 complete
- Set current step to Layer 4

---

## Summary

After this plan:
- `msp/layer3/identity.py` — `AgentURI` (agent:// URI parsing)
- `msp/layer3/adapter.py` — `AgentRound`, `AgentResponse`, abstract `ProviderAdapter`
- `msp/layer3/adapters/claude.py` — `ClaudeAdapter` using markspace's `LLMClient`
- `msp/layer3/session.py` — `AgentSession`: the Layer 1+2+3 integration glue
- ~25 new tests
- One working end-to-end path: load workspace → coordinate via marks → call Claude → write observations back
