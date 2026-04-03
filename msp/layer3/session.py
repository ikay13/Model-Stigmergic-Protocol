"""AgentSession: integrates Layer 1 (markspace) + Layer 2 (context) + Layer 3 (adapter).

One session = one agent doing one round of work:
  1. Load workspace context via ContextLoader (Layer 2)
  2. Import prior PSMM state into context (Layer 5, optional)
  3. Read active marks from MarkSpace (Layer 1)
  4. Assemble prompt and run provider adapter (Layer 3)
  5. Write resulting observations and needs back to MarkSpace (Layer 1)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from markspace import Agent, MarkSpace, Observation, Need, Source
from msp.layer2.context_loader import ContextLoader
from msp.layer3.adapter import AgentResponse, AgentRound, ProviderAdapter
from msp.layer3.identity import AgentURI

if TYPE_CHECKING:
    from msp.layer5.base import WorkspaceState


@dataclass
class AgentSession:
    """Ties Layer 1 + 2 + 3 into a working agent round.

    Attributes:
        uri:              Agent's identity URI.
        workspace_root:   Path to the ICM workspace (Layer 2).
        mark_space:       Shared MarkSpace instance (Layer 1).
        agent:            Authorized markspace Agent for writing marks.
        adapter:          Provider adapter (Layer 3).
        token_budget:     Max tokens for context loading (maps to P61).
        scope:            Mark space scope to write observations/needs into.
        workspace_state:  Optional WorkspaceState for PSMM import at session start.
    """

    uri: AgentURI
    workspace_root: Path
    mark_space: MarkSpace
    agent: Agent
    adapter: ProviderAdapter
    token_budget: int = 8000
    scope: str = "msp"
    workspace_state: "WorkspaceState | None" = None

    def run(self, stage: str | None = None) -> AgentResponse:
        """Execute one agent round.

        1. Load workspace context (Layer 2).
        2. Import prior PSMM state into context (if workspace_state provided).
        3. Serialize current mark space state for the agent.
        4. Run the adapter (Layer 3).
        5. Write observations and needs to the mark space (Layer 1).

        Returns:
            The AgentResponse from the adapter.
        """
        # --- Layer 2: Load context ---
        loader = ContextLoader(self.workspace_root)
        bundle = loader.load(stage=stage, token_budget=self.token_budget)

        # --- PSMM: Inject prior session memory ---
        psmm_section = self._import_psmm()

        # --- Layer 1: Read current marks ---
        mark_summary = self._summarize_marks()

        # Assemble context for the adapter
        context_parts = [bundle.as_text()]
        if psmm_section:
            context_parts.append(psmm_section)
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

    def _import_psmm(self) -> str:
        """Read prior PSMM state and format it as a context section.

        Returns empty string if no workspace_state or no prior PSMM exists.
        """
        if self.workspace_state is None:
            return ""
        psmm = self.workspace_state.psmm_read()
        if not psmm:
            return ""

        lines = ["## Prior Session Memory (PSMM)"]
        if psmm.get("session_id"):
            lines.append(f"**Last agent:** {psmm['session_id']}")
        if psmm.get("timestamp"):
            lines.append(f"**Last session:** {psmm['timestamp']}")
        if psmm.get("scope"):
            lines.append(f"**Scope:** {psmm['scope']}")
        if psmm.get("completed_tasks"):
            lines.append(f"**Completed tasks:** {', '.join(psmm['completed_tasks'])}")
        if psmm.get("next_steps"):
            lines.append("**Next steps:**")
            lines.extend(f"  - {s}" for s in psmm["next_steps"])
        if psmm.get("open_needs"):
            lines.append("**Open questions:**")
            lines.extend(f"  - {q}" for q in psmm["open_needs"])
        if psmm.get("mark_summary"):
            ms = psmm["mark_summary"]
            lines.append(
                f"**Mark snapshot:** {ms.get('observations', 0)} observations, "
                f"{ms.get('intents', 0)} intents, {ms.get('actions', 0)} actions"
            )
        if psmm.get("agent_notes"):
            lines.append(f"**Notes:** {psmm['agent_notes']}")
        return "\n".join(lines)

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
            lines.append(f"- [{mark_type}] {getattr(mark, 'topic', getattr(mark, 'question', ''))}")
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
